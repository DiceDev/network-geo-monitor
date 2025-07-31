# Network Monitor Usage Guide

## 🚀 Quick Start

### Windows (Easiest)
\`\`\`cmd
run_monitor.bat
\`\`\`

### Command Line
\`\`\`bash
# Basic monitoring (filters listening connections by default)
python network_monitor.py

# Include listening connections
python network_monitor.py --show-listening

# Set default country if auto-detection fails
python network_monitor.py --default-country "Germany"

# Force a specific country (skip auto-detection)
python network_monitor.py --country "Canada"

# Disable online geo lookup (use only local databases)
python network_monitor.py --no-online
\`\`\`

## 🔧 Fixed Issues

### ✅ Location Detection
- **Multiple fallback services** for getting your public IP
- **Better error handling** with timeout and retry logic
- **Default country option** (defaults to United States)
- **Manual override** with `--country` option

### ✅ Display Issues
- **Proper column sizing** to prevent screen cutoff
- **Text truncation** for long addresses and names
- **Better geo data** with improved online lookup
- **Cleaner formatting** with consistent spacing

### ✅ Connection Filtering
- **Filters listening connections by default** (use `--show-listening` to include)
- **Shows only active/established connections**
- **Better connection state detection**

### ✅ Geo Lookup Improvements
- **Enhanced online API usage** with better error handling
- **Improved fallback logic** for when databases aren't available
- **Better classification** of private vs public IPs
- **More accurate ASN information**

## 🛠️ Network Tool Support

### Automatic Tool Detection
The monitor automatically detects and uses available network tools:

**Windows:**
- Uses `netstat -ano` (built-in)

**Linux/Unix:**
- **Primary:** `netstat -ant` / `netstat -anu`
- **Backup:** `ss -ant` / `ss -anu` (if netstat unavailable)
- **Enhanced:** `ss -antp` / `ss -anup` (with process info if root)

**macOS:**
- Uses `netstat -an -p tcp` / `netstat -an -p udp`

### Tool Availability
- ✅ **netstat**: Available on most systems by default
- ✅ **ss**: Modern replacement, common on newer Linux distributions
- 🔄 **Automatic fallback**: If netstat fails, automatically tries ss
- ⚡ **Process info**: Shows PID when available (may require elevated privileges)

### Troubleshooting Network Tools
If you see "No network tools available":

**Install netstat:**
\`\`\`bash
# Ubuntu/Debian
sudo apt install net-tools

# CentOS/RHEL/Fedora
sudo yum install net-tools
# or
sudo dnf install net-tools

# Alpine Linux
sudo apk add net-tools
\`\`\`

**ss is usually pre-installed on modern Linux, but if needed:**
\`\`\`bash
# Ubuntu/Debian
sudo apt install iproute2

# CentOS/RHEL/Fedora
sudo yum install iproute
# or  
sudo dnf install iproute
\`\`\`

## 📊 Display Format

\`\`\`
Proto Local              Remote             State      PID    City         Country      Organization
---------------------------------------------------------------------------------------------------------
⚪ TCP  192.168.1.100:5234 142.250.191.14:443 ESTABLISHED 1234  Mountain View United States Google LLC
🔴 TCP  192.168.1.100:5235 46.4.84.25:443     ESTABLISHED 5678  Frankfurt    Germany      Hetzner Online GmbH
\`\`\`

- 🔴 **Red** = Foreign connections (different country than yours)
- ⚪ **White** = Domestic connections (same country or local network)

## 🌍 Location Detection Process

1. **Get Public IP**: Tries multiple services (ipify.org, ipinfo.io, etc.)
2. **Geo Lookup**: Uses GeoIP databases or online APIs
3. **Fallback**: Uses default country if detection fails
4. **Manual Override**: Can be overridden with `--country` option

## 🔍 Connection Types Shown

By default, shows only:
- ✅ **ESTABLISHED** connections
- ✅ **CLOSE_WAIT** connections  
- ✅ **TIME_WAIT** connections

Filters out:
- ❌ **LISTENING** connections (use `--show-listening` to include)

## 📁 File Analysis

\`\`\`bash
# Save netstat output to file
netstat -ano > connections.txt

# Analyze the file
python network_monitor.py connections.txt
\`\`\`

## 🔧 Troubleshooting

### "Could not auto-detect location"
- Check internet connection
- Try: `python network_monitor.py --default-country "Your Country"`
- Or force: `python network_monitor.py --country "Your Country"`

### "Limited geo lookup available"
- Install requests: `pip install requests`
- Or download GeoLite2 databases from MaxMind

### Display cut off
- The new version uses proper column sizing
- Try maximizing your terminal window
- Use `--export results.json` to save full data

### No connections shown
- Try: `python network_monitor.py --show-listening`
- Make sure you have active network connections
- Run as Administrator if needed
