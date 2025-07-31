# Quick Start Guide

## 🚀 Super Easy Setup (Windows)

1. **Download** all files to a folder
2. **Double-click** `run_monitor.bat`
3. **Done!** The script will automatically:
   - Check for Python
   - Install required packages
   - Start monitoring your network connections

## 🐧 Linux/Mac Setup

1. **Download** all files to a folder
2. **Make executable**: `chmod +x run_monitor.sh`
3. **Run**: `./run_monitor.sh`

## 📋 What You Need

- **Python 3.7+** (Download from [python.org](https://python.org))
- **Internet connection** (for automatic setup)
- **Windows/Linux/Mac** (uses netstat command)

## 🎯 Features

- ✅ **Zero configuration** - works out of the box
- ✅ **Multiple network tools** - netstat, ss (automatic detection)
- ✅ **Cross-platform support** - Windows, Linux, macOS
- ✅ **Multiple geo lookup methods** - local databases, online APIs, basic classification
- ✅ **Automatic fallbacks** - if one method fails, tries another
- ✅ **Color coding** - red for foreign connections, white for domestic
- ✅ **Live updates** - refreshes every 5 seconds
- ✅ **Export to JSON** - save results for analysis

## 🔧 Advanced Usage

\`\`\`bash
# Monitor with custom interval
python scripts/network_monitor.py --interval 10

# Parse a saved netstat file
python scripts/network_monitor.py netstat_output.txt

# Export results to JSON
python scripts/network_monitor.py --export results.json

# Use only offline mode (no online lookups)
python scripts/network_monitor.py --no-online
\`\`\`

## 🌍 Enhanced GeoIP (Optional)

For the most accurate results:

1. **Sign up** at [MaxMind](https://www.maxmind.com/en/geolite2/signup) (free)
2. **Download** GeoLite2-City.mmdb and GeoLite2-ASN.mmdb
3. **Place** them in the same folder as the script
4. **Restart** the monitor

## 🆘 Troubleshooting

**"Python not found"**
- Install Python from [python.org](https://python.org)
- Make sure to check "Add to PATH" during installation

**"Permission denied"**
- Run as Administrator (Windows) or with sudo (Linux/Mac)

**"No connections shown"**
- Make sure you have active network connections
- Try running `netstat -ano` manually to test

## 📞 Need Help?

The script includes multiple fallback methods and should work even with minimal setup. If you encounter issues, the error messages will guide you to the solution.
