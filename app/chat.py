"""Retrieval-augmented chat service with short per-session memory."""

from collections import defaultdict, deque
from dataclasses import dataclass

from .knowledge import KnowledgeBase, Match
from .llm import ChatModel

SYSTEM_PROMPT = (
    "You are a friendly customer support assistant. Answer only from the provided context. "
    "If the context does not contain the answer, say you are not sure and offer to connect "
    "the customer with a human agent. Keep answers short and clear."
)
FALLBACK = "I'm not sure about that one. Would you like me to connect you with a human agent?"


@dataclass
class Reply:
    answer: str
    sources: list[str]
    mode: str


class ChatService:
    def __init__(self, knowledge: KnowledgeBase, model: ChatModel | None = None, history_size: int = 6) -> None:
        self.knowledge = knowledge
        self.model = model
        self._history: dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))

    def ask(self, session_id: str, message: str) -> Reply:
        matches = self.knowledge.search(message)
        sources = [match.entry.question for match in matches]

        if self.model is None:
            answer = matches[0].entry.answer if matches else FALLBACK
            return Reply(answer, sources[:1], "offline")

        history = self._history[session_id]
        messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nContext:\n" + self._context(matches)}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        answer = self.model.complete(messages)

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": answer})
        return Reply(answer, sources, "llm")

    def reset(self, session_id: str) -> None:
        self._history.pop(session_id, None)

    @staticmethod
    def _context(matches: list[Match]) -> str:
        if not matches:
            return "(no relevant information found)"
        return "\n\n".join(f"Q: {m.entry.question}\nA: {m.entry.answer}" for m in matches)
