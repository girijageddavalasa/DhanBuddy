import math
import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    source_date: str | None


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


def ingest_documents(directory: Path = KNOWLEDGE_DIR) -> list[Chunk]:
    chunks = []
    for path in directory.glob("*.txt") if directory.exists() else []:
        text = path.read_text(encoding="utf-8")
        parts = [part.strip() for part in text.split("\n\n") if part.strip()]
        chunks.extend(Chunk(part, path.name, None) for part in parts)
    return chunks


def retrieve(query: str, chunks: list[Chunk] | None = None, minimum_score: float = 0.12) -> list[Chunk]:
    query_tokens = _tokens(query)
    scored = []
    for chunk in chunks if chunks is not None else ingest_documents():
        tokens = _tokens(chunk.text)
        score = len(query_tokens & tokens) / math.sqrt(max(len(query_tokens) * len(tokens), 1))
        if score >= minimum_score:
            scored.append((score, chunk))
    return [chunk for _, chunk in sorted(scored, reverse=True, key=lambda pair: pair[0])[:3]]
