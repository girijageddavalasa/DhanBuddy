import tempfile
import unittest
from pathlib import Path

from categorization import categorize, needs_confirmation
from document_parser import normalize_ocr_text, parse_document
from finance_data import (
    correct_category, export_transactions, recent_transactions, save_document,
    spending_summary,
)
from official_info import fetch_rbi_financial_education
from trusted_knowledge import Chunk, retrieve
from upload_validation import validate_image


SAMPLE = "Fresh Mart\n12/08/2026\nRice 500\nSoap 100\nTotal ₹600"


class Day5Tests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "data"
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.db = Path(self.temp.name) / "test.db"
        self.parsed = parse_document(SAMPLE)

    def tearDown(self):
        self.temp.cleanup()

    def test_ocr_normalization(self):
        self.assertEqual(normalize_ocr_text(" A \r\n\n B "), "A\nB")

    def test_upload_validation(self):
        self.assertEqual(validate_image(b"\x89PNG\r\n\x1a\ncontent"), ".png")
        with self.assertRaises(ValueError):
            validate_image(b"not an image")

    def test_structured_extraction_and_multiple_items(self):
        self.assertEqual(self.parsed["merchant"], "Fresh Mart")
        self.assertEqual(self.parsed["total_amount"], 600)
        self.assertEqual(len(self.parsed["line_items"]), 2)

    def test_missing_fields_are_none(self):
        result = parse_document("Merchant only")
        self.assertIsNone(result["date"]); self.assertIsNone(result["total_amount"])

    def test_categorization_and_low_confidence(self):
        self.assertEqual(categorize("Rice")[0], "Groceries")
        self.assertTrue(needs_confirmation(categorize("Mystery item")[1]))

    def test_persistence_correction_summary_recent_and_csv(self):
        document_id = save_document("caller-test", "original.jpg", self.parsed, self.db)
        self.assertGreater(document_id, 0)
        rows = recent_transactions("caller-test", database_path=self.db)
        self.assertEqual(len(rows), 2)
        summary = spending_summary("caller-test", self.db)
        self.assertEqual(summary["total_spending"], 600)
        self.assertEqual(summary["categories"][0]["category"], "Groceries")
        from memory import _connect
        with _connect(self.db) as connection:
            transaction_id = connection.execute("SELECT transaction_id FROM transactions LIMIT 1").fetchone()[0]
        self.assertTrue(correct_category("caller-test", transaction_id, "Food", self.db))
        output = export_transactions("caller-test", Path(self.temp.name) / "out.csv", self.db)
        self.assertIn("merchant", output.read_text(encoding="utf-8"))

    def test_empty_database(self):
        self.assertEqual(spending_summary("nobody", self.db)["categories"], [])

    def test_rag_retrieval_and_no_match(self):
        chunks = [Chunk("A budget compares income and expenses.", "rbi.txt", "2025-01-01")]
        self.assertEqual(retrieve("budget expenses", chunks)[0].source, "rbi.txt")
        self.assertEqual(retrieve("unrelated quantum", chunks), [])

    def test_external_tool_failure(self):
        import asyncio
        from unittest.mock import AsyncMock, patch
        with patch("official_info.asyncio.to_thread", new=AsyncMock(side_effect=OSError("offline"))):
            result = asyncio.run(fetch_rbi_financial_education())
        self.assertFalse(result["available"])


if __name__ == "__main__":
    unittest.main()
