from fastapi.testclient import TestClient

from app.chat import FALLBACK, FALLBACK_FA, ChatService
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


def test_persian_question_gets_persian_answer_offline():
    kb = KnowledgeBase([
        Entry("Can I return a product?", "Returns are accepted within 7 days."),
        Entry("آیا امکان مرجوع کردن کالا وجود دارد؟", "بله، تا ۷ روز پس از تحویل."),
    ])
    client = TestClient(create_app(ChatService(kb)))
    body = client.post("/chat", json={"message": "میخوام کالا رو مرجوع کنم"}).json()
    assert body["answer"] == "بله، تا ۷ روز پس از تحویل."


def test_persian_fallback_when_nothing_matches():
    client = TestClient(create_app(ChatService(make_kb())))
    body = client.post("/chat", json={"message": "سلام خوبی؟"}).json()
    assert body["answer"] == FALLBACK_FA


def test_system_prompt_asks_for_same_language():
    model = FakeModel()
    client = TestClient(create_app(ChatService(make_kb(), model)))
    client.post("/chat", json={"message": "shipping?"})
    assert "same language" in model.calls[0][0]["content"]


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


def test_whitespace_message_is_rejected_without_logging(tmp_path):
    from app.unanswered import UnansweredLog

    log = UnansweredLog(tmp_path / "unanswered.jsonl")
    client = TestClient(create_app(ChatService(make_kb(), unanswered=log)))
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422
    assert log.entries() == []


def test_blank_session_id_is_rejected():
    client = TestClient(create_app(ChatService(make_kb())))
    assert client.post("/chat", json={"message": "shipping", "session_id": "   "}).status_code == 422


def test_homepage_serves_chat_interface():
    client = TestClient(create_app(ChatService(make_kb())))
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="chat-form"' in response.text
    assert "/static/chat.js" in response.text


def test_chat_page_assets_are_served():
    client = TestClient(create_app(ChatService(make_kb())))
    assert client.get("/static/chat.css").status_code == 200
    assert client.get("/static/chat.js").status_code == 200
