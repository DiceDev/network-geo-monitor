#!/usr/bin/env python3
"""
Download GeoLite2 databases from MaxMind
Requires a free MaxMind account and license key
"""

import os
import sys
import urllib.request
import gzip
import tarfile
import shutil
from pathlib import Path

def download_and_extract_geolite2():
    """Guide user through downloading GeoLite2 databases"""
    print("GeoLite2 Database Setup")
    print("=" * 30)
    print()
    print("To use local GeoIP databases, you need to:")
    print("1. Sign up for a free MaxMind account at: https://www.maxmind.com/en/geolite2/signup")
    print("2. Generate a license key in your account")
    print("3. Download the databases manually")
    print()
    print("Required files:")
    print("- GeoLite2-City.mmdb")
    print("- GeoLite2-ASN.mmdb")
    print()
    print("Download URLs (requires login):")
    print("- https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz")
    print("- https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=YOUR_LICENSE_KEY&suffix=tar.gz")
    print()
    
    # Check if files already exist
    city_db = Path("GeoLite2-City.mmdb")
    asn_db = Path("GeoLite2-ASN.mmdb")
    
    if city_db.exists() and asn_db.exists():
        print("✓ Both GeoLite2 databases found!")
        print(f"  - {city_db} ({city_db.stat().st_size} bytes)")
        print(f"  - {asn_db} ({asn_db.stat().st_size} bytes)")
        return True
    
    if city_db.exists():
        print(f"✓ Found: {city_db}")
    else:
        print(f"✗ Missing: {city_db}")
    
    if asn_db.exists():
        print(f"✓ Found: {asn_db}")
    else:
        print(f"✗ Missing: {asn_db}")
    
    print()
    print("Manual setup instructions:")
    print("1. Go to https://www.maxmind.com/en/geolite2/signup")
    print("2. Create a free account")
    print("3. Generate a license key")
    print("4. Download GeoLite2-City and GeoLite2-ASN databases")
    print("5. Extract the .mmdb files to this directory")
    print()
    
    return False

def extract_tar_gz(tar_path, extract_to="."):
    """Extract .tar.gz file and find .mmdb files"""
    print(f"Extracting {tar_path}...")
    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            # Find .mmdb files in the archive
            mmdb_files = [member for member in tar.getmembers() if member.name.endswith('.mmdb')]
            
            for member in mmdb_files:
                # Extract just the filename (remove directory structure)
                filename = os.path.basename(member.name)
                print(f"Extracting {filename}...")
                
                # Extract to current directory with just the filename
                member.name = filename
                tar.extract(member, extract_to)
                
        print(f"✓ Extraction complete")
        return True
    except Exception as e:
        print(f"✗ Error extracting {tar_path}: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        # Extract mode - look for .tar.gz files in current directory
        tar_files = list(Path(".").glob("*.tar.gz"))
        if tar_files:
            print(f"Found {len(tar_files)} .tar.gz files:")
            for tar_file in tar_files:
                print(f"  - {tar_file}")
                extract_tar_gz(tar_file)
        else:
            print("No .tar.gz files found in current directory")
    else:
        # Setup guide mode
        download_and_extract_geolite2()

if __name__ == "__main__":
    main()
