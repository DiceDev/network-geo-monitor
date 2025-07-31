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
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json
import re

# Geo lookup options - multiple fallbacks for ease of use
GEOIP_AVAILABLE = False
REQUESTS_AVAILABLE = False
BUILTIN_ONLY = False

try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
except ImportError:
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except ImportError:
        BUILTIN_ONLY = True

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConnectionType(Enum):
    TCP = "tcp"
    UDP = "udp"


class OSType(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


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
        if ':' in self.foreign_address:
            # Handle IPv6 addresses properly
            if self.foreign_address.startswith('['):
                # IPv6 format: [::1]:80
                return self.foreign_address.split(']:')[0][1:]
            else:
                # IPv4 format: 192.168.1.1:80
                return self.foreign_address.split(':')[0]
        return self.foreign_address
    
    def is_foreign(self, local_country: str) -> bool:
        """Check if connection is to a foreign country"""
        if not self.country or self.country in ['', 'Unknown', 'Local Network', 'Private']:
            return False
        return self.country != local_country
    
    def is_listening(self) -> bool:
        """Check if connection is in listening state"""
        return self.state.upper() in ['LISTENING', 'LISTEN']
    
    def is_established(self) -> bool:
        """Check if connection is established"""
        return self.state.upper() in ['ESTABLISHED', 'CLOSE_WAIT', 'TIME_WAIT']
    
    def is_uninteresting(self) -> bool:
        """Check if connection is uninteresting (should be filtered out)"""
        # Filter out UDP connections to 0.0.0.0 or *.*
        if self.protocol.upper() == 'UDP':
            if (self.foreign_address.startswith('0.0.0.0:') or 
                self.foreign_address.startswith('*:') or
                self.foreign_address == '*:*' or
                self.foreign_address == '0.0.0.0:0'):
                return True
        
        # Filter out loopback connections (127.0.0.1 to 127.0.0.1)
        if ('127.0.0.1' in self.local_address and '127.0.0.1' in self.foreign_address):
            return True
            
        # Filter out connections to unspecified addresses
        if self.foreign_address in ['0.0.0.0:0', '*:*', ':::0']:
            return True
            
        return False


class CountryDetector:
    """Detects the user's country automatically"""
    
    def __init__(self, geoip_lookup=None, default_country: str = "United States"):
        self.geoip_lookup = geoip_lookup
        self.default_country = default_country
        self.detected_country = None
        self.public_ip = None
    
    def detect_country(self) -> str:
        """Auto-detect user's country with fallback to default"""
        if self.detected_country:
            return self.detected_country
            
        print("Auto-detecting your location...")
        
        # Method 1: Get public IP and look it up
        public_ip = self._get_public_ip()
        if public_ip and self.geoip_lookup:
            city, country, asn = self.geoip_lookup.lookup(public_ip)
            if country and country not in ['Unknown', 'Local Network', 'Private', 'Europe', 'Asia']:
                self.detected_country = country
                self.public_ip = public_ip
                print(f"Detected location: {country} (IP: {public_ip})")
                return country
        
        # Method 2: Use online service to detect country directly
        country = self._get_country_online()
        if country and country not in ['Unknown', 'Local Network', 'Private', 'Europe', 'Asia']:
            self.detected_country = country
            print(f"Detected location: {country}")
            return country
        
        # Fallback to default country
        print(f"Could not auto-detect location, using default: {self.default_country}")
        self.detected_country = self.default_country
        return self.default_country
    
    def _get_public_ip(self) -> Optional[str]:
        """Get user's public IP address"""
        if not REQUESTS_AVAILABLE:
            return None
            
        services = [
            "https://api.ipify.org?format=text",
            "https://ipinfo.io/ip",
            "https://icanhazip.com",
            "https://ident.me",
            "https://api.my-ip.io/ip"
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # Basic IP validation
                    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
                        return ip
            except Exception as e:
                continue
        
        return None
    
    def _get_country_online(self) -> Optional[str]:
        """Get country directly from online service"""
        if not REQUESTS_AVAILABLE:
            return None
            
        services = [
            ("https://ipinfo.io/json", lambda x: x.get('country_name') or x.get('country')),
            ("https://ip-api.com/json", lambda x: x.get('country') if x.get('status') == 'success' else None),
        ]
        
        for url, extractor in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    country = extractor(data)
                    if country and len(country) > 2:  # Avoid country codes, get full names
                        return country
            except Exception as e:
                continue
                
        return None


class GeoIPLookup:
    """Handles geographic lookups with multiple fallback methods"""
    
    def __init__(self, city_db_path: str = "./GeoLite2-City.mmdb", 
                 asn_db_path: str = "./GeoLite2-ASN.mmdb", use_online: bool = True):
        self.city_reader = None
        self.asn_reader = None
        self.use_online = use_online
        self.online_cache = {}  # Simple cache for online lookups
        
        # Try to use local GeoIP databases first
        if GEOIP_AVAILABLE:
            try:
                if Path(city_db_path).exists():
                    self.city_reader = geoip2.database.Reader(city_db_path)
                    print("Using local GeoLite2 City database")
                    
                if Path(asn_db_path).exists():
                    self.asn_reader = geoip2.database.Reader(asn_db_path)
                    print("Using local GeoLite2 ASN database")
                    
            except Exception as e:
                print(f"Error initializing GeoIP databases: {e}")
        
        # Fallback methods
        if not (self.city_reader and self.asn_reader):
            if REQUESTS_AVAILABLE and use_online:
                print("Using online geo lookup as fallback")
            else:
                print("Limited geo lookup available")
    
    def lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup geographic and ASN information for an IP address"""
        city, country, asn = "", "", ""
        
        if not ip_address or ip_address in ['0.0.0.0', '127.0.0.1', '::1', '*', '0.0.0.0:0']:
            return city, country, asn
        
        # Skip private IP ranges
        if self._is_private_ip(ip_address):
            return "", "Private", "Local Network"
            
        # Try local databases first (preferred method)
        if self.city_reader and self.asn_reader:
            try:
                city_response = self.city_reader.city(ip_address)
                city = city_response.city.name or ""
                country = city_response.country.name or ""
                
                asn_response = self.asn_reader.asn(ip_address)
                asn = asn_response.autonomous_system_organization or ""
                
                # If we got good data from local databases, return it
                if country and country != "":
                    return city, country, asn
                    
            except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error):
                pass  # Fall through to online lookup
            except Exception as e:
                print(f"Error looking up {ip_address} in local DB: {e}")
        
        # Fallback to online lookup if local databases failed or aren't available
        if REQUESTS_AVAILABLE and self.use_online:
            return self._online_lookup(ip_address)
        
        # Last resort: basic classification (should rarely be used now)
        return self._basic_lookup(ip_address)
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private ranges"""
        try:
            # Handle IPv6
            if ':' in ip:
                return ip.startswith('::1') or ip.startswith('fe80:') or ip.startswith('fc00:')
            
            parts = [int(x) for x in ip.split('.')]
            if len(parts) != 4:
                return False
                
            # Private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
            if parts[0] == 10:
                return True
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            if parts[0] == 192 and parts[1] == 168:
                return True
            if parts[0] == 127:  # Loopback
                return True
                
        except (ValueError, IndexError):
            pass
            
        return False
    
    def _online_lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Use free online API for geo lookup"""
        if ip_address in self.online_cache:
            return self.online_cache[ip_address]
            
        try:
            # Using ip-api.com with more fields for better data
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=city,country,org,as,status", 
                timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    city = data.get('city', '') or ""
                    country = data.get('country', '') or ""
                    # Get ASN info from 'as' field (better than 'org')
                    asn_info = data.get('as', '') or data.get('org', '') or ""
                    
                    result = (city, country, asn_info)
                    self.online_cache[ip_address] = result
                    return result
                    
        except Exception as e:
            pass  # Silently fail and try next method
        
        # Try ipinfo.io as backup
        try:
            response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=3)
            if response.status_code == 200:
                data = response.json()
                city = data.get('city', '') or ""
                country = data.get('country_name', '') or data.get('country', '') or ""
                asn_info = data.get('org', '') or ""
                
                result = (city, country, asn_info)
                self.online_cache[ip_address] = result
                return result
        except Exception:
            pass
            
        return self._basic_lookup(ip_address)
    
    def _basic_lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Basic classification without external services - only for well-known IPs"""
        try:
            if ':' in ip_address:  # IPv6
                return "", "Unknown", "IPv6"
                
            parts = [int(x) for x in ip_address.split('.')]
            if len(parts) != 4:
                return "", "Unknown", ""
                
            # Only classify well-known public DNS and CDN services
            known_services = {
                '8.8.8.8': ("Mountain View", "United States", "Google Public DNS"),
                '8.8.4.4': ("Mountain View", "United States", "Google Public DNS"),
                '1.1.1.1': ("San Francisco", "United States", "Cloudflare DNS"),
                '1.0.0.1': ("San Francisco", "United States", "Cloudflare DNS"),
                '208.67.222.222': ("San Francisco", "United States", "OpenDNS"),
                '208.67.220.220': ("San Francisco", "United States", "OpenDNS"),
                '9.9.9.9': ("Berkeley", "United States", "Quad9 DNS"),
                '149.112.112.112': ("Berkeley", "United States", "Quad9 DNS"),
            }
            
            if ip_address in known_services:
                return known_services[ip_address]
            
            # For unknown IPs, return minimal info instead of guessing
            return "", "Unknown", "Public IP"
                
        except (ValueError, IndexError):
            return "", "Unknown", ""
    
    def close(self):
        """Close database connections"""
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()


class CrossPlatformNetstat:
    """Handles netstat across different operating systems"""
    
    def __init__(self):
        self.os_type = self._detect_os()
        print(f"Detected OS: {self.os_type.value}")
    
    def _detect_os(self) -> OSType:
        """Detect the operating system"""
        system = platform.system().lower()
        if system == "windows":
            return OSType.WINDOWS
        elif system == "darwin":
            return OSType.MACOS
        elif system == "linux":
            return OSType.LINUX
        else:
            return OSType.UNKNOWN
    
    def get_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get network connections for the current OS"""
        if self.os_type == OSType.WINDOWS:
            return self._get_windows_connections(protocol, filter_listening)
        else:
            return self._get_unix_connections(protocol, filter_listening)
    
    def _get_windows_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get connections on Windows using netstat -ano"""
        connections = []
        
        try:
            cmd = ['netstat', '-ano', '-p', protocol.value]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.splitlines()
            
            # Skip header lines - Windows format
            data_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('Active') and not line.startswith('Proto'):
                    # Check if line starts with TCP or UDP
                    if line.startswith(('TCP', 'UDP')):
                        data_lines.append(line)
            
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
                        
                        # Filter out listening connections if requested
                        if filter_listening and conn.is_listening():
                            continue
                            
                        # Filter out uninteresting connections
                        if conn.is_uninteresting():
                            continue
                            
                        connections.append(conn)
                        
                    elif protocol == ConnectionType.UDP and len(parts) >= 4:
                        conn = NetworkConnection(
                            protocol=parts[0],
                            local_address=parts[1],
                            foreign_address=parts[2],
                            state="",  # UDP doesn't have state
                            pid=parts[3]
                        )
                        
                        # Filter out uninteresting connections
                        if conn.is_uninteresting():
                            continue
                            
                        connections.append(conn)
                        
        except subprocess.CalledProcessError as e:
            print(f"Error running Windows netstat: {e}")
        except Exception as e:
            print(f"Error parsing Windows netstat output: {e}")
            
        return connections
    
    def _get_unix_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get connections on Unix/Linux/macOS"""
        connections = []
        
        try:
            # Different commands for different Unix variants
            if self.os_type == OSType.MACOS:
                # macOS netstat
                if protocol == ConnectionType.TCP:
                    cmd = ['netstat', '-an', '-p', 'tcp']
                else:
                    cmd = ['netstat', '-an', '-p', 'udp']
            else:
                # Linux netstat
                if protocol == ConnectionType.TCP:
                    cmd = ['netstat', '-ant']
                else:
                    cmd = ['netstat', '-anu']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            
            # Parse Unix netstat output
            for line in lines:
                line = line.strip()
                if not line or line.startswith(('Active', 'Proto', 'tcp', 'udp')):
                    continue
                
                parts = line.split()
                if len(parts) >= 6:
                    # Unix format: Proto Recv-Q Send-Q Local-Address Foreign-Address State
                    if parts[0].lower() == protocol.value:
                        state = parts[5] if protocol == ConnectionType.TCP else ""
                        
                        conn = NetworkConnection(
                            protocol=parts[0].upper(),
                            local_address=parts[3],
                            foreign_address=parts[4],
                            state=state,
                            pid=""  # Unix netstat doesn't show PID by default
                        )
                        
                        # Filter out listening connections if requested
                        if filter_listening and conn.is_listening():
                            continue
                            
                        # Filter out uninteresting connections
                        if conn.is_uninteresting():
                            continue
                            
                        connections.append(conn)
                        
        except subprocess.CalledProcessError as e:
            print(f"Error running Unix netstat: {e}")
            # Try alternative command
            try:
                cmd = ['ss', '-tuln'] if protocol == ConnectionType.TCP else ['ss', '-uln']
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                connections.extend(self._parse_ss_output(result.stdout, protocol, filter_listening))
            except:
                print("Neither netstat nor ss available")
        except Exception as e:
            print(f"Error parsing Unix netstat output: {e}")
            
        return connections
    
    def _parse_ss_output(self, output: str, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Parse ss command output as fallback"""
        connections = []
        lines = output.splitlines()
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5:
                state = parts[1] if protocol == ConnectionType.TCP else ""
                
                conn = NetworkConnection(
                    protocol=protocol.value.upper(),
                    local_address=parts[3],
                    foreign_address=parts[4],
                    state=state,
                    pid=""
                )
                
                # Filter out listening connections if requested
                if filter_listening and conn.is_listening():
                    continue
                    
                # Filter out uninteresting connections
                if conn.is_uninteresting():
                    continue
                    
                connections.append(conn)
                
        return connections


class NetworkMonitor:
    """Main network monitoring class with cross-platform support"""
    
    def __init__(self, geoip_lookup: GeoIPLookup, default_country: str = "United States"):
        self.geoip = geoip_lookup
        self.console = Console() if RICH_AVAILABLE else None
        self.netstat = CrossPlatformNetstat()
        self.country_detector = CountryDetector(geoip_lookup, default_country)
        self.local_country = None
    
    def initialize(self):
        """Initialize the monitor and detect local country"""
        self.local_country = self.country_detector.detect_country()
    
    def get_netstat_connections(self, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get network connections using cross-platform netstat"""
        connections = []
        
        # Get TCP connections
        connections.extend(self.netstat.get_connections(ConnectionType.TCP, filter_listening))
        
        # Get UDP connections  
        connections.extend(self.netstat.get_connections(ConnectionType.UDP, filter_listening))
        
        # Add geographic information
        for conn in connections:
            city, country, asn = self.geoip.lookup(conn.foreign_ip)
            conn.city = city
            conn.country = country
            conn.asn = asn
        
        return connections
    
    def display_connections_rich(self, connections: List[NetworkConnection]):
        """Display connections using rich formatting with full addresses"""
        if not RICH_AVAILABLE:
            self.display_connections_simple(connections)
            return
        
        # Get terminal width to adjust table size
        console_width = self.console.size.width if self.console else 120
        
        # Create table with dynamic sizing
        table = Table(show_header=True, header_style="bold magenta", show_lines=False, width=console_width)
        table.add_column("Proto", width=5, no_wrap=True)
        table.add_column("Local Address", width=22, no_wrap=False)
        table.add_column("Remote Address", width=22, no_wrap=False)
        table.add_column("State", width=11, no_wrap=True)
        table.add_column("PID", width=6, no_wrap=True)
        table.add_column("City", width=15, no_wrap=False)
        table.add_column("Country", width=15, no_wrap=False)
        table.add_column("Organization", min_width=20, no_wrap=False)
        
        for conn in connections:
            style = "red" if conn.is_foreign(self.local_country) else "white"
            
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
        
        # Add summary
        total = len(connections)
        foreign = sum(1 for conn in connections if conn.is_foreign(self.local_country))
        established = sum(1 for conn in connections if conn.is_established())
        
        self.console.print(f"\nSummary: {total} connections ({established} established), {foreign} foreign, {total-foreign} domestic")
        if self.local_country:
            self.console.print(f"Your location: {self.local_country}")
        
        self.console.print(table)
    
    def display_connections_simple(self, connections: List[NetworkConnection]):
        """Display connections using simple text formatting with full addresses"""
        # Dynamic column widths based on content
        max_local = max(len(conn.local_address) for conn in connections) if connections else 20
        max_remote = max(len(conn.foreign_address) for conn in connections) if connections else 20
        max_city = max(len(conn.city) for conn in connections) if connections else 15
        max_country = max(len(conn.country) for conn in connections) if connections else 15
        
        # Ensure minimum widths
        max_local = max(max_local, 20)
        max_remote = max(max_remote, 20)
        max_city = max(max_city, 15)
        max_country = max(max_country, 15)
        
        # Print header
        print(f"{'Proto':<5} {'Local Address':<{max_local}} {'Remote Address':<{max_remote}} {'State':<11} {'PID':<6} {'City':<{max_city}} {'Country':<{max_country}} {'Organization'}")
        print("-" * (5 + max_local + max_remote + 11 + 6 + max_city + max_country + 20 + 8))
        
        # Print all connections without truncation
        for conn in connections:
            marker = "[F]" if conn.is_foreign(self.local_country) else "[D]"
            
            print(f"{marker} {conn.protocol:<4} {conn.local_address:<{max_local}} {conn.foreign_address:<{max_remote}} "
                  f"{conn.state:<11} {conn.pid:<6} {conn.city:<{max_city}} {conn.country:<{max_country}} {conn.asn}")
        
        # Summary
        total = len(connections)
        foreign = sum(1 for conn in connections if conn.is_foreign(self.local_country))
        established = sum(1 for conn in connections if conn.is_established())
        print(f"\nSummary: {total} connections ({established} established), {foreign} foreign, {total-foreign} domestic")
        if self.local_country:
            print(f"Your location: {self.local_country}")
    
    def monitor_continuous(self, refresh_interval: int = 5, filter_listening: bool = True):
        """Monitor connections continuously"""
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                connections = self.get_netstat_connections(filter_listening)
                
                if connections:
                    self.display_connections_rich(connections)
                else:
                    print("No active connections found.")
                    if self.local_country:
                        print(f"Your location: {self.local_country}")
                
                filter_text = " (no listening)" if filter_listening else ""
                print(f"\nRefreshing every {refresh_interval}s{filter_text} - Press Ctrl+C to stop")
                
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"Error during monitoring: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Cross-Platform Network Connection Monitor with Auto-Country Detection")
    parser.add_argument("file", nargs="?", help="File to parse instead of live monitoring")
    parser.add_argument("--city-db", default="./GeoLite2-City.mmdb", 
                       help="Path to GeoLite2 City database")
    parser.add_argument("--asn-db", default="./GeoLite2-ASN.mmdb",
                       help="Path to GeoLite2 ASN database") 
    parser.add_argument("--interval", type=int, default=5,
                       help="Refresh interval in seconds for continuous monitoring")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--country", help="Override auto-detected country")
    parser.add_argument("--default-country", default="United States", 
                       help="Default country if auto-detection fails")
    parser.add_argument("--show-listening", action="store_true",
                       help="Include listening connections (default: filter them out)")
    parser.add_argument("--no-online", action="store_true",
                       help="Disable online geo lookup (use only local databases)")
    
    args = parser.parse_args()
    
    print("Cross-Platform Network Monitor")
    print("=" * 40)
    
    # Initialize GeoIP lookup
    geoip = GeoIPLookup(args.city_db, args.asn_db, use_online=not args.no_online)
    
    # Initialize monitor
    monitor = NetworkMonitor(geoip, args.default_country)
    
    # Override country if specified
    if args.country:
        monitor.local_country = args.country
        print(f"Using specified country: {args.country}")
    else:
        monitor.initialize()
    
    filter_listening = not args.show_listening
    
    try:
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
                        "asn": conn.asn,
                        "is_foreign": conn.is_foreign(monitor.local_country)
                    }
                    for conn in connections
                ]
                
                with open(args.export, 'w') as f:
                    json.dump(export_data, f, indent=2)
                print(f"Results exported to {args.export}")
        else:
            # Continuous monitoring mode
            filter_text = " (filtering out listening connections)" if filter_listening else ""
            print(f"Starting network monitoring{filter_text}...")
            print("Filtering out: UDP 0.0.0.0:*, loopback connections, uninteresting traffic")
            print("Press Ctrl+C to stop")
            monitor.monitor_continuous(args.interval, filter_listening)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        geoip.close()


if __name__ == "__main__":
    main()
