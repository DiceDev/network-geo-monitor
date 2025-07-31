#!/bin/bash

echo "🐧 Unix/Linux Network Monitor Setup"
echo "===================================="
echo

# Check Python version
echo "📋 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found! Please install Python 3.7+ first."
    exit 1
fi

# Check Python version is 3.7+
python3 -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Python 3.7+ recommended"
fi

# Install dependencies
echo
echo "📦 Installing Python dependencies..."
python3 -m pip install --user requests rich geoip2 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "⚠️  Some dependencies may have failed to install"
    echo "   The script will still work with reduced functionality"
fi

# Check required tools
echo
echo "🔧 Checking system tools..."

# Check netstat
if command -v netstat &> /dev/null; then
    echo "✓ netstat found"
else
    echo "❌ netstat not found"
    echo "   Install with: sudo apt-get install net-tools (Ubuntu/Debian)"
    echo "   Or: sudo yum install net-tools (CentOS/RHEL)"
fi

# Check ss (modern alternative)
if command -v ss &> /dev/null; then
    echo "✓ ss found (modern netstat alternative)"
else
    echo "ℹ️  ss not found (optional modern alternative to netstat)"
fi

# Check lsof (for process info)
if command -v lsof &> /dev/null; then
    echo "✓ lsof found (for process information)"
else
    echo "ℹ️  lsof not found (optional, for enhanced process info)"
    echo "   Install with: sudo apt-get install lsof"
fi

# Test basic functionality
echo
echo "🧪 Testing basic functionality..."
python3 scripts/test_basic.py
if [ $? -eq 0 ]; then
    echo "✓ Basic tests passed"
else
    echo "⚠️  Some basic tests failed"
fi

# Test Unix compatibility
echo
echo "🐧 Testing Unix compatibility..."
python3 scripts/test_unix_compatibility.py

echo
echo "🎉 Setup complete!"
echo
echo "To run the network monitor:"
echo "  python3 scripts/network_monitor.py"
echo
echo "For help:"
echo "  python3 scripts/network_monitor.py --help"
echo
echo "To test geo lookup:"
echo "  python3 scripts/test_all_geo.py"
