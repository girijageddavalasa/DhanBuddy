import pytest

from agent import SYSTEM_PROMPT, calculate_plan


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
    assert "only task is goal-based savings planning" in SYSTEM_PROMPT
