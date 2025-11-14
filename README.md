# reqcache

A simple, transparent caching wrapper for Python's `requests` library. Perfect for data collection, web scraping, and reducing redundant HTTP requests during development.

## Features

- **Drop-in compatibility** with `requests` - just add `cache=True`
- **Automatic caching** to local `.cache/` directory
- **Configurable TTL** (Time To Live) with sensible defaults
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

# Standard request (no caching)
response = reqcache.get('https://api.example.com/data')

# Cached request (default 24-hour TTL)
response = reqcache.get('https://api.example.com/data', cache=True)

# Custom TTL (1 hour = 3600 seconds)
response = reqcache.get('https://api.example.com/data', cache=True, cache_ttl=3600)
```

## Usage Examples

### Basic Caching

```python
import reqcache

# First call makes network request and caches response
response = reqcache.get('https://httpbin.org/uuid', cache=True)
print(response.json())  # {'uuid': 'abc-123-def'}

# Second call returns cached response (no network request)
response = reqcache.get('https://httpbin.org/uuid', cache=True)
print(response.json())  # {'uuid': 'abc-123-def'} - same UUID!
```

### All HTTP Methods Supported

```python
import reqcache

# GET request
reqcache.get('https://api.example.com/users', cache=True)

# POST request
reqcache.post('https://api.example.com/users', json={'name': 'Alice'}, cache=True)

# PUT, DELETE, PATCH, HEAD, OPTIONS also supported
reqcache.put('https://api.example.com/users/1', json={'name': 'Bob'}, cache=True)
reqcache.delete('https://api.example.com/users/1', cache=True)
reqcache.patch('https://api.example.com/users/1', json={'active': False}, cache=True)
```

### Custom TTL

```python
import reqcache

# Cache for 1 hour (3600 seconds)
reqcache.get('https://api.example.com/data', cache=True, cache_ttl=3600)

# Cache for 5 minutes
reqcache.get('https://api.example.com/data', cache=True, cache_ttl=300)

# Cache for 1 week
reqcache.get('https://api.example.com/data', cache=True, cache_ttl=604800)
```

### Full requests Compatibility

All `requests` parameters work as expected:

```python
import reqcache

response = reqcache.get(
    'https://api.example.com/data',
    cache=True,
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

### Custom Cache Directory

```python
import reqcache

# Use custom cache directory
response = reqcache.get(
    'https://api.example.com/data',
    cache=True,
    cache_dir='./my_custom_cache'
)

# Clear specific cache directory
reqcache.clear_cache(cache_dir='./my_custom_cache')
```

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
