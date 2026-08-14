import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "outbound_preferences.json"


def _read(path: Path = DEFAULT_PATH) -> set[str]:
    if not path.exists():
        return set()
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {value for value in values if isinstance(value, str)}


def is_opted_out(user_id: str, path: Path = DEFAULT_PATH) -> bool:
    return user_id in _read(path)


def record_opt_out(user_id: str, path: Path = DEFAULT_PATH) -> None:
    if not user_id.strip() or len(user_id) > 128:
        raise ValueError("Invalid user ID.")
    path.parent.mkdir(parents=True, exist_ok=True)
    values = _read(path)
    values.add(user_id)
    path.write_text(json.dumps(sorted(values), indent=2), encoding="utf-8")
