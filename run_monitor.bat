@echo off
title Network Monitor
echo.
echo Cross-Platform Network Monitor
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.7+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Try to install dependencies if needed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing requests for geo lookup...
    python -m pip install requests
)

python -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo Installing rich for better display...
    python -m pip install rich
)

REM Run the monitor with default settings (filters listening connections)
echo Starting Network Monitor...
echo Will auto-detect your location (defaults to United States if failed)
echo Filtering out listening connections (use --show-listening to include them)
echo [F] = Foreign connections, [D] = Domestic connections
echo Press Ctrl+C to stop monitoring
echo.

python scripts/network_monitor.py --default-country "United States" %*

echo.
echo Network Monitor stopped
pause
