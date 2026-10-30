#!/usr/bin/env bash
# setup.sh - Cross-platform setup script for macOS and Linux
set -euo pipefail

echo "=========================================================="
echo "🇮🇳 Scheme Finder - Quick Setup Script (macOS / Linux)"
echo "=========================================================="

# 1. Check Python version
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "❌ Error: Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

PY_VER=$($PY_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Found Python $PY_VER ($PY_CMD)"

# 2. Check or install uv (Fast package manager)
if command -v uv >/dev/null 2>&1; then
    UV_CMD="uv"
    echo "✓ Found uv package manager ($($UV_CMD --version))"
elif [ -f "$HOME/.local/bin/uv" ]; then
    UV_CMD="$HOME/.local/bin/uv"
    echo "✓ Found uv at $UV_CMD"
else
    echo "ℹ️  'uv' not found. Installing standalone uv for lightning-fast installation..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    UV_CMD="$HOME/.local/bin/uv"
fi

# 3. Create virtual environment and install dependencies
echo ""
echo "📦 Setting up isolated virtual environment (.venv)..."
$UV_CMD venv --allow-existing .venv
echo "✓ Virtual environment ready at .venv"

echo "📥 Installing required dependencies from requirements.txt..."
$UV_CMD pip install -r requirements.txt
echo "✓ Dependencies installed successfully."

# 4. Check Ollama and model
echo ""
echo "🦙 Checking Ollama and Llama 3.2:3b model..."
if command -v ollama >/dev/null 2>&1; then
    echo "✓ Found Ollama installed."
    # Check if daemon is active
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✓ Ollama server is running."
        # Check if llama3.2:3b is already pulled
        if curl -s http://localhost:11434/api/tags | grep -q "llama3.2:3b"; then
            echo "✓ Model 'llama3.2:3b' is already available."
        else
            echo "📥 Pulling 'llama3.2:3b' (approx ~2GB)..."
            ollama pull llama3.2:3b
        fi
    else
        echo "⚠️  Ollama is installed, but the daemon is not running."
        echo "   Please run 'ollama serve' or start the Ollama desktop app, then run:"
        echo "   ollama pull llama3.2:3b"
    fi
else
    echo "⚠️  Ollama is not installed on this system."
    echo "   To use local Llama 3.2:3b, install Ollama from: https://ollama.com/download"
    echo "   Then run: ollama pull llama3.2:3b"
    echo "   (The app will still run in vector-fallback mode if Ollama is not present)."
fi

# 5. Run test suite to verify installation
echo ""
echo "🧪 Running automated verification tests..."
.venv/bin/pytest tests/ -k "not vector_store"

echo ""
echo "=========================================================="
echo "🎉 Setup complete! You are ready to launch Scheme Finder."
echo "=========================================================="
echo ""
echo "To start the Streamlit conversational app:"
echo "  source .venv/bin/activate"
echo "  streamlit run src/app.py"
echo ""
echo "Or using uv directly in one line:"
echo "  uv run streamlit run src/app.py"
echo ""
