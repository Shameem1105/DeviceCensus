from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.collect_data import collect_data


class CollectDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.core_root = self.root / "core"
        self.components_root = self.core_root / "homeassistant" / "components"
        self.components_root.mkdir(parents=True)
        self.output_root = self.root / "data"
        self.commit_sha = "a" * 40

    def write(self, relative_path: str, content: str) -> Path:
        path = self.core_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as output_file:
            output_file.write(content)
        return path

    def collect(self) -> dict[str, Any]:
        return collect_data(
            self.core_root,
            self.output_root,
            self.commit_sha,
            chunk_size=3,
            chunk_overlap=1,
            target_source_files=4,
            target_manifests=2,
            collection_timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

    def test_valid_manifest_preserves_source_and_commit(self) -> None:
        self.write(
            "homeassistant/components/example/manifest.json",
            json.dumps(
                {
                    "domain": "example",
                    "name": "Example",
                    "requirements": ["sample==1.0"],
                    "codeowners": ["@maintainer"],
                }
            ),
        )
        self.write("homeassistant/components/example/sensor.py", "SENSOR = True\n")
        self.write(
            "homeassistant/components/example/sub/coordinator.py",
            "class Coordinator:\n    pass\n",
        )
        summary = self.collect()

        self.assertEqual(summary["successfully_parsed_manifests"], 1)
        with (self.output_root / "processed" / "integrations.json").open(
            encoding="utf-8"
        ) as input_file:
            integration = json.load(input_file)[0]
        self.assertEqual(
            integration["manifest_path"],
            "homeassistant/components/example/manifest.json",
        )
        self.assertEqual(integration["source_commit_sha"], self.commit_sha)
        self.assertEqual(integration["python_file_count"], 2)
        self.assertTrue(integration["has_sensor_py"])
        self.assertFalse(integration["has_config_flow_py"])
        self.assertTrue(integration["has_coordinator_py"])
        with (self.output_root / "raw" / "integration_manifests.jsonl").open(
            encoding="utf-8"
        ) as input_file:
            raw = json.loads(input_file.readline())
        self.assertEqual(raw["source_path"], integration["manifest_path"])
        self.assertEqual(raw["manifest"], integration["original_manifest"])
        self.assertEqual(raw["source_commit_sha"], self.commit_sha)

    def test_invalid_json_is_recorded_and_missing_optional_fields_are_null(self) -> None:
        self.write("homeassistant/components/bad/manifest.json", "{broken")
        self.write(
            "homeassistant/components/sparse/manifest.json",
            json.dumps({"domain": "sparse"}),
        )
        summary = self.collect()

        self.assertEqual(summary["total_manifests_discovered"], 2)
        self.assertEqual(summary["successfully_parsed_manifests"], 1)
        self.assertEqual(summary["manifest_parsing_failures"], 1)
        error_lines = (
            self.output_root / "processed" / "manifest_errors.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(error_lines), 1)
        self.assertIn("homeassistant/components/bad/manifest.json", error_lines[0])
        with (self.output_root / "processed" / "integrations.json").open(
            encoding="utf-8"
        ) as input_file:
            integration = json.load(input_file)[0]
        self.assertIsNone(integration["name"])
        self.assertIsNone(integration["iot_class"])
        self.assertEqual(integration["original_manifest"], {"domain": "sparse"})

    def test_inventory_and_code_chunk_lines_overlap_and_counts(self) -> None:
        self.write(
            "homeassistant/components/example/manifest.json",
            json.dumps({"domain": "example"}),
        )
        self.write(
            "homeassistant/components/example/client.py",
            "line 1\nline 2\nline 3\nline 4\nline 5\n",
        )
        self.write("homeassistant/core.py", "pass\n")
        self.write("homeassistant/components/example/__pycache__/cached.py", "bad\n")
        summary = self.collect()

        self.assertEqual(summary["source_files_inventoried"], 3)
        self.assertEqual(summary["python_files_inventoried"], 2)
        self.assertEqual(summary["integration_python_files_inventoried"], 1)
        self.assertEqual(summary["integration_python_files_indexed"], 1)
        self.assertEqual(summary["code_chunks_generated"], 2)
        with (self.output_root / "processed" / "code_chunks.jsonl").open(
            encoding="utf-8"
        ) as input_file:
            chunks = [json.loads(line) for line in input_file]
        self.assertEqual(
            [(chunk["start_line"], chunk["end_line"]) for chunk in chunks],
            [(1, 3), (3, 5)],
        )
        self.assertEqual(chunks[0]["text"], "line 1\nline 2\nline 3\n")
        self.assertEqual(chunks[1]["text"], "line 3\nline 4\nline 5\n")
        self.assertEqual(chunks[0]["source_commit_sha"], self.commit_sha)
        self.assertEqual(chunks[0]["integration_domain"], "example")

    def test_csv_json_output_and_target_counts_are_accurate(self) -> None:
        self.write(
            "homeassistant/components/example/manifest.json",
            json.dumps({"domain": "example", "name": "Name, with comma"}),
        )
        self.write("homeassistant/components/example/sensor.py", "pass\n")
        self.write("homeassistant/helpers.py", "pass\n")
        summary = self.collect()

        self.assertEqual(summary["collection_timestamp_utc"], "2026-01-02T00:00:00Z")
        self.assertFalse(summary["dataset_size_targets"]["source_files"]["met"])
        self.assertFalse(
            summary["dataset_size_targets"]["integration_manifests"]["met"]
        )
        with (self.output_root / "processed" / "integrations.csv").open(
            encoding="utf-8", newline=""
        ) as input_file:
            integration_csv = list(csv.DictReader(input_file))
        self.assertEqual(integration_csv[0]["name"], "Name, with comma")
        self.assertEqual(
            json.loads(integration_csv[0]["original_manifest"])["domain"], "example"
        )
        with (self.output_root / "processed" / "source_inventory.csv").open(
            encoding="utf-8", newline=""
        ) as input_file:
            inventory_csv = list(csv.DictReader(input_file))
        self.assertEqual(
            [row["relative_path"] for row in inventory_csv],
            sorted(row["relative_path"] for row in inventory_csv),
        )
        self.assertEqual(summary["source_files_inventoried"], len(inventory_csv))
        self.assertEqual(summary["unique_integration_domains"], 1)

    def test_output_ordering_and_chunk_ids_are_deterministic(self) -> None:
        self.write(
            "homeassistant/components/zeta/manifest.json",
            json.dumps({"domain": "zeta"}),
        )
        self.write(
            "homeassistant/components/alpha/manifest.json",
            json.dumps({"domain": "alpha"}),
        )
        self.write("homeassistant/components/zeta/z.py", "z = 1\n")
        self.write("homeassistant/components/alpha/a.py", "a = 1\n")
        first_summary = self.collect()
        chunks_path = self.output_root / "processed" / "code_chunks.jsonl"
        first_chunks = chunks_path.read_text(encoding="utf-8")
        first_integrations = (
            self.output_root / "processed" / "integrations.json"
        ).read_text(encoding="utf-8")

        second_summary = self.collect()
        self.assertEqual(
            first_summary["source_files_inventoried"],
            second_summary["source_files_inventoried"],
        )
        self.assertEqual(first_chunks, chunks_path.read_text(encoding="utf-8"))
        self.assertEqual(
            first_integrations,
            (self.output_root / "processed" / "integrations.json").read_text(
                encoding="utf-8"
            ),
        )
        records = json.loads(first_integrations)
        self.assertEqual(
            [record["manifest_path"] for record in records],
            sorted(record["manifest_path"] for record in records),
        )

    def test_invalid_chunk_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "chunk_overlap"):
            collect_data(
                self.core_root,
                self.output_root,
                self.commit_sha,
                chunk_size=2,
                chunk_overlap=2,
            )


if __name__ == "__main__":
    unittest.main()
