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

# Import our simple geo database
try:
    from simple_geo_db import SimpleGeoDatabase
    SIMPLE_GEO_AVAILABLE = True
except ImportError:
    SIMPLE_GEO_AVAILABLE = False

# Geo lookup options - multiple fallbacks for ease of use
GEOIP_AVAILABLE = False
REQUESTS_AVAILABLE = False

try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
    print("✓ GeoIP2 module available for MaxMind databases")
except ImportError:
    print("✗ GeoIP2 module not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
    print("✓ Requests module available for online lookup")
except ImportError:
    print("✗ Requests module not available")

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
        
        try:
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
        except Exception as e:
            print(f"Error during location detection: {e}")
        
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
        self.simple_db = None
        
        # Country code to name mapping
        self.country_codes = {
            'US': 'United States', 'CA': 'Canada', 'GB': 'United Kingdom', 'DE': 'Germany',
            'FR': 'France', 'IT': 'Italy', 'ES': 'Spain', 'NL': 'Netherlands', 'BE': 'Belgium',
            'CH': 'Switzerland', 'AT': 'Austria', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark',
            'FI': 'Finland', 'IE': 'Ireland', 'PT': 'Portugal', 'GR': 'Greece', 'PL': 'Poland',
            'CZ': 'Czech Republic', 'HU': 'Hungary', 'RO': 'Romania', 'BG': 'Bulgaria',
            'HR': 'Croatia', 'SI': 'Slovenia', 'SK': 'Slovakia', 'LT': 'Lithuania', 'LV': 'Latvia',
            'EE': 'Estonia', 'RU': 'Russia', 'UA': 'Ukraine', 'BY': 'Belarus', 'JP': 'Japan',
            'CN': 'China', 'KR': 'South Korea', 'IN': 'India', 'AU': 'Australia', 'NZ': 'New Zealand',
            'BR': 'Brazil', 'MX': 'Mexico', 'AR': 'Argentina', 'CL': 'Chile', 'CO': 'Colombia',
            'PE': 'Peru', 'VE': 'Venezuela', 'ZA': 'South Africa', 'EG': 'Egypt', 'NG': 'Nigeria',
            'KE': 'Kenya', 'MA': 'Morocco', 'TN': 'Tunisia', 'IL': 'Israel', 'TR': 'Turkey',
            'SA': 'Saudi Arabia', 'AE': 'United Arab Emirates', 'QA': 'Qatar', 'KW': 'Kuwait',
            'SG': 'Singapore', 'MY': 'Malaysia', 'TH': 'Thailand', 'VN': 'Vietnam', 'PH': 'Philippines',
            'ID': 'Indonesia', 'TW': 'Taiwan', 'HK': 'Hong Kong'
        }
        
        # Initialize lookup methods in order of preference
        self._init_lookup_methods(city_db_path, asn_db_path, use_online)
    
    def _init_lookup_methods(self, city_db_path: str, asn_db_path: str, use_online: bool):
        """Initialize lookup methods in order of preference"""
        methods_available = []
        
        # Method 1: Try MaxMind GeoIP databases (most accurate)
        if GEOIP_AVAILABLE:
            try:
                if Path(city_db_path).exists() and Path(asn_db_path).exists():
                    self.city_reader = geoip2.database.Reader(city_db_path)
                    self.asn_reader = geoip2.database.Reader(asn_db_path)
                    methods_available.append("MaxMind GeoLite2 databases")
                    print(f"✓ Using MaxMind GeoLite2 databases")
                else:
                    print(f"✗ MaxMind databases not found: {city_db_path}, {asn_db_path}")
            except Exception as e:
                print(f"Error initializing MaxMind databases: {e}")
        
        # Method 2: Simple built-in database (good coverage for major services)
        if SIMPLE_GEO_AVAILABLE:
            try:
                self.simple_db = SimpleGeoDatabase()
                methods_available.append("Simple built-in database")
                print("✓ Using simple built-in geo database")
            except Exception as e:
                print(f"Error initializing simple database: {e}")
        
        # Method 3: Online APIs (requires internet)
        if REQUESTS_AVAILABLE and use_online:
            methods_available.append("Online APIs")
            print("✓ Online geo lookup available")
        
        # Report available methods
        if methods_available:
            print(f"Geo lookup methods available: {', '.join(methods_available)}")
        else:
            print("⚠ No geo lookup methods available - will show basic info only")
    
    def lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup geographic and ASN information for an IP address"""
        if not ip_address or ip_address in ['0.0.0.0', '127.0.0.1', '::1', '*', '0.0.0.0:0']:
            return "", "", ""
        
        # Skip private IP ranges
        if self._is_private_ip(ip_address):
            return "", "Private", "Local Network"
        
        # Method 1: Try MaxMind databases first (most accurate)
        if self.city_reader and self.asn_reader:
            try:
                city_response = self.city_reader.city(ip_address)
                city = city_response.city.name or ""
                country = city_response.country.name or ""
                
                asn_response = self.asn_reader.asn(ip_address)
                asn = asn_response.autonomous_system_organization or ""
                
                if country:  # If we got good data, return it
                    return city, country, asn
                    
            except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error):
                pass  # Fall through to next method
            except Exception as e:
                print(f"Error in MaxMind lookup for {ip_address}: {e}")
        
        # Method 2: Try simple built-in database
        if self.simple_db:
            try:
                city, country, asn = self.simple_db.lookup(ip_address)
                if country and country != "Unknown":
                    return city, country, asn
            except Exception as e:
                print(f"Error in simple database lookup for {ip_address}: {e}")
        
        # Method 3: Try online APIs
        if REQUESTS_AVAILABLE and self.use_online:
            try:
                return self._online_lookup(ip_address)
            except Exception as e:
                print(f"Error in online lookup for {ip_address}: {e}")
        
        # Method 4: Last resort - return unknown
        return "", "Unknown", ""
    
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
        
        # Try ip-api.com first
        try:
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=city,country,org,as,status", 
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    city = data.get('city', '') or ""
                    country = data.get('country', '') or ""
                    asn_info = data.get('as', '') or data.get('org', '') or ""
                    
                    # Clean up ASN info
                    asn_info = self._clean_asn(asn_info)
                    
                    result = (city, country, asn_info)
                    self.online_cache[ip_address] = result
                    return result
        except Exception as e:
            pass
        
        # Try ipinfo.io as backup
        try:
            response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                city = data.get('city', '') or ""
                country = data.get('country', '') or ""
                asn_info = data.get('org', '') or ""
                
                # Convert country code to full name if needed
                if len(country) == 2 and country.upper() in self.country_codes:
                    country = self.country_codes[country.upper()]
                
                # Clean up ASN info
                asn_info = self._clean_asn(asn_info)
                
                result = (city, country, asn_info)
                self.online_cache[ip_address] = result
                return result
        except Exception as e:
            pass
        
        return "", "Unknown", ""
    
    def _clean_asn(self, asn_info: str) -> str:
        """Clean up ASN information for better display"""
        if not asn_info:
            return ""
        
        # Remove AS prefix (e.g., "AS15169 Google LLC" -> "Google LLC")
        asn_info = re.sub(r'^AS\d+\s+', '', asn_info)
        
        # Remove common prefixes
        prefixes_to_remove = ['AS ', 'ASN ', 'Autonomous System ']
        for prefix in prefixes_to_remove:
            if asn_info.startswith(prefix):
                asn_info = asn_info[len(prefix):]
        
        return asn_info.strip()
    
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
        print(f"Getting {protocol.value.upper()} connections...")
        try:
            if self.os_type == OSType.WINDOWS:
                return self._get_windows_connections(protocol, filter_listening)
            else:
                return self._get_unix_connections(protocol, filter_listening)
        except Exception as e:
            print(f"Error getting {protocol.value} connections: {e}")
            return []
    
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
        except Exception as e:
            print(f"Error parsing Unix netstat output: {e}")
            
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
        try:
            self.local_country = self.country_detector.detect_country()
        except Exception as e:
            print(f"Error during initialization: {e}")
            self.local_country = "United States"  # Fallback
    
    def get_netstat_connections(self, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get network connections using cross-platform netstat"""
        connections = []
        
        try:
            # Get TCP connections
            tcp_connections = self.netstat.get_connections(ConnectionType.TCP, filter_listening)
            connections.extend(tcp_connections)
            
            # Get UDP connections  
            udp_connections = self.netstat.get_connections(ConnectionType.UDP, filter_listening)
            connections.extend(udp_connections)
            
            print(f"Total connections before geo lookup: {len(connections)}")
            
            # Add geographic information
            for i, conn in enumerate(connections):
                try:
                    city, country, asn = self.geoip.lookup(conn.foreign_ip)
                    conn.city = city
                    conn.country = country
                    conn.asn = asn
                    
                    # Debug first few lookups
                    if i < 5:
                        print(f"Lookup {i+1}: {conn.foreign_ip} -> {city}, {country}, {asn}")
                        
                except Exception as e:
                    print(f"Error in geo lookup for {conn.foreign_ip}: {e}")
                    conn.city = ""
                    conn.country = "Lookup Error"
                    conn.asn = "Lookup Error"
            
        except Exception as e:
            print(f"Error getting connections: {e}")
            import traceback
            traceback.print_exc()
        
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
            print("Starting continuous monitoring...")
            while True:
                try:
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
                    break
                except Exception as e:
                    print(f"Error during monitoring iteration: {e}")
                    time.sleep(refresh_interval)  # Wait before retrying
        except Exception as e:
            print(f"Error in continuous monitoring: {e}")


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
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug output")
    
    args = parser.parse_args()
    
    print("Cross-Platform Network Monitor")
    print("=" * 40)
    
    try:
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
        
        if args.file:
            # Parse file mode
            print("File parsing mode not implemented yet")
        else:
            # Continuous monitoring mode
            filter_text = " (filtering out listening connections)" if filter_listening else ""
            print(f"Starting network monitoring{filter_text}...")
            print("Press Ctrl+C to stop")
            monitor.monitor_continuous(args.interval, filter_listening)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            geoip.close()
        except:
            pass


if __name__ == "__main__":
    main()
