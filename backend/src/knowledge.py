"""Deterministic retrieval over DhanBuddy's reviewed RAG collection."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "rag" / "approved_knowledge.json"


@dataclass(frozen=True)
class KnowledgeEntry:
    title: str
    keywords: tuple[str, ...]
    explanation: str
    source_name: str
    source_url: str
    reviewed_on: str


@lru_cache(maxsize=1)
def load_knowledge() -> tuple[KnowledgeEntry, ...]:
    """Load the reviewed collection once per agent process."""
    raw_entries = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    return tuple(
        KnowledgeEntry(
            title=entry["title"],
            keywords=tuple(entry["keywords"]),
            explanation=entry["explanation"],
            source_name=entry["source_name"],
            source_url=entry["source_url"],
            reviewed_on=entry["reviewed_on"],
        )
        for entry in raw_entries
    )


def retrieve_knowledge(query: str) -> KnowledgeEntry | None:
    """Return the most relevant approved entry using keyword scoring."""
    normalized = query.casefold().strip()
    if not normalized:
        return None

    best_entry: KnowledgeEntry | None = None
    best_score = 0
    for entry in load_knowledge():
        score = sum(keyword.casefold() in normalized for keyword in entry.keywords)
        if score > best_score:
            best_entry = entry
            best_score = score
    return best_entry
