#!/usr/bin/env python3
"""
Test GeoIP2 local database functionality
"""

import sys
from pathlib import Path

def test_geoip2_import():
    """Test if geoip2 module is available"""
    try:
        import geoip2.database
        import geoip2.errors
        print("✓ geoip2 module available")
        return True
    except ImportError:
        print("✗ geoip2 module not available")
        print("Install with: pip install geoip2")
        return False

def test_database_files():
    """Test if database files exist"""
    city_db = Path("GeoLite2-City.mmdb")
    asn_db = Path("GeoLite2-ASN.mmdb")
    
    print(f"\nChecking database files:")
    
    city_exists = city_db.exists()
    asn_exists = asn_db.exists()
    
    if city_exists:
        size = city_db.stat().st_size
        print(f"✓ {city_db} ({size:,} bytes)")
    else:
        print(f"✗ {city_db} not found")
    
    if asn_exists:
        size = asn_db.stat().st_size
        print(f"✓ {asn_db} ({size:,} bytes)")
    else:
        print(f"✗ {asn_db} not found")
    
    return city_exists and asn_exists

def test_database_lookup():
    """Test actual database lookups"""
    try:
        import geoip2.database
        import geoip2.errors
        
        city_db = Path("GeoLite2-City.mmdb")
        asn_db = Path("GeoLite2-ASN.mmdb")
        
        if not (city_db.exists() and asn_db.exists()):
            print("Cannot test lookups - database files missing")
            return False
        
        print(f"\nTesting database lookups:")
        
        # Test IPs
        test_ips = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "142.250.191.14", # Google
            "46.4.84.25"    # Hetzner Germany
        ]
        
        with geoip2.database.Reader(str(city_db)) as city_reader, \
             geoip2.database.Reader(str(asn_db)) as asn_reader:
            
            print(f"{'IP Address':<15} {'City':<15} {'Country':<15} {'ASN/Organization'}")
            print("-" * 70)
            
            for ip in test_ips:
                try:
                    # City lookup
                    city_response = city_reader.city(ip)
                    city = city_response.city.name or ""
                    country = city_response.country.name or ""
                    
                    # ASN lookup
                    asn_response = asn_reader.asn(ip)
                    asn = asn_response.autonomous_system_organization or ""
                    
                    print(f"{ip:<15} {city:<15} {country:<15} {asn}")
                    
                except geoip2.errors.AddressNotFoundError:
                    print(f"{ip:<15} {'Not found':<15} {'Not found':<15} {'Not found'}")
                except Exception as e:
                    print(f"{ip:<15} {'Error':<15} {'Error':<15} {str(e)}")
        
        print("✓ Database lookup test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error testing database lookups: {e}")
        return False

def main():
    """Main test function"""
    print("GeoIP2 Database Test")
    print("=" * 25)
    
    # Test 1: Module import
    if not test_geoip2_import():
        print("\nInstall geoip2 with: pip install geoip2")
        return False
    
    # Test 2: Database files
    if not test_database_files():
        print("\nDatabase files missing. Run: python scripts/download_geolite2.py")
        return False
    
    # Test 3: Database lookups
    if not test_database_lookup():
        return False
    
    print("\n✓ All GeoIP2 tests passed!")
    print("The network monitor should now work with local databases.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
