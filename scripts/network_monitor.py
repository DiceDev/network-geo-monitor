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
import logging
import pickle
from datetime import datetime, timedelta

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
    
    def __init__(self, geoip_lookup=None, default_country: str = "United States", logger=None):
        self.geoip_lookup = geoip_lookup
        self.default_country = default_country
        self.detected_country = None
        self.public_ip = None
        self.detection_method = None  # Track how country was determined
        self.logger = logger or logging.getLogger(__name__)
    
    def detect_country(self) -> str:
        """Auto-detect user's country with fallback to default"""
        if self.detected_country:
            return self.detected_country
            
        print("🌍 Auto-detecting your location...")
        
        try:
            # Method 1: Get public IP and look it up
            public_ip = self._get_public_ip()
            if public_ip and self.geoip_lookup:
                city, country, asn = self.geoip_lookup.lookup(public_ip)
                if country and country not in ['Unknown', 'Local Network', 'Private', 'Europe', 'Asia']:
                    self.detected_country = country
                    self.public_ip = public_ip
                    self.detection_method = "auto-detected"
                    print(f"✓ Auto-detected location: {country} (IP: {public_ip})")
                    return country
            
            # Method 2: Use online service to detect country directly
            country = self._get_country_online()
            if country and country not in ['Unknown', 'Local Network', 'Private', 'Europe', 'Asia']:
                self.detected_country = country
                self.detection_method = "auto-detected"
                print(f"✓ Auto-detected location: {country}")
                return country
        except Exception as e:
            self.logger.error(f"Error during location detection: {e}")
        
        # Fallback to default country
        print(f"⚠ Could not auto-detect location, using default: {self.default_country}")
        self.detected_country = self.default_country
        self.detection_method = "default"
        return self.default_country
    
    def set_manual_country(self, country: str):
        """Set country manually (overrides auto-detection)"""
        self.detected_country = country
        self.detection_method = "manual"
    
    def get_location_info(self) -> str:
        """Get formatted location information with detection method"""
        if not self.detected_country:
            return "Unknown location"
        
        method_text = {
            "auto-detected": "auto-detected",
            "manual": "manually set", 
            "default": "default"
        }.get(self.detection_method, "unknown")
        
        return f"{self.detected_country} ({method_text})"
    
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
                self.logger.debug(f"Failed to get IP from {service}: {e}")
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
                self.logger.debug(f"Failed to get country from {url}: {e}")
                continue
                
        return None


class GeoIPLookup:
    """Handles geographic lookups with multiple fallback methods and intelligent caching"""
    
    def __init__(self, city_db_path: str = "./GeoLite2-City.mmdb", 
                 asn_db_path: str = "./GeoLite2-ASN.mmdb", use_online: bool = True, logger=None):
        self.city_reader = None
        self.asn_reader = None
        self.use_online = use_online
        self.online_cache = {}  # Runtime cache
        self.persistent_cache = {}  # Disk-backed cache
        # Always store cache in the same directory as the script
        script_dir = Path(__file__).parent
        self.cache_file = script_dir / "geo_cache.pkl"
        self.simple_db = None
        self.logger = logger or logging.getLogger(__name__)
        self.last_online_lookup = {}  # Rate limiting tracker
        self.online_lookup_delay = 1.0  # Minimum seconds between online lookups
        self.methods_used = []  # Track which methods are available
        
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
        
        # Load persistent cache
        self._load_cache()
        
        # Initialize lookup methods in order of preference
        self._init_lookup_methods(city_db_path, asn_db_path, use_online)
    
    def _load_cache(self):
        """Load persistent cache from disk"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.persistent_cache = cache_data.get('cache', {})
                    # Clean old entries (older than 7 days)
                    cutoff = datetime.now() - timedelta(days=7)
                    self.persistent_cache = {
                        ip: data for ip, data in self.persistent_cache.items()
                        if data.get('timestamp', datetime.now()) > cutoff
                    }
                    self.logger.debug(f"Loaded {len(self.persistent_cache)} cached geo entries")
        except Exception as e:
            self.logger.error(f"Error loading geo cache: {e}")
            self.persistent_cache = {}
    
    def _save_cache(self):
        """Save persistent cache to disk"""
        try:
            cache_data = {
                'cache': self.persistent_cache,
                'saved_at': datetime.now()
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            self.logger.debug(f"Saved {len(self.persistent_cache)} geo entries to cache")
        except Exception as e:
            self.logger.error(f"Error saving geo cache: {e}")
    
    def _init_lookup_methods(self, city_db_path: str, asn_db_path: str, use_online: bool):
        """Initialize lookup methods in order of preference"""
        self.methods_used = []
        
        # Method 1: Try MaxMind GeoIP databases (most accurate)
        if GEOIP_AVAILABLE:
            try:
                if Path(city_db_path).exists() and Path(asn_db_path).exists():
                    self.city_reader = geoip2.database.Reader(city_db_path)
                    self.asn_reader = geoip2.database.Reader(asn_db_path)
                    self.methods_used.append("MaxMind")
                    print("✓ Using MaxMind GeoLite2 databases")
                else:
                    self.logger.debug(f"MaxMind databases not found: {city_db_path}, {asn_db_path}")
            except Exception as e:
                self.logger.error(f"Error initializing MaxMind databases: {e}")
        
        # Method 2: Simple built-in database (good coverage for major services)
        if SIMPLE_GEO_AVAILABLE:
            try:
                self.simple_db = SimpleGeoDatabase()
                self.methods_used.append("Built-in")
                if not self.methods_used or "MaxMind" not in self.methods_used:
                    print("✓ Using built-in geo database")
            except Exception as e:
                self.logger.error(f"Error initializing simple database: {e}")
        
        # Method 3: Online APIs (requires internet)
        if REQUESTS_AVAILABLE and use_online:
            self.methods_used.append("Online")
            if len(self.methods_used) == 1:
                print("✓ Using online geo lookup")
        
        # Report available methods
        if self.methods_used:
            self.logger.info(f"Geo lookup methods: {', '.join(self.methods_used)}")
        else:
            print("⚠ Limited geo lookup available")
    
    def get_methods_summary(self) -> str:
        """Get a summary of available lookup methods"""
        if not self.methods_used:
            return "No geo lookup"
        
        method_map = {
            "MaxMind": "MM",
            "Built-in": "DB", 
            "Online": "API"
        }
        
        short_methods = [method_map.get(method, method) for method in self.methods_used]
        return " + ".join(short_methods)
    
    def lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup geographic and ASN information for an IP address with intelligent caching"""
        if not ip_address or ip_address in ['0.0.0.0', '127.0.0.1', '::1', '*', '0.0.0.0:0']:
            return "", "", ""
        
        # Skip private IP ranges
        if self._is_private_ip(ip_address):
            return "", "Private", "Local Network"
        
        # Check persistent cache first
        if ip_address in self.persistent_cache:
            cached_data = self.persistent_cache[ip_address]
            self.logger.debug(f"Cache hit for {ip_address}")
            return cached_data['city'], cached_data['country'], cached_data['asn']
        
        # Check runtime cache
        if ip_address in self.online_cache:
            return self.online_cache[ip_address]
        
        # Method 1: Try MaxMind databases first (most accurate)
        if self.city_reader and self.asn_reader:
            try:
                city_response = self.city_reader.city(ip_address)
                city = city_response.city.name or ""
                country = city_response.country.name or ""
                
                asn_response = self.asn_reader.asn(ip_address)
                asn = asn_response.autonomous_system_organization or ""
                
                if country:  # If we got good data, cache and return it
                    self._cache_result(ip_address, city, country, asn)
                    self.logger.debug(f"MaxMind lookup {ip_address}: {city}, {country}, {asn}")
                    return city, country, asn
                    
            except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error):
                self.logger.debug(f"IP {ip_address} not found in MaxMind databases")
                pass  # Fall through to next method
            except Exception as e:
                self.logger.error(f"Error in MaxMind lookup for {ip_address}: {e}")
        
        # Method 2: Try simple built-in database
        if self.simple_db:
            try:
                city, country, asn = self.simple_db.lookup(ip_address)
                if country and country != "Unknown":
                    self._cache_result(ip_address, city, country, asn)
                    self.logger.debug(f"Simple DB lookup {ip_address}: {city}, {country}, {asn}")
                    return city, country, asn
            except Exception as e:
                self.logger.error(f"Error in simple database lookup for {ip_address}: {e}")
        
        # Method 3: Try online APIs (with rate limiting)
        if REQUESTS_AVAILABLE and self.use_online:
            try:
                # Rate limiting check
                now = datetime.now()
                if ip_address in self.last_online_lookup:
                    time_since_last = (now - self.last_online_lookup[ip_address]).total_seconds()
                    if time_since_last < self.online_lookup_delay:
                        self.logger.debug(f"Rate limiting online lookup for {ip_address}")
                        return "", "Unknown", ""
                
                result = self._online_lookup(ip_address)
                self.last_online_lookup[ip_address] = now
                
                if result[1] != "Unknown":
                    self._cache_result(ip_address, result[0], result[1], result[2])
                    self.logger.debug(f"Online lookup {ip_address}: {result}")
                    return result
            except Exception as e:
                self.logger.error(f"Error in online lookup for {ip_address}: {e}")
        
        # Method 4: Last resort - return unknown
        self.logger.debug(f"No geo data found for {ip_address}")
        return "", "Unknown", ""
    
    def _cache_result(self, ip_address: str, city: str, country: str, asn: str):
        """Cache a lookup result both in memory and persistently"""
        result_data = {
            'city': city,
            'country': country, 
            'asn': asn,
            'timestamp': datetime.now()
        }
        
        # Cache in memory
        self.online_cache[ip_address] = (city, country, asn)
        
        # Cache persistently
        self.persistent_cache[ip_address] = result_data
        
        # Periodically save cache (every 10 entries)
        if len(self.persistent_cache) % 10 == 0:
            self._save_cache()
    
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
                    
                    return (city, country, asn_info)
        except Exception as e:
            self.logger.debug(f"ip-api.com failed for {ip_address}: {e}")
        
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
                
                return (city, country, asn_info)
        except Exception as e:
            self.logger.debug(f"ipinfo.io failed for {ip_address}: {e}")
        
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
        """Close database connections and save cache"""
        self._save_cache()
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()


class CrossPlatformNetworkTools:
    """Handles network connection retrieval across different operating systems using netstat or ss"""
    
    def __init__(self, logger=None):
        self.os_type = self._detect_os()
        self.logger = logger or logging.getLogger(__name__)
        self.available_tools = self._detect_available_tools()
        self.logger.info(f"Detected OS: {self.os_type.value}")
        self.logger.info(f"Available network tools: {', '.join(self.available_tools)}")
    
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
    
    def _detect_available_tools(self) -> List[str]:
        """Detect which network tools are available"""
        tools = []
        
        # Check for netstat
        try:
            subprocess.run(['netstat', '--version'], capture_output=True, check=True, timeout=5)
            tools.append('netstat')
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            try:
                # Some systems don't support --version, try a simple command
                subprocess.run(['netstat', '-h'], capture_output=True, timeout=5)
                tools.append('netstat')
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Check for ss (only on non-Windows systems)
        if self.os_type != OSType.WINDOWS:
            try:
                subprocess.run(['ss', '--version'], capture_output=True, check=True, timeout=5)
                tools.append('ss')
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                try:
                    # Some versions don't support --version
                    subprocess.run(['ss', '-h'], capture_output=True, timeout=5)
                    tools.append('ss')
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
        
        return tools
    
    def get_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get network connections for the current OS"""
        self.logger.debug(f"Getting {protocol.value.upper()} connections...")
        try:
            if self.os_type == OSType.WINDOWS:
                return self._get_windows_connections(protocol, filter_listening)
            else:
                return self._get_unix_connections(protocol, filter_listening)
        except Exception as e:
            self.logger.error(f"Error getting {protocol.value} connections: {e}")
            return []
    
    def _get_windows_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get connections on Windows using netstat -ano"""
        connections = []
        
        try:
            cmd = ['netstat', '-ano', '-p', protocol.value]
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.splitlines()
            self.logger.debug(f"Got {len(lines)} lines from netstat")
            
            # Skip header lines - Windows format
            data_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('Active') and not line.startswith('Proto'):
                    # Check if line starts with TCP or UDP
                    if line.startswith(('TCP', 'UDP')):
                        data_lines.append(line)
            
            self.logger.debug(f"Found {len(data_lines)} data lines")
            
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
            self.logger.error(f"Error running Windows netstat: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing Windows netstat output: {e}")
            
        self.logger.debug(f"Returning {len(connections)} {protocol.value} connections")
        return connections
    
    def _get_unix_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get connections on Unix/Linux/macOS using netstat or ss as fallback"""
        connections = []
        
        # Try netstat first if available
        if 'netstat' in self.available_tools:
            try:
                return self._get_unix_netstat_connections(protocol, filter_listening)
            except Exception as e:
                self.logger.warning(f"netstat failed, trying ss: {e}")
        
        # Try ss as fallback if available
        if 'ss' in self.available_tools:
            try:
                return self._get_unix_ss_connections(protocol, filter_listening)
            except Exception as e:
                self.logger.error(f"ss also failed: {e}")
        
        # If neither tool is available
        if not self.available_tools:
            self.logger.error("Neither netstat nor ss is available")
            raise Exception("No network tools available (netstat or ss required)")
        
        return connections

    
    def _get_unix_netstat_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get connections using netstat on Unix systems"""
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
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
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
            self.logger.error(f"Error running Unix netstat: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing Unix netstat output: {e}")
            raise
            
        return connections

    def _get_unix_ss_connections(self, protocol: ConnectionType, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get connections using ss command on Linux systems"""
        connections = []
        
        try:
            # ss command options
            if protocol == ConnectionType.TCP:
                cmd = ['ss', '-ant']  # -a all, -n numeric, -t tcp
            else:
                cmd = ['ss', '-anu']  # -a all, -n numeric, -u udp
            
            # Add process info if available (requires root on some systems)
            try:
                # Test if we can get process info
                test_cmd = cmd + ['-p']
                test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    cmd.append('-p')  # Add process info if available
            except:
                pass  # Continue without process info
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            lines = result.stdout.splitlines()
            
            # Parse ss output
            for line in lines:
                line = line.strip()
                if not line or line.startswith(('State', 'Netid', 'UNCONN', 'LISTEN')):
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    # ss format: State Recv-Q Send-Q Local-Address:Port Peer-Address:Port [Process]
                    state = parts[0] if protocol == ConnectionType.TCP else ""
                    local_addr = parts[3]
                    foreign_addr = parts[4]
                    
                    # Extract PID from process info if available
                    pid = ""
                    if len(parts) > 5 and 'pid=' in parts[5]:
                        # Process format: users:(("process",pid=1234,fd=5))
                        import re
                        pid_match = re.search(r'pid=(\d+)', parts[5])
                        if pid_match:
                            pid = pid_match.group(1)
                    
                    conn = NetworkConnection(
                        protocol=protocol.value.upper(),
                        local_address=local_addr,
                        foreign_address=foreign_addr,
                        state=state,
                        pid=pid
                    )
                    
                    # Filter out listening connections if requested
                    if filter_listening and (conn.is_listening() or state == 'LISTEN'):
                        continue
                        
                    # Filter out uninteresting connections
                    if conn.is_uninteresting():
                        continue
                        
                    connections.append(conn)
                    
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running ss command: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing ss output: {e}")
            raise
            
        return connections


class NetworkMonitor:
    """Main network monitoring class with cross-platform support"""
    
    def __init__(self, geoip_lookup: GeoIPLookup, default_country: str = "United States", logger=None):
        self.geoip = geoip_lookup
        self.console = Console() if RICH_AVAILABLE else None
        self.nettools = CrossPlatformNetworkTools(logger)  # Changed from netstat to nettools
        self.country_detector = CountryDetector(geoip_lookup, default_country, logger)
        self.local_country = None
        self.logger = logger or logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize the monitor and detect local country"""
        try:
            self.local_country = self.country_detector.detect_country()
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            self.local_country = "United States"  # Fallback
    
    def get_netstat_connections(self, filter_listening: bool = True) -> List[NetworkConnection]:
        """Get network connections using cross-platform network tools"""
        connections = []
        
        try:
            # Get TCP connections
            tcp_connections = self.nettools.get_connections(ConnectionType.TCP, filter_listening)  # Changed from netstat to nettools
            connections.extend(tcp_connections)
            
            # Get UDP connections  
            udp_connections = self.nettools.get_connections(ConnectionType.UDP, filter_listening)  # Changed from netstat to nettools
            connections.extend(udp_connections)
            
            self.logger.info(f"Found {len(connections)} connections before geo lookup")
            
            # Add geographic information
            for i, conn in enumerate(connections):
                try:
                    city, country, asn = self.geoip.lookup(conn.foreign_ip)
                    conn.city = city
                    conn.country = country
                    conn.asn = asn
                    
                except Exception as e:
                    self.logger.error(f"Error in geo lookup for {conn.foreign_ip}: {e}")
                    conn.city = ""
                    conn.country = "Lookup Error"
                    conn.asn = "Lookup Error"
        
        except Exception as e:
            self.logger.error(f"Error getting connections: {e}")
        
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
        
        # Enhanced summary with location and geo source info
        total = len(connections)
        foreign = sum(1 for conn in connections if conn.is_foreign(self.local_country))
        established = sum(1 for conn in connections if conn.is_established())
        
        self.console.print(f"\n📊 Summary: {total} connections ({established} established), {foreign} foreign, {total-foreign} domestic")
        
        # Show location info with detection method
        location_info = self.country_detector.get_location_info()
        self.console.print(f"🏠 Your location: {location_info}")
        
        # Show geo lookup methods being used
        geo_methods = self.geoip.get_methods_summary()
        cache_size = len(self.geoip.persistent_cache)
        self.console.print(f"🗺️  Geo sources: {geo_methods} | Cache: {cache_size} entries")
        
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
        
        # Enhanced summary
        total = len(connections)
        foreign = sum(1 for conn in connections if conn.is_foreign(self.local_country))
        established = sum(1 for conn in connections if conn.is_established())
        
        print(f"\n📊 Summary: {total} connections ({established} established), {foreign} foreign, {total-foreign} domestic")
        
        # Show location info with detection method
        location_info = self.country_detector.get_location_info()
        print(f"🏠 Your location: {location_info}")
        
        # Show geo lookup methods being used
        geo_methods = self.geoip.get_methods_summary()
        cache_size = len(self.geoip.persistent_cache)
        print(f"🗺️  Geo sources: {geo_methods} | Cache: {cache_size} entries")
    
    def monitor_continuous(self, refresh_interval: int = 5, filter_listening: bool = True):
        """Monitor connections continuously"""
        try:
            print("🚀 Starting network monitoring...")
            print("Press Ctrl+C to stop\n")
            
            while True:
                try:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("🖥️  Network Connection Monitor")
                    print("=" * 40)
                    
                    connections = self.get_netstat_connections(filter_listening)
                    
                    if connections:
                        self.display_connections_rich(connections)
                    else:
                        print("No active connections found.")
                        if self.local_country:
                            print(f"🏠 Your location: {self.local_country}")
                    
                    filter_text = " (excluding listening)" if filter_listening else ""
                    print(f"\n⏱️  Refreshing every {refresh_interval}s{filter_text} - Press Ctrl+C to stop")
                    
                    time.sleep(refresh_interval)
                except KeyboardInterrupt:
                    print("\n👋 Monitoring stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error during monitoring iteration: {e}")
                    print(f"⚠ Error occurred, retrying in {refresh_interval}s...")
                    time.sleep(refresh_interval)  # Wait before retrying
        except Exception as e:
            self.logger.error(f"Error in continuous monitoring: {e}")


def setup_logging(debug: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.WARNING
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler only if debug mode
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


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
                       help="Enable debug output to console")
    parser.add_argument("--log-file", help="Save debug logs to file")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.debug, args.log_file)
    
    print("🖥️  Network Connection Monitor")
    print("=" * 40)
    
    try:
        # Initialize GeoIP lookup
        geoip = GeoIPLookup(args.city_db, args.asn_db, use_online=not args.no_online, logger=logger)
        
        # Initialize monitor
        monitor = NetworkMonitor(geoip, args.default_country, logger)
        
        # Override country if specified
        if args.country:
            monitor.country_detector.set_manual_country(args.country)
            monitor.local_country = args.country
            print(f"🌍 Using specified country: {args.country}")
        else:
            monitor.initialize()
        
        filter_listening = not args.show_listening
        
        if args.file:
            # Parse file mode
            print("📁 File parsing mode not implemented yet")
        else:
            # Continuous monitoring mode
            monitor.monitor_continuous(args.interval, filter_listening)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
    finally:
        try:
            geoip.close()
        except:
            pass


if __name__ == "__main__":
    main()
