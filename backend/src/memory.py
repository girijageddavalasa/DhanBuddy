"""Privacy-safe persistent caller memory backed by SQLite."""

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "dhanbuddy.db"


@dataclass(frozen=True)
class CallerProfile:
    user_id: str
    name: str
    language_preference: str
    facts: dict[str, Any]
    consent_granted: bool
    last_interaction: str


def _connect(database_path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize_database(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    """Create the memory table if it does not already exist."""
    with _connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS caller_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language_preference TEXT NOT NULL,
                facts_json TEXT NOT NULL,
                consent_granted INTEGER NOT NULL CHECK (consent_granted IN (0, 1)),
                last_interaction TEXT NOT NULL
            )
            """
        )


def get_caller_profile(
    user_id: str, database_path: Path = DEFAULT_DATABASE_PATH
) -> CallerProfile | None:
    """Return a saved caller profile, if one exists."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM caller_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return CallerProfile(
        user_id=row["user_id"],
        name=row["name"],
        language_preference=row["language_preference"],
        facts=json.loads(row["facts_json"]),
        consent_granted=bool(row["consent_granted"]),
        last_interaction=row["last_interaction"],
    )


def save_caller_profile(
    user_id: str,
    name: str,
    language_preference: str,
    facts: dict[str, Any],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> CallerProfile:
    """Insert or update a caller profile after consent was verified by the tool."""
    initialize_database(database_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    profile = CallerProfile(
        user_id=user_id,
        name=name.strip(),
        language_preference=language_preference.strip() or "English",
        facts=facts,
        consent_granted=True,
        last_interaction=timestamp,
    )
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO caller_profiles
                (user_id, name, language_preference, facts_json,
                 consent_granted, last_interaction)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts_json = excluded.facts_json,
                consent_granted = 1,
                last_interaction = excluded.last_interaction
            """,
            (
                profile.user_id,
                profile.name,
                profile.language_preference,
                json.dumps(profile.facts, ensure_ascii=False),
                profile.last_interaction,
            ),
        )
    return profile


def delete_caller_profile(
    user_id: str, database_path: Path = DEFAULT_DATABASE_PATH
) -> bool:
    """Permanently delete a caller profile and return whether it existed."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM caller_profiles WHERE user_id = ?", (user_id,)
        )
    return cursor.rowcount > 0


def profile_as_dict(profile: CallerProfile) -> dict[str, Any]:
    return asdict(profile)
