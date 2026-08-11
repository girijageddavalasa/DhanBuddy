from pathlib import Path

import pytest

from outbound.call_logic import (
    build_outbound_opening,
    classify_call_failure,
    retry_rule,
    validate_e164,
)
from outbound.preferences import is_opted_out, record_opt_out


def test_outbound_opening_has_identity_reason_and_opt_out() -> None:
    opening = build_outbound_opening("Asha")
    assert "this is DhanBuddy" in opening
    assert "savings check-in you requested" in opening
    assert "say stop calling" in opening
    assert opening.index("say stop calling") < len(opening)


def test_phone_number_requires_e164() -> None:
    assert validate_e164("+919876543210") == "+919876543210"
    with pytest.raises(ValueError):
        validate_e164("9876543210")


@pytest.mark.parametrize(
    ("message", "outcome"),
    [
        ("486 Busy Here", "busy"),
        ("603 Decline", "rejected"),
        ("408 Request Timeout", "no_answer"),
        ("SIP_TRUNK_FAILURE", "trunk_failure"),
        ("unexpected", "failed"),
    ],
)
def test_classifies_call_failure(message: str, outcome: str) -> None:
    assert classify_call_failure(message) == outcome


def test_every_outcome_has_retry_rule() -> None:
    for outcome in (
        "answered",
        "busy",
        "no_answer",
        "rejected",
        "immediate_hangup",
        "voicemail",
        "trunk_failure",
        "failed",
    ):
        assert retry_rule(outcome)


def test_opt_out_persists(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json"
    record_opt_out("caller-demo", path)
    assert is_opted_out("caller-demo", path) is True
    assert is_opted_out("another-caller", path) is False
