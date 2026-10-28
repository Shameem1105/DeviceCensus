"""Collect Home Assistant integration metadata and source-code chunks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ELIGIBLE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".scss",
    ".sh",
    ".sql",
}
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".nox",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "env",
    "generated",
    "node_modules",
    "site-packages",
    "target",
    "venv",
    "virtualenv",
}
MANIFEST_FIELDS = (
    "domain",
    "name",
    "iot_class",
    "quality_scale",
    "integration_type",
    "config_flow",
    "requirements",
    "dependencies",
    "after_dependencies",
    "codeowners",
)
INTEGRATION_CSV_FIELDS = (
    "domain",
    "name",
    "iot_class",
    "quality_scale",
    "integration_type",
    "config_flow",
    "requirements",
    "dependencies",
    "after_dependencies",
    "codeowners",
    "manifest_path",
    "source_commit_sha",
    "python_file_count",
    "has_sensor_py",
    "has_config_flow_py",
    "has_coordinator_py",
    "original_manifest",
)
SOURCE_CSV_FIELDS = (
    "relative_path",
    "extension",
    "size_bytes",
    "is_python",
    "is_integration_file",
    "integration_domain",
    "source_commit_sha",
)


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _record_error(
    errors: list[dict[str, str]],
    stage: str,
    path: Path | str,
    error: Exception | str,
) -> None:
    errors.append(
        {
            "stage": stage,
            "path": str(path),
            "error_type": type(error).__name__ if isinstance(error, Exception) else "Error",
            "message": str(error),
        }
    )


def _walk_repository(
    root: Path,
    errors: list[dict[str, str]],
) -> tuple[list[Path], list[Path]]:
    source_files: list[Path] = []
    manifest_files: list[Path] = []
    components_root = root / "homeassistant" / "components"

    def on_walk_error(error: OSError) -> None:
        _record_error(errors, "repository_walk", error.filename or root, error)

    for current, directories, filenames in os.walk(root, onerror=on_walk_error):
        directories[:] = sorted(
            name for name in directories if name.lower() not in EXCLUDED_DIRECTORIES
        )
        current_path = Path(current)
        for filename in sorted(filenames):
            file_path = current_path / filename
            if (
                filename == "manifest.json"
                and file_path.is_relative_to(components_root)
            ):
                manifest_files.append(file_path)
            if file_path.suffix.lower() in ELIGIBLE_EXTENSIONS:
                source_files.append(file_path)

    return source_files, manifest_files


def _integration_for_path(relative_path: str) -> str | None:
    parts = Path(relative_path).parts
    if len(parts) >= 3 and parts[0:2] == ("homeassistant", "components"):
        return parts[2]
    return None


def _load_manifests(
    manifest_paths: list[Path],
    root: Path,
    source_commit_sha: str,
    errors: list[dict[str, str]],
    python_files_by_directory: dict[Path, list[Path]],
) -> list[dict[str, Any]]:
    integrations: list[dict[str, Any]] = []
    for manifest_path in sorted(manifest_paths, key=lambda path: _relative_path(path, root)):
        relative_path = _relative_path(manifest_path, root)
        try:
            with manifest_path.open(encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
        except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
            _record_error(errors, "manifest_parse", relative_path, error)
            continue

        if not isinstance(manifest, dict):
            _record_error(
                errors,
                "manifest_parse",
                relative_path,
                "Manifest JSON root must be an object",
            )
            continue

        integration_root = manifest_path.parent
        python_paths = python_files_by_directory.get(integration_root, [])
        has_sensor = False
        has_config_flow = False
        has_coordinator = False
        for candidate in python_paths:
            if candidate.parent == integration_root:
                has_sensor = has_sensor or candidate.name == "sensor.py"
                has_config_flow = has_config_flow or candidate.name == "config_flow.py"
            has_coordinator = has_coordinator or candidate.name == "coordinator.py"

        record: dict[str, Any] = {
            field: manifest.get(field) for field in MANIFEST_FIELDS
        }
        record.update(
            {
                "manifest_path": relative_path,
                "source_commit_sha": source_commit_sha,
                "python_file_count": len(python_paths),
                "has_sensor_py": has_sensor,
                "has_config_flow_py": has_config_flow,
                "has_coordinator_py": has_coordinator,
                "original_manifest": manifest,
            }
        )
        integrations.append(record)

    return integrations


def _inventory_sources(
    source_paths: list[Path],
    root: Path,
    source_commit_sha: str,
    errors: list[dict[str, str]],
) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for file_path in sorted(source_paths, key=lambda path: _relative_path(path, root)):
        relative_path = _relative_path(file_path, root)
        try:
            size_bytes = file_path.stat().st_size
        except OSError as error:
            _record_error(errors, "source_inventory", relative_path, error)
            continue

        integration_domain = _integration_for_path(relative_path)
        inventory.append(
            {
                "relative_path": relative_path,
                "extension": file_path.suffix.lower(),
                "size_bytes": size_bytes,
                "is_python": file_path.suffix.lower() == ".py",
                "is_integration_file": integration_domain is not None,
                "integration_domain": integration_domain,
                "source_commit_sha": source_commit_sha,
            }
        )
    return inventory


def _make_chunks(
    inventory: list[dict[str, Any]],
    root: Path,
    source_commit_sha: str,
    chunk_size: int,
    chunk_overlap: int,
    errors: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], int]:
    chunks: list[dict[str, Any]] = []
    indexed_python_files = 0
    python_paths = (
        row
        for row in inventory
        if row["is_python"] and row["is_integration_file"]
    )
    for row in python_paths:
        file_path = root.joinpath(*Path(row["relative_path"]).parts)
        try:
            with file_path.open(encoding="utf-8", newline="") as source_file:
                lines = source_file.readlines()
        except (OSError, UnicodeError) as error:
            _record_error(errors, "code_chunk_read", row["relative_path"], error)
            continue

        indexed_python_files += 1
        start = 0
        while start < len(lines):
            end = min(start + chunk_size, len(lines))
            start_line = start + 1
            end_line = end
            identity = (
                f"{source_commit_sha}\0{row['relative_path']}\0"
                f"{start_line}\0{end_line}"
            )
            chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "relative_path": row["relative_path"],
                    "integration_domain": row["integration_domain"],
                    "start_line": start_line,
                    "end_line": end_line,
                    "text": "".join(lines[start:end]),
                    "source_commit_sha": source_commit_sha,
                }
            )
            if end == len(lines):
                break
            start = end - chunk_overlap

    return chunks, indexed_python_files


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_csv(
    path: Path,
    fields: tuple[str, ...],
    records: list[dict[str, Any]],
    json_fields: set[str] | None = None,
) -> None:
    json_fields = json_fields or set()
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    key: (
                        json.dumps(record.get(key), ensure_ascii=False)
                        if key in json_fields
                        else record.get(key)
                    )
                    for key in fields
                }
            )


def collect_data(
    core_root: Path,
    output_root: Path,
    source_commit_sha: str,
    chunk_size: int = 100,
    chunk_overlap: int = 15,
    target_source_files: int = 19_000,
    target_manifests: int = 1_500,
    collection_timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Collect and write the dataset; the returned value is the summary."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and less than chunk_size")
    if not core_root.is_dir():
        raise FileNotFoundError(f"Home Assistant Core directory not found: {core_root}")

    root = core_root.resolve()
    collection_errors: list[dict[str, str]] = []
    source_paths, manifest_paths = _walk_repository(root, collection_errors)
    components_root = root / "homeassistant" / "components"
    python_files_by_directory: dict[Path, list[Path]] = {}
    for source_path in source_paths:
        if source_path.suffix.lower() != ".py" or not source_path.is_relative_to(
            components_root
        ):
            continue
        directory = source_path.parent
        while directory.is_relative_to(components_root):
            python_files_by_directory.setdefault(directory, []).append(source_path)
            directory = directory.parent
    integrations = _load_manifests(
        manifest_paths,
        root,
        source_commit_sha,
        collection_errors,
        python_files_by_directory,
    )
    inventory = _inventory_sources(
        source_paths, root, source_commit_sha, collection_errors
    )
    chunks, indexed_python_files = _make_chunks(
        inventory,
        root,
        source_commit_sha,
        chunk_size,
        chunk_overlap,
        collection_errors,
    )

    raw_dir = output_root / "raw"
    processed_dir = output_root / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_manifests = [
        {
            "source_path": integration["manifest_path"],
            "source_commit_sha": source_commit_sha,
            "manifest": integration["original_manifest"],
        }
        for integration in integrations
    ]
    manifest_errors = [
        error for error in collection_errors if error["stage"] == "manifest_parse"
    ]
    non_manifest_errors = [
        error for error in collection_errors if error["stage"] != "manifest_parse"
    ]
    _write_jsonl(raw_dir / "integration_manifests.jsonl", raw_manifests)
    _write_jsonl(processed_dir / "manifest_errors.jsonl", manifest_errors)
    _write_jsonl(processed_dir / "collection_errors.jsonl", non_manifest_errors)
    _write_jsonl(processed_dir / "code_chunks.jsonl", chunks)
    _write_csv(
        processed_dir / "integrations.csv",
        INTEGRATION_CSV_FIELDS,
        integrations,
        set(MANIFEST_FIELDS[6:]) | {"original_manifest"},
    )
    with (processed_dir / "integrations.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as output_file:
        json.dump(integrations, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")
    _write_csv(
        processed_dir / "source_inventory.csv",
        SOURCE_CSV_FIELDS,
        inventory,
    )

    domains = sorted(
        {
            integration["domain"]
            for integration in integrations
            if isinstance(integration["domain"], str)
        }
    )
    python_files = sum(1 for row in inventory if row["is_python"])
    integration_python_files = sum(
        1
        for row in inventory
        if row["is_python"] and row["is_integration_file"]
    )
    timestamp = collection_timestamp or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("collection_timestamp must include a timezone")
    timestamp_text = (
        timestamp.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
    error_counts = dict(sorted(Counter(error["stage"] for error in collection_errors).items()))
    summary: dict[str, Any] = {
        "collection_timestamp_utc": timestamp_text,
        "source_repository": str(root),
        "source_commit_sha": source_commit_sha,
        "total_manifests_discovered": len(manifest_paths),
        "successfully_parsed_manifests": len(integrations),
        "manifest_parsing_failures": len(manifest_errors),
        "unique_integration_domains": len(domains),
        "integration_domains": domains,
        "source_files_inventoried": len(inventory),
        "python_files_inventoried": python_files,
        "integration_python_files_inventoried": integration_python_files,
        "integration_python_files_indexed": indexed_python_files,
        "code_chunks_generated": len(chunks),
        "skipped_files": sum(
            1
            for error in collection_errors
            if error["stage"] in {"source_inventory", "code_chunk_read"}
        ),
        "collection_error_count": len(collection_errors),
        "collection_error_counts_by_stage": error_counts,
        "dataset_size_targets": {
            "source_files": {
                "target": target_source_files,
                "actual": len(inventory),
                "met": len(inventory) >= target_source_files,
            },
            "integration_manifests": {
                "target": target_manifests,
                "actual": len(integrations),
                "met": len(integrations) >= target_manifests,
                "actual_basis": "successfully parsed manifests",
            },
        },
    }
    with (processed_dir / "collection_summary.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as summary_file:
        json.dump(summary, summary_file, ensure_ascii=False, indent=2)
        summary_file.write("\n")

    return summary


def get_source_commit_sha(core_root: Path) -> str:
    """Return HEAD of the local Core repository or fail with command details."""
    if not core_root.is_dir():
        raise FileNotFoundError(f"Home Assistant Core directory not found: {core_root}")
    result = subprocess.run(
        ["git", "-C", str(core_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or "Git returned a non-zero exit status"
        raise ValueError(f"Unable to read source commit from {core_root}: {detail}")
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--core-root",
        type=Path,
        default=(project_root / "core") if (project_root / "core").is_dir() else (project_root.parent / "core"),
        help="Path to the locally cloned Home Assistant Core repository",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=project_root / "data",
        help="Directory for raw and processed collection artifacts",
    )
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--chunk-overlap", type=int, default=15)
    args = parser.parse_args(argv)

    try:
        commit_sha = get_source_commit_sha(args.core_root)
        summary = collect_data(
            args.core_root,
            args.output_root,
            commit_sha,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"Collection failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
