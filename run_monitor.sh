#!/bin/bash

echo "🖥️  Network Connection Monitor"
echo "================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found! Please install Python 3.7+ first."
    exit 1
fi

# Check Python version
python3 -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Python 3.7+ recommended"
fi

# Try to install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import geoip2, rich, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "🔧 Installing dependencies..."
    python3 scripts/install_dependencies.py
    echo
fi

# Run the monitor
echo "🚀 Starting Network Monitor..."
echo "Press Ctrl+C to stop monitoring"
echo
python3 scripts/network_monitor.py "$@"

echo
echo "👋 Network Monitor stopped"
