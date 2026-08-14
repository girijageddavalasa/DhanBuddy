from agent import setup_inactivity_handler
from prompt import FIRST_TURN_GREETING, SILENCE_CLOSE, SILENCE_REPROMPT, SYSTEM_PROMPT


def test_prompt_has_modular_day_two_sections() -> None:
    for section in (
        "# IDENTITY",
        "# OBJECTIVES",
        "# KNOWLEDGE",
        "# LANGUAGE",
        "# GUARDRAILS",
        "# ESCALATION",
        "# STYLE",
        "# SILENCE HANDLING",
    ):
        assert section in SYSTEM_PROMPT


def test_prompt_has_financial_boundaries() -> None:
    assert "Never ask for an OTP, PIN, CVV, password" in SYSTEM_PROMPT
    payment_boundary = "Never claim a payment, refund, or bank transaction occurred"
    assert payment_boundary in SYSTEM_PROMPT
    assert "Never guarantee investment returns" in SYSTEM_PROMPT
    assert "Never fabricate financial information" in SYSTEM_PROMPT


def test_prompt_does_not_claim_unverified_data_or_languages() -> None:
    assert "Use only the implemented financial-data tools" in SYSTEM_PROMPT
    assert "runtime support is not verified" in SYSTEM_PROMPT
    assert "Use Devanagari for Hindi" in SYSTEM_PROMPT


def test_voice_copy_is_short_and_reusable() -> None:
    assert FIRST_TURN_GREETING.startswith("Hi, I'm DhanBuddy")
    assert SILENCE_REPROMPT == "Are you still there? Take your time."
    assert SILENCE_CLOSE == "No problem. We can continue whenever you're ready."
    assert callable(setup_inactivity_handler)
