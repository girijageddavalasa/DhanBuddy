import pytest

from agent import (
    FIRST_TURN_GREETING,
    SILENCE_CLOSE,
    SILENCE_REPROMPT,
    SYSTEM_PROMPT,
    calculate_plan,
)
from knowledge import retrieve_knowledge


def test_plan_on_track_with_monthly_surplus() -> None:
    plan = calculate_plan(500_000, 24, 100_000, 20_000)
    assert plan.projected_amount == 580_000
    assert plan.required_monthly_saving == 16_666.67
    assert plan.monthly_difference == 3_333.33
    assert plan.on_track is True


def test_plan_behind_with_monthly_shortfall() -> None:
    plan = calculate_plan(1_000_000, 36, 100_000, 20_000)
    assert plan.projected_amount == 820_000
    assert plan.required_monthly_saving == 25_000
    assert plan.monthly_difference == -5_000
    assert plan.on_track is False


@pytest.mark.parametrize(
    ("target", "months", "saved", "monthly"),
    [(0, 12, 0, 1_000), (100_000, 0, 0, 1_000), (100_000, 12, -1, 1_000)],
)
def test_plan_rejects_invalid_inputs(
    target: float, months: int, saved: float, monthly: float
) -> None:
    with pytest.raises(ValueError):
        calculate_plan(target, months, saved, monthly)


def test_prompt_contains_safety_and_scope_rules() -> None:
    assert "exactly one question per response" in SYSTEM_PROMPT
    assert "educational estimate" in SYSTEM_PROMPT
    assert "OTP, PIN, CVV" in SYSTEM_PROMPT
    assert "qualified financial professional" in SYSTEM_PROMPT
    assert "Never claim guaranteed returns" in SYSTEM_PROMPT


@pytest.mark.parametrize(
    "section",
    [
        "# IDENTITY",
        "# OBJECTIVES",
        "# KNOWLEDGE",
        "# LANGUAGE",
        "# GUARDRAILS",
        "# STYLE",
    ],
)
def test_prompt_has_required_structure(section: str) -> None:
    assert section in SYSTEM_PROMPT


def test_prompt_supports_code_mixed_language() -> None:
    assert "natural Hinglish to Hinglish" in SYSTEM_PROMPT
    assert "If the user changes language, change with them" in SYSTEM_PROMPT


def test_voice_messages_are_short_plain_text() -> None:
    assert FIRST_TURN_GREETING.startswith("Namaste! I'm DhanBuddy.")
    assert "?" in FIRST_TURN_GREETING
    assert len(SILENCE_REPROMPT.split()) < 20
    assert len(SILENCE_CLOSE.split()) < 30
    assert "[" not in FIRST_TURN_GREETING


def test_retrieves_approved_knowledge() -> None:
    entry = retrieve_knowledge("What is my monthly shortfall?")
    assert entry is not None
    assert entry.title == "Monthly shortfall"


def test_unknown_knowledge_is_not_invented() -> None:
    assert retrieve_knowledge("Which crypto will double tomorrow?") is None
