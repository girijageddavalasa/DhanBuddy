import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "dhanbuddy.db"
ALLOWED_MEMORY_KEYS = {
    "name", "preferred_language", "financial_goal", "budgeting_style",
    "transaction_categories",
}
SENSITIVE_TERMS = {"otp", "pin", "cvv", "password", "banking credential", "card security"}


@dataclass(frozen=True)
class UserMemory:
    user_id: str
    name: str | None
    preferred_language: str | None
    memory_consent: bool
    facts: dict[str, str]
    last_interaction: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_user_id(user_id: str) -> str:
    value = user_id.strip()
    if not value or len(value) > 128:
        raise ValueError("Invalid user ID.")
    return value


@contextmanager
def _connect(database_path: Path):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    with _connect(database_path) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, name TEXT, preferred_language TEXT,
                memory_consent INTEGER NOT NULL DEFAULT 0 CHECK (memory_consent IN (0, 1)),
                created_at TEXT NOT NULL, last_interaction TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                key TEXT NOT NULL, value TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, UNIQUE (user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                summary TEXT NOT NULL, created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        """)


def create_user(user_id: str, database_path: Path = DEFAULT_DATABASE_PATH) -> UserMemory:
    user_id = _validate_user_id(user_id)
    initialize_database(database_path)
    timestamp = _now()
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT INTO users (user_id, created_at, last_interaction) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET last_interaction = excluded.last_interaction",
            (user_id, timestamp, timestamp),
        )
    memory = lookup_user(user_id, database_path)
    if memory is None:
        raise RuntimeError("User creation failed.")
    return memory


def lookup_user(user_id: str, database_path: Path = DEFAULT_DATABASE_PATH) -> UserMemory | None:
    user_id = _validate_user_id(user_id)
    initialize_database(database_path)
    with _connect(database_path) as connection:
        user = connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if user is None:
            return None
        rows = connection.execute(
            "SELECT key, value FROM user_facts WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()
    return UserMemory(
        user_id=user["user_id"], name=user["name"],
        preferred_language=user["preferred_language"],
        memory_consent=bool(user["memory_consent"]),
        facts={row["key"]: row["value"] for row in rows},
        last_interaction=user["last_interaction"],
    )


def save_user_memory(
    user_id: str, key: str, value: str, consent: bool,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> UserMemory:
    user_id = _validate_user_id(user_id)
    key, value = key.strip().casefold(), value.strip()
    if not consent:
        raise PermissionError("Memory consent is required.")
    if key not in ALLOWED_MEMORY_KEYS:
        raise ValueError("This memory type is not allowed.")
    if not value or len(value) > 500:
        raise ValueError("Invalid memory value.")
    if any(term in f"{key} {value}".casefold() for term in SENSITIVE_TERMS):
        raise ValueError("Sensitive credentials cannot be stored.")
    initialize_database(database_path)
    timestamp = _now()
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT INTO users (user_id, memory_consent, created_at, last_interaction) "
            "VALUES (?, 1, ?, ?) ON CONFLICT(user_id) DO UPDATE SET "
            "memory_consent = 1, last_interaction = excluded.last_interaction",
            (user_id, timestamp, timestamp),
        )
        connection.execute(
            "INSERT INTO user_facts (user_id, key, value, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET "
            "value = excluded.value, updated_at = excluded.updated_at",
            (user_id, key, value, timestamp, timestamp),
        )
        if key == "name":
            connection.execute("UPDATE users SET name = ? WHERE user_id = ?", (value, user_id))
        elif key == "preferred_language":
            connection.execute(
                "UPDATE users SET preferred_language = ? WHERE user_id = ?", (value, user_id)
            )
    memory = lookup_user(user_id, database_path)
    if memory is None:
        raise RuntimeError("Memory save failed.")
    return memory


def record_interaction(
    user_id: str, summary: str, database_path: Path = DEFAULT_DATABASE_PATH
) -> None:
    user_id, summary = _validate_user_id(user_id), summary.strip()
    if not summary or len(summary) > 500:
        raise ValueError("Invalid interaction summary.")
    if lookup_user(user_id, database_path) is None:
        create_user(user_id, database_path)
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT INTO interactions (user_id, summary, created_at) VALUES (?, ?, ?)",
            (user_id, summary, _now()),
        )


def forget_me(user_id: str, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    user_id = _validate_user_id(user_id)
    initialize_database(database_path)
    with _connect(database_path) as connection:
        cursor = connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    return cursor.rowcount > 0


def memory_as_dict(memory: UserMemory) -> dict[str, object]:
    return asdict(memory)
