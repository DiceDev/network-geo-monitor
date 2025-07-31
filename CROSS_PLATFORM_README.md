# Cross-Platform Network Monitor

## 🌟 New Features

### 🌍 Auto-Country Detection
- **Automatically detects your location** instead of assuming United States
- Uses your public IP to determine your actual country
- Properly classifies connections as foreign or domestic based on YOUR location
- Fallback methods if auto-detection fails

### 🖥️ Cross-Platform Support
- **Windows**: Uses `netstat -ano -p tcp/udp`
- **Linux**: Uses `netstat -ant/-anu` or `ss -tuln/-uln` as fallback
- **macOS**: Uses `netstat -an -p tcp/udp`
- **Automatic OS detection** and appropriate command selection

## 🚀 Usage Examples

### Basic Usage (Auto-detects everything)
\`\`\`bash
python network_monitor.py
\`\`\`

### Override Country Detection
\`\`\`bash
python network_monitor.py --country "Germany"
\`\`\`

### Export with Location Info
\`\`\`bash
python network_monitor.py --export connections.json
\`\`\`

## 🔍 How It Works

### Country Detection Process
1. **Get Public IP**: Queries multiple services (ipify.org, ipinfo.io, etc.)
2. **Geo Lookup**: Uses GeoIP databases or online APIs to find country
3. **Cache Result**: Remembers your location for the session
4. **Fallback**: If detection fails, asks user or uses "Unknown"

### OS-Specific Handling
- **Windows**: Parses `netstat -ano` output with PID information
- **Unix/Linux**: Parses `netstat -an` or falls back to `ss` command
- **macOS**: Handles Darwin-specific netstat format differences

### Connection Classification
- 🔴 **Foreign**: Connections to countries different from yours
- ⚪ **Local**: Connections to your country or local network
- 🏠 **Private**: Local network connections (192.168.x.x, 10.x.x.x, etc.)

## 📊 Sample Output

\`\`\`
🌍 Auto-detecting your location...
✓ Detected location: Germany (IP: 85.214.132.117)
✓ Detected OS: linux
✓ Using online geo lookup as fallback

Proto  Local Address          Remote Address       State        PID      City            Country              ASN
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
⚪ TCP   192.168.1.100:52341   142.250.191.14:443   ESTABLISHED  1234     Mountain View   United States        Google LLC
🔴 TCP   192.168.1.100:52342   46.4.84.25:443       ESTABLISHED  5678     Frankfurt       Germany              Hetzner Online GmbH
🔴 TCP   192.168.1.100:52343   13.225.78.64:443     ESTABLISHED  9012     Tokyo           Japan                Amazon CloudFront

📊 Summary: 15 total connections, 8 foreign, 7 local/domestic
🏠 Your detected location: Germany
\`\`\`

## 🛠️ Technical Details

### Supported Platforms
- ✅ Windows 10/11
- ✅ Ubuntu/Debian Linux
- ✅ CentOS/RHEL/Fedora
- ✅ macOS (Intel & Apple Silicon)
- ✅ WSL (Windows Subsystem for Linux)

### Network Protocols
- ✅ TCP connections (with state information)
- ✅ UDP connections
- ✅ IPv4 and IPv6 addresses
- ✅ Local and remote connections

### Geo Lookup Methods (in order of preference)
1. **Local GeoLite2 databases** (most accurate, fastest)
2. **Online APIs** (ip-api.com, ipinfo.io - free tier)
3. **Basic classification** (limited but works offline)

## 🔧 Advanced Configuration

### Custom Database Paths
\`\`\`bash
python network_monitor.py --city-db /path/to/GeoLite2-City.mmdb --asn-db /path/to/GeoLite2-ASN.mmdb
\`\`\`

### Different Refresh Intervals
\`\`\`bash
python network_monitor.py --interval 10  # Update every 10 seconds
\`\`\`

### File Analysis Mode
\`\`\`bash
# Save netstat output to file first
netstat -ano > connections.txt

# Then analyze it
python network_monitor.py connections.txt
\`\`\`
