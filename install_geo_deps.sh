#!/bin/bash

echo "🌍 Geographic Lookup Dependencies Installation"
echo "============================================="
echo

# Install Python dependencies
echo "📦 Installing Python packages..."
python3 -m pip install --user requests rich

# Check if installation was successful
echo
echo "🧪 Testing installations..."

# Test requests
python3 -c "import requests; print('✓ requests installed')" 2>/dev/null || echo "❌ requests installation failed"

# Test rich
python3 -c "import rich; print('✓ rich installed')" 2>/dev/null || echo "❌ rich installation failed"

# Test geographic lookup
echo
echo "🌍 Testing geographic lookup..."
python3 scripts/test_geo_lookup.py

echo
echo "🎉 Installation complete!"
echo
echo "The network monitor should now show geographic information."
echo "Run: python3 scripts/network_monitor.py"
