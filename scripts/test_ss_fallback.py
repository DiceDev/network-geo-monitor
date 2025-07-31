#!/usr/bin/env python3
"""
Test the ss command fallback functionality
"""

import subprocess
import sys
from pathlib import Path

def test_ss_command():
    """Test if ss command works"""
    print("🔍 Testing ss command...")
    
    try:
        # Test ss version
        result = subprocess.run(['ss', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ ss version: {result.stderr.strip()}")  # ss outputs version to stderr
        
        # Test ss TCP connections
        result = subprocess.run(['ss', '-tn'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(f"✓ ss TCP: {len(lines)} lines returned")
            
            # Show sample output
            for i, line in enumerate(lines[:3]):
                print(f"  {i+1}: {line}")
            
            return True
        else:
            print(f"✗ ss failed with return code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("✗ ss command not found")
        return False
    except Exception as e:
        print(f"✗ Error testing ss: {e}")
        return False

def test_netstat_command():
    """Test if netstat command works"""
    print("\n🔍 Testing netstat command...")
    
    try:
        # Test netstat
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(f"✓ netstat: {len(lines)} lines returned")
            return True
        else:
            print(f"✗ netstat failed with return code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("✗ netstat command not found")
        return False
    except Exception as e:
        print(f"✗ Error testing netstat: {e}")
        return False

def test_network_monitor_import():
    """Test importing our network monitor"""
    print("\n🧪 Testing network monitor import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Try to import
        from network_monitor import NetworkMonitor, GeoIPLookup, ModernNetstat, CrossPlatformNetstat
        print("✓ Successfully imported all classes")
        
        # Test ModernNetstat
        modern = ModernNetstat()
        print(f"✓ ModernNetstat available: {modern.available}")
        
        # Test CrossPlatformNetstat
        cross_platform = CrossPlatformNetstat()
        print(f"✓ CrossPlatformNetstat OS: {cross_platform.os_type}")
        print(f"✓ Netstat available: {cross_platform.netstat_available}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 SS Fallback Test")
    print("=" * 20)
    
    netstat_works = test_netstat_command()
    ss_works = test_ss_command()
    import_works = test_network_monitor_import()
    
    print("\n📊 Test Results")
    print("=" * 15)
    print(f"Netstat available: {'✓' if netstat_works else '✗'}")
    print(f"SS available: {'✓' if ss_works else '✗'}")
    print(f"Network monitor: {'✓' if import_works else '✗'}")
    
    if ss_works or netstat_works:
        print("\n🎉 Network monitoring should work!")
        if ss_works and not netstat_works:
            print("   Using modern 'ss' command")
        elif netstat_works:
            print("   Using traditional 'netstat' command")
    else:
        print("\n❌ No network monitoring tools available")
        print("   Install net-tools: sudo apt-get install net-tools")
    
    print(f"\nRecommendation:")
    if not netstat_works and not ss_works:
        print("  Install network tools: sudo apt-get install net-tools iproute2")
    elif not netstat_works:
        print("  The network monitor will use 'ss' command (modern alternative)")
    else:
        print("  Network monitoring tools are properly configured")

if __name__ == "__main__":
    main()
