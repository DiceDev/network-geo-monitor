#!/usr/bin/env python3
"""
Demo showing cross-platform capabilities and auto-country detection
"""

import platform
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
    
    def is_foreign(self, local_country: str) -> bool:
        return self.country not in [local_country, '', 'Local Network'] and self.country is not None

def simulate_country_detection():
    """Simulate auto-country detection"""
    print("🌍 Auto-Country Detection Demo")
    print("=" * 35)
    
    # Simulate different scenarios
    scenarios = [
        ("United States", "192.168.1.100", "American user"),
        ("Germany", "192.168.1.100", "German user"),
        ("Japan", "192.168.1.100", "Japanese user"),
        ("Canada", "192.168.1.100", "Canadian user"),
        ("Australia", "192.168.1.100", "Australian user")
    ]
    
    for country, local_ip, description in scenarios:
        print(f"\n📍 Scenario: {description}")
        print(f"   Detected country: {country}")
        print(f"   Local IP: {local_ip}")
        
        # Show how connections would be classified
        sample_connections = [
            ("Google", "142.250.191.14", "United States", "Google LLC"),
            ("GitHub", "140.82.112.4", "United States", "GitHub Inc"),
            ("Baidu", "220.181.38.148", "China", "Beijing Baidu Netcom"),
            ("Yandex", "87.250.250.242", "Russia", "Yandex LLC"),
            ("Local Router", "192.168.1.1", "Local Network", "Private")
        ]
        
        for name, ip, conn_country, org in sample_connections:
            is_foreign = conn_country not in [country, 'Local Network']
            status = "🔴 FOREIGN" if is_foreign else "⚪ LOCAL"
            print(f"   {status} {name} ({ip}) - {conn_country}")

def simulate_os_detection():
    """Simulate OS detection and netstat differences"""
    print(f"\n🖥️  Operating System Detection")
    print("=" * 35)
    
    current_os = platform.system()
    print(f"Current OS: {current_os}")
    
    os_info = {
        "Windows": {
            "command": "netstat -ano -p tcp",
            "format": "Proto Local-Address Foreign-Address State PID",
            "example": "TCP 192.168.1.100:52341 142.250.191.14:443 ESTABLISHED 1234"
        },
        "Linux": {
            "command": "netstat -ant",
            "format": "Proto Recv-Q Send-Q Local-Address Foreign-Address State",
            "example": "tcp 0 0 192.168.1.100:52341 142.250.191.14:443 ESTABLISHED"
        },
        "Darwin": {
            "command": "netstat -an -p tcp",
            "format": "Proto Recv-Q Send-Q Local-Address Foreign-Address State",
            "example": "tcp4 0 0 192.168.1.100.52341 142.250.191.14.443 ESTABLISHED"
        }
    }
    
    for os_name, info in os_info.items():
        print(f"\n🔧 {os_name}:")
        print(f"   Command: {info['command']}")
        print(f"   Format:  {info['format']}")
        print(f"   Example: {info['example']}")

def demo_foreign_detection():
    """Demo showing foreign connection detection with different home countries"""
    print(f"\n🌐 Foreign Connection Detection Demo")
    print("=" * 40)
    
    # Sample connections
    connections = [
        MockConnection("TCP", "192.168.1.100:52341", "142.250.191.14:443", "ESTABLISHED", "1234",
                      "Mountain View", "United States", "Google LLC"),
        MockConnection("TCP", "192.168.1.100:52342", "46.4.84.25:443", "ESTABLISHED", "5678",
                      "Frankfurt", "Germany", "Hetzner Online GmbH"),
        MockConnection("TCP", "192.168.1.100:52343", "13.225.78.64:443", "ESTABLISHED", "9012",
                      "Tokyo", "Japan", "Amazon CloudFront"),
        MockConnection("TCP", "192.168.1.100:52344", "185.70.41.130:443", "ESTABLISHED", "3456",
                      "Amsterdam", "Netherlands", "DigitalOcean LLC"),
        MockConnection("TCP", "192.168.1.100:52345", "192.168.1.1:80", "ESTABLISHED", "7890",
                      "Local", "Local Network", "Private")
    ]
    
    # Test with different home countries
    test_countries = ["United States", "Germany", "Japan"]
    
    for home_country in test_countries:
        print(f"\n🏠 If you're in: {home_country}")
        print(f"{'Connection':<20} {'Country':<15} {'Status':<10}")
        print("-" * 45)
        
        for conn in connections:
            status = "🔴 Foreign" if conn.is_foreign(home_country) else "⚪ Local"
            service = conn.asn.split()[0] if conn.asn else "Unknown"
            print(f"{service:<20} {conn.country:<15} {status}")

def main():
    print("🚀 Cross-Platform Network Monitor Demo")
    print("=" * 45)
    
    simulate_country_detection()
    simulate_os_detection()
    demo_foreign_detection()
    
    print(f"\n✨ Key Improvements:")
    print(f"   ✓ Auto-detects your actual country")
    print(f"   ✓ Works on Windows, Linux, and macOS")
    print(f"   ✓ Handles different netstat output formats")
    print(f"   ✓ Properly classifies foreign vs domestic connections")
    print(f"   ✓ Supports IPv4 and IPv6 addresses")
    print(f"   ✓ Falls back gracefully when tools aren't available")

if __name__ == "__main__":
    main()
