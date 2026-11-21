import json

from fastapi.testclient import TestClient

from app.chat import ChatService
from app.knowledge import Entry, KnowledgeBase
from app.main import create_app
from app.unanswered import UnansweredLog


def make_kb() -> KnowledgeBase:
    return KnowledgeBase([
        Entry("How long does shipping take?", "Delivery takes 2 to 4 business days."),
        Entry("آیا امکان مرجوع کردن کالا وجود دارد؟", "بله، تا ۷ روز."),
    ])


def make_client(tmp_path) -> tuple[TestClient, UnansweredLog]:
    log = UnansweredLog(tmp_path / "unanswered.jsonl")
    return TestClient(create_app(ChatService(make_kb(), unanswered=log))), log


def test_unanswered_question_is_written_to_file(tmp_path):
    client, log = make_client(tmp_path)
    client.post("/chat", json={"message": "Do you sell gift cards?"})

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["message"] == "Do you sell gift cards?"
    assert entry["language"] == "en"
    assert entry["time"]


def test_answered_question_is_not_logged(tmp_path):
    client, log = make_client(tmp_path)
    client.post("/chat", json={"message": "how long does shipping take"})
    assert log.entries() == []


def test_persian_text_is_stored_readably(tmp_path):
    client, log = make_client(tmp_path)
    client.post("/chat", json={"message": "کارت هدیه دارید؟"})
    raw = log.path.read_text(encoding="utf-8")
    assert "کارت هدیه" in raw  # not \\u escapes
    assert log.entries()[0]["language"] == "fa"


def test_summary_groups_spelling_variants(tmp_path):
    log = UnansweredLog(tmp_path / "unanswered.jsonl")
    log.record("کارت هدیه دارید؟")
    log.record("كارت هديه داريد")  # Arabic keyboard, no question mark
    log.record("Do you sell gift cards?")

    summary = log.summary()
    assert [q.count for q in summary] == [2, 1]
    assert summary[0].language == "fa"


def test_unanswered_endpoint_reports_most_common_first(tmp_path):
    client, _ = make_client(tmp_path)
    for message in ["Do you sell gift cards?", "do you sell gift cards", "Is there a store in Tabriz?"]:
        client.post("/chat", json={"message": message})

    body = client.get("/unanswered").json()
    assert body["total"] == 3
    assert body["questions"][0]["count"] == 2
    assert body["questions"][1]["question"] == "Is there a store in Tabriz?"


def test_endpoint_returns_404_when_log_is_off():
    client = TestClient(create_app(ChatService(make_kb())))
    assert client.get("/unanswered").status_code == 404


def test_corrupt_line_is_skipped(tmp_path):
    log = UnansweredLog(tmp_path / "unanswered.jsonl")
    log.record("first")
    with log.path.open("a", encoding="utf-8") as file:
        file.write('{"message": "half writ')
    assert [e["message"] for e in log.entries()] == ["first"]
