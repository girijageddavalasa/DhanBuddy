CATEGORIES = (
    "Food", "Groceries", "Transport", "Shopping", "Utilities",
    "Healthcare", "Education", "Entertainment", "Bills", "Other",
)

KEYWORDS = {
    "Groceries": {"rice", "milk", "soap", "atta", "dal", "vegetable", "grocery"},
    "Food": {"restaurant", "cafe", "meal", "pizza", "biryani", "food"},
    "Transport": {"uber", "ola", "metro", "bus", "petrol", "fuel", "taxi"},
    "Shopping": {"shirt", "shoe", "clothing", "amazon", "flipkart"},
    "Utilities": {"electricity", "water", "gas", "broadband", "internet"},
    "Healthcare": {"medicine", "pharmacy", "clinic", "hospital"},
    "Education": {"school", "tuition", "book", "course", "college"},
    "Entertainment": {"movie", "cinema", "ticket", "game"},
    "Bills": {"bill", "recharge", "subscription"},
}


def categorize(description: str) -> tuple[str, float]:
    words = description.casefold()
    for category, keywords in KEYWORDS.items():
        if any(keyword in words for keyword in keywords):
            return category, 0.95
    return "Other", 0.35


def needs_confirmation(confidence: float, threshold: float = 0.7) -> bool:
    return confidence < threshold
