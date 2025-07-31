#!/usr/bin/env python3
"""
Test cross-platform compatibility to ensure identical behavior on Windows and Unix
"""

import subprocess
import sys
import platform
from pathlib import Path

def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == "windows":
        return "Windows"
    elif system == "darwin":
        return "macOS"
    elif system == "linux":
        return "Linux"
    else:
        return f"Unix-like ({system})"

def test_network_tools():
    """Test available network monitoring tools"""
    print("🔧 Testing Network Tools")
    print("=" * 25)
    
    tools_status = {}
    
    # Test netstat
    try:
        result = subprocess.run(['netstat', '--version'], capture_output=True, timeout=5)
        tools_status['netstat'] = result.returncode == 0
    except:
        try:
            result = subprocess.run(['netstat'], capture_output=True, timeout=2)
            tools_status['netstat'] = True
        except:
            tools_status['netstat'] = False
    
    # Test ss (Unix)
    try:
        result = subprocess.run(['ss', '--version'], capture_output=True, timeout=5)
        tools_status['ss'] = result.returncode == 0
    except:
        tools_status['ss'] = False
    
    for tool, available in tools_status.items():
        status = "✓" if available else "✗"
        print(f"  {status} {tool}")
    
    return tools_status

def test_network_monitor_import():
    """Test importing and initializing the network monitor"""
    print("\n🧪 Testing Network Monitor")
    print("=" * 27)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from network_monitor import NetworkMonitor, GeoIPLookup, CrossPlatformNetstat
        
        print("✓ Successfully imported network monitor")
        
        # Test initialization
        geoip = GeoIPLookup()
        monitor = NetworkMonitor(geoip)
        
        print("✓ Successfully initialized monitor")
        
        # Test platform detection
        netstat = CrossPlatformNetstat()
        print(f"✓ Detected OS: {netstat.os_type}")
        print(f"✓ Netstat available: {netstat.netstat_available}")
        
        if hasattr(netstat, 'modern_netstat') and netstat.modern_netstat:
            print(f"✓ SS fallback available: {netstat.modern_netstat.available}")
        
        geoip.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_basic_functionality():
    """Test basic network monitoring functionality"""
    print("\n🌐 Testing Basic Functionality")
    print("=" * 30)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from network_monitor import NetworkMonitor, GeoIPLookup, ConnectionType
        
        geoip = GeoIPLookup()
        monitor = NetworkMonitor(geoip)
        
        # Test getting connections
        connections = monitor.get_netstat_connections()
        print(f"✓ Retrieved {len(connections)} network connections")
        
        # Test geographic lookup on a few connections
        geo_count = 0
        for conn in connections[:3]:  # Test first 3 connections
            if conn.foreign_ip and conn.foreign_ip not in ['0.0.0.0', '127.0.0.1', '*']:
                city, country, asn = geoip.lookup(conn.foreign_ip)
                if city or country or asn:
                    geo_count += 1
        
        print(f"✓ Geographic lookup working for {geo_count} connections")
        
        # Show sample connection
        if connections:
            sample = connections[0]
            print(f"✓ Sample connection: {sample.protocol} {sample.local_address} -> {sample.foreign_address}")
        
        geoip.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_command_line_options():
    """Test command line options work"""
    print("\n⚙️  Testing Command Line Options")
    print("=" * 32)
    
    script_path = Path(__file__).parent / "network_monitor.py"
    
    # Test help option
    try:
        result = subprocess.run([sys.executable, str(script_path), "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "usage:" in result.stdout.lower():
            print("✓ Help option works")
        else:
            print("✗ Help option failed")
    except Exception as e:
        print(f"✗ Help test error: {e}")
    
    # Test stats option
    try:
        result = subprocess.run([sys.executable, str(script_path), "--stats"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Stats option works")
        else:
            print("✗ Stats option failed")
    except Exception as e:
        print(f"✗ Stats test error: {e}")

def main():
    """Main test function"""
    print("🖥️  Cross-Platform Compatibility Test")
    print("=" * 37)
    
    platform_name = detect_platform()
    print(f"Platform: {platform_name}")
    print()
    
    # Run tests
    tools_status = test_network_tools()
    import_success = test_network_monitor_import()
    functionality_success = test_basic_functionality()
    test_command_line_options()
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 15)
    print(f"Platform: {platform_name}")
    print(f"Network tools: {list(k for k, v in tools_status.items() if v)}")
    print(f"Import test: {'✓' if import_success else '✗'}")
    print(f"Functionality: {'✓' if functionality_success else '✗'}")
    
    if import_success and functionality_success:
        print(f"\n🎉 Network monitor ready on {platform_name}!")
        print("Run: python3 scripts/network_monitor.py")
    else:
        print(f"\n⚠️  Some issues found on {platform_name}")
        
        if not any(tools_status.values()):
            print("   Install network tools:")
            if "linux" in platform_name.lower():
                print("     sudo apt-get install net-tools")
            elif "windows" in platform_name.lower():
                print("     netstat should be built-in")

if __name__ == "__main__":
    main()
