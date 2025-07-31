#!/usr/bin/env python3
"""
Simple dependency installer that tries multiple methods
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_with_pip():
    """Try to install with pip"""
    packages = ["geoip2", "rich", "requests"]
    
    print("Trying to install with pip...")
    for package in packages:
        print(f"Installing {package}...", end=" ")
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {package}")
        if success:
            print("✓")
        else:
            print("✗")
            print(f"  Error: {stderr}")
    
def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("⚠ Warning: Python 3.7+ recommended")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def main():
    print("🔧 Network Monitor Dependency Installer")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Try to install packages
    install_with_pip()
    
    print("\n📋 Testing imports...")
    test_imports = {
        "geoip2": "GeoIP2 database support",
        "rich": "Enhanced terminal display", 
        "requests": "Online geo lookup fallback"
    }
    
    for module, description in test_imports.items():
        try:
            __import__(module)
            print(f"✓ {module} - {description}")
        except ImportError:
            print(f"✗ {module} - {description} (will use fallback)")
    
    print("\n🎯 Ready to run network_monitor.py!")

if __name__ == "__main__":
    main()
