@echo off
REM ============================================================
REM  ALIAS_X — Windows Launcher
REM  Starts the Streamlit dashboard and opens the browser.
REM  Run this file to start ALIAS_X.
REM ============================================================

title ALIAS_X — Autonomous Verification Protocol

echo.
echo  ===================================================
echo   ALIAS_X — Autonomous Verification Protocol
echo   Department of Computer Science, 2023-2026
echo  ===================================================
echo.

REM Check Python is available
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [ERROR] Python not found on PATH.
    echo  Please install Python 3.10+ (64-bit) from https://python.org
    pause
    exit /b 1
)

REM Check virtual environment exists, create if not
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo  [SETUP] Creating virtual environment...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install / update dependencies silently
echo  [SETUP] Checking dependencies...
pip install -r requirements.txt -q --disable-pip-version-check

REM Check .env exists
IF NOT EXIST ".env" (
    echo.
    echo  [WARNING] .env file not found.
    echo  Copying .env.example to .env — please edit it with your API keys.
    copy .env.example .env >nul
    echo.
    echo  Edit .env and set:
    echo    GEMINI_API_KEY=your_key_here
    echo    BLAND_AI_KEY=your_key_here
    echo.
    echo  Then re-run this script. Launching in Simulation Mode for now.
    echo.
)

REM Launch Streamlit
echo  [START] Launching ALIAS_X dashboard...
echo  Opening http://localhost:8501 in your browser...
echo.
echo  Press Ctrl+C to stop the server.
echo.

REM Open browser after a short delay (runs in background)
start "" /B cmd /c "timeout /t 3 >nul && start http://localhost:8501"

REM Start Streamlit
streamlit run app.py --server.port 8501 --server.headless false

pause
