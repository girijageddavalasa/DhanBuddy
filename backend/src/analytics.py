import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from memory import DEFAULT_DATABASE_PATH, _connect, create_user, initialize_database

CHANNELS = {"browser", "sip"}
FAILURE_TYPES = {"user_hangup", "incomplete_task", "tool_failure", "api_error", "no_response", "connection_error", "unknown"}
TASK_OUTCOMES = {"spending_summary", "document_processed", "financial_information", "human_escalation", "general_question", "incomplete"}
AGENT_ROLES = {"main", "scheme_specialist"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def initialize_calls_schema(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                call_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, session_id TEXT NOT NULL,
                channel TEXT NOT NULL, language TEXT, started_at TEXT NOT NULL, ended_at TEXT,
                duration_seconds REAL, outcome TEXT, task_outcome TEXT NOT NULL DEFAULT 'incomplete',
                failure_type TEXT, success_reason TEXT, latency_ms REAL, created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(calls)")}
        migrations = {
            "agent_role": "TEXT NOT NULL DEFAULT 'main'",
            "handoff_requested": "INTEGER NOT NULL DEFAULT 0",
            "handoff_success": "INTEGER NOT NULL DEFAULT 0",
            "handoff_failure": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, definition in migrations.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE calls ADD COLUMN {name} {definition}")


def record_call_start(user_id: str, session_id: str, channel: str, language: str | None = None, database_path: Path = DEFAULT_DATABASE_PATH, started_at: datetime | None = None) -> str:
    if channel not in CHANNELS:
        raise ValueError("Invalid call channel.")
    create_user(user_id, database_path); initialize_calls_schema(database_path)
    call_id, timestamp = f"call-{uuid.uuid4().hex}", started_at or _now()
    with _connect(database_path) as connection:
        connection.execute("INSERT INTO calls (call_id,user_id,session_id,channel,language,started_at,created_at) VALUES (?,?,?,?,?,?,?)", (call_id, user_id, session_id, channel, language, timestamp.isoformat(), timestamp.isoformat()))
    return call_id


def record_call_end(call_id: str, outcome: str, task_outcome: str = "incomplete", failure_type: str | None = None, success_reason: str | None = None, latency_ms: float | None = None, database_path: Path = DEFAULT_DATABASE_PATH, ended_at: datetime | None = None) -> bool:
    if outcome not in {"success", "failure"} or task_outcome not in TASK_OUTCOMES:
        raise ValueError("Invalid call outcome.")
    if outcome == "failure" and failure_type not in FAILURE_TYPES:
        raise ValueError("A valid failure type is required.")
    if outcome == "success" and not success_reason:
        raise ValueError("Successful calls require a task completion reason.")
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("Latency cannot be negative.")
    ended = ended_at or _now()
    with _connect(database_path) as connection:
        row = connection.execute("SELECT started_at FROM calls WHERE call_id=?", (call_id,)).fetchone()
        if not row: return False
        duration = max((ended - datetime.fromisoformat(row["started_at"])).total_seconds(), 0)
        connection.execute("UPDATE calls SET ended_at=?,duration_seconds=?,outcome=?,task_outcome=?,failure_type=?,success_reason=?,latency_ms=COALESCE(?,latency_ms) WHERE call_id=?", (ended.isoformat(), duration, outcome, task_outcome, failure_type, success_reason, latency_ms, call_id))
    return True


def record_latency(call_id: str, latency_ms: float, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    if latency_ms < 0: raise ValueError("Latency cannot be negative.")
    with _connect(database_path) as connection:
        cursor = connection.execute("UPDATE calls SET latency_ms=? WHERE call_id=?", (latency_ms, call_id))
    return cursor.rowcount == 1


def record_call_language(call_id: str, language: str, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    value = language.strip()[:50]
    if not value:
        raise ValueError("Language is required.")
    with _connect(database_path) as connection:
        cursor = connection.execute("UPDATE calls SET language=? WHERE call_id=?", (value, call_id))
    return cursor.rowcount == 1


def record_handoff(call_id: str, status: str, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    if status not in {"requested", "success", "failure"}:
        raise ValueError("Invalid handoff status.")
    assignments = {
        "requested": "handoff_requested=1",
        "success": "handoff_requested=1,handoff_success=1,handoff_failure=0,agent_role='scheme_specialist'",
        "failure": "handoff_requested=1,handoff_failure=1",
    }
    with _connect(database_path) as connection:
        cursor = connection.execute(f"UPDATE calls SET {assignments[status]} WHERE call_id=?", (call_id,))
    return cursor.rowcount == 1


def record_agent_role(call_id: str, role: str, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    if role not in AGENT_ROLES:
        raise ValueError("Invalid agent role.")
    with _connect(database_path) as connection:
        cursor = connection.execute("UPDATE calls SET agent_role=? WHERE call_id=?", (role, call_id))
    return cursor.rowcount == 1


@dataclass
class CallTracker:
    call_id: str
    task_outcome: str = "incomplete"
    success_reason: str | None = None
    latency_ms: float | None = None

    def mark_success(self, task_outcome: str, reason: str) -> None:
        if task_outcome not in TASK_OUTCOMES - {"incomplete"}: raise ValueError("Invalid task outcome.")
        self.task_outcome, self.success_reason = task_outcome, reason

    def finish(self, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
        if self.success_reason:
            return record_call_end(self.call_id, "success", self.task_outcome, success_reason=self.success_reason, latency_ms=self.latency_ms, database_path=database_path)
        return record_call_end(self.call_id, "failure", "incomplete", "incomplete_task", latency_ms=self.latency_ms, database_path=database_path)


def analytics_summary(database_path: Path = DEFAULT_DATABASE_PATH, date_from: str | None = None, date_to: str | None = None, language: str | None = None, channel: str | None = None, outcome: str | None = None) -> dict:
    initialize_calls_schema(database_path)
    if date_from and len(date_from) == 10: date_from += "T00:00:00+00:00"
    if date_to and len(date_to) == 10: date_to += "T23:59:59+00:00"
    clauses, values = ["ended_at IS NOT NULL"], []
    for column, value, operator in (("started_at", date_from, ">="), ("started_at", date_to, "<="), ("language", language, "="), ("channel", channel, "="), ("outcome", outcome, "=")):
        if value: clauses.append(f"{column} {operator} ?"); values.append(value)
    where = " AND ".join(clauses)
    with _connect(database_path) as connection:
        rows = connection.execute(f"SELECT * FROM calls WHERE {where} ORDER BY started_at DESC", values).fetchall()
        escalation_count = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='escalations'").fetchone()[0]
        escalations = connection.execute("SELECT COUNT(*) FROM escalations").fetchone()[0] if escalation_count else 0
    total, successful = len(rows), sum(row["outcome"] == "success" for row in rows)
    durations = [row["duration_seconds"] for row in rows if row["duration_seconds"] is not None]
    latencies = [row["latency_ms"] for row in rows if row["latency_ms"] is not None]
    def distribution(field):
        result = {}
        for row in rows:
            key = row[field] or "unknown"; result[key] = result.get(key, 0) + 1
        return result
    history = [{key: row[key] for key in ("started_at", "duration_seconds", "channel", "language", "outcome", "failure_type", "agent_role", "handoff_requested", "handoff_success", "handoff_failure")} for row in rows[:50]]
    calls_over_time = {}
    for row in rows:
        day = row["started_at"][:10]
        calls_over_time[day] = calls_over_time.get(day, 0) + 1
    return {"total_calls": total, "successful_calls": successful, "failed_calls": total-successful, "success_rate": round(successful*100/total, 1) if total else 0, "average_duration_seconds": round(sum(durations)/len(durations), 2) if durations else None, "average_latency_ms": round(sum(latencies)/len(latencies), 2) if latencies else None, "escalation_count": escalations, "failure_types": distribution("failure_type"), "languages": distribution("language"), "channels": distribution("channel"), "outcomes": distribution("outcome"), "calls_over_time": calls_over_time, "recent_calls": history}


def last_call_activity(database_path: Path = DEFAULT_DATABASE_PATH) -> str | None:
    initialize_calls_schema(database_path)
    with _connect(database_path) as connection:
        row = connection.execute("SELECT MAX(started_at) value FROM calls").fetchone()
    return row["value"] if row else None


def health_snapshot(database_path: Path = DEFAULT_DATABASE_PATH, livekit_configured: bool = False) -> dict[str, object]:
    database_status = "connected"
    try:
        with _connect(database_path) as connection: connection.execute("SELECT 1").fetchone()
    except sqlite3.Error:
        database_status = "unavailable"
    healthy = database_status == "connected" and livekit_configured
    return {"status": "healthy" if healthy else "degraded", "service": "DhanBuddy", "database_status": database_status, "agent_status": "ready" if livekit_configured else "configuration_pending", "livekit_status": "configured" if livekit_configured else "not_configured", "last_activity": last_call_activity(database_path) if database_status == "connected" else None, "timestamp": _now().isoformat()}
