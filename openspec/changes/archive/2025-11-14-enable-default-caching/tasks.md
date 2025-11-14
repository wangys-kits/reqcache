## 1. API Redesign - Remove Boolean Parameters
- [x] 1.1 Remove `cache` parameter from `request()` function signature
- [x] 1.2 Remove `cache_dir` parameter from `request()` function signature
- [x] 1.3 Remove `cache` parameter from all HTTP method functions (get, post, put, delete, patch, head, options)
- [x] 1.4 Remove `cache_dir` parameter from all HTTP method functions
- [x] 1.5 Keep only `cache_ttl` parameter in all function signatures
- [x] 1.6 Set default `cache_ttl=86400` for all functions

## 2. Implement TTL-Based Cache Logic
- [x] 2.1 Update cache control logic to handle TTL=0 (no caching)
- [x] 2.2 Implement TTL=-1 (permanent caching) logic
- [x] 2.3 Ensure TTL>0 (timed caching) works correctly
- [x] 2.4 Add input validation for cache_ttl parameter
- [x] 2.5 Update cache expiration check to handle permanent caching
- [x] 2.6 Modify cache save logic to skip caching when TTL=0

## 3. Add TTL Constants and Utilities
- [x] 3.1 Define `TTL_DISABLED = 0` constant
- [x] 3.2 Define `TTL_PERMANENT = -1` constant
- [x] 3.3 Define `TTL_ONE_DAY = 86400` constant
- [x] 3.4 Add type hints for cache_ttl parameter
- [x] 3.5 Add documentation for TTL values in docstrings

## 4. Update Core Cache Functions
- [x] 4.1 Modify `_load_from_cache()` to handle TTL=0 (no check)
- [x] 4.2 Modify `_save_to_cache()` to handle TTL=0 (no save)
- [x] 4.3 Update TTL validation in cache operations
- [x] 4.4 Ensure permanent caching (TTL=-1) never expires
- [x] 4.5 Update cache key generation (no change needed, but verify)

## 5. Complete Documentation Rewrite
- [x] 5.1 Update README.md to show TTL-only API examples
- [x] 5.2 Document TTL semantics (0=disabled, -1=permanent, >0=seconds)
- [x] 5.3 Add comprehensive migration guide for 1.x → 2.0.0
- [x] 5.4 Update all usage examples to use TTL-only approach
- [x] 5.5 Add breaking change notice to README and docs
- [x] 5.6 Document removed parameters and alternatives

## 6. Update and Rewrite Tests
- [x] 6.1 Remove all tests using `cache` parameter
- [x] 6.2 Update all tests to use TTL-only control
- [x] 6.3 Add tests for TTL=0 (no caching) behavior
- [x] 6.4 Add tests for TTL=-1 (permanent caching) behavior
- [x] 6.5 Test TTL validation and error handling
- [x] 6.6 Verify default TTL=86400 works correctly
- [x] 6.7 Test that cache_dir parameter is no longer accepted

## 7. Version Management and Release
- [x] 7.1 Update version number to 2.0.0 (major breaking change)
- [x] 7.2 Update CHANGELOG.md with comprehensive breaking change details
- [x] 7.3 Add migration guide in separate MIGRATION.md file
- [x] 7.4 Update pyproject.toml and other metadata
- [x] 7.5 Prepare release notes for breaking change

## 8. Validation and Testing
- [x] 8.1 Run complete test suite to ensure all functionality works
- [x] 8.2 Test migration scenarios with sample code from 1.x
- [x] 8.3 Validate that cache management utilities work unchanged
- [x] 8.4 Test edge cases: negative TTL (except -1), non-integer inputs
- [x] 8.5 Verify cache performance with new TTL logic
- [x] 8.6 Confirm no regressions in cache hit/miss behavior