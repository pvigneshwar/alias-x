@echo off
REM ============================================================
REM  ALIAS_X — Run Full Test Suite (Windows)
REM  Usage: run_tests.bat
REM ============================================================

title ALIAS_X — Test Suite

IF EXIST "venv\Scripts\activate.bat" call venv\Scripts\activate.bat

pip install pytest -q --disable-pip-version-check

echo.
echo  Running ALIAS_X test suite (29 test cases)...
echo.

pytest test_alias_x.py -v --tb=short

echo.
pause
