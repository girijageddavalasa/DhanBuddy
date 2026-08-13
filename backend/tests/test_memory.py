import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from memory import create_user, forget_me, lookup_user, save_user_memory


class MemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        test_root = Path(__file__).resolve().parents[1] / "data"
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp_directory = tempfile.TemporaryDirectory(dir=test_root)
        self.database_path = Path(self.temp_directory.name) / "dhanbuddy.db"
        self.user_id = "caller-test-user"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_create_and_lookup_user(self) -> None:
        created = create_user(self.user_id, self.database_path)
        found = lookup_user(self.user_id, self.database_path)
        self.assertEqual(created.user_id, self.user_id)
        self.assertEqual(found, created)

    def test_save_retrieve_and_update_memory(self) -> None:
        save_user_memory(self.user_id, "name", "Ravi", True, self.database_path)
        first = lookup_user(self.user_id, self.database_path)
        self.assertEqual(first.name, "Ravi")
        save_user_memory(self.user_id, "name", "Ravindra", True, self.database_path)
        updated = lookup_user(self.user_id, self.database_path)
        self.assertEqual(updated.name, "Ravindra")
        self.assertEqual(updated.facts["name"], "Ravindra")

    def test_rejects_save_without_consent(self) -> None:
        with self.assertRaises(PermissionError):
            save_user_memory(self.user_id, "name", "Ravi", False, self.database_path)
        self.assertIsNone(lookup_user(self.user_id, self.database_path))

    def test_forget_me_deletes_user_and_related_facts(self) -> None:
        save_user_memory(self.user_id, "name", "Ravi", True, self.database_path)
        self.assertTrue(forget_me(self.user_id, self.database_path))
        self.assertIsNone(lookup_user(self.user_id, self.database_path))
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM user_facts").fetchone()[0]
        self.assertEqual(count, 0)

    def test_returning_user_gets_only_stored_context(self) -> None:
        save_user_memory(self.user_id, "name", "Ravi", True, self.database_path)
        save_user_memory(
            self.user_id, "financial_goal", "save more monthly", True, self.database_path
        )
        returning = lookup_user(self.user_id, self.database_path)
        self.assertEqual(returning.name, "Ravi")
        self.assertEqual(returning.facts["financial_goal"], "save more monthly")

    def test_unknown_user_returns_no_memory(self) -> None:
        self.assertIsNone(lookup_user("caller-unknown", self.database_path))

    def test_database_survives_new_connection(self) -> None:
        save_user_memory(self.user_id, "name", "Ravi", True, self.database_path)
        reopened = lookup_user(self.user_id, Path(str(self.database_path)))
        self.assertEqual(reopened.name, "Ravi")


if __name__ == "__main__":
    unittest.main()
