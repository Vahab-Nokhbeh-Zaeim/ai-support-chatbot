"""Client for any OpenAI-compatible chat completions API."""

from typing import Protocol

import httpx


class ChatModel(Protocol):
    def complete(self, messages: list[dict]) -> str: ...


class OpenAIChatModel:
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", timeout: float = 30) -> None:
        self.model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def complete(self, messages: list[dict]) -> str:
        response = self._client.post(
            "/chat/completions",
            json={"model": self.model, "messages": messages, "temperature": 0.2},
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
