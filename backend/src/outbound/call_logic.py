"""Pure outbound-call validation, opening, and outcome rules."""

import re

E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def validate_e164(phone_number: str) -> str:
    """Validate and return an E.164 phone number."""
    normalized = phone_number.strip()
    if not E164_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Phone number must use E.164 format, for example +919876543210."
        )
    return normalized


def build_outbound_opening(caller_name: str) -> str:
    """Build the mandatory who, why, and opt-out opening."""
    name = caller_name.strip() or "there"
    return (
        "Hello, this is DhanBuddy, your educational savings assistant, calling "
        "for the savings check-in you requested. You can say stop calling at any "
        f"time, and I will end this call. Am I speaking with {name}?"
    )


def classify_call_failure(message: str) -> str:
    """Map carrier/RPC failure text to a privacy-safe outcome label."""
    normalized = message.casefold()
    if "486" in normalized or "busy" in normalized:
        return "busy"
    if "603" in normalized or "decline" in normalized or "rejected" in normalized:
        return "rejected"
    if any(value in normalized for value in ("408", "480", "timeout", "unavailable")):
        return "no_answer"
    if "trunk" in normalized or re.search(r"\b5\d\d\b", normalized):
        return "trunk_failure"
    return "failed"


def retry_rule(outcome: str) -> str:
    """Return the defined retry behavior for an outbound outcome."""
    rules = {
        "answered": "No retry. The conversation was connected.",
        "busy": "Do not retry immediately. Offer one retry on the next day only if still opted in.",
        "no_answer": "Allow at most one retry after thirty minutes if the caller remains opted in.",
        "rejected": "Do not retry. Treat the decline as a stop signal for this reminder.",
        "immediate_hangup": "Do not retry. Wait for the caller to request another check-in.",
        "voicemail": "Leave no financial details. State DhanBuddy's name and a callback-free reminder only.",
        "trunk_failure": "Do not call again until the telephony configuration is fixed.",
        "failed": "Do not retry automatically. Review the carrier error first.",
    }
    return rules.get(outcome, rules["failed"])
