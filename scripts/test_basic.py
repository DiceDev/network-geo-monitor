#!/usr/bin/env python3
"""
Basic test script to verify core functionality
"""

import subprocess
import sys
import platform

def test_netstat():
    """Test if netstat command works"""
    print("Testing netstat command...")
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(['netstat', '-ano', '-p', 'tcp'], 
                                  capture_output=True, text=True, check=True, timeout=10)
        else:
            result = subprocess.run(['netstat', '-ant'], 
                                  capture_output=True, text=True, check=True, timeout=10)
        
        lines = result.stdout.splitlines()
        print(f"SUCCESS: Got {len(lines)} lines from netstat")
        
        # Show first few lines
        for i, line in enumerate(lines[:10]):
            print(f"  {i+1}: {line}")
        
        return True
    except Exception as e:
        print(f"ERROR: netstat failed: {e}")
        return False

def test_imports():
    """Test if required modules can be imported"""
    print("Testing imports...")
    
    modules = ['subprocess', 'time', 'os', 'sys', 'platform', 'json', 're']
    optional_modules = ['requests', 'rich', 'geoip2']
    
    for module in modules:
        try:
            __import__(module)
            print(f"  {module}: OK")
        except ImportError as e:
            print(f"  {module}: FAILED - {e}")
            return False
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"  {module}: OK (optional)")
        except ImportError:
            print(f"  {module}: Not available (optional)")
    
    return True

def main():
    print("Basic Network Monitor Test")
    print("=" * 30)
    
    # Test imports
    if not test_imports():
        print("FAILED: Import test failed")
        return False
    
    print()
    
    # Test netstat
    if not test_netstat():
        print("FAILED: Netstat test failed")
        return False
    
    print("\nAll basic tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
