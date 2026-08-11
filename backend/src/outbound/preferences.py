"""Local opt-out registry keyed only by anonymous caller ID."""

import json
from pathlib import Path

DEFAULT_PREFERENCES_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "outbound_preferences.json"
)


def _read(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    return {str(value) for value in values if isinstance(value, str)}


def is_opted_out(caller_id: str, path: Path = DEFAULT_PREFERENCES_PATH) -> bool:
    return caller_id in _read(path)


def record_opt_out(caller_id: str, path: Path = DEFAULT_PREFERENCES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    values = _read(path)
    values.add(caller_id)
    path.write_text(json.dumps(sorted(values), indent=2), encoding="utf-8")
