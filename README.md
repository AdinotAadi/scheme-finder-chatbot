# 🇮🇳 Scheme Finder

**Trustworthy, Source-Grounded Government Scheme Eligibility Assistant**

A research system that matches citizens—specifically women and vulnerable demographics in India—to government welfare schemes. 
The system couples **deterministic 3-valued symbolic eligibility logic** (ensuring 0% false positive hallucinations) with a **Qdrant Vector Database** and **Local Llama 3.2:3b** for conversational explanation and interactive triage.

---

## ⚡ 1-Minute Quick Start

### 🍎 macOS / 🐧 Linux
Open your terminal in the cloned repository folder and run:
```bash
./setup.sh
```
Then start the application:
```bash
uv run streamlit run src/app.py
```
*(Or activate `.venv`: `source .venv/bin/activate && streamlit run src/app.py`)*

---

### 🪟 Windows
Double-click `setup.bat` or run in PowerShell / Command Prompt:
```cmd
setup.bat
```
Then start the application:
```cmd
call .venv\Scripts\activate.bat
streamlit run src/app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## 🦙 Local LLM Setup (Ollama + Llama 3.2:3b)

The conversational layer uses **Meta's Llama 3.2:3b** hosted locally on your device for complete data privacy:

1. **Install Ollama**:
   - **macOS / Linux**: Download from [ollama.com/download](https://ollama.com/download) or install via terminal:
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ```
   - **Windows**: Download the Windows installer from [ollama.com/download/windows](https://ollama.com/download/windows).
2. **Pull the model**:
   ```bash
   ollama pull llama3.2:3b
   ```
3. **Verify Ollama is running**:
   - Ensure the Ollama app is open in your tray/menu bar or run `ollama serve`.
   - *(Note: If Ollama is not running, the application will still function smoothly in verified vector-fallback mode).*

---

## 🏛️ System Architecture

```
[User Natural Language Input]
               │
               ▼
   [1. Input Guardrail Inspection] ──> Regex Threat Detection & Prompt Sandboxing
               │
               ▼
   [2. Profile Triage Extractor]   ──> Detects Missing Demographics (State, Age, Gender)
               │                       • If missing -> Asks targeted triage questions
               │                       • If present -> Proceeds to retrieval
               ▼
   [3. Qdrant Hybrid Retrieval]    ──> Dense Vector Similarity + Lexical Boost
               │                       (145 Scraped Official Portal Documents)
               ▼
   [4. Guarded Llama 3.2:3b RAG]   ──> Strictly Grounded in Retrieved Official Passages
               │                       (Delimited XML Boundary Sandboxing)
               ▼
   [5. Output Guardrail Checks]    ──> Enforces "May Be Eligible", Strips Promised Payouts
               │
               ▼
[Streamlit UI + Transparency Expander with Verbatim Portal Links & Documents]
```

---

## 🧪 Running the Verification Test Suite

The repository contains an automated test suite verifying data cleaning, web scraping integrity, 3-valued logic, boundary cases, vector search, and prompt injection security.

Run all tests via `uv`:
```bash
uv run pytest tests/ -v
```
Or within the activated virtual environment:
```bash
pytest tests/ -v
```

All 20 tests should pass:
- `test_guardrails.py`: Verifies prompt injection, role-hijacking, and jailbreak blocking.
- `test_profile_extractor.py`: Tests stateful conversational demographic extraction.
- `test_slice0_cleaning.py`: Verifies seed data normalization and deduplication.
- `test_slice1_ingestion.py`: Verifies web snapshot archiving and database storage.
- `test_slice3_engine.py`: Verifies three-valued logic boundaries (age limits, unknown fields).
- `test_slice4_harness.py`: Benchmarks precision and recall against keyword baseline.
- `test_slice5_cli.py`: Verifies deterministic evaluation.
- `test_vector_store.py`: Tests Qdrant vector retrieval and jurisdiction filtering.

---

## 📁 Repository Structure

```
.
├── src/
│   ├── app.py                      # Main Streamlit web application
│   ├── cli.py                      # Terminal-based interactive questionnaire
│   ├── engine/
│   │   ├── evaluator.py            # Three-valued deterministic logic engine
│   │   ├── guardrails.py           # Multi-layered prompt injection & output defenses
│   │   ├── profile_extractor.py    # Conversational user demographic extraction
│   │   ├── rag_pipeline.py         # Grounded retrieval-augmented generation pipeline
│   │   └── vector_store.py         # Embedded Qdrant vector database interface
│   ├── ingestion/
│   │   ├── fetch_schemes.py        # Snapshot fetcher with polite rate-limiting
│   │   └── scrape_all_schemes.py   # Bulk scraper for all 145 schemes
│   ├── llm/
│   │   ├── llm_interface.py        # Generic LLM provider interface
│   │   └── ollama_client.py        # Local Ollama client with Llama 3.2:3b
│   └── schema/
│       ├── review_queue.py         # Human-in-the-loop review queue manager
│       └── rules.py                # Pydantic schemas for atomic criteria & profiles
├── data/
│   ├── clean/                      # Normalized CSV datasets (schemes_seed.csv)
│   ├── qdrant_db/                  # Embedded Qdrant vector store on disk
│   ├── raw_html/                   # Verbatim HTML snapshots of official scheme pages
│   ├── raw_snapshots/              # Structured JSON snapshots with fetch timestamps
│   ├── review/                     # Human-in-the-loop CSV review queue
│   └── schemes.db                  # Local SQLite database with content hashes
├── scripts/
│   └── clean_seed_data.py          # Seed data cleaning and alignment script
├── tests/                          # 20 automated unit and regression tests
├── setup.sh                        # One-click setup script for macOS and Linux
├── setup.bat                       # One-click setup script for Windows
├── pyproject.toml                  # Pytest configuration and pythonpath
├── requirements.txt                # Python package dependencies
└── README.md                       # Main documentation
```

---

## 🔒 Security & Research Hard Rules
1. **Never Invent Rules**: Every recommendation links to an official verbatim sentence and `https://www.myscheme.gov.in/schemes/<slug>`.
2. **Three-Valued Uncertainty**: Unknown fields remain unknown. Missing attributes trigger triage questions rather than guesses.
3. **Prompt Injection Defense**: All user inputs undergo regex pattern filtering and XML delimiter encapsulation so inputs cannot override system directives.
4. **Offline Privacy**: Model weights and vector embeddings execute 100% locally on your machine with zero external data transmission.
