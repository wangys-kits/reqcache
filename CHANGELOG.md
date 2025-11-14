# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-14

### ⚠️ BREAKING CHANGES
- **Major API redesign**: Removed `cache` boolean parameter completely
- **Removed**: `cache_dir` parameter from all HTTP request functions
- **Changed**: Default behavior now caches for 1 day instead of no caching
- **Simplified**: Only `cache_ttl` parameter controls caching behavior

### 🚀 New Features
- **TTL-only control**: Single parameter to control all cache behavior
- **TTL constants**: Added `TTL_DISABLED` (0), `TTL_PERMANENT` (-1), `TTL_ONE_DAY` (86400)
- **Input validation**: Validates `cache_ttl` parameter values and types
- **Improved documentation**: Updated examples and added comprehensive migration guide

### 🔄 Changed
- **Function signatures**: All HTTP methods now use `cache_ttl` parameter only
- **Default behavior**: Caching enabled by default with 1-day TTL
- **Cache logic**: Enhanced to handle TTL=0 (no cache) and TTL=-1 (permanent cache)
- **Error handling**: Better validation and error messages

### 🗑️ Removed
- **`cache` parameter**: Boolean cache control removed
- **`cache_dir` parameter**: Per-request cache directory specification removed
- **Old API patterns**: No longer supports opt-in caching model

### 📚 Documentation
- **Migration guide**: Comprehensive pre-1.0.0 → 1.0.0 migration guide
- **Updated README**: New examples and TTL-based usage patterns
- **API reference**: Updated function signatures and parameter documentation

### 💥 Migration Required
All existing code must be updated to use the new TTL-only API. See [MIGRATION.md](MIGRATION.md) for detailed migration instructions.

### Examples
```python
# Before (pre-1.0.0)
reqcache.get('https://api.example.com/data', cache=True, cache_ttl=3600)
reqcache.get('https://api.example.com/data', cache=False)

# After (1.0.0)
reqcache.get('https://api.example.com/data', cache_ttl=3600)
reqcache.get('https://api.example.com/data', cache_ttl=0)  # or TTL_DISABLED
```

## [0.1.0] - Initial Release

### ✨ Features
- Initial release with basic caching functionality
- Support for all HTTP methods (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- Opt-in caching with `cache=True` parameter
- Configurable TTL with `cache_ttl` parameter
- Cache key generation based on URL, method, and parameters
- Cache management utilities (`get_cache_info()`, `clear_cache()`)
- Thread-safe operations
- Pickle-based response serialization

## [2.0.0] - 2024-11-14 (skipped)

**Note**: Version 2.0.0 was planned but released as 1.0.0 instead.