from fastapi.testclient import TestClient

from app.chat import FALLBACK, ChatService
from app.knowledge import Entry, KnowledgeBase
from app.main import create_app


class FakeModel:
    def __init__(self) -> None:
        self.calls: list[list[dict]] = []

    def complete(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        return "Delivery takes 2 to 4 business days."


def make_kb() -> KnowledgeBase:
    return KnowledgeBase([
        Entry("How long does shipping take?", "Delivery takes 2 to 4 business days."),
        Entry("Can I return a product?", "Returns are accepted within 7 days."),
    ])


def test_health_reports_offline_mode():
    client = TestClient(create_app(ChatService(make_kb())))
    assert client.get("/health").json() == {"status": "ok", "mode": "offline"}


def test_offline_mode_answers_from_faq():
    client = TestClient(create_app(ChatService(make_kb())))
    body = client.post("/chat", json={"message": "can I return this product?"}).json()
    assert body["answer"] == "Returns are accepted within 7 days."
    assert body["mode"] == "offline"


def test_offline_mode_falls_back_when_nothing_matches():
    client = TestClient(create_app(ChatService(make_kb())))
    body = client.post("/chat", json={"message": "tell me a joke about cats"}).json()
    assert body["answer"] == FALLBACK


def test_llm_mode_sends_context_and_keeps_history():
    model = FakeModel()
    client = TestClient(create_app(ChatService(make_kb(), model)))

    first = client.post("/chat", json={"message": "how long is shipping?", "session_id": "u1"}).json()
    assert first["mode"] == "llm"
    assert "How long does shipping take?" in first["sources"]
    assert "Delivery takes 2 to 4 business days." in model.calls[0][0]["content"]

    client.post("/chat", json={"message": "and returns?", "session_id": "u1"})
    roles = [message["role"] for message in model.calls[1]]
    assert roles == ["system", "user", "assistant", "user"]


def test_reset_clears_history():
    model = FakeModel()
    client = TestClient(create_app(ChatService(make_kb(), model)))
    client.post("/chat", json={"message": "shipping?", "session_id": "u1"})
    assert client.delete("/chat/u1").status_code == 204
    client.post("/chat", json={"message": "shipping?", "session_id": "u1"})
    assert [m["role"] for m in model.calls[1]] == ["system", "user"]


def test_empty_message_is_rejected():
    client = TestClient(create_app(ChatService(make_kb())))
    assert client.post("/chat", json={"message": ""}).status_code == 422
