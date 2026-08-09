from pathlib import Path

from memory import delete_caller_profile, get_caller_profile, save_caller_profile


def test_profile_persists_across_connections(tmp_path: Path) -> None:
    database = tmp_path / "memory.db"
    save_caller_profile(
        "caller-1",
        "Asha",
        "Hindi",
        {"savings_goal": "college fees", "target_amount": 500_000},
        database,
    )

    loaded = get_caller_profile("caller-1", database)

    assert loaded is not None
    assert loaded.name == "Asha"
    assert loaded.facts["target_amount"] == 500_000
    assert loaded.consent_granted is True


def test_unknown_caller_returns_none(tmp_path: Path) -> None:
    assert get_caller_profile("missing", tmp_path / "memory.db") is None


def test_forget_permanently_deletes_profile(tmp_path: Path) -> None:
    database = tmp_path / "memory.db"
    save_caller_profile("caller-2", "Ravi", "English", {}, database)

    assert delete_caller_profile("caller-2", database) is True
    assert get_caller_profile("caller-2", database) is None
    assert delete_caller_profile("caller-2", database) is False
