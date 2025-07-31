#!/usr/bin/env python3
"""
Geo Cache Manager - Utility to manage the persistent geo lookup cache
"""

import pickle
import sys
from pathlib import Path
from datetime import datetime, timedelta

def show_cache_stats():
    """Show statistics about the geo cache"""
    script_dir = Path(__file__).parent
    cache_file = script_dir / "geo_cache.pkl"
    
    if not cache_file.exists():
        print("No geo cache file found.")
        return
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
            cache = cache_data.get('cache', {})
            saved_at = cache_data.get('saved_at', 'Unknown')
        
        print("🗺️  Geo Cache Statistics")
        print("=" * 30)
        print(f"Cache file: {cache_file}")
        print(f"Last saved: {saved_at}")
        print(f"Total entries: {len(cache)}")
        
        if cache:
            # Analyze cache contents
            countries = {}
            cities = {}
            orgs = {}
            
            for ip, data in cache.items():
                country = data.get('country', 'Unknown')
                city = data.get('city', 'Unknown')
                org = data.get('asn', 'Unknown')
                
                countries[country] = countries.get(country, 0) + 1
                if city:
                    cities[city] = cities.get(city, 0) + 1
                if org:
                    orgs[org] = orgs.get(org, 0) + 1
            
            print(f"\nTop countries:")
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {country}: {count} IPs")
            
            print(f"\nTop cities:")
            for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]:
                if city and city != 'Unknown':
                    print(f"  {city}: {count} IPs")
            
            print(f"\nTop organizations:")
            for org, count in sorted(orgs.items(), key=lambda x: x[1], reverse=True)[:10]:
                if org and org != 'Unknown':
                    print(f"  {org}: {count} IPs")
        
    except Exception as e:
        print(f"Error reading cache: {e}")

def clean_cache():
    """Clean old entries from the cache"""
    script_dir = Path(__file__).parent
    cache_file = script_dir / "geo_cache.pkl"
    
    if not cache_file.exists():
        print("No geo cache file found.")
        return
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
            cache = cache_data.get('cache', {})
        
        original_count = len(cache)
        cutoff = datetime.now() - timedelta(days=7)
        
        # Remove old entries
        cleaned_cache = {
            ip: data for ip, data in cache.items()
            if data.get('timestamp', datetime.now()) > cutoff
        }
        
        removed_count = original_count - len(cleaned_cache)
        
        if removed_count > 0:
            # Save cleaned cache
            cache_data['cache'] = cleaned_cache
            cache_data['saved_at'] = datetime.now()
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"✓ Cleaned cache: removed {removed_count} old entries")
            print(f"Cache now has {len(cleaned_cache)} entries")
        else:
            print("✓ Cache is already clean (no old entries found)")
        
    except Exception as e:
        print(f"Error cleaning cache: {e}")

def clear_cache():
    """Clear the entire cache"""
    script_dir = Path(__file__).parent
    cache_file = script_dir / "geo_cache.pkl"
    
    if cache_file.exists():
        try:
            cache_file.unlink()
            print("✓ Geo cache cleared")
        except Exception as e:
            print(f"Error clearing cache: {e}")
    else:
        print("No cache file to clear")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Geo Cache Manager")
        print("=" * 20)
        print("Usage:")
        print("  python cache_manager.py stats   - Show cache statistics")
        print("  python cache_manager.py clean   - Remove old entries (>7 days)")
        print("  python cache_manager.py clear   - Clear entire cache")
        return
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_cache_stats()
    elif command == "clean":
        clean_cache()
    elif command == "clear":
        clear_cache()
    else:
        print(f"Unknown command: {command}")
        print("Use: stats, clean, or clear")

if __name__ == "__main__":
    main()
