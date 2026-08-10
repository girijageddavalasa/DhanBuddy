"""Zero-return savings scenario calculations for Day 5."""

import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SavingsScenarioResult:
    target_amount: float
    current_projected_amount: float
    current_monthly_saving: float
    current_months: int
    on_track: bool
    required_monthly_saving: float
    monthly_increase_needed: float
    months_needed_at_current_saving: int | None
    deadline_extension_months: int | None
    calculated_at: str
    data_source: str


def parse_deadline_months(value: str) -> int | None:
    """Convert simple saved durations such as '3 years' or '18 months' to months."""
    normalized = value.casefold().strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(year|years|yr|yrs)", normalized)
    if match:
        return max(1, round(float(match.group(1)) * 12))
    match = re.search(r"(\d+(?:\.\d+)?)\s*(month|months|mo)", normalized)
    if match:
        return max(1, round(float(match.group(1))))
    return None


def compare_scenarios(
    target_amount: float,
    months: int,
    already_saved: float,
    monthly_saving: float,
) -> SavingsScenarioResult:
    """Compare the current plan with monthly-increase and deadline options."""
    if target_amount <= 0 or months <= 0:
        raise ValueError("Target amount and remaining months must be positive.")
    if already_saved < 0 or monthly_saving < 0:
        raise ValueError("Savings amounts cannot be negative.")

    remaining = max(target_amount - already_saved, 0)
    required_monthly = remaining / months
    projected = already_saved + monthly_saving * months
    months_needed = (
        math.ceil(remaining / monthly_saving) if monthly_saving > 0 else None
    )
    extension = max(months_needed - months, 0) if months_needed is not None else None

    return SavingsScenarioResult(
        target_amount=round(target_amount, 2),
        current_projected_amount=round(projected, 2),
        current_monthly_saving=round(monthly_saving, 2),
        current_months=months,
        on_track=projected >= target_amount,
        required_monthly_saving=round(required_monthly, 2),
        monthly_increase_needed=round(max(required_monthly - monthly_saving, 0), 2),
        months_needed_at_current_saving=months_needed,
        deadline_extension_months=extension,
        calculated_at=datetime.now(timezone.utc).isoformat(),
        data_source="Local deterministic calculation with zero investment returns",
    )


def scenario_as_dict(result: SavingsScenarioResult) -> dict[str, object]:
    return asdict(result)
