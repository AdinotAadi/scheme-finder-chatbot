# Quick Setup Guide for Evaluators & Faculty

This guide allows you to clone and run **Scheme Finder** on any machine (macOS, Linux, or Windows) with zero manual configuration.

---

## Prerequisites
1. **Python 3.10+** (check using `python3 --version` or `python --version`).
2. *(Recommended for local AI Chat)*: **Ollama** installed with `llama3.2:3b`.
   - Download from: [https://ollama.com/download](https://ollama.com/download)
   - In terminal / command prompt, run: `ollama pull llama3.2:3b`

---

## 🍎 macOS Setup Instructions
```bash
git clone <repo-url>
cd "Scheme Finder"

# 1. Run automated setup (creates virtual environment and installs packages)
./setup.sh

# 2. Launch the Streamlit Chatbot
uv run streamlit run src/app.py
```
*(Or manually: `source .venv/bin/activate && streamlit run src/app.py`)*

---

## 🐧 Linux (Ubuntu / Debian / Fedora / Arch) Setup Instructions
```bash
git clone <repo-url>
cd "Scheme Finder"

# 1. Ensure bash setup script is executable and run
chmod +x setup.sh
./setup.sh

# 2. Launch the Streamlit Chatbot
uv run streamlit run src/app.py
```

---

## 🪟 Windows Setup Instructions
1. Open PowerShell or Command Prompt inside the cloned folder:
   ```cmd
   git clone <repo-url>
   cd "Scheme Finder"
   ```
2. Double-click `setup.bat` (or run in command line):
   ```cmd
   setup.bat
   ```
3. Activate the environment and run Streamlit:
   ```cmd
   call .venv\Scripts\activate.bat
   streamlit run src/app.py
   ```

---

## 🧪 Verifying the Installation

To verify that the database, vector store, deterministic rules engine, and security guardrails are functioning properly, run the test suite:

- **macOS / Linux**:
  ```bash
  uv run pytest tests/ -v
  ```
- **Windows**:
  ```cmd
  .venv\Scripts\pytest.exe tests/ -v
  ```

All **20 tests** should pass.

