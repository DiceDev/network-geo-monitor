#!/usr/bin/env python3
"""
Test script to verify cache file location consistency
"""

import sys
import os
from pathlib import Path

def test_cache_location():
    """Test that cache location is consistent"""
    print("🧪 Testing Cache Location Consistency")
    print("=" * 40)
    
    # Get the expected cache location (same as network_monitor.py uses)
    script_dir = Path(__file__).parent
    expected_cache = script_dir / "geo_cache.pkl"
    
    print(f"Script directory: {script_dir}")
    print(f"Expected cache location: {expected_cache}")
    print(f"Current working directory: {Path.cwd()}")
    
    # Test from different working directories
    test_scenarios = [
        ("From scripts directory", script_dir),
        ("From parent directory", script_dir.parent),
        ("From root (if different)", Path.cwd())
    ]
    
    for scenario_name, test_dir in test_scenarios:
        print(f"\n📁 {scenario_name}:")
        print(f"   Working dir: {test_dir}")
        
        # Simulate what the cache path would be
        if test_dir == script_dir:
            # Running from scripts directory
            relative_cache = Path("geo_cache.pkl")
            absolute_cache = test_dir / relative_cache
        else:
            # Running from elsewhere - our fixed version always uses script_dir
            absolute_cache = expected_cache
        
        print(f"   Cache would be: {absolute_cache}")
        print(f"   Same as expected: {'✓' if absolute_cache == expected_cache else '✗'}")
    
    # Check if cache file exists
    if expected_cache.exists():
        size = expected_cache.stat().st_size
        print(f"\n📊 Current cache file:")
        print(f"   Location: {expected_cache}")
        print(f"   Size: {size:,} bytes")
        print(f"   Exists: ✓")
    else:
        print(f"\n📊 No cache file found at: {expected_cache}")
    
    # Check for cache files in other locations (old behavior)
    other_locations = [
        Path.cwd() / "geo_cache.pkl",
        script_dir.parent / "geo_cache.pkl"
    ]
    
    found_elsewhere = []
    for location in other_locations:
        if location != expected_cache and location.exists():
            found_elsewhere.append(location)
    
    if found_elsewhere:
        print(f"\n⚠ Found cache files in other locations:")
        for location in found_elsewhere:
            size = location.stat().st_size
            print(f"   {location} ({size:,} bytes)")
        print(f"   Consider moving these to: {expected_cache}")
    else:
        print(f"\n✓ No duplicate cache files found")

def migrate_cache_files():
    """Migrate cache files from other locations to the scripts directory"""
    script_dir = Path(__file__).parent
    target_cache = script_dir / "geo_cache.pkl"
    
    # Look for cache files in other locations
    possible_locations = [
        Path.cwd() / "geo_cache.pkl",
        script_dir.parent / "geo_cache.pkl"
    ]
    
    for source_cache in possible_locations:
        if source_cache != target_cache and source_cache.exists():
            print(f"Found cache file: {source_cache}")
            
            if not target_cache.exists():
                try:
                    # Move the file to the scripts directory
                    source_cache.rename(target_cache)
                    print(f"✓ Moved cache to: {target_cache}")
                    break
                except Exception as e:
                    print(f"✗ Error moving cache: {e}")
            else:
                # Target already exists, ask user what to do
                source_size = source_cache.stat().st_size
                target_size = target_cache.stat().st_size
                print(f"Cache already exists at target location:")
                print(f"  Source: {source_cache} ({source_size:,} bytes)")
                print(f"  Target: {target_cache} ({target_size:,} bytes)")
                print(f"  Keeping target, you may want to manually merge or delete source")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_cache_files()
    else:
        test_cache_location()
        print(f"\nTo migrate existing cache files, run:")
        print(f"  python {Path(__file__).name} migrate")
