# reqcache

A simple, transparent caching wrapper for Python's `requests` library with TTL-based cache control. Perfect for data collection, web scraping, and reducing redundant HTTP requests during development.

## Features

- **TTL-based caching** - control caching with time-to-live values
- **Default caching enabled** - caches for 1 day by default
- **Simple API** - just use `cache_ttl` parameter
- **Smart cache keys** based on URL, HTTP method, and request parameters
- **Thread-safe** for concurrent usage
- **Complete response preservation** using pickle serialization
- **Cache management utilities** for inspection and cleanup

## Installation

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import reqcache

# Cached request (default 1-day TTL)
response = reqcache.get('https://api.example.com/data')

# Custom TTL (1 hour = 3600 seconds)
response = reqcache.get('https://api.example.com/data', cache_ttl=3600)

# Disable caching
response = reqcache.get('https://api.example.com/data', cache_ttl=0)

# Permanent caching (never expires)
response = reqcache.get('https://api.example.com/data', cache_ttl=-1)

# Use TTL constants
response = reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_ONE_DAY)
response = reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_DISABLED)
response = reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_PERMANENT)
```

## Usage Examples

### Basic Caching

```python
import reqcache

# First call makes network request and caches response (default 1 day)
response = reqcache.get('https://httpbin.org/uuid')
print(response.json())  # {'uuid': 'abc-123-def'}

# Second call returns cached response (no network request)
response = reqcache.get('https://httpbin.org/uuid')
print(response.json())  # {'uuid': 'abc-123-def'} - same UUID!
```

### TTL Control

```python
import reqcache

# Cache for 1 hour (3600 seconds)
response = reqcache.get('https://api.example.com/data', cache_ttl=3600)

# Cache for 5 minutes
response = reqcache.get('https://api.example.com/data', cache_ttl=300)

# Cache for 1 week
response = reqcache.get('https://api.example.com/data', cache_ttl=604800)

# Disable caching (no cache)
response = reqcache.get('https://api.example.com/data', cache_ttl=0)

# Permanent caching (never expires)
response = reqcache.get('https://api.example.com/data', cache_ttl=-1)
```

### All HTTP Methods Supported

```python
import reqcache

# All HTTP methods support TTL-based caching
reqcache.get('https://api.example.com/users')                    # Default 1-day cache
reqcache.post('https://api.example.com/users', json={'name': 'Alice'})  # Default 1-day cache
reqcache.put('https://api.example.com/users/1', json={'name': 'Bob'})    # Default 1-day cache
reqcache.delete('https://api.example.com/users/1')                     # Default 1-day cache
reqcache.patch('https://api.example.com/users/1', json={'active': False}) # Default 1-day cache
reqcache.head('https://api.example.com/users/1')                        # Default 1-day cache
reqcache.options('https://api.example.com/users/1')                     # Default 1-day cache

# Disable caching for any method
reqcache.get('https://api.example.com/users', cache_ttl=0)
reqcache.post('https://api.example.com/users', json={'name': 'Alice'}, cache_ttl=0)
```

### Full requests Compatibility

All `requests` parameters work as expected:

```python
import reqcache

response = reqcache.get(
    'https://api.example.com/data',
    cache_ttl=3600,  # 1 hour cache
    headers={'Authorization': 'Bearer token123'},
    params={'page': 1, 'limit': 10},
    timeout=30,
    verify=True,
)
```

### Cache Management

```python
import reqcache

# Get cache statistics
info = reqcache.get_cache_info()
print(f"Total cache files: {info['total_files']}")
print(f"Valid entries: {info['valid_entries']}")
print(f"Expired entries: {info['expired_entries']}")
print(f"Total size: {info['total_size_mb']} MB")

# Clear all cached responses
deleted = reqcache.clear_cache()
print(f"Deleted {deleted} cache files")
```

## Migration Guide (pre-1.0.0 → v1.0.0)

Version 1.0.0 introduces breaking changes with a simplified TTL-only API.

### Key Changes
- **Removed**: `cache` boolean parameter
- **Removed**: `cache_dir` parameter from request functions
- **Changed**: Default behavior is now to cache for 1 day
- **Added**: TTL constants (`TTL_DISABLED`, `TTL_PERMANENT`, `TTL_ONE_DAY`)

### API Migration

**Before (pre-1.0.0):**
```python
# No caching (default)
reqcache.get('https://api.example.com/data')

# Enable caching
reqcache.get('https://api.example.com/data', cache=True)

# Custom TTL
reqcache.get('https://api.example.com/data', cache=True, cache_ttl=3600)

# Custom cache directory
reqcache.get('https://api.example.com/data', cache=True, cache_dir='./my_cache')
```

**After (v1.0.0):**
```python
# Default caching (1 day)
reqcache.get('https://api.example.com/data')

# Disable caching
reqcache.get('https://api.example.com/data', cache_ttl=0)

# Custom TTL
reqcache.get('https://api.example.com/data', cache_ttl=3600)

# Use constants
reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_DISABLED)
reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_PERMANENT)
reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_ONE_DAY)
```

### TTL Values Reference
- `0` or `reqcache.TTL_DISABLED`: No caching
- `-1` or `reqcache.TTL_PERMANENT`: Permanent caching (never expires)
- `86400` or `reqcache.TTL_ONE_DAY`: 1 day (default)
- Any positive integer: Cache for that many seconds

## How It Works

### Cache Key Generation

Cache keys are generated based on:
- **URL** (normalized, without query string)
- **HTTP method** (GET, POST, etc.)
- **Query parameters** (sorted for consistency)
- **Request body** (for POST/PUT/PATCH requests)

This ensures that:
```python
# These produce the SAME cache key
reqcache.get('https://example.com?a=1&b=2', cache=True)
reqcache.get('https://example.com?b=2&a=1', cache=True)

# These produce DIFFERENT cache keys
reqcache.get('https://example.com', cache=True)
reqcache.post('https://example.com', cache=True)
reqcache.get('https://example.com?page=1', cache=True)
reqcache.get('https://example.com?page=2', cache=True)
```

### Storage Format

Cached responses are stored in `.cache/` directory with:
- **Filename**: SHA256 hash of cache key (e.g., `a3b2c1d4e5f6.pkl`)
- **Format**: Python pickle (preserves complete Response object)
- **Metadata**: Timestamp and TTL stored with response

### TTL Behavior

- **Default TTL**: 24 hours (86400 seconds)
- **Custom TTL**: Specify per-request with `cache_ttl` parameter
- **Expiration**: Checked on cache read; expired entries treated as cache miss
- **No auto-cleanup**: Expired files remain until manually cleared (they don't hurt)

## Use Cases

### Data Collection / Web Scraping

```python
import reqcache

# Scrape data with automatic caching to avoid re-fetching
urls = [
    'https://example.com/page1',
    'https://example.com/page2',
    'https://example.com/page3',
]

for url in urls:
    response = reqcache.get(url, cache=True, cache_ttl=86400)
    # Process response...
    # If script crashes and restarts, already-fetched pages are cached!
```

### Development / Testing

```python
import reqcache

# During development, cache API responses to speed up testing
def fetch_user_data(user_id):
    response = reqcache.get(
        f'https://api.example.com/users/{user_id}',
        cache=True,
        cache_ttl=3600,  # Cache for 1 hour during dev
    )
    return response.json()

# First call: network request
user = fetch_user_data(123)

# Subsequent calls: instant response from cache
user = fetch_user_data(123)  # No network delay!
```

### API Rate Limit Protection

```python
import reqcache

# Cache responses to avoid hitting API rate limits
def get_expensive_api_data():
    return reqcache.get(
        'https://api.example.com/expensive-endpoint',
        cache=True,
        cache_ttl=3600,  # Re-fetch at most once per hour
        headers={'Authorization': f'Bearer {API_KEY}'},
    )
```

## Configuration

### Default Settings

```python
DEFAULT_CACHE_DIR = ".cache"
DEFAULT_TTL = 86400  # 24 hours in seconds
```

### Per-Request Configuration

```python
import reqcache

response = reqcache.get(
    'https://api.example.com/data',
    cache=True,           # Enable caching (default: False)
    cache_ttl=3600,       # TTL in seconds (default: 86400)
    cache_dir='.mycache', # Cache directory (default: '.cache')
)
```

## Important Notes

### Security Warning

**Pickle Security**: This library uses Python's `pickle` module for serialization. Only use the cache in trusted environments where you control the cache directory. Never load cache files from untrusted sources.

### Cache Behavior

- **Opt-in**: Caching is disabled by default; you must explicitly pass `cache=True`
- **No HTTP semantics**: Cache-Control, ETag, and other HTTP caching headers are ignored
- **Error responses cached**: 4xx and 5xx responses are cached just like successful responses
- **Thread-safe**: Safe for use in multi-threaded applications
- **No size limits**: Cache can grow unbounded; monitor with `get_cache_info()`

### When NOT to Use Caching

- **Production APIs**: Use proper HTTP caching or Redis/Memcached instead
- **Authentication flows**: Don't cache login/token requests
- **Real-time data**: Don't cache if you need fresh data every time
- **Sensitive data**: Be careful with caching responses containing secrets

## Troubleshooting

### Cache Not Working

```python
# Make sure cache=True is set
response = reqcache.get('https://example.com', cache=True)  # ✓
response = reqcache.get('https://example.com')  # ✗ (no caching)
```

### Cache Directory Not Created

The cache directory is created automatically on first cached request. If you see no `.cache/` directory, verify that:
1. You've made at least one request with `cache=True`
2. You have write permissions in the working directory

### Stale Data

If cached data is outdated:
```python
# Option 1: Clear all cache
reqcache.clear_cache()

# Option 2: Use shorter TTL
reqcache.get('https://api.example.com/data', cache=True, cache_ttl=60)

# Option 3: Disable cache for specific request
reqcache.get('https://api.example.com/data', cache=False)
```

### Cache Growing Too Large

Monitor cache size:
```python
info = reqcache.get_cache_info()
print(f"Cache size: {info['total_size_mb']} MB")

if info['total_size_mb'] > 100:  # More than 100 MB
    reqcache.clear_cache()
```

### Import Error

If you get `ModuleNotFoundError: No module named 'reqcache'`:
```bash
# Install the package
pip install -e .

# Or install requests dependency manually
pip install requests
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=reqcache --cov-report=html

# Run specific test class
pytest tests/test_reqcache.py::TestCacheKeyGeneration
```

### Project Structure

```
reqcache/
├── reqcache/
│   └── __init__.py       # Main implementation
├── tests/
│   ├── __init__.py
│   └── test_reqcache.py  # Test suite
├── pyproject.toml        # Package configuration
├── README.md             # This file
└── .gitignore
```

## API Reference

### Main Functions

- `reqcache.get(url, cache=False, cache_ttl=None, **kwargs)` - GET request
- `reqcache.post(url, cache=False, cache_ttl=None, **kwargs)` - POST request
- `reqcache.put(url, cache=False, cache_ttl=None, **kwargs)` - PUT request
- `reqcache.delete(url, cache=False, cache_ttl=None, **kwargs)` - DELETE request
- `reqcache.patch(url, cache=False, cache_ttl=None, **kwargs)` - PATCH request
- `reqcache.head(url, cache=False, cache_ttl=None, **kwargs)` - HEAD request
- `reqcache.options(url, cache=False, cache_ttl=None, **kwargs)` - OPTIONS request
- `reqcache.request(method, url, cache=False, cache_ttl=None, **kwargs)` - Generic request

### Utility Functions

- `reqcache.clear_cache(cache_dir='.cache')` - Delete all cache files
- `reqcache.get_cache_info(cache_dir='.cache')` - Get cache statistics

### Parameters

- `cache` (bool): Enable caching (default: False)
- `cache_ttl` (int): Time to live in seconds (default: 86400)
- `cache_dir` (str): Cache directory path (default: '.cache')
- `**kwargs`: All other parameters passed to `requests.request()`

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Changelog

### 0.1.0 (Initial Release)
- Basic caching functionality
- Support for all HTTP methods
- Configurable TTL
- Cache management utilities
- Comprehensive test suite
