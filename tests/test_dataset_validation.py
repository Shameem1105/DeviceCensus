from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class DatasetValidationTests(unittest.TestCase):
    """Validate that the collected dataset artifacts exist, reconcile, and meet targets."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data_dir = PROJECT_ROOT / "data"
        cls.processed_dir = cls.data_dir / "processed"
        cls.raw_dir = cls.data_dir / "raw"
        cls.summary_path = cls.processed_dir / "collection_summary.json"

        if not cls.summary_path.is_file():
            raise unittest.SkipTest(
                f"Collection summary not found at {cls.summary_path}; skipping dataset validation."
            )

        with cls.summary_path.open(encoding="utf-8") as f:
            cls.summary = json.load(f)

    def test_summary_targets_are_met(self) -> None:
        targets = self.summary.get("dataset_size_targets", {})
        self.assertIn("integration_manifests", targets)
        self.assertIn("source_files", targets)

        manifests_met = targets["integration_manifests"]["met"]
        manifests_actual = targets["integration_manifests"]["actual"]
        manifests_target = targets["integration_manifests"]["target"]
        self.assertTrue(
            manifests_met,
            f"Expected at least {manifests_target} manifests, got {manifests_actual}",
        )
        self.assertGreaterEqual(manifests_actual, 1500)

        sources_met = targets["source_files"]["met"]
        sources_actual = targets["source_files"]["actual"]
        sources_target = targets["source_files"]["target"]
        self.assertTrue(
            sources_met,
            f"Expected at least {sources_target} source files, got {sources_actual}",
        )
        self.assertGreaterEqual(sources_actual, 19000)

    def test_integrations_files_reconcile_with_summary(self) -> None:
        json_path = self.processed_dir / "integrations.json"
        csv_path = self.processed_dir / "integrations.csv"
        self.assertTrue(json_path.is_file(), "integrations.json should exist")
        self.assertTrue(csv_path.is_file(), "integrations.csv should exist")

        with json_path.open(encoding="utf-8") as f:
            integrations_json = json.load(f)
        self.assertEqual(
            len(integrations_json),
            self.summary["successfully_parsed_manifests"],
            "integrations.json count must match summary successfully_parsed_manifests",
        )

        with csv_path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(
            len(rows),
            self.summary["successfully_parsed_manifests"],
            "integrations.csv row count must match summary successfully_parsed_manifests",
        )

        # Check provenance and key fields
        expected_sha = self.summary["source_commit_sha"]
        for item in integrations_json[:50]:  # sample check
            self.assertEqual(item["source_commit_sha"], expected_sha)
            self.assertTrue(item["manifest_path"].endswith("manifest.json"))
            self.assertIsInstance(item["domain"], str)

    def test_source_inventory_reconciles_with_summary(self) -> None:
        inventory_path = self.processed_dir / "source_inventory.csv"
        self.assertTrue(inventory_path.is_file(), "source_inventory.csv should exist")

        with inventory_path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(
            len(rows),
            self.summary["source_files_inventoried"],
            "source_inventory.csv row count must match summary source_files_inventoried",
        )

        # Check deterministic ordering
        paths = [r["relative_path"] for r in rows]
        self.assertEqual(paths, sorted(paths), "source_inventory.csv must be deterministically sorted")

    def test_code_chunks_reconcile_and_have_valid_structure(self) -> None:
        chunks_path = self.processed_dir / "code_chunks.jsonl"
        if not chunks_path.is_file():
            raise unittest.SkipTest("code_chunks.jsonl not present on disk.")

        count = 0
        expected_sha = self.summary["source_commit_sha"]
        with chunks_path.open(encoding="utf-8") as f:
            for idx, line in enumerate(f):
                count += 1
                if idx < 100:  # sample first 100 chunks for structure
                    chunk = json.loads(line)
                    self.assertIn("chunk_id", chunk)
                    self.assertEqual(chunk["source_commit_sha"], expected_sha)
                    self.assertGreaterEqual(chunk["start_line"], 1)
                    self.assertGreaterEqual(chunk["end_line"], chunk["start_line"])
                    self.assertIsInstance(chunk["text"], str)

        self.assertEqual(
            count,
            self.summary["code_chunks_generated"],
            "code_chunks.jsonl count must match summary code_chunks_generated",
        )

    def test_raw_manifests_reconcile_with_summary(self) -> None:
        raw_manifests_path = self.raw_dir / "integration_manifests.jsonl"
        if not raw_manifests_path.is_file():
            raise unittest.SkipTest("integration_manifests.jsonl not present on disk.")

        count = 0
        with raw_manifests_path.open(encoding="utf-8") as f:
            for _line in f:
                count += 1
        self.assertEqual(
            count,
            self.summary["successfully_parsed_manifests"],
            "raw manifests count must match successfully_parsed_manifests",
        )


if __name__ == "__main__":
    unittest.main()

