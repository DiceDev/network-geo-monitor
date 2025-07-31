#!/bin/bash

echo "🔧 Network Tools Installation Helper"
echo "==================================="
echo

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
else
    OS=$(uname -s)
    VER=$(uname -r)
fi

echo "Detected OS: $OS"

# Check if netstat is available
if command -v netstat &> /dev/null; then
    echo "✓ netstat is already installed"
    netstat --version 2>/dev/null || echo "  (version info not available)"
else
    echo "❌ netstat not found"
    echo
    echo "Installing netstat..."
    
    # Ubuntu/Debian
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        echo "Using apt package manager..."
        sudo apt-get update
        sudo apt-get install -y net-tools
    
    # CentOS/RHEL/Fedora
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
        if command -v dnf &> /dev/null; then
            echo "Using dnf package manager..."
            sudo dnf install -y net-tools
        elif command -v yum &> /dev/null; then
            echo "Using yum package manager..."
            sudo yum install -y net-tools
        fi
    
    # Arch Linux
    elif [[ "$OS" == *"Arch"* ]]; then
        echo "Using pacman package manager..."
        sudo pacman -S --noconfirm net-tools
    
    # openSUSE
    elif [[ "$OS" == *"openSUSE"* ]]; then
        echo "Using zypper package manager..."
        sudo zypper install -y net-tools
    
    # macOS
    elif [[ "$OS" == *"Darwin"* ]]; then
        echo "netstat should be available on macOS by default"
        echo "If not working, try: xcode-select --install"
    
    else
        echo "⚠️  Unknown distribution: $OS"
        echo "Please install net-tools package manually:"
        echo "  - Ubuntu/Debian: sudo apt-get install net-tools"
        echo "  - CentOS/RHEL: sudo yum install net-tools"
        echo "  - Fedora: sudo dnf install net-tools"
        echo "  - Arch: sudo pacman -S net-tools"
    fi
fi

echo
echo "Checking ss command (modern alternative)..."
if command -v ss &> /dev/null; then
    echo "✓ ss command is available"
    ss --version
else
    echo "❌ ss command not found (usually part of iproute2 package)"
fi

echo
echo "Testing network commands..."

# Test netstat
if command -v netstat &> /dev/null; then
    echo "Testing netstat..."
    netstat_lines=$(netstat -an 2>/dev/null | wc -l)
    echo "  ✓ netstat returned $netstat_lines lines"
else
    echo "  ❌ netstat still not available"
fi

# Test ss
if command -v ss &> /dev/null; then
    echo "Testing ss..."
    ss_lines=$(ss -tuln 2>/dev/null | wc -l)
    echo "  ✓ ss returned $ss_lines lines"
else
    echo "  ❌ ss not available"
fi

echo
echo "🎉 Installation complete!"
echo
echo "The network monitor will now work with available tools."
echo "Run: python3 scripts/network_monitor.py"
