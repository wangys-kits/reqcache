## Context

This design adds a caching layer to Python's requests library for data collection and web scraping use cases. The primary goal is to reduce redundant network calls by caching HTTP responses to local disk, while maintaining full API compatibility with the requests library.

**Background:**
- Target users: Data collectors, web scrapers, developers testing against external APIs
- Constraint: Must be drop-in compatible with requests library
- Environment: Single-machine, file-based storage (no distributed cache needed)

**Stakeholders:**
- Developers using the library for data collection pipelines
- CI/CD systems that may benefit from cached test fixtures

## Goals / Non-Goals

**Goals:**
- Provide transparent, opt-in caching for requests library
- Store complete response objects including status, headers, and body
- Support configurable TTL with sensible defaults
- Minimize code changes needed to adopt caching (simple `cache=True` parameter)
- Maintain thread-safety for concurrent usage

**Non-Goals:**
- Distributed caching or multi-machine coordination
- Cache invalidation based on HTTP cache headers (Cache-Control, ETag)
- Database-backed storage (stick to simple file system)
- Automatic cache warming or prefetching
- Request deduplication or request coalescing

## Decisions

### Decision 1: Cache Key Algorithm
**Choice:** Hash of `(URL, HTTP method, sorted query params, request body hash)`

**Rationale:**
- URL alone is insufficient (same URL with different methods/params)
- Include method to differentiate GET vs POST to same endpoint
- Hash request body for POST/PUT to handle different payloads
- Sort query params to ensure `?a=1&b=2` matches `?b=2&a=1`
- Use SHA256 for collision resistance and filesystem-safe filenames

**Alternatives considered:**
- URL-only: Too coarse, would incorrectly cache different requests
- Include headers: Too granular, would reduce cache hit rate unnecessarily
- Database key-value store: Adds dependency and complexity

### Decision 2: Serialization Format
**Choice:** Python pickle

**Rationale:**
- Preserves full response object graph (status, headers, cookies, etc.)
- Native Python support, no external dependencies
- Efficient for Python-to-Python serialization
- Allows cached responses to behave identically to fresh responses

**Alternatives considered:**
- JSON: Cannot preserve binary content, loses response object methods
- MessagePack: Requires additional dependency
- Plain text: Only works for text responses, loses metadata

**Trade-off:** Pickle files are not human-readable and not portable across Python versions. This is acceptable since the cache is ephemeral and local to development/scraping environment.

### Decision 3: Storage Structure
**Choice:** Flat directory `.cache/` with hashed filenames

```
.cache/
├── a3b2c1d4e5f6.pkl  # SHA256 hash of cache key
├── f6e5d4c3b2a1.pkl
└── metadata.json     # Optional: cache statistics
```

**Rationale:**
- Simple implementation, no directory traversal needed
- Hash provides collision resistance and filename safety
- `.cache` prefix hides from normal directory listings
- No subdirectory structure needed for expected cache sizes (<10k entries)

**Alternatives considered:**
- Hierarchical structure (e.g., `.cache/ab/cd/abcd123.pkl`): Unnecessary complexity for typical use case
- SQLite database: Adds overhead, harder to debug, overkill for key-value storage

### Decision 4: TTL Implementation
**Choice:** Store timestamp in pickle metadata, check on cache read

```python
{
    'timestamp': 1699999999.0,
    'ttl': 86400,  # seconds
    'response': <Response object>
}
```

**Rationale:**
- Simple in-band storage (no separate metadata file)
- Default 24 hours handles common scraping patterns
- Per-request override allows flexibility
- No background cleanup needed (stale files don't hurt)

**Alternatives considered:**
- Filesystem mtime: Less explicit, harder to test, platform-dependent
- Separate metadata file: Extra I/O operations, can get out of sync
- Background cleanup job: Unnecessary complexity

### Decision 5: API Design
**Choice:** Wrapper functions mirroring requests API with optional `cache` parameter

```python
import reqcache

# Original requests
response = requests.get('https://api.example.com/data')

# With caching
response = reqcache.get('https://api.example.com/data', cache=True)
response = reqcache.get('https://api.example.com/data', cache=True, cache_ttl=3600)
```

**Rationale:**
- Minimal migration effort (change import and add `cache=True`)
- Explicit opt-in prevents accidental caching of sensitive data
- Familiar API for requests users
- Allows gradual adoption (can use both libraries in same codebase)

**Alternatives considered:**
- Monkey-patch requests: Too magical, hard to debug
- Session-based configuration: More verbose, harder to enable per-request
- Decorator-based: Doesn't fit imperative request pattern well

## Risks / Trade-offs

### Risk: Pickle Security
**Concern:** Pickle can execute arbitrary code if loading untrusted data

**Mitigation:**
- Cache directory is local and controlled by developer
- Document security warning in README
- Consider adding `--cache-dir` option for custom location
- Future: Add opt-in JSON mode for paranoid environments

### Risk: Stale Data
**Concern:** Cached responses may become outdated, causing incorrect behavior

**Mitigation:**
- Make cache opt-in per request (default is no caching)
- Document TTL behavior clearly
- Provide cache management utilities (clear, inspect)
- Future: Add `cache_refresh=True` to force cache bypass

### Risk: Disk Space
**Concern:** Cache can grow unbounded with large responses or many requests

**Mitigation:**
- Cache is in working directory (visible to developers)
- Document cache location in README
- Provide `reqcache.clear_cache()` utility function
- Future: Add `max_cache_size` or LRU eviction

### Trade-off: No HTTP Semantics
**Choice:** Ignore HTTP caching headers (Cache-Control, ETag, etc.)

**Rationale:**
- Simpler implementation focuses on local performance
- Scraping use cases often ignore origin server cache directives
- TTL-based caching is more predictable for automated pipelines

**Impact:** Users expecting HTTP-compliant caching will be surprised. Document this clearly.

## Migration Plan

**Phase 1: Initial Release**
1. Publish package to PyPI
2. No breaking changes (new package)
3. Users adopt at their own pace

**Phase 2: Adoption**
- Existing requests code continues to work
- Gradual migration by adding `cache=True` to selected requests
- No global state or configuration required

**Rollback:**
- Remove `cache=True` parameters to revert to standard requests
- Delete `.cache/` directory if desired
- No data migration needed

## Open Questions

1. **Should we support cache sharing across projects?**
   - Current: `.cache/` in working directory (project-scoped)
   - Alternative: Global cache in `~/.reqcache/` (system-scoped)
   - Decision: Start with local, add global as opt-in later if needed

2. **Should we validate response integrity?**
   - Current: No checksum validation
   - Alternative: Store SHA256 of response body, verify on read
   - Decision: Skip for v1, low risk of corruption in normal use

3. **Should we support custom cache backends?**
   - Current: File system only
   - Alternative: Pluggable storage (Redis, S3, etc.)
   - Decision: Not needed for initial use case, consider for v2+
