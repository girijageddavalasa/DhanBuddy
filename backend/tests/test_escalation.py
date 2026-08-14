import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from escalation import (
    create_escalation, generate_reference_id, get_escalation_status,
    has_escalation_consent, list_escalations, sanitize, should_escalate,
    update_escalation_status, urgency_for,
)


class EscalationTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "data"; root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.db = Path(self.temp.name) / "escalation.db"

    def tearDown(self): self.temp.cleanup()

    def create(self, issue="suspected_fraud", consent="yes"):
        return create_escalation(
            "caller-test", issue, "Possible unauthorized transaction",
            "User reported a transaction they do not recognize.",
            "Recorded transaction history was checked.", urgency_for(issue),
            "English", "phone", consent, self.db,
        )

    def test_fraud_and_dispute_triggers(self):
        self.assertEqual(should_escalate("I don't recognize this transaction"), "suspected_fraud")
        self.assertEqual(should_escalate("I want to dispute this transaction"), "financial_dispute")
        self.assertEqual(urgency_for("suspected_fraud"), "high")
        self.assertEqual(urgency_for("financial_dispute"), "medium")

    def test_yes_no_and_unclear_consent(self):
        self.assertTrue(has_escalation_consent("Yes"))
        self.assertFalse(self.create(consent="no")["created"])
        self.assertFalse(self.create(consent="maybe")["created"])
        self.assertEqual(list_escalations(self.db), [])

    def test_redaction(self):
        result = sanitize("OTP is 123456, PIN: 9876 and account 1234 5678 9012 3456")
        self.assertNotIn("123456", result); self.assertNotIn("9876", result)
        self.assertNotIn("1234 5678 9012 3456", result)

    def test_reference_id(self):
        reference = generate_reference_id(datetime(2026, 8, 13, tzinfo=timezone.utc))
        self.assertRegex(reference, r"^DHN-20260813-[A-Z0-9]{4}$")

    def test_create_duplicate_status_and_update(self):
        first = self.create(); duplicate = self.create()
        self.assertTrue(first["created"]); self.assertTrue(duplicate["duplicate"])
        self.assertEqual(first["reference_id"], duplicate["reference_id"])
        status = get_escalation_status("caller-test", first["reference_id"], self.db)
        self.assertEqual(status["status"], "open")
        self.assertTrue(update_escalation_status(first["reference_id"], "in_progress", self.db))
        self.assertEqual(get_escalation_status("caller-test", first["reference_id"], self.db)["status"], "in_progress")

    def test_normal_question_does_not_trigger_or_create(self):
        self.assertIsNone(should_escalate("Where did I spend the most?"))
        self.assertEqual(list_escalations(self.db), [])

    def test_stored_summary_contains_no_credential_values(self):
        result = create_escalation(
            "caller-private", "suspected_fraud", "OTP is 123456",
            "PIN 9876 and account 1234567890123456", "CVV: 111", "high",
            "English", "phone", "yes", self.db,
        )
        self.assertTrue(result["created"])
        stored = " ".join(str(value) for value in list_escalations(self.db)[0].values())
        for secret in ("123456", "9876", "1234567890123456", "111"):
            self.assertNotIn(secret, stored)


if __name__ == "__main__": unittest.main()
