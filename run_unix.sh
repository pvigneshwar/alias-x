#!/usr/bin/env bash
# ============================================================
#  ALIAS_X — macOS / Linux Launcher
#  Starts the Streamlit dashboard.
#  Usage: chmod +x run_unix.sh && ./run_unix.sh
# ============================================================

set -e

echo ""
echo " ==================================================="
echo "  ALIAS_X — Autonomous Verification Protocol"
echo "  Department of Computer Science, 2023-2026"
echo " ==================================================="
echo ""

# Check Python 3.10+
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] python3 not found. Install Python 3.10+ and retry."
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(sys.version_info[:2] >= (3,10))")
if [ "$PYTHON_VER" != "True" ]; then
    echo " [ERROR] Python 3.10+ required. Current: $(python3 --version)"
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo " [SETUP] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo " [SETUP] Checking dependencies..."
pip install -r requirements.txt -q --disable-pip-version-check

# Check .env
if [ ! -f ".env" ]; then
    echo ""
    echo " [WARNING] .env not found. Copying .env.example → .env"
    cp .env.example .env
    echo " Edit .env with your GEMINI_API_KEY and BLAND_AI_KEY, then rerun."
    echo " Launching in Simulation Mode for now."
    echo ""
fi

echo " [START] Launching ALIAS_X on http://localhost:8501"
echo " Press Ctrl+C to stop."
echo ""

# Open browser in background (best-effort)
(sleep 3 && \
    if command -v xdg-open &>/dev/null; then xdg-open http://localhost:8501; \
    elif command -v open &>/dev/null; then open http://localhost:8501; fi) &

streamlit run app.py --server.port 8501
