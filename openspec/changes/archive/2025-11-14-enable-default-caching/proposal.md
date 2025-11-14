# Change: Simplify Cache Control with TTL-Only Design

## Why
The current reqcache library uses both `cache` boolean and `cache_ttl` parameters, which creates unnecessary complexity. A simpler TTL-only control where cache behavior is determined by the TTL value (0 = disabled, -1 = permanent, positive = seconds) would be more intuitive and reduce API surface area.

## What Changes
- **BREAKING**: Remove `cache` parameter entirely from all HTTP method functions
- **BREAKING**: Use TTL-based cache control:
  - `cache_ttl=0` (default disabled): No caching
  - `cache_ttl=-1`: Permanent caching (no expiration)
  - `cache_ttl>0`: Cache for specified seconds
- **BREAKING**: Change default behavior to cache for 1 day (86400 seconds)
- **BREAKING**: Remove `cache_dir` parameter (use global configuration or default)

## Impact
- Affected specs: `request-caching`
- Affected code: All HTTP method functions in `reqcache/__init__.py`
- **MAJOR BREAKING CHANGE**: Complete API redesign with simplified interface
- Migration: Users must update to use TTL-only cache control