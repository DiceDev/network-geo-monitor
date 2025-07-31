#!/usr/bin/env python3
"""
Test geographic lookup functionality
"""

import sys
from pathlib import Path

def test_geo_lookup():
    """Test the geographic lookup with various IP addresses"""
    print("🌍 Testing Geographic Lookup")
    print("=" * 30)
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from network_monitor import GeoIPLookup
        
        # Initialize lookup
        geoip = GeoIPLookup()
        
        # Show available methods
        stats = geoip.get_lookup_stats()
        print(f"Available methods: {', '.join(stats['methods_available'])}")
        print()
        
        # Test various IP addresses
        test_ips = [
            ("8.8.8.8", "Google DNS"),
            ("1.1.1.1", "Cloudflare DNS"),
            ("208.67.222.222", "OpenDNS"),
            ("74.125.224.72", "Google"),
            ("151.101.193.140", "Reddit"),
            ("127.0.0.1", "Localhost"),
            ("192.168.1.1", "Private IP"),
        ]
        
        print("Testing IP addresses:")
        print("-" * 80)
        print(f"{'IP Address':<16} {'Description':<15} {'City':<15} {'Country':<20} {'ASN':<25}")
        print("-" * 80)
        
        for ip, description in test_ips:
            city, country, asn = geoip.lookup(ip)
            print(f"{ip:<16} {description:<15} {city:<15} {country:<20} {asn:<25}")
        
        # Show final statistics
        print("\n📊 Lookup Statistics:")
        final_stats = geoip.get_lookup_stats()
        for key, value in final_stats.items():
            print(f"  {key}: {value}")
        
        geoip.close()
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_requests_availability():
    """Test if requests library is available"""
    print("\n📦 Testing requests library...")
    
    try:
        import requests
        print("✓ requests library is available")
        
        # Test a simple request
        try:
            response = requests.get("http://httpbin.org/ip", timeout=5)
            if response.status_code == 200:
                print("✓ HTTP requests working")
                return True
            else:
                print(f"⚠️  HTTP request returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  HTTP request failed: {e}")
            return False
            
    except ImportError:
        print("❌ requests library not available")
        print("   Install with: pip install requests")
        return False

def main():
    """Main test function"""
    requests_ok = test_requests_availability()
    geo_ok = test_geo_lookup()
    
    print(f"\n🎯 Test Summary")
    print("=" * 15)
    print(f"Requests library: {'✓' if requests_ok else '❌'}")
    print(f"Geographic lookup: {'✓' if geo_ok else '❌'}")
    
    if requests_ok and geo_ok:
        print("\n🎉 Geographic lookup should work!")
    else:
        print("\n⚠️  Some issues found")
        if not requests_ok:
            print("   Install requests: pip install requests")

if __name__ == "__main__":
    main()
