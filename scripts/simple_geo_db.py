#!/usr/bin/env python3
"""
Simple IP geolocation database that doesn't require registration
Uses publicly available IP range data
"""

import json
import ipaddress
from typing import Dict, List, Tuple, Optional

class SimpleGeoDatabase:
    """Simple IP geolocation database using public IP range data"""
    
    def __init__(self):
        self.ip_ranges = []
        self.asn_data = {}
        self._load_data()
    
    def _load_data(self):
        """Load IP range and ASN data"""
        # Major cloud providers and well-known services
        self.ip_ranges = [
            # Google
            {"start": "8.8.8.0", "end": "8.8.8.255", "country": "United States", "city": "Mountain View", "org": "Google LLC"},
            {"start": "8.8.4.0", "end": "8.8.4.255", "country": "United States", "city": "Mountain View", "org": "Google LLC"},
            {"start": "142.250.0.0", "end": "142.251.255.255", "country": "United States", "city": "Mountain View", "org": "Google LLC"},
            {"start": "172.217.0.0", "end": "172.217.255.255", "country": "United States", "city": "Mountain View", "org": "Google LLC"},
            {"start": "216.58.192.0", "end": "216.58.223.255", "country": "United States", "city": "Mountain View", "org": "Google LLC"},
            
            # Cloudflare
            {"start": "1.1.1.0", "end": "1.1.1.255", "country": "United States", "city": "San Francisco", "org": "Cloudflare Inc"},
            {"start": "1.0.0.0", "end": "1.0.0.255", "country": "United States", "city": "San Francisco", "org": "Cloudflare Inc"},
            {"start": "104.16.0.0", "end": "104.31.255.255", "country": "United States", "city": "San Francisco", "org": "Cloudflare Inc"},
            
            # Amazon AWS
            {"start": "52.0.0.0", "end": "52.255.255.255", "country": "United States", "city": "Seattle", "org": "Amazon.com Inc"},
            {"start": "54.0.0.0", "end": "54.255.255.255", "country": "United States", "city": "Seattle", "org": "Amazon.com Inc"},
            {"start": "13.32.0.0", "end": "13.35.255.255", "country": "United States", "city": "Seattle", "org": "Amazon CloudFront"},
            
            # Microsoft
            {"start": "13.64.0.0", "end": "13.107.255.255", "country": "United States", "city": "Redmond", "org": "Microsoft Corporation"},
            {"start": "20.0.0.0", "end": "20.255.255.255", "country": "United States", "city": "Redmond", "org": "Microsoft Corporation"},
            {"start": "40.0.0.0", "end": "40.255.255.255", "country": "United States", "city": "Redmond", "org": "Microsoft Corporation"},
            
            # Facebook/Meta
            {"start": "31.13.24.0", "end": "31.13.127.255", "country": "United States", "city": "Menlo Park", "org": "Meta Platforms Inc"},
            {"start": "157.240.0.0", "end": "157.240.255.255", "country": "United States", "city": "Menlo Park", "org": "Meta Platforms Inc"},
            {"start": "173.252.64.0", "end": "173.252.127.255", "country": "United States", "city": "Menlo Park", "org": "Meta Platforms Inc"},
            
            # GitHub
            {"start": "140.82.112.0", "end": "140.82.127.255", "country": "United States", "city": "San Francisco", "org": "GitHub Inc"},
            {"start": "185.199.108.0", "end": "185.199.111.255", "country": "United States", "city": "San Francisco", "org": "GitHub Inc"},
            
            # Hetzner (Germany)
            {"start": "46.4.0.0", "end": "46.4.255.255", "country": "Germany", "city": "Falkenstein", "org": "Hetzner Online GmbH"},
            {"start": "78.46.0.0", "end": "78.47.255.255", "country": "Germany", "city": "Falkenstein", "org": "Hetzner Online GmbH"},
            {"start": "88.99.0.0", "end": "88.99.255.255", "country": "Germany", "city": "Falkenstein", "org": "Hetzner Online GmbH"},
            
            # DigitalOcean
            {"start": "104.131.0.0", "end": "104.131.255.255", "country": "United States", "city": "New York", "org": "DigitalOcean LLC"},
            {"start": "159.89.0.0", "end": "159.89.255.255", "country": "United States", "city": "New York", "org": "DigitalOcean LLC"},
            {"start": "185.70.40.0", "end": "185.70.43.255", "country": "Netherlands", "city": "Amsterdam", "org": "DigitalOcean LLC"},
            
            # OVH
            {"start": "51.68.0.0", "end": "51.68.255.255", "country": "France", "city": "Roubaix", "org": "OVH SAS"},
            {"start": "54.36.0.0", "end": "54.39.255.255", "country": "France", "city": "Roubaix", "org": "OVH SAS"},
            
            # Linode
            {"start": "45.33.0.0", "end": "45.33.255.255", "country": "United States", "city": "Fremont", "org": "Linode LLC"},
            {"start": "50.116.0.0", "end": "50.116.255.255", "country": "United States", "city": "Fremont", "org": "Linode LLC"},
            
            # Common DNS servers
            {"start": "208.67.222.0", "end": "208.67.222.255", "country": "United States", "city": "San Francisco", "org": "OpenDNS"},
            {"start": "208.67.220.0", "end": "208.67.220.255", "country": "United States", "city": "San Francisco", "org": "OpenDNS"},
            {"start": "9.9.9.0", "end": "9.9.9.255", "country": "United States", "city": "Berkeley", "org": "Quad9 DNS"},
            {"start": "149.112.112.0", "end": "149.112.112.255", "country": "United States", "city": "Berkeley", "org": "Quad9 DNS"},
        ]
        
        # Convert string IPs to integers for faster comparison
        for range_data in self.ip_ranges:
            range_data['start_int'] = int(ipaddress.IPv4Address(range_data['start']))
            range_data['end_int'] = int(ipaddress.IPv4Address(range_data['end']))
    
    def lookup(self, ip_address: str) -> Tuple[str, str, str]:
        """Lookup IP address in simple database"""
        try:
            ip_int = int(ipaddress.IPv4Address(ip_address))
            
            for range_data in self.ip_ranges:
                if range_data['start_int'] <= ip_int <= range_data['end_int']:
                    return (
                        range_data.get('city', ''),
                        range_data.get('country', ''),
                        range_data.get('org', '')
                    )
            
            # Not found in our database
            return ("", "Unknown", "")
            
        except (ipaddress.AddressValueError, ValueError):
            return ("", "Unknown", "")

def create_simple_geo_db():
    """Create and return a simple geo database instance"""
    return SimpleGeoDatabase()

def test_simple_db():
    """Test the simple database"""
    db = SimpleGeoDatabase()
    
    test_ips = [
        "8.8.8.8",
        "1.1.1.1", 
        "142.250.191.14",
        "46.4.84.25",
        "185.70.41.130",
        "192.168.1.1"  # Should not be found
    ]
    
    print("Testing Simple Geo Database")
    print("=" * 30)
    print(f"{'IP Address':<15} {'City':<15} {'Country':<15} {'Organization'}")
    print("-" * 70)
    
    for ip in test_ips:
        city, country, org = db.lookup(ip)
        print(f"{ip:<15} {city:<15} {country:<15} {org}")

if __name__ == "__main__":
    test_simple_db()
