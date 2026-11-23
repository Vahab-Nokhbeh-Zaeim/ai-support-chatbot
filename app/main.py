"""FastAPI application exposing the support chatbot."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .chat import ChatService
from .knowledge import KnowledgeBase
from .llm import OpenAIChatModel
from .unanswered import UnansweredLog

DEFAULT_FAQ = Path(__file__).resolve().parent.parent / "data" / "faq.json"
DEFAULT_UNANSWERED_LOG = Path(__file__).resolve().parent.parent / "data" / "unanswered.jsonl"
STATIC_DIR = Path(__file__).resolve().parent / "static"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(default="default", max_length=64)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    mode: str


class UnansweredItem(BaseModel):
    question: str
    count: int
    language: str
    last_asked: str


class UnansweredReport(BaseModel):
    total: int
    questions: list[UnansweredItem]


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
    # Set UNANSWERED_LOG to an empty value to turn the log off.
    log_path = os.environ.get("UNANSWERED_LOG", str(DEFAULT_UNANSWERED_LOG))
    unanswered = UnansweredLog(log_path) if log_path else None
    return ChatService(knowledge, model, unanswered=unanswered)


def create_app(service: ChatService | None = None) -> FastAPI:
    app = FastAPI(title="AI Support Chatbot", version="1.0.0")
    chat_service = service or build_service()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def chat_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "mode": "llm" if chat_service.model else "offline"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        message = request.message.strip()
        session_id = request.session_id.strip()
        if not message or not session_id:
            raise HTTPException(status_code=422, detail="message and session_id must not be blank")
        reply = chat_service.ask(session_id, message)
        return ChatResponse(answer=reply.answer, sources=reply.sources, mode=reply.mode)

    @app.get("/unanswered", response_model=UnansweredReport)
    def unanswered(limit: int = Query(default=20, ge=1, le=200)) -> UnansweredReport:
        log = chat_service.unanswered
        if log is None:
            raise HTTPException(status_code=404, detail="The unanswered-questions log is turned off")
        questions = log.summary(limit)
        return UnansweredReport(
            total=len(log.entries()),
            questions=[UnansweredItem(**vars(question)) for question in questions],
        )

    @app.delete("/chat/{session_id}", status_code=204)
    def reset(session_id: str) -> None:
        chat_service.reset(session_id)

    return app


app = create_app()
