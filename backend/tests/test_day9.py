import sqlite3
import tempfile
import unittest
from pathlib import Path

from analytics import record_call_start, record_handoff
from escalation import create_escalation
from orchestrator import (
    HANDOFF_ANNOUNCEMENT,
    HANDOFF_FAILURE_MESSAGE,
    SPECIALIST_INTRODUCTION,
    build_handoff_context,
    route_request,
)
from scheme_specialist import SPECIALIST_PROMPT, guardrail_response


class Day9Tests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "data"
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.db = Path(self.temp.name) / "day9.db"

    def tearDown(self):
        self.temp.cleanup()

    def test_normal_finance_question_stays_with_main(self):
        self.assertEqual(route_request("Where did I spend the most this month?"), "main")

    def test_scheme_question_routes_to_specialist(self):
        self.assertEqual(route_request("Am I eligible for this government scheme?"), "scheme_specialist")
        self.assertEqual(route_request("What documents do I need for this scheme?"), "scheme_specialist")

    def test_specialist_receives_question_without_repeat(self):
        question = "What documents do I need for this scheme?"
        context = build_handoff_context("user-1", "English", question)
        self.assertEqual(context.user_question, question)
        self.assertIn("without asking them to repeat", SPECIALIST_PROMPT)

    def test_handoff_ux_is_explicit(self):
        self.assertIn("connect you", HANDOFF_ANNOUNCEMENT)
        self.assertIn("government scheme specialist", SPECIALIST_INTRODUCTION)

    def test_specialist_guardrail_refuses_approval_claim(self):
        response = guardrail_response("Just tell me I'm approved")
        self.assertIn("can't claim", response)

    def test_credentials_and_transcript_are_not_passed(self):
        context = build_handoff_context(
            "user-1", "Hindi", "My OTP is 123456. Am I eligible?",
            {"scheme_name": "PM scheme", "transcript": "secret", "cvv": "123", "state": "PIN: 9999"},
        )
        serialized = repr(context).casefold()
        self.assertNotIn("123456", serialized)
        self.assertNotIn("9999", serialized)
        self.assertNotIn("transcript", serialized)
        self.assertNotIn("cvv", serialized)

    def test_handoff_failure_returns_control_safely(self):
        self.assertIn("still help", HANDOFF_FAILURE_MESSAGE)
        self.assertNotIn("connected", HANDOFF_FAILURE_MESSAGE)

    def test_existing_escalation_path_accepts_scheme_review(self):
        result = create_escalation(
            "user-1", "scheme_eligibility_review", "Needs human judgment",
            "Published rules are inconclusive", "Checked trusted sources", "low",
            "English", "email", "yes", self.db,
        )
        self.assertTrue(result["created"])

    def test_language_preference_is_preserved(self):
        context = build_handoff_context("user-1", "Hindi-English code-mixed", "Yojana eligibility kya hai?")
        self.assertEqual(context.user_language, "Hindi-English code-mixed")

    def test_analytics_records_successful_handoff(self):
        call_id = record_call_start("user-1", "session-1", "browser", database_path=self.db)
        self.assertTrue(record_handoff(call_id, "requested", self.db))
        self.assertTrue(record_handoff(call_id, "success", self.db))
        connection = sqlite3.connect(self.db)
        try:
            row = connection.execute("SELECT agent_role,handoff_requested,handoff_success,handoff_failure FROM calls WHERE call_id=?", (call_id,)).fetchone()
        finally:
            connection.close()
        self.assertEqual(row, ("scheme_specialist", 1, 1, 0))


if __name__ == "__main__":
    unittest.main()
