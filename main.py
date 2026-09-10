#!/usr/bin/env python3
"""Flora — fully local personal companion."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.flora.config import STATIC_DIR, settings
from src.flora.memory import MemoryStore
from src.flora.ollama_client import OllamaClient, OllamaError
from src.flora.persona import build_system_message


store = MemoryStore()
ollama = OllamaClient()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    store.db_path.parent.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Flora", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    reply: str
    new_memories: list[dict[str, str]] = []


class MemoryCreate(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=500)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    ollama_status = await ollama.health()
    return {
        "app": "flora",
        "ok": True,
        "ollama": ollama_status,
        "memory_count": len(store.list_memories()),
    }


@app.get("/api/history")
async def history() -> dict:
    return {"messages": store.recent_messages()}


@app.delete("/api/history")
async def clear_history() -> dict:
    store.clear_messages()
    return {"ok": True}


@app.get("/api/memory")
async def list_memory() -> dict:
    return {"memories": store.list_memories()}


@app.post("/api/memory")
async def create_memory(body: MemoryCreate) -> dict:
    store.upsert_memory(body.key, body.value)
    return {"ok": True, "memories": store.list_memories()}


@app.delete("/api/memory/{key}")
async def delete_memory(key: str) -> dict:
    if not store.delete_memory(key):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"ok": True, "memories": store.list_memories()}


@app.delete("/api/memory")
async def clear_memory() -> dict:
    store.clear_memories()
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    user_text = body.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    memories = store.list_memories()
    history = store.recent_messages()
    messages = [
        {"role": "system", "content": build_system_message(memories)},
        *history,
        {"role": "user", "content": user_text},
    ]

    try:
        reply = await ollama.chat(messages)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    store.add_message("user", user_text)
    store.add_message("assistant", reply)
    new_memories = await store.extract_and_store(user_text, reply, ollama)
    return ChatResponse(reply=reply, new_memories=new_memories)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
