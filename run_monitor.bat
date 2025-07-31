@echo off
title Network Monitor
echo.
echo 🖥️  Network Connection Monitor
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.7+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Try to install dependencies if needed (silently)
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing requests for geo lookup...
    python -m pip install requests >nul 2>&1
)

python -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing rich for better display...
    python -m pip install rich >nul 2>&1
)

REM Run the monitor with clean output
python scripts/network_monitor.py --default-country "United States" %*

echo.
echo 👋 Network Monitor stopped
pause
