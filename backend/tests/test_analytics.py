import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analytics import (
    CallTracker, analytics_summary, health_snapshot, record_call_end,
    record_call_start, record_latency,
)


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "data"; root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.db = Path(self.temp.name) / "analytics.db"
        self.start = datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc)

    def tearDown(self): self.temp.cleanup()

    def start_call(self, user="caller-a", channel="browser", language="English", day=0):
        return record_call_start(user, f"session-{user}-{day}", channel, language, self.db, self.start + timedelta(days=day))

    def test_call_start_and_completion_duration(self):
        call = self.start_call()
        self.assertTrue(record_call_end(call, "success", "general_question", success_reason="Task completed.", database_path=self.db, ended_at=self.start + timedelta(seconds=75)))
        summary = analytics_summary(self.db)
        self.assertEqual(summary["total_calls"], 1); self.assertEqual(summary["average_duration_seconds"], 75)

    def test_success_failed_failure_type_and_rate(self):
        success = self.start_call("caller-success")
        failure = self.start_call("caller-failure", "sip", "Hindi")
        record_call_end(success, "success", "spending_summary", success_reason="Database answer returned.", database_path=self.db, ended_at=self.start + timedelta(seconds=10))
        record_call_end(failure, "failure", failure_type="tool_failure", database_path=self.db, ended_at=self.start + timedelta(seconds=20))
        result = analytics_summary(self.db)
        self.assertEqual(result["successful_calls"], 1); self.assertEqual(result["failed_calls"], 1)
        self.assertEqual(result["success_rate"], 50); self.assertEqual(result["failure_types"]["tool_failure"], 1)

    def test_latency_recording(self):
        call = self.start_call(); self.assertTrue(record_latency(call, 321.5, self.db))
        record_call_end(call, "failure", failure_type="incomplete_task", database_path=self.db, ended_at=self.start)
        self.assertEqual(analytics_summary(self.db)["average_latency_ms"], 321.5)

    def test_tracker_defaults_to_incomplete_failure(self):
        tracker = CallTracker(self.start_call()); tracker.finish(self.db)
        result = analytics_summary(self.db)
        self.assertEqual(result["failed_calls"], 1); self.assertEqual(result["failure_types"]["incomplete_task"], 1)

    def test_empty_database(self):
        result = analytics_summary(self.db)
        self.assertEqual(result["total_calls"], 0); self.assertEqual(result["success_rate"], 0)
        self.assertIsNone(result["average_latency_ms"])

    def test_date_language_channel_and_outcome_filters(self):
        first = self.start_call("caller-one", "browser", "English", 0)
        second = self.start_call("caller-two", "sip", "Hindi", 2)
        record_call_end(first, "success", "general_question", success_reason="Done", database_path=self.db, ended_at=self.start + timedelta(seconds=5))
        record_call_end(second, "failure", failure_type="no_response", database_path=self.db, ended_at=self.start + timedelta(days=2, seconds=5))
        self.assertEqual(analytics_summary(self.db, date_from="2026-08-12")["total_calls"], 1)
        self.assertEqual(analytics_summary(self.db, language="Hindi")["total_calls"], 1)
        self.assertEqual(analytics_summary(self.db, channel="browser")["total_calls"], 1)
        self.assertEqual(analytics_summary(self.db, outcome="success")["total_calls"], 1)

    def test_health_and_privacy(self):
        health = health_snapshot(self.db, False)
        self.assertEqual(health["database_status"], "connected")
        forbidden = {"otp", "pin", "cvv", "password", "account_number", "raw_text", "transcript"}
        self.assertTrue(forbidden.isdisjoint(health))
        self.assertTrue(forbidden.isdisjoint(analytics_summary(self.db)))


if __name__ == "__main__": unittest.main()
