# MP3 Library to Zvuk.com Comparator

Compare your local MP3 library with your collection on zvuk.com music streaming service.

## Features

- 📁 Scan local MP3 library with metadata extraction (ID3 tags)
- 🎵 Fetch your collection from zvuk.com via GraphQL API
- 🔍 Compare libraries and find differences
- 📊 Export results to CSV files
- 💻 Console output with summary and detailed view

## Installation

### Requirements

- Python 3.10 or higher

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Library Comparison

```bash
python main.py compare --token YOUR_TOKEN --library-path /path/to/your/mp3/library
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

**Examples:**

```bash
# Compare libraries
python main.py compare -t TOKEN -l "D:\Music" -o output

# Test connection first
python main.py compare -t TOKEN -l "D:\Music" --test-connection

# Verbose output
python main.py compare -t TOKEN -l "D:\Music" -v
```

## Output

### Comparison Results

Three CSV files are created in the output directory:

| File | Description |
|------|-------------|
| `comparison_result_only_local.csv` | Tracks only in your local library |
| `comparison_result_only_zvuk.csv` | Tracks only in zvuk.com collection |
| `comparison_result_match.csv` | Tracks present in both libraries |

Each CSV contains the following columns:
- `title` - Track title
- `artist` - Artist name
- `album` - Album name
- `year` - Release year
- `genre` - Genre
- `duration` - Duration in seconds
- `file_path` - Local file path (for local tracks)
- `zvuk_id` - Zvuk.com track ID (for zvuk tracks)

### Console Output

```
============================================================
LIBRARY COMPARISON SUMMARY
============================================================
Only in local library:     150 tracks
Only in zvuk.com:           75 tracks
Match (in both):           500 tracks
============================================================

📁 ONLY IN LOCAL LIBRARY:
----------------------------------------
  • Artist Name - Track Title
  • ...

🎵 ONLY IN ZVUK.COM:
----------------------------------------
  • Artist Name - Track Title
  • ...

✅ MATCH (IN BOTH):
----------------------------------------
  • Artist Name - Track Title
  • ...

============================================================
CSV files saved to: C:\path\to\output
============================================================
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
│   └── cli.py              # Click CLI commands
├── tests/
│   └── test_comparator.py  # Unit tests
└── output/                 # Generated CSV files
```

## API Reference

Based on [sberzvuk-api](https://github.com/Aiving/sberzvuk-api)

The application uses zvuk.com's GraphQL API at `https://zvuk.com/api/v1/graphql`

## Troubleshooting

### "Configuration error: Path does not exist"

Check that `--library-path` points to an existing directory.

### API connection fails

- Verify your token is valid
- Check internet connection
- Try getting a new token

### CSV files are empty

- Check that your local library contains MP3 files
- Verify the library path is correct
- Run with `-v` flag for detailed logging

## Testing

Run unit tests:
```bash
python -m pytest tests/ -v
```

## Version

0.2.0 (current)

### Changelog

**v0.2.0**
- Improved CSV export with UTF-8 BOM encoding
- Semicolon delimiter for better Excel compatibility
- Bug fixes and stability improvements

**v0.1.0**
- Initial release
- Library comparison with zvuk.com
- CSV export

## License

MIT License
