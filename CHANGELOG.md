# CHANGELOG - Scheme Finder

All notable changes and milestones for the Trustworthy Eligibility Assessment PhD prototype.

## [Slice 0 - Data Audit & Cleaning] - 2026-10-30
### Added
- Created `scripts/clean_seed_data.py` to audit and clean `Docs/Final data 1.xlsx`.
- Corrected column offsets in Sheet1 (realigned `data`, `data2`, `data3`, tags).
- Parsed asymmetric two-pair column structure in Sheet2 (16 schemes).
- Extracted clean slugs and classified jurisdictions into `Central`, `State`, and `UT`.
- Produced normalized `data/clean/schemes_seed.csv` (145 deduplicated schemes).
- Created `reports/slice0_data_quality_report.md` with complete analysis.
- Added comprehensive unit tests in `tests/test_slice0_cleaning.py`.

## [Slice 1 - Ingestion with Provenance] - 2026-10-30
### Added
- Discovered and integrated myScheme's public JSON API endpoint with polite rate-limiting.
- Built `src/ingestion/fetch_schemes.py` supporting exponential backoff, raw JSON snapshots, and SQLite persistence.
- Successfully ingested all 16 pilot schemes for **Uttarakhand** into `data/schemes.db`.
- Created raw snapshots in `data/raw_snapshots/*.json` with verbatim eligibility text and SHA-256 content hashes.
- Produced `reports/slice1_ingestion_report.md`.
- Added unit tests in `tests/test_slice1_ingestion.py`.

## [Slice 2 - Structured Eligibility Schema & Review Queue] - 2026-10-30
### Added
- Defined Pydantic models in `src/schema/rules.py` for atomic criteria, Boolean composition groups (`ALL`, `ANY`, `NOT`), provenance tracking, and partial user profiles.
- Built review queue manager in `src/schema/review_queue.py` with CSV export/import for human-in-the-loop validation.
- Created `src/llm/llm_interface.py` with environment-variable-backed LLM rule proposition prompting and fallback extractor.
- Generated `data/review/review_queue_uttarakhand.csv` with proposed atomic rules.

## [Slice 3 - Deterministic Eligibility Engine] - 2026-10-30
### Added
- Implemented three-valued logic engine in `src/engine/evaluator.py` (`SATISFIED`, `NOT_SATISFIED`, `UNKNOWN`).
- Supported nested `ALL`, `ANY`, and `NOT` boolean rule evaluations.
- Categorized outcomes strictly into `POTENTIAL_MATCH`, `MORE_INFORMATION_NEEDED`, `LIKELY_NOT_ELIGIBLE`, and `NEEDS_MANUAL_VERIFICATION`.
- Added automated boundary, missing value, and logic tests in `tests/test_slice3_engine.py` (100% pass rate).

## [Slice 4 - Evaluation Harness & Gold Standard Set] - 2026-10-30
### Added
- Created hand-curated gold standard ruleset for 16 Uttarakhand pilot schemes in `data/gold_standard/gold_rules_uttarakhand.py`.
- Developed diverse synthetic test persona suite in `data/gold_standard/synthetic_profiles.py`.
- Built comparative evaluation harness in `src/engine/harness.py` evaluating Precision@K, Recall@K, False Positives/Negatives, and Evidence Support Rate.
- Implemented keyword and metadata baseline model for experimental comparison.
- Added automated regression benchmark test in `tests/test_slice4_harness.py`.
- Produced comprehensive academic report in `reports/slice4_evaluation_report.md`.

## [Slice 5 - Interactive CLI Assessment] - 2026-10-30
### Added
- Built conversational questionnaire interface in `src/cli.py` collecting age, income, gender, occupation, marital status and children (conditioned on female gender), and state/district.
- Evaluated inputs deterministically against verified rules with 3-valued logic.
- Output formatting strictly enforces research constraints: states "may be eligible", presents verified reasons for match, lists missing information, official portal link, and required documents.
- Added automated integration test suite in `tests/test_slice5_cli.py`.

## [Document & Vector Store Integration (Qdrant & RAG)] - 2026-10-30
### Added
- Scraped all 145 schemes nationwide and saved both raw HTML snapshots (`data/raw_html/`) and structured JSON payloads (`data/raw_snapshots/`).
- Eliminated hardcoded scheme rules in code: persistent storage in embedded Qdrant vector database (`data/qdrant_db`) and SQLite (`data/schemes.db`).
- Built `src/engine/vector_store.py` with dense semantic embedding search and jurisdiction filtering.
- Implemented `src/engine/rag_pipeline.py` combining vector retrieval with grounded generation and official portal citation.
- Added comprehensive unit and integration tests in `tests/test_vector_store.py`.

## [Cross-Platform Setup & Evaluator Documentation] - 2026-10-30
### Added
- Created `setup.sh` for one-click setup on macOS and Linux (detects Python, auto-installs `uv`, sets up `.venv`, verifies Ollama/Llama 3.2:3b, and runs test suite).
- Created `setup.bat` for one-click setup on Windows command prompt / PowerShell.
- Produced comprehensive `SETUP_GUIDE.md` for faculty and academic evaluators.
- Updated root `README.md` with system architecture diagrams, quickstart commands, and directory layouts.
- Created project `.gitignore` covering virtual environments (`.venv`, `venv`), bytecode, testing caches (`.pytest_cache`), Qdrant runtime lock files (`data/qdrant_db/.lock`), OS metadata (`.DS_Store`, `Thumbs.db`), and editor folders.
  - Input regex defense detecting jailbreak patterns, system prompt overrides, and role-hijacking.
  - Strict XML delimiter boundary sandboxing ensuring user input is treated as untrusted data.
  - Output constraint enforcement guaranteeing "may be eligible" phrasing and preventing promised payouts.
- Built `src/llm/ollama_client.py` connecting directly to local `llama3.2:3b` via Ollama with low temperature for high factual precision.
- Built interactive conversational UI in `src/app.py` using Streamlit with natural language intake, Qdrant retrieval, source transparency expanders, and state filtering.
- Added live real-time pipeline status container showing guardrail checks, Qdrant retrieved candidates with similarity scores, and prompt construction.
- Added "Live LLM Execution Inspector" expander revealing exact XML sandboxed prompt delivered to Llama 3.2:3b and guardrail post-processing metrics.
- Added stateful conversational profile extraction in `src/engine/profile_extractor.py`:
  - Incrementally collects state of residence, age, gender, pregnancy/lactation, and occupation.
  - Automatically identifies missing essential triage attributes (`state_residence`, `gender`, `age`).
  - Active triage directive prevents LLM from prematurely recommending state schemes until key demographic filters are provided.
  - Shows real-time profile dashboard in the Streamlit sidebar.
- Added test suite in `tests/test_profile_extractor.py`.

