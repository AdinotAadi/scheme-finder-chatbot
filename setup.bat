@echo off
REM setup.bat - Automated setup script for Windows PowerShell / Command Prompt
setlocal enabledelayedexpansion

echo ==========================================================
echo Scheme Finder - Quick Setup Script (Windows)
echo ==========================================================

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [X] Python is not found in your PATH.
        echo Please install Python 3.10+ from https://www.python.org/
        pause
        exit /b 1
    ) else (
        set PY_CMD=python3
    )
) else (
    set PY_CMD=python
)
echo [OK] Found Python.

REM 2. Check uv or install
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    set UV_CMD=uv
    echo [OK] Found uv package manager.
) else (
    echo [INFO] 'uv' not found. Installing standalone uv for Windows...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set UV_CMD="%USERPROFILE%\.local\bin\uv.exe"
)

REM 3. Create virtual environment
echo.
echo Setting up isolated virtual environment (.venv)...
%UV_CMD% venv --allow-existing .venv
echo [OK] Virtual environment ready.

echo Installing dependencies from requirements.txt...
%UV_CMD% pip install -r requirements.txt
echo [OK] Dependencies installed.

REM 4. Check Ollama
echo.
echo Checking Ollama and Llama 3.2:3b...
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Found Ollama.
    echo Pulling 'llama3.2:3b' (if not present)...
    ollama pull llama3.2:3b
) else (
    echo [NOTICE] Ollama is not installed or not in PATH.
    echo To enable the local LLM, download Ollama from https://ollama.com/download/windows
    echo and run 'ollama pull llama3.2:3b'.
)

REM 5. Run tests
echo.
echo Running automated verification tests...
call .venv\Scripts\pytest.exe tests/ -k "not vector_store"

echo.
echo ==========================================================
echo Setup complete! To launch Scheme Finder:
echo   call .venv\Scripts\activate.bat
echo   streamlit run src/app.py
echo ==========================================================
echo.
pause
