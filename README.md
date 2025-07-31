# Network Connection Monitor

An enhanced Python script for monitoring network connections on Windows and *Nix with geographical and ASN information lookup.

## Features

- Monitor TCP and UDP connections in real-time
- Geographic location lookup (city, country) for remote IP addresses
- ASN (Autonomous System Number) information
- Color-coded display (red for foreign connections, white for domestic/unknown)
- File parsing mode for analyzing saved netstat output
- JSON export functionality
- Rich terminal UI with live updates
- Configurable refresh intervals

## Installation

1. Install required dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Download GeoLite2 databases from MaxMind:
   - [GeoLite2 City](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
   - [GeoLite2 ASN](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
   
   Place the `.mmdb` files in the same directory as the script.

3. If you don't use MaxMind, the script defaults to a combination of a simple local database and API calls for new IP's which are then cached.

## Usage

The simplest way to start up the monitor and check for dependencies is with either .\run_monitor.bat or ./run_monitor.sh

### Live Monitoring
\`\`\`bash
python network_monitor.py
\`\`\`

### Monitor with custom interval
\`\`\`bash
python network_monitor.py --interval 10
\`\`\`

### Parse a file
\`\`\`bash
python network_monitor.py connections.txt
\`\`\`

### Export to JSON
\`\`\`bash
python network_monitor.py --export results.json
\`\`\`

### Custom database paths
\`\`\`bash
python network_monitor.py --city-db /path/to/city.mmdb --asn-db /path/to/asn.mmdb
\`\`\`

## Command Line Options

- `file`: Optional file to parse instead of live monitoring
- `--city-db`: Path to GeoLite2 City database (default: ./GeoLite2-City.mmdb)
- `--asn-db`: Path to GeoLite2 ASN database (default: ./GeoLite2-ASN.mmdb)
- `--interval`: Refresh interval in seconds (default: 5)
- `--export`: Export results to JSON file

## Requirements

- Python 3.7+
- Windows (uses netstat command)
- GeoLite2 databases from MaxMind

## Dependencies

- `geoip2`: For IP geolocation lookup
- `rich`: For enhanced terminal display (optional, falls back to simple text)
