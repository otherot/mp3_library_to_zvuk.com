# MP3 Library to Zvuk.com Comparator

Compare your local MP3 library with your collection on zvuk.com music streaming service. Optionally search for missing tracks on torrent trackers.

## Features

### Core Features
- 📁 Scan local MP3 library with metadata extraction (ID3 tags)
- 🎵 Fetch your collection from zvuk.com via GraphQL API
- 🔍 Compare libraries and find differences
- 📊 Export results to CSV files
- 💻 Console output with summary and detailed view

### Torrent Search (v0.2.0+)
- 🔎 Search for missing tracks on torrent trackers
- 🌐 Multiple sources: RuTracker, 1337x, nnmclub
- 🧲 Generate magnet links
- ⬇️ Auto-download via qBittorrent Web API

## Installation

### Requirements

- Python 3.10 or higher
- qBittorrent with Web UI enabled (optional, for auto-download)

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Library Comparison

```bash
python main.py compare --token YOUR_TOKEN --library-path /path/to/your/mp3/library
```

### Search for Missing Tracks

```bash
python main.py search-missing -t YOUR_TOKEN -l /path/to/library -o output
```

### Get API Token

**Anonymous token (limited):**
```bash
python -c "from src.zvuk_api import ZvukAPIClient; print(ZvukAPIClient.get_anonymous_token())"
```

**Personal token (recommended):**
1. Log in to https://zvuk.com
2. Open browser DevTools (F12)
3. Go to Network tab
4. Visit https://zvuk.com/api/tiny/profile
5. Copy the `token` value from the response

## Commands

### `compare` - Compare libraries

```bash
python main.py compare [OPTIONS]

Options:
  -t, --token TEXT        Zvuk.com API token (required)
  -l, --library-path PATH Path to local MP3 library (required)
  -o, --output PATH       Output directory for CSV files
  --test-connection       Test API connection and exit
  -v, --verbose           Enable verbose output
  -q, --quiet             Suppress console output
```

### `search-missing` - Search torrents for missing tracks

```bash
python main.py search-missing [OPTIONS]

Options:
  -t, --token TEXT                Zvuk.com API token (required)
  -l, --library-path PATH         Path to local MP3 library (required)
  -o, --output PATH               Output directory for search results
  -s, --sources [rutracker|1337x|nnmclub]
                                  Torrent sources to search (default: all)
  --rutracker-login TEXT          RuTracker login (optional)
  --rutracker-password TEXT       RuTracker password (optional)
  --limit INTEGER                 Max results per track (default: 5)
  -v, --verbose                   Enable verbose output
  -q, --quiet                     Suppress console output
```

**Examples:**

```bash
# Search all sources
python main.py search-missing -t TOKEN -l "D:\Music" -o torrent_results

# Search only RuTracker with credentials
python main.py search-missing -t TOKEN -l "D:\Music" -s rutracker \
  --rutracker-login myuser --rutracker-password mypass

# Search 1337x and nnmclub only
python main.py search-missing -t TOKEN -l "D:\Music" -s 1337x -s nnmclub
```

### `add-torrent` - Add torrent to qBittorrent

```bash
python main.py add-torrent [OPTIONS]

Options:
  -m, --magnet TEXT     Magnet link or torrent URL (required)
  -p, --save-path PATH  Download path
  --host TEXT           qBittorrent host (default: localhost)
  --port INTEGER        qBittorrent Web UI port (default: 8080)
  --username TEXT       qBittorrent Web UI username
  --password TEXT       qBittorrent Web UI password
```

**Examples:**

```bash
# Add magnet link
python main.py add-torrent -m "magnet:?xt=urn:btih:..."

# Add with custom save path
python main.py add-torrent -m "magnet:..." -p "D:\Downloads\Music"

# Connect to remote qBittorrent
python main.py add-torrent -m "magnet:..." --host 192.168.1.100 --port 8080 \
  --username admin --password adminadmin
```

## Output

### Comparison Results

Three CSV files are created:
- `comparison_result_only_local.csv` - Tracks only in your local library
- `comparison_result_only_zvuk.csv` - Tracks only in zvuk.com collection
- `comparison_result_match.csv` - Tracks present in both libraries

### Torrent Search Results

- `torrent_search_results.csv` - All search results with magnet links
- `missing_tracks_summary.csv` - Summary of missing tracks with top results
- `missing_tracks_magnets.txt` - Magnet links for manual download

## qBittorrent Setup

To use the auto-download feature:

1. **Enable Web UI in qBittorrent:**
   - Tools → Options → Web UI
   - Check "Enable Web User Interface"
   - Set port (default: 8080)
   - Set username and password

2. **Allow remote connections (if needed):**
   - Check "Allow remote connections"
   - Add your IP to allowed IPs if restricting

3. **Test connection:**
   ```bash
   python main.py add-torrent -m "magnet:?xt=urn:btih:TEST" --host localhost --port 8080
   ```

## Project Structure

```
mp3_library_to_zvuk.com/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── src/
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration management
│   ├── models.py           # Data models (Track, LibraryDiff)
│   ├── local_scanner.py    # Local MP3 library scanner
│   ├── zvuk_api.py         # Zvuk.com GraphQL API client
│   ├── comparator.py       # Library comparison logic
│   ├── exporter.py         # Results exporter (CSV, console)
│   ├── cli.py              # Click CLI commands
│   └── torrent/            # Torrent search module
│       ├── __init__.py
│       ├── models.py       # Torrent search models
│       ├── rutracker_client.py
│       ├── thirteensx_client.py
│       ├── nnmclub_client.py
│       ├── qbittorrent_client.py
│       ├── search_engine.py
│       └── exporter.py
├── tests/
│   └── test_comparator.py  # Unit tests
├── output/                 # Comparison CSV files
└── torrent_output/         # Torrent search results
```

## API Reference

Based on [sberzvuk-api](https://github.com/Aiving/sberzvuk-api)

The application uses zvuk.com's GraphQL API at `https://zvuk.com/api/v1/graphql`

## Torrent Sources

| Source | Auth Required | Notes |
|--------|---------------|-------|
| RuTracker | Optional | Best for Russian content, requires account for full access |
| 1337x | No | International tracker, good for English content |
| nnmclub | No | Russian tracker, mirror of RuTracker |

## Troubleshooting

### "Configuration error: Path does not exist"

Check that `--library-path` points to an existing directory.

### API connection fails

- Verify your token is valid
- Check internet connection
- Try getting a new token

### qBittorrent connection fails

- Ensure Web UI is enabled
- Check host/port settings
- Verify username/password
- Check firewall settings

### Torrent search returns no results

- Try different sources with `-s` option
- Increase limit with `--limit`
- Some tracks may not be available on torrent trackers

## Legal Notice

⚠️ **Important:** Downloading copyrighted material may be illegal in your jurisdiction. This tool is provided for educational purposes only. Use responsibly and in compliance with applicable laws.

## Testing

Run unit tests:
```bash
python -m pytest tests/ -v
```

## Version

0.2.0 (current)

### Changelog

**v0.2.0**
- Added torrent search functionality
- Support for RuTracker, 1337x, nnmclub
- qBittorrent integration for auto-download
- Export magnet links to file

**v0.1.0**
- Initial release
- Library comparison with zvuk.com
- CSV export

## License

MIT License
