"""A small TF-IDF retriever over a FAQ knowledge base (no external dependencies)."""

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a", "an", "the", "is", "are", "do", "does", "i", "you", "your", "my", "to", "of",
    "and", "or", "in", "on", "for", "can", "how", "what", "when", "it", "be", "with",
}


def tokenize(text: str) -> list[str]:
    return [word for word in TOKEN.findall(text.lower()) if word not in STOP_WORDS]


@dataclass(frozen=True)
class Entry:
    question: str
    answer: str


@dataclass(frozen=True)
class Match:
    entry: Entry
    score: float


class KnowledgeBase:
    def __init__(self, entries: list[Entry]) -> None:
        if not entries:
            raise ValueError("The knowledge base needs at least one entry")
        self.entries = entries
        documents = [tokenize(f"{e.question} {e.answer}") for e in entries]
        doc_freq = Counter(word for doc in documents for word in set(doc))
        total = len(documents)
        self._idf = {word: math.log((1 + total) / (1 + df)) + 1 for word, df in doc_freq.items()}
        self._vectors = [self._vectorize(doc) for doc in documents]

    @classmethod
    def from_file(cls, path: str | Path) -> "KnowledgeBase":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Entry(**item) for item in data])

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        vector = {word: tf * self._idf.get(word, 0.0) for word, tf in counts.items()}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        return {word: value / norm for word, value in vector.items()}

    def search(self, query: str, top_k: int = 3, min_score: float = 0.05) -> list[Match]:
        query_vector = self._vectorize(tokenize(query))
        matches = []
        for entry, vector in zip(self.entries, self._vectors):
            score = sum(weight * vector.get(word, 0.0) for word, weight in query_vector.items())
            if score >= min_score:
                matches.append(Match(entry, round(score, 4)))
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:top_k]
