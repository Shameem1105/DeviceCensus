# Data Dictionary

All paths in generated records are relative to the Home Assistant Core repository root. The source commit SHA identifies the exact checkout that was collected. Collection timestamps are in UTC. Generated outputs are empirical observations of that checkout, not claims about device runtime behavior.

## Raw Integration Manifests

`data/raw/integration_manifests.jsonl` contains one record per successfully parsed manifest:

| Field | Type | Description |
|---|---|---|
| `source_path` | string | Observed repository-relative path to the manifest (e.g., `homeassistant/components/<domain>/manifest.json`). |
| `source_commit_sha` | string | Observed Git `HEAD` SHA for the source checkout. |
| `manifest` | object | Original parsed JSON object, preserved verbatim without editing or filling missing keys. |

Invalid JSON, unreadable manifests, and JSON roots that are not objects are omitted from this raw parsed-manifest file and recorded in `data/processed/manifest_errors.jsonl`.

## Integration Records

`data/processed/integrations.json` is a JSON array of integration records; `data/processed/integrations.csv` contains the same tabular fields, with list/object-valued columns serialized as JSON strings.

| Field | Type | Description |
|---|---|---|
| `domain` | string | Declared integration domain (e.g., `fronius`, `hue`). |
| `name` | string | Human-readable title of the integration. |
| `iot_class` | string \| null | Declared IoT connectivity class (e.g., `local_polling`, `cloud_polling`, `local_push`, `cloud_push`, `assumed_state`). |
| `quality_scale` | string \| null | Declared Home Assistant integration quality scale (e.g., `platinum`, `gold`, `silver`, `internal`, `legacy`). |
| `integration_type` | string \| null | Architectural classification (e.g., `hub`, `device`, `service`, `virtual`, `system`). |
| `config_flow` | boolean \| null | Whether the manifest declares support for UI config flow (`true` / `false` / `null`). |
| `requirements` | list[string] \| null | External PyPI packages required by the integration. |
| `dependencies` | list[string] \| null | Other Home Assistant components required as prerequisites. |
| `after_dependencies` | list[string] \| null | Components to load after this integration if present. |
| `codeowners` | list[string] \| null | GitHub handles or team tags responsible for the component. |
| `manifest_path` | string | Observed manifest path relative to the Core repository root. |
| `source_commit_sha` | string | Git commit SHA of the collected Home Assistant Core repository. |
| `python_file_count` | integer | Count of `.py` files found below the manifest's integration directory (excluding configured generated/cache directories). |
| `has_sensor_py` | boolean | Whether a top-level `sensor.py` exists in the integration directory (file presence indicator only). |
| `has_config_flow_py` | boolean | Whether a top-level `config_flow.py` exists in the integration directory (file presence indicator only). |
| `has_coordinator_py` | boolean | Whether any descendant Python file is named `coordinator.py` (file presence indicator only). |
| `original_manifest` | object | Complete original parsed manifest object, preserved for provenance. |

> [!NOTE]
> File presence flags (`has_sensor_py`, `has_coordinator_py`, etc.) indicate file existence only. They do not prove runtime polling behavior, Modbus support, energy sensor availability, or error recovery correctness.

## Source Inventory

`data/processed/source_inventory.csv` inventories all eligible source and configuration files across Home Assistant Core. Eligible extensions: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.json`, `.yaml`, `.yml`, `.toml`, `.html`, `.css`, `.scss`, `.sh`, and `.sql`.

Exclusions: `.git`, `node_modules`, `.venv`, `venv`, `env`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `build`, `dist`, `coverage`, and `generated` directories.

| Field | Type | Description |
|---|---|---|
| `relative_path` | string | Path relative to the Core repository root. |
| `extension` | string | Lowercase file extension (e.g., `.py`, `.yaml`). |
| `size_bytes` | integer | File size in bytes from filesystem metadata. |
| `is_python` | boolean | True if file has `.py` extension. |
| `is_integration_file` | boolean | True if file resides under `homeassistant/components/<domain>/`. |
| `integration_domain` | string \| null | Component directory name extracted from the path when identifiable. |
| `source_commit_sha` | string | Source commit revision SHA. |

## Code Chunks

`data/processed/code_chunks.jsonl` contains line-bounded chunks from readable Python files under `homeassistant/components/`. Configurable via `--chunk-size` (default: 100 lines) and `--chunk-overlap` (default: 15 lines). Line numbers are 1-based and inclusive.

| Field | Type | Description |
|---|---|---|
| `chunk_id` | string | SHA-256 hash of `{source_commit_sha}\0{relative_path}\0{start_line}\0{end_line}`; stable for a given revision and chunk configuration. |
| `relative_path` | string | Path to the source file relative to the Core repository. |
| `integration_domain` | string \| null | Integration domain derived from path. |
| `start_line` | integer | 1-based inclusive start line number in the source file. |
| `end_line` | integer | 1-based inclusive end line number in the source file. |
| `text` | string | Exact decoded source code text for lines `[start_line, end_line]`. |
| `source_commit_sha` | string | Observed source commit revision. |

## Errors and Collection Summary

- `data/processed/manifest_errors.jsonl`: Records any manifest discovery or JSON parsing failures (`stage`, `path`, `error_type`, `message`).
- `data/processed/collection_errors.jsonl`: Records filesystem traversal, stat, or source-read errors with the same schema.
- `data/processed/collection_summary.json`: High-level execution metrics and size target verification.

| Field | Type | Description |
|---|---|---|
| `collection_timestamp_utc` | string | ISO 8601 UTC timestamp of pipeline execution. |
| `source_repository` | string | Local file path to the Home Assistant Core repository used. |
| `source_commit_sha` | string | Observed Git commit SHA of the source checkout. |
| `total_manifests_discovered` | integer | Number of `manifest.json` files found under `homeassistant/components/`. |
| `successfully_parsed_manifests`| integer | Number of candidates parsed as valid JSON objects. |
| `manifest_parsing_failures` | integer | Number of manifest candidates that failed parsing. |
| `unique_integration_domains` | integer | Count of distinct non-null manifest domain names. |
| `integration_domains` | list[string] | Alphabetically sorted list of all unique domains. |
| `source_files_inventoried` | integer | Number of eligible source files traversed and statted. |
| `python_files_inventoried` | integer | Number of inventoried `.py` files. |
| `integration_python_files_inventoried` | integer | Number of inventoried `.py` files under `homeassistant/components/`. |
| `integration_python_files_indexed` | integer | Number of component Python files successfully chunked. |
| `code_chunks_generated` | integer | Total number of code chunks generated. |
| `skipped_files` | integer | Files skipped due to read or stat errors. |
| `collection_error_count` | integer | Total error count across all stages. |
| `collection_error_counts_by_stage` | object | Error counts broken down by stage. |
| `dataset_size_targets` | object | Target checks: `integration_manifests` (>= 1,500) and `source_files` (>= 19,000). |

## Artifact Storage and Git Hygiene

| Artifact | Typical Size | Recommended Git Action | Rationale |
|---|---|---|---|
| `collection_summary.json` | ~27 KB | Track in Git | Essential lightweight audit artifact tracking counts, commit SHA, and target status. |
| `manifest_errors.jsonl` | 0 KB | Track in Git | Logs parse errors; zero bytes on a clean run. |
| `collection_errors.jsonl` | 0 KB | Track in Git | Logs traversal/read errors; zero bytes on a clean run. |
| `integrations.csv` | ~964 KB | Track in Git | Primary compact tabular dataset for SQL analysis and inspection. |
| `integrations.json` | ~1.76 MB | Track in Git | Structured hierarchical manifest dataset for downstream programmatic consumption. |
| `source_inventory.csv` | ~3.15 MB | Track in Git | Complete file-level audit trail across Home Assistant Core. |
| `data/raw/integration_manifests.jsonl` | ~788 KB | Exclude from Git (`.gitignore`) | Raw dump; fully reproducible from upstream Core repository checkout. |
| `data/processed/code_chunks.jsonl` | ~69.2 MB | Exclude from Git (`.gitignore`) | Exceeds GitHub recommended file limits (>50 MB push warning threshold); reproducible on demand. |

## Baseline Cross-Check Reference

For verification against Home Assistant Core commit `fbee16b2aae664f10d819c0121575102326eaa17`:
- Manifests discovered & parsed: 1,554 (Target: >= 1,500)
- Source files inventoried: 27,376 (Target: >= 19,000)
- Component Python files: 10,567
- Code chunks generated (100 lines / 15 overlap): 22,707
- Total errors: 0
