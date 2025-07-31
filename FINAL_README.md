# Network Monitor - Enhanced Python Script

A comprehensive network connection monitoring tool with geographic IP lookup, cross-platform support, and real-time display.

## 🌟 Features

- **🌍 Auto-Country Detection**: Automatically detects your location for accurate foreign/domestic classification
- **🗺️ Multiple Geo Lookup Methods**: 
  - Built-in database (no setup required)
  - Online APIs (ip-api.com, ipinfo.io)
  - MaxMind GeoLite2 support (optional)
- **🖥️ Cross-Platform**: Works on Windows, Linux, and macOS
- **🔴 Visual Highlighting**: Red for foreign connections, white for domestic
- **🧹 Smart Filtering**: Filters out uninteresting connections automatically
- **📊 Rich Display**: Color-coded terminal output with proper formatting
- **⚡ Real-Time**: Live monitoring with configurable refresh intervals

## 🚀 Quick Start

### Windows (Easiest)
\`\`\`cmd
run_monitor.bat
\`\`\`

### Command Line
\`\`\`bash
python scripts/network_monitor.py
\`\`\`

## 📋 Requirements

- **Python 3.7+**
- **Optional**: `pip install requests rich geoip2` (for enhanced features)

The script works with minimal dependencies and will automatically fall back to simpler methods if optional packages aren't available.

## 🔧 Usage Examples

### Basic Monitoring
\`\`\`bash
python scripts/network_monitor.py
\`\`\`

### Custom Options
\`\`\`bash
# Override country detection
python scripts/network_monitor.py --country "Germany"

# Include listening connections
python scripts/network_monitor.py --show-listening

# Disable online lookups (offline mode)
python scripts/network_monitor.py --no-online

# Custom refresh interval
python scripts/network_monitor.py --interval 10
\`\`\`

## 🧪 Testing

### Test All Features
\`\`\`bash
python scripts/test_all_geo.py
\`\`\`

### Test Basic Functionality
\`\`\`bash
python scripts/test_basic.py
\`\`\`

### Test Simple Database
\`\`\`bash
python scripts/simple_geo_db.py
\`\`\`

## 🗺️ Geo Lookup Methods

The script uses multiple fallback methods for IP geolocation:

1. **MaxMind GeoLite2** (most accurate, requires download)
2. **Simple Built-in Database** (covers major services, no setup)
3. **Online APIs** (comprehensive coverage, requires internet)
4. **Basic Classification** (minimal fallback)

## 📊 Sample Output

\`\`\`
Cross-Platform Network Monitor
========================================
✓ Using simple built-in geo database
✓ Online geo lookup available
Auto-detecting your location...
Detected location: United States (IP: 203.0.113.1)

Proto Local Address          Remote Address       State        PID    City         Country      Organization
──────────────────────────────────────────────────────────────────────────────────────────────────────────
[D] TCP  192.168.1.100:52341  142.250.191.14:443   ESTABLISHED  1234  Mountain View United States Google LLC
[F] TCP  192.168.1.100:52342  46.4.84.25:443       ESTABLISHED  5678  Falkenstein  Germany      Hetzner Online GmbH

Summary: 25 connections (18 established), 7 foreign, 18 domestic
Your location: United States
\`\`\`

## 🔧 Advanced Configuration

### MaxMind GeoLite2 Setup (Optional)
For the most accurate results:

1. Sign up at [MaxMind](https://www.maxmind.com/en/geolite2/signup) (free)
2. Download GeoLite2-City.mmdb and GeoLite2-ASN.mmdb
3. Place them in the script directory
4. Run: `python scripts/download_geolite2.py` for guidance

### Custom Database Paths
\`\`\`bash
python scripts/network_monitor.py --city-db /path/to/city.mmdb --asn-db /path/to/asn.mmdb
\`\`\`

## 🛠️ Troubleshooting

### "No connections shown"
- Try: `python scripts/network_monitor.py --show-listening`
- Run as Administrator (Windows) or with sudo (Linux/Mac)

### "Limited geo lookup available"
- Install requests: `pip install requests`
- Or download MaxMind databases

### "Could not auto-detect location"
- Check internet connection
- Use: `python scripts/network_monitor.py --country "Your Country"`

## 📁 Project Structure

\`\`\`
network-monitor/
├── scripts/
│   ├── network_monitor.py      # Main script
│   ├── simple_geo_db.py        # Built-in geo database
│   ├── test_all_geo.py         # Comprehensive tests
│   ├── test_basic.py           # Basic functionality test
│   └── download_geolite2.py    # MaxMind setup guide
├── run_monitor.bat             # Windows launcher
├── run_monitor.sh              # Unix launcher
├── requirements.txt            # Python dependencies
└── README.md                   # This file
\`\`\`

## 🎯 Key Improvements Over Original

- ✅ **No mandatory setup** - works immediately
- ✅ **Multiple geo lookup fallbacks** - always shows useful data
- ✅ **Cross-platform compatibility** - Windows, Linux, macOS
- ✅ **Auto-country detection** - no manual configuration needed
- ✅ **Better error handling** - graceful fallbacks
- ✅ **Enhanced filtering** - cleaner output
- ✅ **Rich terminal display** - colors and proper formatting
- ✅ **Comprehensive testing** - verify everything works

## 📝 License

This project is open source and available under the MIT License.
