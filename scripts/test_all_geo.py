#!/usr/bin/env python3
"""
Test all geo lookup methods
"""

import sys
import os

def test_simple_geo():
    """Test the simple geo database"""
    print("Testing Simple Geo Database")
    print("=" * 30)
    
    try:
        from simple_geo_db import SimpleGeoDatabase
        db = SimpleGeoDatabase()
        
        test_ips = ["8.8.8.8", "1.1.1.1", "142.250.191.14", "46.4.84.25"]
        
        for ip in test_ips:
            city, country, org = db.lookup(ip)
            print(f"{ip:<15} -> {city}, {country}, {org}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_online_geo():
    """Test online geo lookup"""
    print("\nTesting Online Geo Lookup")
    print("=" * 30)
    
    try:
        import requests
        
        # Test ip-api.com
        ip = "8.8.8.8"
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=city,country,org,as,status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f"✓ ip-api.com works: {data}")
                return True
        
        print("✗ Online lookup failed")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_integrated_lookup():
    """Test the integrated lookup system"""
    print("\nTesting Integrated Lookup System")
    print("=" * 35)
    
    try:
        # Add current directory to path so we can import
        sys.path.insert(0, os.path.dirname(__file__))
        
        from network_monitor import GeoIPLookup
        
        geoip = GeoIPLookup(use_online=True)
        
        test_ips = ["8.8.8.8", "1.1.1.1", "142.250.191.14", "46.4.84.25", "192.168.1.1"]
        
        print(f"{'IP Address':<15} {'City':<15} {'Country':<15} {'Organization'}")
        print("-" * 70)
        
        for ip in test_ips:
            city, country, org = geoip.lookup(ip)
            print(f"{ip:<15} {city:<15} {country:<15} {org}")
        
        geoip.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Comprehensive Geo Lookup Test")
    print("=" * 35)
    
    success = True
    
    # Test 1: Simple database
    if not test_simple_geo():
        success = False
    
    # Test 2: Online lookup
    if not test_online_geo():
        success = False
    
    # Test 3: Integrated system
    if not test_integrated_lookup():
        success = False
    
    if success:
        print("\n✓ All geo lookup tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
