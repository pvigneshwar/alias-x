#!/usr/bin/env bash
# ============================================================
#  ALIAS_X — Run Full Test Suite (macOS / Linux)
#  Usage: chmod +x run_tests.sh && ./run_tests.sh
# ============================================================

set -e

if [ -d "venv" ]; then
    source venv/bin/activate
fi

pip install pytest -q --disable-pip-version-check

echo ""
echo " Running ALIAS_X test suite (29 test cases)..."
echo ""

pytest test_alias_x.py -v --tb=short
