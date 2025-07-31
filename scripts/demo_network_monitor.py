#!/usr/bin/env python3
"""
Demo Network Monitor - Shows how the real script would work with mock data
This runs in the online environment to demonstrate functionality
"""

import json
import time
from dataclasses import dataclass
from typing import List

@dataclass
class MockConnection:
    protocol: str
    local_address: str
    foreign_address: str
    state: str
    pid: str
    city: str = ""
    country: str = ""
    asn: str = ""
    
    @property
    def is_foreign(self) -> bool:
        return self.country not in ['United States', ''] and self.country is not None

def create_mock_data() -> List[MockConnection]:
    """Create realistic mock network connection data"""
    mock_connections = [
        MockConnection("TCP", "192.168.1.100:52341", "142.250.191.14:443", "ESTABLISHED", "1234", 
                      "Mountain View", "United States", "Google LLC"),
        MockConnection("TCP", "192.168.1.100:52342", "157.240.22.35:443", "ESTABLISHED", "5678",
                      "Menlo Park", "United States", "Meta Platforms"),
        MockConnection("TCP", "192.168.1.100:52343", "13.107.42.14:443", "ESTABLISHED", "9012",
                      "Redmond", "United States", "Microsoft Corporation"),
        MockConnection("TCP", "192.168.1.100:52344", "185.199.108.153:443", "ESTABLISHED", "3456",
                      "San Francisco", "United States", "GitHub Inc"),
        MockConnection("TCP", "192.168.1.100:52345", "104.16.132.229:443", "ESTABLISHED", "7890",
                      "San Francisco", "United States", "Cloudflare Inc"),
        MockConnection("TCP", "192.168.1.100:52346", "52.84.223.94:443", "ESTABLISHED", "2468",
                      "Seattle", "United States", "Amazon.com Inc"),
        MockConnection("TCP", "192.168.1.100:52347", "151.101.193.140:443", "ESTABLISHED", "1357",
                      "San Francisco", "United States", "Fastly Inc"),
        # Some foreign connections
        MockConnection("TCP", "192.168.1.100:52348", "46.4.84.25:443", "ESTABLISHED", "9876",
                      "Frankfurt", "Germany", "Hetzner Online GmbH"),
        MockConnection("TCP", "192.168.1.100:52349", "185.70.41.130:443", "ESTABLISHED", "5432",
                      "Amsterdam", "Netherlands", "DigitalOcean LLC"),
        MockConnection("TCP", "192.168.1.100:52350", "13.225.78.64:443", "ESTABLISHED", "8765",
                      "Tokyo", "Japan", "Amazon CloudFront"),
        # UDP connections
        MockConnection("UDP", "192.168.1.100:53", "8.8.8.8:53", "", "4321",
                      "", "United States", "Google DNS"),
        MockConnection("UDP", "192.168.1.100:123", "pool.ntp.org:123", "", "6543",
                      "Various", "Global", "NTP Pool"),
    ]
    
    return mock_connections

def display_connections_simple(connections: List[MockConnection]):
    """Display connections in simple text format"""
    print(f"{'Proto':<6} {'Local Address':<22} {'Remote Address':<20} {'State':<12} {'PID':<8} {'City':<15} {'Country':<20} {'ASN':<25}")
    print("-" * 130)
    
    for conn in connections:
        # Color coding simulation (would be colored in real terminal)
        marker = "🔴" if conn.is_foreign else "⚪"
        print(f"{marker} {conn.protocol:<5} {conn.local_address:<22} {conn.foreign_address:<20} "
              f"{conn.state:<12} {conn.pid:<8} {conn.city:<15} {conn.country:<20} {conn.asn:<25}")

def analyze_connections(connections: List[MockConnection]):
    """Analyze the mock connections"""
    total = len(connections)
    foreign = sum(1 for conn in connections if conn.is_foreign)
    domestic = total - foreign
    
    countries = {}
    for conn in connections:
        if conn.country:
            countries[conn.country] = countries.get(conn.country, 0) + 1
    
    print(f"\n📊 Connection Analysis:")
    print(f"   Total connections: {total}")
    print(f"   Domestic (US): {domestic}")
    print(f"   Foreign: {foreign}")
    print(f"\n🌍 Countries connected to:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        print(f"   {country}: {count} connections")

def demo_monitoring():
    """Demonstrate the monitoring functionality"""
    print("🖥️  Network Connection Monitor - DEMO MODE")
    print("=" * 50)
    print("This shows how the script would work on your local computer")
    print("🔴 = Foreign connection, ⚪ = Domestic/Local connection")
    print()
    
    # Show mock data
    connections = create_mock_data()
    display_connections_simple(connections)
    
    # Analysis
    analyze_connections(connections)
    
    print(f"\n💡 On your real computer, this would:")
    print(f"   • Run 'netstat -ano' to get actual connections")
    print(f"   • Look up real IP addresses in GeoIP databases")
    print(f"   • Update every 5 seconds with live data")
    print(f"   • Show colors (red for foreign, white for domestic)")
    print(f"   • Monitor actual processes and their network activity")

def export_demo_data():
    """Show how export functionality works"""
    connections = create_mock_data()
    
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
            "is_foreign": conn.is_foreign
        }
        for conn in connections
    ]
    
    print("\n📄 Export to JSON (sample):")
    print(json.dumps(export_data[:3], indent=2))  # Show first 3 entries
    print("... (and more)")

if __name__ == "__main__":
    demo_monitoring()
    export_demo_data()
