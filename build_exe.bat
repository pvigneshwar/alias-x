@echo off
REM ============================================================
REM  ALIAS_X — Windows .exe Build Script
REM  Produces dist\ALIAS_X.exe (standalone, zero-install)
REM  Requirements: Python 3.10+, venv activated, pip deps installed
REM ============================================================

title ALIAS_X — Build .exe

echo.
echo  Building ALIAS_X.exe with PyInstaller...
echo.

REM Activate venv if present
IF EXIST "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Ensure PyInstaller is installed
pip install pyinstaller>=6.0.0 -q --disable-pip-version-check

REM Clean previous build artifacts
IF EXIST "dist" rmdir /s /q dist
IF EXIST "build" rmdir /s /q build

REM Run PyInstaller
pyinstaller ALIAS_X.spec --noconfirm --clean

IF ERRORLEVEL 1 (
    echo.
    echo  [ERROR] PyInstaller build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo  =====================================================
echo   Build complete!
echo   Executable: dist\ALIAS_X.exe
echo   Copy dist\ALIAS_X.exe and your .env file together.
echo  =====================================================
echo.
pause
