import re
from dataclasses import dataclass
from typing import Mapping

SCHEME_TERMS = ("government scheme", "govt scheme", "sarkari yojana", "सरकारी योजना", "योजना", "scheme eligibility", "scheme documents", "scheme benefits", "scheme application", "pm kisan", "mudra yojana", "jan dhan", "atal pension")
SECRET_PATTERN = re.compile(r"(?i)\b(otp|pin|cvv|password|bank credentials?|card security(?: information)?)\b\s*(?:is|:|=)?\s*\S*")
ALLOWED_CONTEXT_KEYS = {"scheme_name", "state", "age_band", "occupation"}

HANDOFF_ANNOUNCEMENT = "I'll connect you with our government scheme specialist."
SPECIALIST_INTRODUCTION = "Hi, I'm DhanBuddy's government scheme specialist. Let's look at the scheme requirements together."
HANDOFF_FAILURE_MESSAGE = "I couldn't connect you to the specialist right now. I can still help with general financial information."


def route_request(question: str) -> str:
    """Return the narrow specialist route only for explicit scheme intent."""
    normalized = question.casefold()
    explicit_term = any(term in normalized for term in SCHEME_TERMS)
    scheme_detail = "scheme" in normalized and any(
        term in normalized
        for term in ("eligible", "eligibility", "document", "benefit", "apply", "application", "requirement")
    )
    return "scheme_specialist" if explicit_term or scheme_detail else "main"


def redact_secrets(text: str) -> str:
    value = SECRET_PATTERN.sub("[REDACTED]", text.strip())
    return re.sub(r"\b(?:\d[ -]?){12,19}\b", "[REDACTED]", value)


@dataclass(frozen=True)
class HandoffContext:
    user_id: str
    user_language: str
    user_question: str
    relevant_context: dict[str, str]


def build_handoff_context(user_id: str, user_language: str, user_question: str, relevant_context: Mapping[str, object] | None = None) -> HandoffContext:
    filtered = {key: redact_secrets(str(value)) for key, value in (relevant_context or {}).items() if key in ALLOWED_CONTEXT_KEYS and value is not None}
    return HandoffContext(user_id=user_id, user_language=redact_secrets(user_language)[:50] or "unknown", user_question=redact_secrets(user_question)[:1000], relevant_context=filtered)
