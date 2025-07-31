#!/usr/bin/env python3
"""
Setup script for Network Monitor
Automatically installs dependencies and downloads GeoIP databases
"""

import subprocess
import sys
import os
import urllib.request
import gzip
import shutil
from pathlib import Path

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def download_file(url, filename):
    """Download a file with progress indication"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

def extract_gzip(gz_file, output_file):
    """Extract a gzip file"""
    try:
        with gzip.open(gz_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(gz_file)  # Clean up the gz file
        return True
    except Exception as e:
        print(f"Error extracting {gz_file}: {e}")
        return False

def main():
    print("🚀 Setting up Network Monitor...")
    print("=" * 50)
    
    # Install required packages
    packages = [
        "geoip2",
        "rich", 
        "requests"
    ]
    
    print("📦 Installing Python packages...")
    failed_packages = []
    
    for package in packages:
        print(f"  Installing {package}...", end=" ")
        if install_package(package):
            print("✓")
        else:
            print("✗")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠ Failed to install: {', '.join(failed_packages)}")
        print("The script will still work with reduced functionality.")
    
    # Download GeoIP databases (optional)
    print("\n🌍 Setting up GeoIP databases...")
    print("Note: This requires a MaxMind account for the latest databases.")
    print("Using alternative lightweight geo lookup for now.")
    
    # Create a simple IP ranges file for basic geo lookup
    basic_ranges = """# Basic IP range classifications
# Format: start_ip,end_ip,country,description
8.8.8.8,8.8.8.8,United States,Google DNS
8.8.4.4,8.8.4.4,United States,Google DNS
1.1.1.1,1.1.1.1,United States,Cloudflare DNS
1.0.0.1,1.0.0.1,United States,Cloudflare DNS
"""
    
    with open("basic_geo.txt", "w") as f:
        f.write(basic_ranges)
    
    print("✓ Created basic geo lookup file")
    
    # Create a simple launcher script
    launcher_script = '''@echo off
echo Starting Network Monitor...
python network_monitor.py %*
pause
'''
    
    with open("run_monitor.bat", "w") as f:
        f.write(launcher_script)
    
    print("✓ Created Windows launcher script (run_monitor.bat)")
    
    print("\n🎉 Setup complete!")
    print("\nTo run the network monitor:")
    print("  Windows: Double-click run_monitor.bat")
    print("  Command line: python network_monitor.py")
    print("\nFor full GeoIP functionality:")
    print("  1. Sign up at https://www.maxmind.com/en/geolite2/signup")
    print("  2. Download GeoLite2-City.mmdb and GeoLite2-ASN.mmdb")
    print("  3. Place them in this directory")

if __name__ == "__main__":
    main()
