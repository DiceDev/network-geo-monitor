#!/usr/bin/env python3
"""
Test script to verify geo lookup functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from network_monitor import GeoIPLookup

def test_geo_lookup():
    """Test geo lookup with known IPs"""
    print("🧪 Testing Geo Lookup Functionality")
    print("=" * 40)
    
    # Initialize geo lookup
    geoip = GeoIPLookup()
    
    # Test IPs with known locations
    test_ips = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("142.250.191.14", "Google (likely)"),
        ("46.4.84.25", "Hetzner (Germany)"),
        ("13.225.78.64", "Amazon CloudFront"),
        ("185.70.41.130", "DigitalOcean"),
        ("192.168.1.1", "Private IP"),
        ("127.0.0.1", "Loopback"),
    ]
    
    print(f"{'IP Address':<15} {'City':<15} {'Country':<15} {'ASN/Organization'}")
    print("-" * 70)
    
    for ip, description in test_ips:
        city, country, asn = geoip.lookup(ip)
        print(f"{ip:<15} {city:<15} {country:<15} {asn}")
    
    geoip.close()
    
    print(f"\n💡 If you see 'Unknown' or 'Public IP' for most entries:")
    print(f"   • Install requests: pip install requests")
    print(f"   • Or download GeoLite2 databases from MaxMind")

if __name__ == "__main__":
    test_geo_lookup()
