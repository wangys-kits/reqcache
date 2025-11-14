# Migration Guide: reqcache pre-1.0.0 → v1.0.0

Version 1.0.0 introduces a major breaking change with a simplified TTL-only API design.

## Overview of Changes

### 🔄 Breaking Changes
- **Removed `cache` parameter**: No more boolean `cache=True/False`
- **Removed `cache_dir` parameter**: No per-request cache directory specification
- **Changed default behavior**: Caching is now enabled by default (1-day TTL)
- **Simplified API**: Only use `cache_ttl` parameter to control caching

### ✨ New Features
- **TTL constants**: `TTL_DISABLED`, `TTL_PERMANENT`, `TTL_ONE_DAY`
- **Simplified cache control**: Single parameter for all cache behavior
- **Input validation**: Ensures TTL values are valid
- **Version bump**: Now 1.0.0 to indicate breaking changes

## API Reference Changes

### Function Signatures

**Before (pre-1.0.0):**
```python
def request(method, url, cache=False, cache_ttl=None, cache_dir=DEFAULT_CACHE_DIR, **kwargs):
def get(url, cache=False, cache_ttl=None, **kwargs):
def post(url, cache=False, cache_ttl=None, **kwargs):
# ... etc for all HTTP methods
```

**After (v1.0.0):**
```python
def request(method, url, cache_ttl=DEFAULT_TTL, **kwargs):
def get(url, cache_ttl=DEFAULT_TTL, **kwargs):
def post(url, cache_ttl=DEFAULT_TTL, **kwargs):
# ... etc for all HTTP methods
```

## Migration Examples

### Basic Caching

**Before:**
```python
import reqcache

# No caching (default behavior)
response = reqcache.get('https://api.example.com/data')

# Enable caching
response = reqcache.get('https://api.example.com/data', cache=True)

# Custom TTL with caching enabled
response = reqcache.get('https://api.example.com/data', cache=True, cache_ttl=3600)
```

**After:**
```python
import reqcache

# Default caching (1 day)
response = reqcache.get('https://api.example.com/data')

# Disable caching
response = reqcache.get('https://api.example.com/data', cache_ttl=0)

# Custom TTL
response = reqcache.get('https://api.example.com/data', cache_ttl=3600)

# Use constants for clarity
response = reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_DISABLED)
response = reqcache.get('https://api.example.com/data', cache_ttl=reqcache.TTL_ONE_DAY)
```

### Advanced Caching Patterns

**Before:**
```python
# Different TTL values
reqcache.get('https://api.example.com/users', cache=True, cache_ttl=3600)      # 1 hour
reqcache.get('https://api.example.com/posts', cache=True, cache_ttl=86400)      # 1 day
reqcache.get('https://api.example.com/config', cache=True, cache_ttl=604800)    # 1 week

# No caching for specific endpoints
reqcache.post('https://api.example.com/login', cache=False)

# Custom cache directory
reqcache.get('https://api.example.com/data', cache=True, cache_dir='./custom_cache')
```

**After:**
```python
# Different TTL values
reqcache.get('https://api.example.com/users', cache_ttl=3600)      # 1 hour
reqcache.get('https://api.example.com/posts', cache_ttl=86400)      # 1 day (default)
reqcache.get('https://api.example.com/config', cache_ttl=604800)    # 1 week

# Use constants for common patterns
reqcache.get('https://api.example.com/users', cache_ttl=reqcache.TTL_ONE_DAY)
reqcache.get('https://api.example.com/static', cache_ttl=reqcache.TTL_PERMANENT)

# No caching for specific endpoints
reqcache.post('https://api.example.com/login', cache_ttl=reqcache.TTL_DISABLED)

# Cache directory is now fixed (.cache/) - use global config if needed
reqcache.get('https://api.example.com/data', cache_ttl=3600)
```

### Working with All HTTP Methods

**Before:**
```python
reqcache.get('https://api.example.com/users', cache=True)
reqcache.post('https://api.example.com/users', json={'name': 'Alice'}, cache=True)
reqcache.put('https://api.example.com/users/1', json={'name': 'Bob'}, cache=True)
reqcache.delete('https://api.example.com/users/1', cache=True)
```

**After:**
```python
reqcache.get('https://api.example.com/users')                              # Default 1-day cache
reqcache.post('https://api.example.com/users', json={'name': 'Alice'})     # Default 1-day cache
reqcache.put('https://api.example.com/users/1', json={'name': 'Bob'})       # Default 1-day cache
reqcache.delete('https://api.example.com/users/1')                          # Default 1-day cache

# Or explicitly disable caching for specific operations
reqcache.post('https://api.example.com/users', json={'name': 'Alice'}, cache_ttl=0)
```

## TTL Value Reference

| Value | Constant | Meaning | Use Case |
|-------|----------|---------|-----------|
| `0` | `reqcache.TTL_DISABLED` | No caching | Real-time data, authentication |
| `-1` | `reqcache.TTL_PERMANENT` | Never expires | Static configuration, rarely changing data |
| `86400` | `reqcache.TTL_ONE_DAY` | 1 day | Default caching behavior |
| `3600` | - | 1 hour | Frequently changing data |
| `300` | - | 5 minutes | Very dynamic data |
| Any positive integer | - | Custom seconds | Application-specific needs |

## Validation and Error Handling

Version 1.0.0 includes input validation for TTL values:

```python
import reqcache

# These will raise ValueError
try:
    reqcache.get('https://api.example.com/data', cache_ttl=-2)  # Invalid: less than -1
except ValueError as e:
    print(f"Error: {e}")

try:
    reqcache.get('https://api.example.com/data', cache_ttl="invalid")  # Invalid: not integer
except ValueError as e:
    print(f"Error: {e}")
```

## Backward Compatibility

There is **no backward compatibility** for v1.x code. The API changes are intentional to provide a cleaner, more intuitive interface.

## Migration Checklist

- [ ] Update all function calls to remove `cache` parameter
- [ ] Replace `cache=True` with appropriate `cache_ttl` value
- [ ] Replace `cache=False` with `cache_ttl=0` or `cache_ttl=reqcache.TTL_DISABLED`
- [ ] Remove `cache_dir` parameters from function calls
- [ ] Update imports if using constants: `from reqcache import TTL_DISABLED, TTL_PERMANENT, TTL_ONE_DAY`
- [ ] Update tests to use new API
- [ ] Update documentation and examples
- [ ] Pin to `reqcache>=1.0.0` in requirements

## Need Help?

If you need help with migration:

1. Check the [README.md](README.md) for updated examples
2. Look at the TTL constants and choose appropriate values for your use case
3. Consider your caching strategy - most endpoints work well with the default 1-day cache
4. For complex migrations, consider updating incrementally and testing thoroughly

## Benefits of v1.0.0

- **Simpler API**: Fewer parameters, less cognitive overhead
- **More intuitive**: TTL values directly correspond to cache behavior
- **Better defaults**: Caching enabled by default for most use cases
- **Clearer intent**: TTL constants make code more readable
- **Input validation**: Prevents invalid cache configurations