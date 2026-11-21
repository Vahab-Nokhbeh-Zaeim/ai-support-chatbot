"""Keeps a log of questions the knowledge base could not answer.

Every unanswered question is appended to a JSON Lines file (one JSON object per line),
so the log survives restarts and can be opened in any editor or loaded with pandas.
The summary groups questions that only differ in spelling, punctuation or Arabic/Persian
keyboard letters, which shows the FAQ owner which entries are worth adding first.
"""

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .knowledge import is_persian, tokenize


@dataclass
class UnansweredQuestion:
    question: str
    count: int
    language: str
    last_asked: str


class UnansweredLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def record(self, message: str) -> None:
        entry = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "language": "fa" if is_persian(message) else "en",
            "message": message,
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def entries(self) -> list[dict]:
        with self._lock:
            if not self.path.exists():
                return []
            lines = self.path.read_text(encoding="utf-8").splitlines()
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a half-written line must not break the whole report
        return entries

    def summary(self, limit: int = 20) -> list[UnansweredQuestion]:
        """Most frequently asked unanswered questions, most common first."""
        groups: dict[str, UnansweredQuestion] = {}
        for entry in self.entries():
            message = entry.get("message", "")
            key = " ".join(tokenize(message)) or message.strip().lower()
            group = groups.get(key)
            if group is None:
                groups[key] = UnansweredQuestion(message, 1, entry.get("language", ""), entry.get("time", ""))
            else:
                group.count += 1
                group.question = message  # show the latest wording
                group.last_asked = max(group.last_asked, entry.get("time", ""))
        ranked = sorted(groups.values(), key=lambda q: (q.count, q.last_asked), reverse=True)
        return ranked[:limit]
