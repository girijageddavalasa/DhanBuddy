import pytest

from tools.savings_scenarios import compare_scenarios, parse_deadline_months


def test_parses_saved_deadline() -> None:
    assert parse_deadline_months("3 years") == 36
    assert parse_deadline_months("18 months") == 18
    assert parse_deadline_months("by graduation") is None


def test_compares_shortfall_scenarios() -> None:
    result = compare_scenarios(500_000, 36, 50_000, 10_000)
    assert result.current_projected_amount == 410_000
    assert result.on_track is False
    assert result.required_monthly_saving == 12_500
    assert result.monthly_increase_needed == 2_500
    assert result.months_needed_at_current_saving == 45
    assert result.deadline_extension_months == 9
    assert "zero investment returns" in result.data_source


def test_zero_monthly_saving_has_no_deadline_projection() -> None:
    result = compare_scenarios(100_000, 12, 10_000, 0)
    assert result.months_needed_at_current_saving is None
    assert result.deadline_extension_months is None


@pytest.mark.parametrize(
    ("target", "months", "saved", "monthly"),
    [(0, 12, 0, 1_000), (100_000, 0, 0, 1_000), (100_000, 12, -1, 1_000)],
)
def test_rejects_invalid_scenario_inputs(
    target: float, months: int, saved: float, monthly: float
) -> None:
    with pytest.raises(ValueError):
        compare_scenarios(target, months, saved, monthly)
