#!/usr/bin/env python3
"""
Test Unix/Linux/macOS compatibility for the network monitor
"""

import subprocess
import platform
import sys
import os
from pathlib import Path

def test_platform_detection():
    """Test platform detection"""
    print("🖥️  Platform Detection Test")
    print("=" * 30)
    
    system = platform.system()
    print(f"Platform.system(): {system}")
    print(f"Platform.platform(): {platform.platform()}")
    print(f"Platform.machine(): {platform.machine()}")
    print(f"Platform.processor(): {platform.processor()}")
    
    # Test our OS detection logic
    system_lower = system.lower()
    if system_lower == "windows":
        detected_os = "Windows"
    elif system_lower == "darwin":
        detected_os = "macOS"
    elif system_lower == "linux":
        detected_os = "Linux"
    else:
        detected_os = "Unknown"
    
    print(f"Our detection: {detected_os}")
    return detected_os

def test_netstat_commands():
    """Test different netstat commands on Unix systems"""
    print("\n🔍 Netstat Command Test")
    print("=" * 25)
    
    # Commands to test
    commands = [
        # Linux style
        (["netstat", "-ant"], "Linux TCP connections"),
        (["netstat", "-anu"], "Linux UDP connections"),
        
        # macOS style  
        (["netstat", "-an", "-p", "tcp"], "macOS TCP connections"),
        (["netstat", "-an", "-p", "udp"], "macOS UDP connections"),
        
        # Generic
        (["netstat", "-an"], "Generic connections"),
        
        # Alternative: ss command (modern Linux)
        (["ss", "-tuln"], "ss command (modern Linux)"),
    ]
    
    working_commands = []
    
    for cmd, description in commands:
        try:
            print(f"\nTesting: {' '.join(cmd)} ({description})")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                print(f"  ✓ Success: {len(lines)} lines returned")
                
                # Show first few lines as sample
                for i, line in enumerate(lines[:5]):
                    print(f"    {i+1}: {line}")
                if len(lines) > 5:
                    print(f"    ... and {len(lines) - 5} more lines")
                
                working_commands.append((cmd, description, len(lines)))
            else:
                print(f"  ✗ Failed with return code: {result.returncode}")
                if result.stderr:
                    print(f"    Error: {result.stderr.strip()}")
                    
        except FileNotFoundError:
            print(f"  ✗ Command not found: {cmd[0]}")
        except subprocess.TimeoutExpired:
            print(f"  ✗ Command timed out")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n📊 Summary: {len(working_commands)} working commands found")
    for cmd, desc, lines in working_commands:
        print(f"  ✓ {' '.join(cmd)} - {desc} ({lines} lines)")
    
    return working_commands

def test_netstat_parsing():
    """Test parsing netstat output on Unix systems"""
    print("\n📝 Netstat Parsing Test")
    print("=" * 25)
    
    # Try to get some actual netstat output
    commands_to_try = [
        ["netstat", "-ant"],  # Linux
        ["netstat", "-an", "-p", "tcp"],  # macOS
        ["netstat", "-an"],  # Generic
    ]
    
    for cmd in commands_to_try:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"Using command: {' '.join(cmd)}")
                lines = result.stdout.splitlines()
                
                # Parse like our script does
                parsed_connections = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith(('Active', 'Proto')):
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 6:
                        # Unix format: Proto Recv-Q Send-Q Local-Address Foreign-Address State
                        if parts[0].lower() in ['tcp', 'tcp4', 'tcp6']:
                            connection = {
                                'protocol': parts[0].upper(),
                                'local_address': parts[3],
                                'foreign_address': parts[4],
                                'state': parts[5],
                                'pid': ''  # Unix netstat doesn't show PID by default
                            }
                            parsed_connections.append(connection)
                
                print(f"Parsed {len(parsed_connections)} TCP connections")
                
                # Show first few parsed connections
                for i, conn in enumerate(parsed_connections[:5]):
                    print(f"  {i+1}: {conn['protocol']} {conn['local_address']} -> {conn['foreign_address']} ({conn['state']})")
                
                if len(parsed_connections) > 5:
                    print(f"  ... and {len(parsed_connections) - 5} more connections")
                
                return True
                
        except Exception as e:
            print(f"Failed with {' '.join(cmd)}: {e}")
            continue
    
    print("❌ Could not parse any netstat output")
    return False

def test_process_info():
    """Test getting process information on Unix"""
    print("\n🔍 Process Information Test")
    print("=" * 30)
    
    # Test different ways to get process info
    methods = [
        (["ps", "aux"], "ps aux - all processes"),
        (["ps", "-ef"], "ps -ef - all processes"),
        (["lsof", "-i"], "lsof -i - network connections with processes"),
        (["ss", "-tulpn"], "ss -tulpn - sockets with process info"),
    ]
    
    working_methods = []
    
    for cmd, description in methods:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                print(f"✓ {description}: {len(lines)} lines")
                working_methods.append((cmd, description))
            else:
                print(f"✗ {description}: failed")
        except FileNotFoundError:
            print(f"✗ {description}: command not found")
        except Exception as e:
            print(f"✗ {description}: {e}")
    
    return working_methods

def test_permissions():
    """Test if we need special permissions"""
    print("\n🔐 Permissions Test")
    print("=" * 20)
    
    print(f"Current user: {os.getenv('USER', 'unknown')}")
    print(f"Effective UID: {os.geteuid() if hasattr(os, 'geteuid') else 'N/A'}")
    print(f"Running as root: {os.geteuid() == 0 if hasattr(os, 'geteuid') else 'N/A'}")
    
    # Test if we can access network info without root
    try:
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ Can run netstat without special permissions")
        else:
            print("✗ netstat failed - might need elevated permissions")
    except Exception as e:
        print(f"✗ Error testing netstat: {e}")

def test_our_monitor():
    """Test our actual network monitor on Unix"""
    print("\n🧪 Network Monitor Test")
    print("=" * 25)
    
    try:
        # Import our network monitor
        sys.path.insert(0, str(Path(__file__).parent))
        from network_monitor import NetworkMonitor, GeoIPLookup, CrossPlatformNetstat, ConnectionType
        
        print("✓ Successfully imported network monitor modules")
        
        # Test OS detection
        netstat = CrossPlatformNetstat()
        print(f"✓ Detected OS type: {netstat.os_type}")
        
        # Test getting connections
        print("Testing TCP connection retrieval...")
        tcp_connections = netstat.get_connections(ConnectionType.TCP, filter_listening=True)
        print(f"✓ Found {len(tcp_connections)} TCP connections")
        
        print("Testing UDP connection retrieval...")
        udp_connections = netstat.get_connections(ConnectionType.UDP, filter_listening=True)
        print(f"✓ Found {len(udp_connections)} UDP connections")
        
        # Show a few sample connections
        all_connections = tcp_connections + udp_connections
        if all_connections:
            print(f"\nSample connections:")
            for i, conn in enumerate(all_connections[:3]):
                print(f"  {i+1}: {conn.protocol} {conn.local_address} -> {conn.foreign_address} ({conn.state})")
        
        return True
        
    except ImportError as e:
        print(f"✗ Could not import network monitor: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing network monitor: {e}")
        return False

def main():
    """Main test function"""
    print("🐧 Unix/Linux/macOS Compatibility Test")
    print("=" * 40)
    
    # Test 1: Platform detection
    detected_os = test_platform_detection()
    
    if detected_os == "Windows":
        print("\n⚠️  Running on Windows - Unix tests may not be relevant")
        print("   Run this script on Linux or macOS for proper testing")
        return
    
    # Test 2: Netstat commands
    working_commands = test_netstat_commands()
    
    # Test 3: Netstat parsing
    parsing_works = test_netstat_parsing()
    
    # Test 4: Process information
    process_methods = test_process_info()
    
    # Test 5: Permissions
    test_permissions()
    
    # Test 6: Our actual monitor
    monitor_works = test_our_monitor()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 15)
    print(f"Platform: {detected_os}")
    print(f"Working netstat commands: {len(working_commands)}")
    print(f"Netstat parsing: {'✓' if parsing_works else '✗'}")
    print(f"Process info methods: {len(process_methods)}")
    print(f"Network monitor: {'✓' if monitor_works else '✗'}")
    
    if working_commands and parsing_works and monitor_works:
        print("\n🎉 Unix compatibility looks good!")
    else:
        print("\n⚠️  Some issues found - may need fixes for this platform")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not working_commands:
        print("   • Install net-tools package: sudo apt-get install net-tools")
    if len(process_methods) == 0:
        print("   • Install additional tools: sudo apt-get install lsof")
    if detected_os == "Linux" and "ss" not in [cmd[0] for cmd, _, _ in working_commands]:
        print("   • Consider using 'ss' command as modern alternative to netstat")

if __name__ == "__main__":
    main()
