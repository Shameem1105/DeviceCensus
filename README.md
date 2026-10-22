# DeviceCensus

## Problem

IoT engineers and developers building Home Assistant integrations need to understand how existing integrations communicate with devices, retrieve sensor data, and handle connection errors. This information is spread across more than 1,500 integration manifests and thousands of Python source files, making manual research time-consuming and error-prone. General-purpose LLMs can also produce incorrect counts or unsupported explanations when answering questions about a large codebase. DeviceCensus parses Home Assistant Core source code into structured data and combines Python/SQL analysis with AI-powered code retrieval to provide accurate, evidence-backed answers with links to the original files.

## Who it is for

- IoT engineers at smart-energy startups developing Home Assistant integrations for solar inverters and smart meters.
- Software developers who need to research, compare, and understand existing Home Assistant integrations before implementing new ones.

## Signature feature

A natural-language AI analyst that combines exact SQL/Python counting with source-code retrieval to answer integration research questions and provide traceable evidence from the Home Assistant Core repository.

## Hardest problem (my interview story)

The main technical challenge is extracting reliable information from thousands of integration manifests and Python files while distinguishing explicitly declared metadata from capabilities that require source-code analysis. The system must answer natural-language questions without allowing the LLM to invent counts, execute unsafe database queries, or make unsupported claims. We will validate counting accuracy against 50 manually checked questions, targeting at least 98% exact-match accuracy.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| Home Assistant Core | https://github.com/home-assistant/core | 19,000+ source files and 1,500+ integration manifests (minimum project scope) | Not applicable | Apache-2.0, as specified in the project brief; verify the repository's current licence and preserve applicable notices |

## 10 real questions

See [docs/QUESTIONS.md](docs/QUESTIONS.md).

## Run it

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements-dev.txt

# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env

uvicorn app.main:app --reload

curl localhost:8000/health
```

## Live link

Added in Week 2.
