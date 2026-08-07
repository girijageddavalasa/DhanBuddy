"""Small, approved knowledge base for grounded financial-literacy answers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeEntry:
    title: str
    keywords: tuple[str, ...]
    explanation: str


KNOWLEDGE_BASE = (
    KnowledgeEntry(
        title="Savings goal",
        keywords=("savings goal", "saving goal", "goal", "lakshya", "bachat"),
        explanation=(
            "A savings goal is a specific amount you want to set aside for a "
            "purpose by a chosen date."
        ),
    ),
    KnowledgeEntry(
        title="Monthly shortfall",
        keywords=("shortfall", "kami", "monthly gap", "gap"),
        explanation=(
            "A monthly shortfall is the extra amount you would need to save each "
            "month to reach the target on time."
        ),
    ),
    KnowledgeEntry(
        title="Monthly surplus",
        keywords=("surplus", "extra", "adhik", "more than required"),
        explanation=(
            "A monthly surplus means your planned monthly saving is higher than "
            "the estimated amount required."
        ),
    ),
    KnowledgeEntry(
        title="Emergency fund",
        keywords=("emergency fund", "emergency savings", "aapatkal"),
        explanation=(
            "An emergency fund is money kept separately for unexpected essential "
            "expenses. DhanBuddy does not recommend a specific account or product."
        ),
    ),
    KnowledgeEntry(
        title="Deadline extension",
        keywords=("extend", "extension", "deadline", "more time", "samay"),
        explanation=(
            "Extending the deadline gives you more months to save and can reduce "
            "the estimated amount needed each month."
        ),
    ),
    KnowledgeEntry(
        title="Educational estimate",
        keywords=("educational estimate", "estimate", "advice", "return"),
        explanation=(
            "The estimate uses only the amounts and deadline you provide. It "
            "assumes no investment returns and is not personalized financial advice."
        ),
    ),
)


def retrieve_knowledge(query: str) -> KnowledgeEntry | None:
    """Return the most relevant approved entry using deterministic keyword scoring."""
    normalized = query.casefold().strip()
    if not normalized:
        return None

    best_entry: KnowledgeEntry | None = None
    best_score = 0
    for entry in KNOWLEDGE_BASE:
        score = sum(keyword.casefold() in normalized for keyword in entry.keywords)
        if score > best_score:
            best_entry = entry
            best_score = score
    return best_entry
