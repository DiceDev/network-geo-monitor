#!/usr/bin/env python3
"""
Test online geo lookup functionality
"""

import sys
import os

# Test if requests is available
try:
    import requests
    print("✓ requests module available")
except ImportError:
    print("✗ requests module not available - installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests
    print("✓ requests module installed")

def test_ip_api(ip):
    """Test ip-api.com lookup"""
    print(f"\nTesting ip-api.com with {ip}...")
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}?fields=city,country,org,as,status", 
            timeout=10
        )
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            if data.get('status') == 'success':
                city = data.get('city', '')
                country = data.get('country', '')
                asn = data.get('as', '') or data.get('org', '')
                print(f"✓ Parsed: {city}, {country}, {asn}")
                return True
            else:
                print(f"✗ API error: {data}")
        else:
            print(f"✗ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    return False

def test_ipinfo(ip):
    """Test ipinfo.io lookup"""
    print(f"\nTesting ipinfo.io with {ip}...")
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            city = data.get('city', '')
            country = data.get('country', '')
            org = data.get('org', '')
            print(f"✓ Parsed: {city}, {country}, {org}")
            return True
        else:
            print(f"✗ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    return False

def main():
    print("Testing Online Geo Lookup")
    print("=" * 30)
    
    # Test with well-known IPs
    test_ips = [
        "8.8.8.8",      # Google DNS
        "1.1.1.1",      # Cloudflare DNS
        "142.250.191.14", # Google
        "46.4.84.25"    # Hetzner Germany
    ]
    
    for ip in test_ips:
        print(f"\n{'='*50}")
        print(f"Testing IP: {ip}")
        
        success1 = test_ip_api(ip)
        success2 = test_ipinfo(ip)
        
        if success1 or success2:
            print(f"✓ At least one service worked for {ip}")
        else:
            print(f"✗ Both services failed for {ip}")
    
    print(f"\n{'='*50}")
    print("Test complete!")

if __name__ == "__main__":
    main()
