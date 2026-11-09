"""FastAPI application exposing the support chatbot."""

import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .chat import ChatService
from .knowledge import KnowledgeBase
from .llm import OpenAIChatModel

DEFAULT_FAQ = Path(__file__).resolve().parent.parent / "data" / "faq.json"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(default="default", max_length=64)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    mode: str


def build_service() -> ChatService:
    knowledge = KnowledgeBase.from_file(os.environ.get("FAQ_PATH", DEFAULT_FAQ))
    api_key = os.environ.get("OPENAI_API_KEY")
    model = None
    if api_key:
        model = OpenAIChatModel(
            api_key=api_key,
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    return ChatService(knowledge, model)


def create_app(service: ChatService | None = None) -> FastAPI:
    app = FastAPI(title="AI Support Chatbot", version="1.0.0")
    chat_service = service or build_service()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "mode": "llm" if chat_service.model else "offline"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        reply = chat_service.ask(request.session_id, request.message.strip())
        return ChatResponse(answer=reply.answer, sources=reply.sources, mode=reply.mode)

    @app.delete("/chat/{session_id}", status_code=204)
    def reset(session_id: str) -> None:
        chat_service.reset(session_id)

    return app


app = create_app()
