"""Thin async client for the local Ollama HTTP API."""

from __future__ import annotations

import httpx

from src.flora.config import settings


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error."""


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as exc:
            raise OllamaError(
                "Cannot reach Ollama. Install it from https://ollama.com, "
                f"run `ollama serve`, then `ollama pull {self.model}`."
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            raise OllamaError(f"Ollama error ({exc.response.status_code}): {detail}") from exc

        message = data.get("message") or {}
        content = message.get("content")
        if not content:
            raise OllamaError("Ollama returned an empty reply.")
        return content.strip()

    async def health(self) -> dict:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {
                    "ok": True,
                    "base_url": self.base_url,
                    "model": self.model,
                    "models": models,
                    "model_ready": any(
                        name == self.model or name.startswith(f"{self.model}:") for name in models
                    ),
                }
        except Exception as exc:  # noqa: BLE001 — surface health details to UI
            return {
                "ok": False,
                "base_url": self.base_url,
                "model": self.model,
                "error": str(exc),
            }
