#!/bin/bash

echo "🌍 Cross-Platform Network Monitor Setup"
echo "======================================="
echo

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
    PLATFORM="Windows (Git Bash)"
else
    PLATFORM="Unknown Unix"
fi

echo "Detected platform: $PLATFORM"
echo

# Check Python
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ $PYTHON_VERSION"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Install Python dependencies
echo
echo "📦 Installing Python dependencies..."
python3 -m pip install --user requests rich geoip2 2>/dev/null

# Check dependencies
echo
echo "🔍 Checking dependencies..."
python3 -c "import requests; print('✓ requests')" 2>/dev/null || echo "⚠️  requests not available"
python3 -c "import rich; print('✓ rich')" 2>/dev/null || echo "⚠️  rich not available"
python3 -c "import geoip2; print('✓ geoip2')" 2>/dev/null || echo "⚠️  geoip2 not available"

# Check network tools
echo
echo "🔧 Checking network tools..."

if command -v netstat &> /dev/null; then
    echo "✓ netstat available"
else
    echo "❌ netstat not found"
    if [[ "$PLATFORM" == "Linux" ]]; then
        echo "   Install with: sudo apt-get install net-tools"
    fi
fi

if command -v ss &> /dev/null; then
    echo "✓ ss available (modern alternative)"
else
    echo "ℹ️  ss not found (optional)"
fi

# Run cross-platform test
echo
echo "🧪 Running cross-platform test..."
python3 scripts/test_cross_platform.py

echo
echo "🎉 Setup complete!"
echo
echo "To run the network monitor:"
echo "  python3 scripts/network_monitor.py"
echo
echo "For help:"
echo "  python3 scripts/network_monitor.py --help"
