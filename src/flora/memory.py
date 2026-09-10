"""SQLite-backed memory and conversation history for Flora."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from src.flora.config import settings
from src.flora.ollama_client import OllamaClient
from src.flora.persona import MEMORY_EXTRACT_PROMPT


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or settings.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def list_memories(self) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value, updated_at FROM memories ORDER BY key COLLATE NOCASE"
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_memory(self, key: str, value: str) -> None:
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if not key or not value:
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, _utc_now()),
            )

    def delete_memory(self, key: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
            return cur.rowcount > 0

    def clear_memories(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM memories")

    def add_message(self, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, _utc_now()),
            )

    def recent_messages(self, limit: int | None = None) -> list[dict[str, str]]:
        limit = limit or settings.max_history_messages
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def clear_messages(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM messages")

    async def extract_and_store(
        self,
        user_text: str,
        assistant_text: str,
        client: OllamaClient | None = None,
    ) -> list[dict[str, str]]:
        """Ask the local model for new facts and persist them."""
        client = client or OllamaClient()
        prompt = (
            "Extract durable facts about the USER from this USER message only.\n"
            "If the message has no stable personal facts, return [].\n\n"
            f"USER message:\n{user_text}\n"
        )
        try:
            raw = await client.chat(
                [
                    {"role": "system", "content": MEMORY_EXTRACT_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
        except Exception:
            return []

        facts = _parse_facts_json(raw)
        stored: list[dict[str, str]] = []
        for fact in facts:
            key = str(fact.get("key", "")).strip()
            value = str(fact.get("value", "")).strip()
            if not key or not value:
                continue
            if value.lower() in {"unknown", "n/a", "none", "null", "not sure", "unspecified"}:
                continue
            self.upsert_memory(key, value)
            stored.append({"key": key, "value": value})
        return stored


def _parse_facts_json(raw: str) -> list[dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return []

    if not isinstance(data, list):
        return []

    normalized: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "key" in item and "value" in item:
            key = str(item.get("key", "")).strip()
            value = str(item.get("value", "")).strip()
            if key and value and value.lower() not in {"unknown", "n/a", "none", "null"}:
                normalized.append({"key": key, "value": value})
            continue
        # Some small models return {"preferred_name": "Alex"} instead of key/value.
        for key, value in item.items():
            key_s = str(key).strip()
            value_s = str(value).strip()
            if not key_s or not value_s:
                continue
            if key_s.lower() == "flora" or value_s.lower() in {"flora", "unknown", "n/a", "none", "null"}:
                continue
            normalized.append({"key": key_s, "value": value_s})
    return normalized
