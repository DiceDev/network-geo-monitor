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
    """Handles GeoIP database operations"""
    
    def __init__(self, city_db_path: str = "./GeoLite2-City.mmdb", 
                 asn_db_path: str = "./GeoLite2-ASN.mmdb"):
        self.city_reader = None
        self.asn_reader = None
        
        if not GEOIP_AVAILABLE:
            print("GeoIP2 not available - geographic data will be empty")
            return
            
        try:
            if Path(city_db_path).exists():
                self.city_reader = geoip2.database.Reader(city_db_path)
            else:
                print(f"Warning: City database not found at {city_db_path}")
                
            if Path(asn_db_path).exists():
                self.asn_reader = geoip2.database.Reader(asn_db_path)
            else:
                print(f"Warning: ASN database not found at {asn_db_path}")
                
        except Exception as e:
            print(f"Error initializing GeoIP databases: {e}")
    
    def lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup geographic and ASN information for an IP address"""
        city, country, asn = "", "", ""
        
        if not ip_address or ip_address in ['0.0.0.0', '127.0.0.1', '::1']:
            return city, country, asn
            
        try:
            if self.city_reader:
                response = self.city_reader.city(ip_address)
                city = response.city.name or ""
                country = response.country.name or ""
                
            if self.asn_reader:
                response_asn = self.asn_reader.asn(ip_address)
                asn = response_asn.autonomous_system_organization or ""
                
        except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error):
            pass  # IP not found in database
        except Exception as e:
            print(f"Error looking up {ip_address}: {e}")
            
        return city, country, asn
    
    def close(self):
        """Close database connections"""
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()


class NetworkMonitor:
    """Main network monitoring class"""
    
    def __init__(self, geoip_lookup: GeoIPLookup):
        self.geoip = geoip_lookup
        self.console = Console() if RICH_AVAILABLE else None
    
    def get_netstat_connections(self) -> List[NetworkConnection]:
        """Get network connections using netstat"""
        connections = []
        
        # Get TCP connections
        connections.extend(self._get_connections_by_protocol(ConnectionType.TCP))
        
        # Get UDP connections  
        connections.extend(self._get_connections_by_protocol(ConnectionType.UDP))
        
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
    
    args = parser.parse_args()
    
    # Initialize GeoIP lookup
    geoip = GeoIPLookup(args.city_db, args.asn_db)
    
    # Initialize monitor
    monitor = NetworkMonitor(geoip)
    
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
    except Exception as e:
        print(f"Error: {e}")
    finally:
        geoip.close()


if __name__ == "__main__":
    main()
