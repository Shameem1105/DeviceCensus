# Data dictionary

All paths in generated records are relative to the Home Assistant Core repository
root. The source commit SHA identifies the exact checkout that was collected.
Collection timestamps are UTC. Generated outputs are observations of that checkout,
not claims about device behavior.

## Raw integration manifests

`data/raw/integration_manifests.jsonl` has one record per successfully parsed
manifest:

| Field | Meaning |
|---|---|
| `source_path` | Observed repository-relative path to the manifest. |
| `source_commit_sha` | Observed Git `HEAD` SHA for the source checkout. |
| `manifest` | Original parsed JSON object, preserved without editing or filling missing keys. |

Invalid JSON, unreadable manifests, and JSON roots that are not objects are omitted
from this raw parsed-manifest file and described in
`data/processed/manifest_errors.jsonl`.

## Integration records

`data/processed/integrations.json` is an array; `integrations.csv` has the same
fields, with list/object-valued columns serialized as JSON text.

| Field | Meaning |
|---|---|
| `domain`, `name`, `iot_class`, `quality_scale`, `integration_type`, `config_flow`, `requirements`, `dependencies`, `after_dependencies`, `codeowners` | Values read from the manifest when present; `null` means the key was absent or null. No value is inferred to fill a missing manifest field. |
| `manifest_path` | Observed manifest path relative to the Core repository. |
| `source_commit_sha` | Observed source revision. |
| `python_file_count` | Count of `.py` files found below the manifest's integration directory, excluding configured generated/cache directories. |
| `has_sensor_py` | Whether `sensor.py` exists at the integration directory's top level. This is file-presence metadata only. |
| `has_config_flow_py` | Whether `config_flow.py` exists at the integration directory's top level. This is file-presence metadata only. |
| `has_coordinator_py` | Whether any descendant Python file is named `coordinator.py`. This is file-presence metadata only. |
| `original_manifest` | Original parsed manifest object, retained for provenance. |

File-presence metadata does not verify polling, protocol support, sensor behavior,
energy capabilities, or any other runtime behavior.

## Source inventory

`data/processed/source_inventory.csv` includes one row for each eligible file that
was successfully statted. Eligible extensions are `.py`, `.js`, `.ts`, `.tsx`,
`.jsx`, `.json`, `.yaml`, `.yml`, `.toml`, `.html`, `.css`, `.scss`, `.sh`, and
`.sql`. Directories named `.git`, `node_modules`, common virtual environments,
caches, build output, and `generated` are excluded; the exact set is maintained in
`scripts/collect_data.py`.

| Field | Meaning |
|---|---|
| `relative_path` | Observed path relative to the Core repository. |
| `extension` | Lowercase filename extension. |
| `size_bytes` | Observed file size from filesystem metadata. |
| `is_python` | Whether the extension is `.py`. |
| `is_integration_file` | Whether the path is below `homeassistant/components/<directory>/`; path-derived, not a manifest claim. |
| `integration_domain` | Component directory name from the path when identifiable; it may not match a manifest's declared domain. |
| `source_commit_sha` | Observed source revision. |

Inventory counts reflect files actually traversed and statted, not a target or
estimate. Skipped files and traversal/read errors are in
`data/processed/collection_errors.jsonl`.

## Code chunks

`data/processed/code_chunks.jsonl` contains chunks from readable Python files under
`homeassistant/components/`. The default is 100 lines per chunk with 15 lines of
overlap; both values can be changed through command-line options. Start and end
line numbers are one-based and inclusive.

| Field | Meaning |
|---|---|
| `chunk_id` | SHA-256 of source commit, relative path, and line bounds; stable for that source revision and chunk layout. |
| `relative_path` | Observed source file path. |
| `integration_domain` | Component directory name derived from the path, when identifiable. |
| `start_line`, `end_line` | One-based inclusive source line bounds. |
| `text` | Exact decoded source text for those lines. |
| `source_commit_sha` | Observed source revision. |

Chunk availability is not evidence that protocols or runtime behavior have been
identified or verified.

## Errors and summary

`manifest_errors.jsonl` records each failed manifest parse with `stage`, `path`,
`error_type`, and `message`. `collection_errors.jsonl` uses the same fields for
repository traversal, inventory, and code-read failures.

`collection_summary.json` records:

| Field | Meaning |
|---|---|
| `collection_timestamp_utc` | UTC timestamp when the collection summary was generated. |
| `source_repository` | Absolute local path used for collection. |
| `source_commit_sha` | Observed Core revision. |
| `total_manifests_discovered` | Number of `manifest.json` candidates found under `homeassistant/components/`. |
| `successfully_parsed_manifests` | Number of candidates that parsed as JSON objects. |
| `manifest_parsing_failures` | Number of candidate manifests recorded as parse errors. |
| `unique_integration_domains` | Count of distinct non-null string `domain` values in valid manifests. |
| `integration_domains` | Sorted distinct non-null string manifest domain values. |
| `source_files_inventoried` | Number of eligible files successfully statted. |
| `python_files_inventoried` | Number of inventoried `.py` files. |
| `integration_python_files_inventoried` | Number of inventoried `.py` files below the components directory. |
| `integration_python_files_indexed` | Number of component Python files successfully read for chunk generation, including empty files. |
| `code_chunks_generated` | Number of emitted code chunks. |
| `skipped_files` | Count of inventory-stat and code-read failures. |
| `collection_error_count` | Total manifest and non-manifest collection errors. |
| `collection_error_counts_by_stage` | Error counts grouped by stage. |
| `dataset_size_targets` | Measured counts compared with the brief's minimums: 19,000 inventoried files and 1,500 successfully parsed manifests. |

`met` is calculated from the measured count; manifest target status is explicitly
based on successfully parsed manifests.
