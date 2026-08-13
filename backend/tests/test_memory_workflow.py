import tempfile
import unittest
from pathlib import Path

from memory import lookup_user
from memory_workflow import run_memory_workflow


class MemoryWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        test_root = Path(__file__).resolve().parents[1] / "data"
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp_directory = tempfile.TemporaryDirectory(dir=test_root)
        self.database_path = Path(self.temp_directory.name) / "workflow.db"
        self.base = {
            "user_id": "caller-workflow",
            "database_path": str(self.database_path),
        }

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_no_consent_discards_fact(self) -> None:
        result = run_memory_workflow(
            self.base
            | {
                "action": "save",
                "new_fact_key": "name",
                "new_fact_value": "Ravi",
                "memory_consent": False,
            }
        )
        self.assertFalse(result["operation_succeeded"])
        self.assertIsNone(lookup_user(self.base["user_id"], self.database_path))

    def test_consent_branch_persists_fact(self) -> None:
        result = run_memory_workflow(
            self.base
            | {
                "action": "save",
                "new_fact_key": "name",
                "new_fact_value": "Ravi",
                "memory_consent": True,
            }
        )
        self.assertTrue(result["operation_succeeded"])
        self.assertEqual(lookup_user(self.base["user_id"], self.database_path).name, "Ravi")

    def test_lookup_and_forget_branches(self) -> None:
        unknown = run_memory_workflow(self.base | {"action": "lookup"})
        self.assertIsNone(unknown["memory_lookup_result"])
        deleted = run_memory_workflow(self.base | {"action": "forget"})
        self.assertFalse(deleted["operation_succeeded"])


if __name__ == "__main__":
    unittest.main()
