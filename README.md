# DeviceCensus

## Problem

IoT engineers and developers building Home Assistant integrations need to understand how existing integrations communicate with devices, retrieve sensor data, and handle connection errors. This information is spread across more than 1,500 integration manifests and thousands of Python source files, making manual research time-consuming and error-prone. General-purpose LLMs can also produce incorrect counts or unsupported explanations when answering questions about a large codebase. DeviceCensus will parse Home Assistant Core source code into structured data and combine Python/SQL analysis with source-code retrieval to provide accurate, evidence-backed answers with links to the original files.

## Who it is for

- IoT engineers at smart-energy startups developing Home Assistant integrations for solar inverters and smart meters.
- Software developers who need to research, compare, and understand existing Home Assistant integrations before implementing new ones.

## Signature feature

A planned natural-language AI analyst that combines exact SQL/Python counting with source-code retrieval to answer integration research questions and provide traceable evidence from the Home Assistant Core repository.

## Hardest problem (my interview story)

The main technical challenge is extracting reliable information from thousands of integration manifests and Python files while distinguishing explicitly declared metadata from capabilities that require source-code analysis. The system must answer natural-language questions without allowing the LLM to invent counts, execute unsafe database queries, or make unsupported claims. We will validate counting accuracy against 50 manually checked questions, targeting at least 98% exact-match accuracy.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| Home Assistant Core | https://github.com/home-assistant/core | Targets: at least 19,000 inventoried source/configuration files and 1,500 successfully parsed integration manifests; actual counts are recorded by the collector | Not applicable | Preserve upstream licence notices and record the collected source commit |

## 10 real questions

See [docs/QUESTIONS.md](docs/QUESTIONS.md).

## Collect the data

```bash
py -3 .\scripts\collect_data.py
```

The standard-library collector uses the sibling `core\` checkout by default and
writes generated artifacts under `data\`. From the workspace parent folder:

```powershell
py -3 .\DeviceCensus\scripts\collect_data.py `
  --core-root .\core `
  --output-root .\DeviceCensus\data
Push-Location .\DeviceCensus
py -3 -m unittest discover -s .\tests -v
Pop-Location
```

From inside `DeviceCensus\`, run `py -3 .\scripts\collect_data.py` and
`py -3 -m unittest discover -s .\tests -v`. Use `--chunk-size` and
`--chunk-overlap` to configure the default 100-line chunks and 15-line overlap.
Actual counts and target status are written to
`data\processed\collection_summary.json`. The collector does not infer or verify
integration behavior. See [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) for
field definitions and provenance.

## Live link

Added in Week 2.
