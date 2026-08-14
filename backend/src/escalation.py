import re
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path

from memory import DEFAULT_DATABASE_PATH, _connect, create_user, initialize_database

ISSUE_TYPES = {"suspected_fraud", "financial_dispute", "scheme_eligibility_review"}
URGENCIES = {"low", "medium", "high", "emergency"}
STATUSES = {"open", "in_progress", "resolved", "cancelled"}
EXPLICIT_YES = {"yes", "yes please", "okay", "ok", "sure", "हाँ", "हां", "जी हाँ"}
PROHIBITED_TERMS = ("otp", "pin", "cvv", "password", "bank credentials", "card security")


def initialize_escalation_schema(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_id TEXT NOT NULL UNIQUE, user_id TEXT NOT NULL,
                issue_type TEXT NOT NULL, summary TEXT NOT NULL,
                what_happened TEXT NOT NULL, what_checked TEXT NOT NULL,
                urgency TEXT NOT NULL, language TEXT NOT NULL,
                preferred_follow_up TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)


def has_escalation_consent(reply: str) -> bool:
    return reply.casefold().strip(" .,!?") in EXPLICIT_YES


def should_escalate(text: str) -> str | None:
    normalized = text.casefold()
    fraud = ("don't recognize", "do not recognize", "unauthorized", "someone used my account", "not my transaction")
    dispute = ("dispute this transaction", "someone to review", "human review", "financial dispute")
    if any(phrase in normalized for phrase in fraud):
        return "suspected_fraud"
    if any(phrase in normalized for phrase in dispute):
        return "financial_dispute"
    return None


def urgency_for(issue_type: str) -> str:
    if issue_type == "suspected_fraud":
        return "high"
    if issue_type == "financial_dispute":
        return "medium"
    if issue_type == "scheme_eligibility_review":
        return "low"
    raise ValueError("Unsupported issue type.")


def sanitize(text: str) -> str:
    value = text.strip()[:1000]
    for term in PROHIBITED_TERMS:
        value = re.sub(rf"(?i)\b{re.escape(term)}\b\s*(?:is|:|=)?\s*\S*", f"{term.upper()} [REDACTED]", value)
    value = re.sub(r"\b(?:\d[ -]?){12,19}\b", "[REDACTED ACCOUNT NUMBER]", value)
    return value


def generate_reference_id(now: datetime | None = None) -> str:
    timestamp = now or datetime.now(timezone.utc)
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"DHN-{timestamp:%Y%m%d}-{suffix}"


def create_escalation(
    user_id: str, issue_type: str, short_summary: str, what_happened: str,
    what_dhanbuddy_checked: str, urgency: str, language: str,
    preferred_follow_up_method: str, consent_confirmation: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> dict[str, object]:
    if not has_escalation_consent(consent_confirmation):
        return {"created": False, "reason": "explicit_consent_required"}
    if issue_type not in ISSUE_TYPES or urgency not in URGENCIES:
        raise ValueError("Invalid escalation classification.")
    expected = urgency_for(issue_type)
    if urgency != expected:
        raise ValueError(f"Urgency for {issue_type} must be {expected}.")
    create_user(user_id, database_path)
    initialize_escalation_schema(database_path)
    with _connect(database_path) as connection:
        existing = connection.execute(
            "SELECT reference_id FROM escalations WHERE user_id=? AND issue_type=? AND status IN ('open','in_progress') ORDER BY escalation_id DESC LIMIT 1",
            (user_id, issue_type),
        ).fetchone()
        if existing:
            return {"created": False, "duplicate": True, "reference_id": existing["reference_id"]}
        reference = generate_reference_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        connection.execute(
            "INSERT INTO escalations (reference_id,user_id,issue_type,summary,what_happened,what_checked,urgency,language,preferred_follow_up,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,'open',?,?)",
            (reference, user_id, issue_type, sanitize(short_summary), sanitize(what_happened), sanitize(what_dhanbuddy_checked), urgency, sanitize(language), sanitize(preferred_follow_up_method), timestamp, timestamp),
        )
    return {"created": True, "reference_id": reference, "status": "open"}


def get_escalation_status(user_id: str, reference_id: str, database_path: Path = DEFAULT_DATABASE_PATH) -> dict | None:
    initialize_escalation_schema(database_path)
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT reference_id,status,updated_at FROM escalations WHERE user_id=? AND reference_id=?",
            (user_id, reference_id),
        ).fetchone()
    return dict(row) if row else None


def update_escalation_status(reference_id: str, status: str, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    if status not in STATUSES:
        raise ValueError("Invalid escalation status.")
    with _connect(database_path) as connection:
        cursor = connection.execute(
            "UPDATE escalations SET status=?,updated_at=? WHERE reference_id=?",
            (status, datetime.now(timezone.utc).isoformat(), reference_id),
        )
    return cursor.rowcount == 1


def list_escalations(database_path: Path = DEFAULT_DATABASE_PATH) -> list[dict]:
    initialize_escalation_schema(database_path)
    with _connect(database_path) as connection:
        rows = connection.execute(
            "SELECT reference_id,issue_type,urgency,summary,status,created_at FROM escalations ORDER BY escalation_id DESC"
        ).fetchall()
    return [dict(row) for row in rows]
