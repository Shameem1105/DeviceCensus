# DeviceCensus (E-CODE-07)

A code-driven intelligence system for analysing Home Assistant integrations using structured metadata, Python/SQL analysis, and evidence-backed source-code retrieval.

## Problem

IoT engineers and developers building Home Assistant integrations need to understand how existing integrations communicate with devices, retrieve sensor data, and handle connection errors. This information is spread across more than 1,500 integration manifests and tens of thousands of Python source files, making manual research time-consuming and error-prone. General-purpose LLMs frequently hallucinate counts or make unsupported assertions when answering questions about a large codebase.

DeviceCensus solves this by extracting Home Assistant Core source code into structured datasets and combining exact Python/SQL counting with evidence-backed source-code retrieval to provide traceable answers linked to the original files.

## Who It Is For

- **IoT Engineers** at smart-energy startups developing Home Assistant integrations for solar inverters, battery storage systems, and smart meters.
- **Integration Developers** who need to research, compare, and audit existing Home Assistant patterns (coordinators, error handling, config flows) before implementing new ones.

## Signature Feature (Planned)

A natural-language AI analyst that combines exact SQL/Python counting with source-code retrieval to answer integration research questions and provide traceable evidence from the Home Assistant Core repository.

## Implementation Status

| Feature / Capability | Status | Description |
|---|---|---|
| Repository Traversal & File Inventory | **Implemented** | Scans Home Assistant Core, filters exclusions, records file sizes, extensions, and component associations. |
| Manifest Discovery & Ingestion | **Implemented** | Discovers and parses all 1,554 `manifest.json` files, preserving original JSON and extracting key fields. |
| Code Chunking Corpus | **Implemented** | Generates line-bounded overlapping chunks (default: 100 lines / 15 lines overlap) with SHA-256 chunk IDs. |
| Automated Test Suite | **Implemented** | 11 unit and validation tests covering manifest parsing, chunk boundaries, deterministic ordering, and summary reconciliation. |
| Data Dictionary & Provenance | **Implemented** | Complete schema specification and provenance rules in [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md). |
| Real User Questions | **Implemented** | 10 realistic domain questions in [docs/QUESTIONS.md](docs/QUESTIONS.md). |
| Vector Indexing & RAG Retrieval | *Planned (Phase 2)* | Embedding code chunks into vector storage (e.g., pgvector / Chroma) for semantic retrieval. |
| Natural-Language SQL Querying | *Planned (Phase 2)* | Translating natural-language questions into safe, deterministic SQL queries over `integrations.csv`. |
| Behavioral & Protocol Detection | *Planned (Phase 3)* | AST / static-analysis pipeline to verify protocol support and runtime error recovery beyond manifest declarations. |
| Accuracy Evaluation | *Planned (Phase 3)* | Scoring retrieval and counting accuracy against 50 manually verified questions, targeting 98% exact match. |

> [!NOTE]
> File presence metadata (such as `has_sensor_py` or `has_coordinator_py`) records filesystem facts only. It does not prove runtime behavior, local polling, Modbus protocol support, or error recovery correctness.

## Upstream Data Source

The real data source is the official [Home Assistant Core](https://github.com/home-assistant/core) repository.

- **Source Repository**: `homeassistant/core`
- **Checkout Branch**: `dev`
- **Source Commit SHA**: `fbee16b2aae664f10d819c0121575102326eaa17`
- **License**: Apache-2.0 (preserve upstream license notices)

## Dataset Targets & Measured Results

The project brief establishes minimum scope targets: at least 1,500 integration manifests and at least 19,000 source files.

| Metric | Target | Measured Actual | Target Status |
|---|---|---|---|
| Manifests Discovered | >= 1,500 | **1,554** | **MET** |
| Successfully Parsed Manifests | >= 1,500 | **1,554** | **MET** |
| Manifest Parsing Failures | 0 | **0** | **MET** |
| Unique Integration Domains | - | **1,554** | - |
| Source Files Inventoried | >= 19,000 | **27,376** | **MET** |
| Python Files Inventoried | - | **20,024** | - |
| Integration Python Files | - | **10,567** | - |
| Integration Python Files Indexed | - | **10,567** | - |
| Code Chunks Generated (100L / 15O) | - | **22,707** | - |
| Skipped Files / Traversal Errors | 0 | **0** | **MET** |

Generated summary details are saved to `data/processed/collection_summary.json`.

## Repository Structure

```text
DeviceCensus/
├── README.md                          # Project overview, setup, and status
├── .gitignore                         # Excludes large corpora and caches
├── scripts/
│   └── collect_data.py                # Reproducible data collection pipeline
├── tests/
│   ├── test_collect_data.py           # Unit tests for parsing, chunking, and edge cases
│   └── test_dataset_validation.py     # End-to-end dataset reconciliation and target validation
├── docs/
│   ├── DATA_DICTIONARY.md             # Dataset schemas, types, and git storage policy
│   └── QUESTIONS.md                   # 10 real-world user research questions
└── data/
    ├── raw/
    │   └── integration_manifests.jsonl  # Verbatim manifest dumps (gitignored)
    └── processed/
        ├── collection_summary.json    # Run metadata, error counts, and target verification
        ├── collection_errors.jsonl    # Repository walk and read error log
        ├── manifest_errors.jsonl      # Manifest JSON parse error log
        ├── integrations.csv           # Tabular metadata for SQL analysis (tracked)
        ├── integrations.json          # Structured manifest records (tracked)
        ├── source_inventory.csv       # File inventory audit trail (tracked)
        └── code_chunks.jsonl          # 100-line overlapping code chunks (gitignored)
```

## Running the Data Collection Pipeline

The collection pipeline is written using Python's standard library with zero external dependencies.

### Windows PowerShell

Run from the `DeviceCensus` directory:

```powershell
# Execute collection pipeline using sibling core repository
python .\scripts\collect_data.py --core-root "..\core" --output-root ".\data"

# Optional parameters for custom chunk size and overlap:
python .\scripts\collect_data.py --core-root "..\core" --output-root ".\data" --chunk-size 100 --chunk-overlap 15
```

Alternatively, from the workspace parent directory:

```powershell
python .\DeviceCensus\scripts\collect_data.py `
  --core-root .\core `
  --output-root .\DeviceCensus\data
```

### Running the Test Suite

```powershell
# Run all tests (unit tests and dataset validation)
python -m unittest discover -s .\tests -v
```

All 11 tests pass deterministically:
- `test_collect_data.py` validates valid manifest parsing, non-dict root errors, broken JSON recovery, deterministic ordering, line chunk boundaries, and chunk parameter validation.
- `test_dataset_validation.py` validates that generated artifacts reconcile with `collection_summary.json` and fulfill the brief's dataset size targets.

## 10 Real Questions

See [docs/QUESTIONS.md](docs/QUESTIONS.md) for 10 real questions asked by IoT engineers and developers.

## Data Dictionary

See [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) for complete schema definitions, types, and git artifact recommendations.
