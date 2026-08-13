import re
from dataclasses import asdict, dataclass

from categorization import categorize


@dataclass
class LineItem:
    description: str
    quantity: float | None
    unit_price: float | None
    amount: float | None
    category: str
    category_confidence: float


def normalize_ocr_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\r", "\n").splitlines() if line.strip())


def parse_document(text: str) -> dict[str, object]:
    raw = normalize_ocr_text(text)
    lines = raw.splitlines()
    merchant = lines[0] if lines else None
    date_match = re.search(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", raw)
    total_match = re.search(r"(?im)\btotal\s*[:₹rs.]*\s*([\d,]+(?:\.\d{1,2})?)", raw)
    items = []
    for line in lines:
        match = re.match(r"(.+?)\s+[₹]?(\d[\d,]*(?:\.\d{1,2})?)$", line)
        if not match or re.search(r"(?i)total", line):
            continue
        description, amount_text = match.groups()
        category, confidence = categorize(description)
        items.append(LineItem(description.strip(), None, None, float(amount_text.replace(",", "")), category, confidence))
    return {
        "merchant": merchant,
        "date": date_match.group(1) if date_match else None,
        "total_amount": float(total_match.group(1).replace(",", "")) if total_match else None,
        "currency": "INR" if "₹" in raw or re.search(r"(?i)\brs\.?\b", raw) else None,
        "line_items": [asdict(item) for item in items],
        "raw_text": raw,
    }
