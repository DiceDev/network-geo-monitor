#!/usr/bin/env python3
"""
Test script to verify ss tool integration
"""

import subprocess
import sys
import platform
from pathlib import Path

def test_ss_availability():
    """Test if ss command is available"""
    print("Testing ss command availability...")
    
    if platform.system().lower() == "windows":
        print("⚠ ss command not available on Windows")
        return False
    
    try:
        # Try ss --version
        result = subprocess.run(['ss', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ ss version: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try ss -h as fallback
        result = subprocess.run(['ss', '-h'], capture_output=True, text=True, timeout=5)
        print("✓ ss command available (no version info)")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("✗ ss command not found")
        return False

def test_ss_output():
    """Test ss command output parsing"""
    print("\nTesting ss command output...")
    
    try:
        # Test TCP connections
        print("Testing TCP connections with ss...")
        result = subprocess.run(['ss', '-ant'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(f"✓ Got {len(lines)} lines from 'ss -ant'")
            
            # Show first few data lines
            data_lines = [line for line in lines if line.strip() and not line.startswith(('State', 'Netid'))]
            for i, line in enumerate(data_lines[:5]):
                print(f"  {i+1}: {line}")
        else:
            print(f"✗ ss -ant failed with return code {result.returncode}")
            return False
        
        # Test UDP connections
        print("\nTesting UDP connections with ss...")
        result = subprocess.run(['ss', '-anu'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(f"✓ Got {len(lines)} lines from 'ss -anu'")
        else:
            print(f"✗ ss -anu failed with return code {result.returncode}")
            return False
        
        # Test with process info (may require root)
        print("\nTesting process info with ss...")
        result = subprocess.run(['ss', '-antp'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(f"✓ Got {len(lines)} lines from 'ss -antp' (with process info)")
            
            # Look for process info in output
            process_lines = [line for line in lines if 'pid=' in line]
            if process_lines:
                print(f"✓ Found {len(process_lines)} lines with process info")
                print(f"  Example: {process_lines[0]}")
            else:
                print("⚠ No process info found (may need root privileges)")
        else:
            print("⚠ ss with process info failed (may need root privileges)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing ss output: {e}")
        return False

def test_integrated_ss():
    """Test the integrated ss functionality"""
    print("\nTesting integrated ss functionality...")
    
    try:
        # Add current directory to path so we can import
        sys.path.insert(0, str(Path(__file__).parent))
        
        from network_monitor import CrossPlatformNetworkTools, ConnectionType
        
        # Create network tools instance
        nettools = CrossPlatformNetworkTools()
        
        print(f"Available tools: {nettools.available_tools}")
        
        if 'ss' not in nettools.available_tools:
            print("⚠ ss not detected as available tool")
            return False
        
        # Test getting connections
        print("Testing TCP connection retrieval...")
        tcp_connections = nettools.get_connections(ConnectionType.TCP, filter_listening=True)
        print(f"✓ Retrieved {len(tcp_connections)} TCP connections")
        
        if tcp_connections:
            conn = tcp_connections[0]
            print(f"  Example: {conn.protocol} {conn.local_address} -> {conn.foreign_address} [{conn.state}] PID:{conn.pid}")
        
        print("Testing UDP connection retrieval...")
        udp_connections = nettools.get_connections(ConnectionType.UDP, filter_listening=True)
        print(f"✓ Retrieved {len(udp_connections)} UDP connections")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing integrated ss: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("ss Tool Integration Test")
    print("=" * 30)
    
    if platform.system().lower() == "windows":
        print("This test is for Unix/Linux systems only")
        return True
    
    success = True
    
    # Test 1: ss availability
    if not test_ss_availability():
        print("\nss command not available - this is normal on some systems")
        print("netstat will be used as primary tool")
        return True  # Not a failure, just not available
    
    # Test 2: ss output
    if not test_ss_output():
        success = False
    
    # Test 3: Integrated functionality
    if not test_integrated_ss():
        success = False
    
    if success:
        print("\n✓ All ss integration tests passed!")
        print("The network monitor can now use ss as a backup tool")
    else:
        print("\n✗ Some ss tests failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
