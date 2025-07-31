#!/usr/bin/env python3
"""
Network Connection Monitor with GeoIP Lookup
Enhanced version with better error handling, configuration, and structure
"""

import subprocess
import csv
import time
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import requests

try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False
    print("Warning: geoip2 not available. Install with: pip install geoip2")

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich not available. Install with: pip install rich")


class ConnectionType(Enum):
    TCP = "tcp"
    UDP = "udp"


@dataclass
class NetworkConnection:
    protocol: str
    local_address: str
    foreign_address: str
    state: str
    pid: str
    city: str = ""
    country: str = ""
    asn: str = ""
    
    @property
    def foreign_ip(self) -> str:
        """Extract IP address from foreign_address (remove port)"""
        return self.foreign_address.split(':')[0] if ':' in self.foreign_address else self.foreign_address
    
    @property
    def is_foreign(self) -> bool:
        """Check if connection is to a foreign country"""
        return self.country not in ['United States', ''] and self.country is not None


class GeoIPLookup:
    """Handles GeoIP database operations with multiple fallback methods"""
    
    def __init__(self, city_db_path: str = "./GeoLite2-City.mmdb", 
                 asn_db_path: str = "./GeoLite2-ASN.mmdb"):
        self.city_reader = None
        self.asn_reader = None
        self.cache = {}  # Simple cache for API lookups
        self.api_calls_made = 0
        self.max_api_calls = 100  # Rate limiting
        
        # Try to initialize MaxMind databases first
        self._init_maxmind_dbs(city_db_path, asn_db_path)
        
        # If MaxMind not available, we'll use fallback methods
        if not self.city_reader and not self.asn_reader:
            print("ℹ️  MaxMind databases not available - using online fallback methods")
    
    def _init_maxmind_dbs(self, city_db_path: str, asn_db_path: str):
        """Initialize MaxMind databases if available"""
        if not GEOIP_AVAILABLE:
            return
            
        try:
            if Path(city_db_path).exists():
                self.city_reader = geoip2.database.Reader(city_db_path)
                print(f"✓ Loaded MaxMind City database: {city_db_path}")
            
            if Path(asn_db_path).exists():
                self.asn_reader = geoip2.database.Reader(asn_db_path)
                print(f"✓ Loaded MaxMind ASN database: {asn_db_path}")
                
        except Exception as e:
            print(f"Warning: Error loading MaxMind databases: {e}")
    
    def _lookup_online_ipapi(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup using ip-api.com (free, no key required)"""
        try:
            import requests
            
            if self.api_calls_made >= self.max_api_calls:
                return "", "", ""
            
            url = f"http://ip-api.com/json/{ip_address}?fields=city,country,org"
            response = requests.get(url, timeout=5)
            self.api_calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    city = data.get('city', '')
                    country = data.get('country', '')
                    asn = data.get('org', '')
                    return city, country, asn
                    
        except Exception as e:
            print(f"Warning: Online lookup failed: {e}")
        
        return "", "", ""
    
    def _lookup_builtin_ranges(self, ip_address: str) -> Tuple[str, str, str]:
        """Basic lookup using known IP ranges"""
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)
            
            # Private/local ranges
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return "Local", "Local Network", "Private"
            
            # Some basic country detection based on known ranges
            # This is very limited but better than nothing
            ip_int = int(ip)
            
            # Some basic ranges (this is very simplified)
            if 0x08000000 <= ip_int <= 0x08FFFFFF:  # 8.0.0.0/8 (Google DNS, US)
                return "Mountain View", "United States", "Google LLC"
            elif 0x01010100 <= ip_int <= 0x010101FF:  # 1.1.1.0/24 (Cloudflare DNS)
                return "San Francisco", "United States", "Cloudflare"
            elif 0x4A7D0000 <= ip_int <= 0x4A7DFFFF:  # 74.125.0.0/16 (Google)
                return "Mountain View", "United States", "Google LLC"
            
            # Default for unknown public IPs
            return "", "Unknown", "Unknown ISP"
            
        except Exception:
            return "", "", ""
    
    def lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup geographic and ASN information for an IP address"""
        if not ip_address or ip_address in ['0.0.0.0', '127.0.0.1', '::1', '*']:
            return "", "", ""
        
        # Check cache first
        if ip_address in self.cache:
            return self.cache[ip_address]
        
        city, country, asn = "", "", ""
        
        # Method 1: Try MaxMind databases
        if self.city_reader or self.asn_reader:
            try:
                if self.city_reader:
                    response = self.city_reader.city(ip_address)
                    city = response.city.name or ""
                    country = response.country.name or ""
                    
                if self.asn_reader:
                    response_asn = self.asn_reader.asn(ip_address)
                    asn = response_asn.autonomous_system_organization or ""
                    
                if city or country or asn:
                    result = (city, country, asn)
                    self.cache[ip_address] = result
                    return result
                    
            except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error):
                pass  # Try next method
            except Exception as e:
                print(f"MaxMind lookup error for {ip_address}: {e}")
        
        # Method 2: Try online API (with rate limiting)
        if self.api_calls_made < self.max_api_calls:
            city, country, asn = self._lookup_online_ipapi(ip_address)
            if city or country or asn:
                result = (city, country, asn)
                self.cache[ip_address] = result
                return result
        
        # Method 3: Basic built-in ranges
        city, country, asn = self._lookup_builtin_ranges(ip_address)
        result = (city, country, asn)
        self.cache[ip_address] = result
        return result
    
    def get_lookup_stats(self) -> Dict[str, any]:
        """Get statistics about lookups performed"""
        return {
            "cache_size": len(self.cache),
            "api_calls_made": self.api_calls_made,
            "max_api_calls": self.max_api_calls,
            "maxmind_available": bool(self.city_reader or self.asn_reader),
            "methods_available": self._get_available_methods()
        }
    
    def _get_available_methods(self) -> List[str]:
        """Get list of available lookup methods"""
        methods = []
        if self.city_reader or self.asn_reader:
            methods.append("MaxMind")
        if self.api_calls_made < self.max_api_calls:
            methods.append("Online API")
        methods.append("Built-in ranges")
        return methods
    
    def close(self):
        """Close database connections"""
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()

class ModernNetstat:
    """Uses 'ss' command as modern alternative to netstat"""
    
    def __init__(self):
        self.available = self._check_ss_available()
    
    def _check_ss_available(self) -> bool:
        """Check if ss command is available"""
        try:
            subprocess.run(['ss', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_connections(self, connection_type: ConnectionType, filter_listening: bool = False) -> List[NetworkConnection]:
        """Get connections using ss command"""
        if not self.available:
            return []
        
        connections = []
        
        try:
            # ss command options:
            # -t = TCP, -u = UDP, -l = listening, -n = numeric, -p = show process
            if connection_type == ConnectionType.TCP:
                cmd = ['ss', '-tnp'] if not filter_listening else ['ss', '-tlnp']
            else:  # UDP
                cmd = ['ss', '-unp'] if not filter_listening else ['ss', '-ulnp']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse ss output
            lines = result.stdout.splitlines()
            
            # Skip header line
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    # ss format: State Recv-Q Send-Q Local-Address:Port Peer-Address:Port Process
                    state = parts[0] if connection_type == ConnectionType.TCP else ""
                    local_addr = parts[3]
                    foreign_addr = parts[4]
                    process_info = parts[5] if len(parts) > 5 else ""
                    
                    # Extract PID from process info (format: users:(("process",pid=1234,fd=5)))
                    pid = ""
                    if process_info and "pid=" in process_info:
                        try:
                            pid_start = process_info.find("pid=") + 4
                            pid_end = process_info.find(",", pid_start)
                            if pid_end == -1:
                                pid_end = process_info.find(")", pid_start)
                            pid = process_info[pid_start:pid_end]
                        except:
                            pass
                    
                    conn = NetworkConnection(
                        protocol=connection_type.value.upper(),
                        local_address=local_addr,
                        foreign_address=foreign_addr,
                        state=state,
                        pid=pid
                    )
                    connections.append(conn)
                    
        except subprocess.CalledProcessError as e:
            print(f"Error running ss command: {e}")
        except Exception as e:
            print(f"Error parsing ss output: {e}")
            
        return connections

class CrossPlatformNetstat:
    """Cross-platform netstat wrapper with ss fallback"""
    
    def __init__(self):
        self.os_type = self._detect_os()
        self.netstat_available = self._check_netstat_available()
        self.modern_netstat = ModernNetstat() if not self.netstat_available else None
        
        if not self.netstat_available and self.modern_netstat and self.modern_netstat.available:
            print("ℹ️  Using 'ss' command (netstat not available)")
        elif not self.netstat_available:
            print("⚠️  Neither netstat nor ss available - limited functionality")
    
    def _check_netstat_available(self) -> bool:
        """Check if netstat command is available"""
        try:
            subprocess.run(['netstat', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try without --version flag (some systems don't support it)
                subprocess.run(['netstat'], capture_output=True, timeout=1)
                return True
            except:
                return False
    
    def get_connections(self, connection_type: ConnectionType, filter_listening: bool = False) -> List[NetworkConnection]:
        """Get network connections using available method"""
        if self.netstat_available:
            return self._get_netstat_connections(connection_type, filter_listening)
        elif self.modern_netstat and self.modern_netstat.available:
            return self.modern_netstat.get_connections(connection_type, filter_listening)
        else:
            print("❌ No network monitoring tools available")
            return []

    def _detect_os(self) -> str:
        """Detect the operating system"""
        return sys.platform

    def _get_netstat_connections(self, connection_type: ConnectionType, filter_listening: bool = False) -> List[NetworkConnection]:
        """Get network connections using netstat"""
        connections = []
        
        try:
            cmd = ['netstat', '-ano', '-p', connection_type.value]
            if filter_listening:
                cmd.append('-l')
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse netstat output
            lines = result.stdout.splitlines()
            
            # Skip header lines
            data_lines = [line for line in lines if line.strip() and 
                         not line.startswith('Active') and not line.startswith('Proto')]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 4:
                    if connection_type == ConnectionType.TCP and len(parts) >= 5:
                        conn = NetworkConnection(
                            protocol=parts[0],
                            local_address=parts[1],
                            foreign_address=parts[2],
                            state=parts[3],
                            pid=parts[4]
                        )
                    elif connection_type == ConnectionType.UDP and len(parts) >= 4:
                        conn = NetworkConnection(
                            protocol=parts[0],
                            local_address=parts[1],
                            foreign_address=parts[2],
                            state="",  # UDP doesn't have state
                            pid=parts[3]
                        )
                    else:
                        continue
                    
                    connections.append(conn)
                    
        except subprocess.CalledProcessError as e:
            print(f"Error running netstat: {e}")
        except Exception as e:
            print(f"Error parsing netstat output: {e}")
            
        return connections


class NetworkMonitor:
    """Main network monitoring class"""
    
    def __init__(self, geoip_lookup: GeoIPLookup):
        self.geoip = geoip_lookup
        self.console = Console() if RICH_AVAILABLE else None
        self.netstat = CrossPlatformNetstat()
    
    def get_netstat_connections(self) -> List[NetworkConnection]:
        """Get network connections using netstat"""
        connections = []
        
        # Get TCP connections
        connections.extend(self.netstat.get_connections(ConnectionType.TCP))
        
        # Get UDP connections  
        connections.extend(self.netstat.get_connections(ConnectionType.UDP))
        
        return connections
    
    def _get_connections_by_protocol(self, protocol: ConnectionType) -> List[NetworkConnection]:
        """Get connections for a specific protocol"""
        connections = []
        
        try:
            cmd = ['netstat', '-ano', '-p', protocol.value]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse netstat output
            lines = result.stdout.splitlines()
            
            # Skip header lines
            data_lines = [line for line in lines if line.strip() and 
                         not line.startswith('Active') and not line.startswith('Proto')]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 4:
                    if protocol == ConnectionType.TCP and len(parts) >= 5:
                        conn = NetworkConnection(
                            protocol=parts[0],
                            local_address=parts[1],
                            foreign_address=parts[2],
                            state=parts[3],
                            pid=parts[4]
                        )
                    elif protocol == ConnectionType.UDP and len(parts) >= 4:
                        conn = NetworkConnection(
                            protocol=parts[0],
                            local_address=parts[1],
                            foreign_address=parts[2],
                            state="",  # UDP doesn't have state
                            pid=parts[3]
                        )
                    else:
                        continue
                    
                    # Lookup geographic information
                    city, country, asn = self.geoip.lookup(conn.foreign_ip)
                    conn.city = city
                    conn.country = country
                    conn.asn = asn
                    
                    connections.append(conn)
                    
        except subprocess.CalledProcessError as e:
            print(f"Error running netstat: {e}")
        except Exception as e:
            print(f"Error parsing netstat output: {e}")
            
        return connections
    
    def parse_file_connections(self, file_path: str) -> List[NetworkConnection]:
        """Parse connections from a file"""
        connections = []
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        conn = NetworkConnection(
                            protocol="",
                            local_address=parts[0] if len(parts) > 0 else "",
                            foreign_address=parts[1] if len(parts) > 1 else "",
                            state=parts[2] if len(parts) > 2 else "",
                            pid=""
                        )
                        
                        # Lookup geographic information
                        city, country, asn = self.geoip.lookup(conn.foreign_ip)
                        conn.city = city
                        conn.country = country
                        conn.asn = asn
                        
                        connections.append(conn)
                        
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            
        return connections
    
    def display_connections_rich(self, connections: List[NetworkConnection]):
        """Display connections using rich formatting"""
        if not RICH_AVAILABLE:
            self.display_connections_simple(connections)
            return
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Proto", width=6)
        table.add_column("Local Address", width=22)
        table.add_column("Remote Address", width=20)
        table.add_column("State", width=12)
        table.add_column("PID", width=8)
        table.add_column("City", width=15)
        table.add_column("Country", width=20)
        table.add_column("ASN", width=25)
        
        for conn in connections:
            style = "red" if conn.is_foreign else "white"
            
            table.add_row(
                conn.protocol,
                conn.local_address,
                conn.foreign_address,
                conn.state,
                conn.pid,
                conn.city,
                conn.country,
                conn.asn,
                style=style
            )
        
        self.console.print(table)
    
    def display_connections_simple(self, connections: List[NetworkConnection]):
        """Display connections using simple text formatting"""
        # Print header
        print(f"{'Proto':<6} {'Local Address':<22} {'Remote Address':<20} {'State':<12} {'PID':<8} {'City':<15} {'Country':<20} {'ASN':<25}")
        print("-" * 130)
        
        # Print connections
        for conn in connections:
            print(f"{conn.protocol:<6} {conn.local_address:<22} {conn.foreign_address:<20} "
                  f"{conn.state:<12} {conn.pid:<8} {conn.city:<15} {conn.country:<20} {conn.asn:<25}")
    
    def monitor_continuous(self, refresh_interval: int = 5):
        """Monitor connections continuously"""
        if RICH_AVAILABLE:
            with Live(refresh_per_second=1/refresh_interval) as live:
                while True:
                    connections = self.get_netstat_connections()
                    
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Proto", width=6)
                    table.add_column("Local Address", width=22)
                    table.add_column("Remote Address", width=20)
                    table.add_column("State", width=12)
                    table.add_column("PID", width=8)
                    table.add_column("City", width=15)
                    table.add_column("Country", width=20)
                    table.add_column("ASN", width=25)
                    
                    for conn in connections:
                        style = "red" if conn.is_foreign else "white"
                        table.add_row(
                            conn.protocol,
                            conn.local_address,
                            conn.foreign_address,
                            conn.state,
                            conn.pid,
                            conn.city,
                            conn.country,
                            conn.asn,
                            style=style
                        )
                    
                    live.update(table)
                    time.sleep(refresh_interval)
        else:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                connections = self.get_netstat_connections()
                self.display_connections_simple(connections)
                time.sleep(refresh_interval)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Network Connection Monitor with GeoIP Lookup")
    parser.add_argument("file", nargs="?", help="File to parse instead of live monitoring")
    parser.add_argument("--city-db", default="./GeoLite2-City.mmdb", 
                       help="Path to GeoLite2 City database")
    parser.add_argument("--asn-db", default="./GeoLite2-ASN.mmdb",
                       help="Path to GeoLite2 ASN database") 
    parser.add_argument("--interval", type=int, default=5,
                       help="Refresh interval in seconds for continuous monitoring")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--stats", action="store_true", help="Show lookup statistics")
    
    args = parser.parse_args()
    
    # Initialize GeoIP lookup
    geoip = GeoIPLookup(args.city_db, args.asn_db)
    
    # Show available lookup methods
    stats = geoip.get_lookup_stats()
    print(f"🌍 Geographic lookup methods: {', '.join(stats['methods_available'])}")
    
    # Initialize monitor
    monitor = NetworkMonitor(geoip)
    
    try:
        if args.stats:
            # Show detailed statistics
            print("\n📊 Lookup Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            return
            
        if args.file:
            # Parse file mode
            connections = monitor.parse_file_connections(args.file)
            monitor.display_connections_rich(connections)
            
            if args.export:
                export_data = [
                    {
                        "protocol": conn.protocol,
                        "local_address": conn.local_address,
                        "foreign_address": conn.foreign_address,
                        "state": conn.state,
                        "pid": conn.pid,
                        "city": conn.city,
                        "country": conn.country,
                        "asn": conn.asn
                    }
                    for conn in connections
                ]
                
                with open(args.export, 'w') as f:
                    json.dump(export_data, f, indent=2)
                print(f"Results exported to {args.export}")
        else:
            # Continuous monitoring mode
            print("Starting network monitoring... Press Ctrl+C to stop")
            monitor.monitor_continuous(args.interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        
        # Show final statistics
        final_stats = geoip.get_lookup_stats()
        print(f"\n📊 Final Statistics:")
        print(f"  Cached lookups: {final_stats['cache_size']}")
        print(f"  API calls made: {final_stats['api_calls_made']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        geoip.close()


if __name__ == "__main__":
    main()
