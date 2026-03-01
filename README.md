# McAfee Sync

A Python tool to synchronize HTTP directory structures with local storage. Supports single-threaded, multi-threaded, and async modes for optimal performance.

## Features

- **Multiple Execution Modes**: Single-threaded, multi-threaded, or async/await
- **Connection Pooling**: Reuses HTTP connections for efficiency
- **Streaming Downloads**: Memory-efficient handling of large files
- **MD5 Verification**: Automatic integrity checking via ETag headers
- **Bandwidth Limiting**: Rate limit downloads to control network usage
- **Resume Support**: Skip already downloaded and verified files
- **Progress Display**: Visual progress bars for long operations
- **Flexible Configuration**: CLI args, environment variables, or JSON config files
- **Structured Logging**: Text or JSON log formats
- **Cross-Platform**: Works on Windows, Linux, and macOS

## Installation

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# Default mode (multi-threaded)
python -m mcafee_sync --source http://example.com/files --dest ./downloads

# Single-threaded mode
python -m mcafee_sync --mode=single --source http://example.com/files --dest ./downloads

# High-concurrency async mode
python -m mcafee_sync --mode=async --workers=100 --source http://example.com/files
```

### Advanced Options

```bash
# Dry run (preview what would be downloaded)
python -m mcafee_sync --dry-run --source http://example.com/files --dest ./downloads

# Bandwidth limiting
python -m mcafee_sync --rate-limit=10MB/s --source http://example.com/files

# Custom workers and retention
python -m mcafee_sync --workers=16 --retention-days=14 --source http://example.com/files

# JSON logging
python -m mcafee_sync --log-format=json --log-level=DEBUG
```

### Configuration File

Create a `config.json`:

```json
{
  "source_path": "http://update.nai.com/products/commonupdater/",
  "destination_path": "./downloads",
  "mode": "async",
  "workers": 50,
  "rate_limit": 10485760,
  "retention_days": 7.0,
  "log_level": "INFO"
}
```

Use it with:

```bash
python -m mcafee_sync --config=config.json
```

### Environment Variables

All options can be set via environment variables:

```bash
export MCAFEE_SYNC_SOURCE_PATH="http://example.com/files"
export MCAFEE_SYNC_DEST_PATH="./downloads"
export MCAFEE_SYNC_MODE="async"
export MCAFEE_SYNC_WORKERS="50"

python -m mcafee_sync
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --source` | Source URL | http://update.nai.com/products/commonupdater/ |
| `-d, --dest` | Destination directory | ./downloads |
| `-m, --mode` | Execution mode (single/thread/async) | thread |
| `-w, --workers` | Number of workers | CPU count * 4 |
| `--rate-limit` | Bandwidth limit (e.g., 10MB/s) | 0 (unlimited) |
| `--retention-days` | Days to keep files | 7.0 |
| `--dry-run` | Preview without downloading | False |
| `--no-resume` | Disable resume support | False |
| `--proxy` | HTTP proxy URL | None |
| `--timeout` | HTTP timeout in seconds | 30 |
| `--retries` | Number of retry attempts | 3 |
| `--log-level` | Log level (DEBUG/INFO/WARNING/ERROR) | INFO |
| `--log-format` | Log format (text/json) | text |
| `--no-progress` | Disable progress bar | False |
| `-c, --config` | Configuration JSON file | None |
| `--save-config` | Save settings to JSON file | None |

## Architecture

```
mcafee_sync/
├── __init__.py          # Package version info
├── __main__.py          # CLI entry point
├── cli.py               # Argument parsing
├── config.py            # Configuration management
├── crawler.py           # HTTP directory discovery
├── downloader.py        # Download logic (sync/async)
├── hasher.py            # MD5/ETag verification
├── utils.py             # Logging and helpers
└── workers.py           # Worker pool implementations
```

## Performance Tips

1. **Async mode**: Best for high-latency connections or many small files
2. **Thread mode**: Good balance for most use cases
3. **Single mode**: Use for debugging or resource-constrained environments
4. **Rate limiting**: Use `--rate-limit` to avoid overwhelming the server
5. **Workers**: Increase for high-bandwidth connections (up to 100-200 for async)

## License

MIT License

## Author

Stuart Graham (stuart@stuart-graham.com)
