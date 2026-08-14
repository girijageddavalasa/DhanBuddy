import asyncio
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from telephony.outbound import build_call_opening, make_outbound_call, select_provider, validate_request
from telephony.preferences import is_opted_out, record_opt_out
from telephony.provider import CallResult, TelephonyProvider


class MockProvider(TelephonyProvider):
    name = "mock"
    def __init__(self, result=None): self.result = result or CallResult("answered", "mock")
    async def place_call(self, request): return self.result


class OutboundTests(unittest.TestCase):
    def test_missing_and_invalid_recipient(self):
        with self.assertRaises(ValueError): validate_request("", "financial_check_in", "user")
        with self.assertRaises(ValueError): validate_request("9876543210", "financial_check_in", "user")

    def test_missing_provider_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): select_provider("linphone")

    def test_provider_selection(self):
        with patch.dict(os.environ, {"LIVEKIT_SIP_OUTBOUND_TRUNK_ID": "ST_test"}, clear=True):
            self.assertEqual(select_provider("linphone").name, "linphone")

    def test_mock_success_and_failure(self):
        success = asyncio.run(make_outbound_call("+919876543210", "financial_check_in", "user", MockProvider(), True))
        self.assertEqual(success.status, "answered")
        failed_provider = MockProvider(CallResult("failed", "mock", "telephony_provider_unavailable"))
        failure = asyncio.run(make_outbound_call("+919876543210", "financial_check_in", "user", failed_provider, True))
        self.assertEqual(failure.reason, "telephony_provider_unavailable")

    def test_opt_out(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "data") as directory:
            path = Path(directory) / "preferences.json"
            record_opt_out("user", path)
            self.assertTrue(is_opted_out("user", path))

    def test_opening_has_who_why_and_control(self):
        opening = build_call_opening("financial_check_in")
        self.assertIn("I'm DhanBuddy", opening)
        self.assertIn("financial check-in", opening)
        self.assertIn("end the call anytime", opening)

    def test_logs_do_not_contain_secrets(self):
        with self.assertLogs("dhanbuddy.outbound", logging.WARNING) as logs:
            asyncio.run(make_outbound_call("bad", "financial_check_in", "user", confirmed_opt_in=True))
        output = " ".join(logs.output)
        self.assertNotIn("TWILIO_AUTH_TOKEN", output)
        self.assertNotIn("LIVEKIT_API_SECRET", output)


if __name__ == "__main__": unittest.main()
