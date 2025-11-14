# Change: Add Request Caching Capability

## Why
Python's requests library is widely used for HTTP requests but lacks built-in caching. For data collection and web scraping scenarios, repeated requests to the same endpoints waste bandwidth, time, and may trigger rate limits. A local disk-based cache can significantly improve performance and reduce redundant network calls.

## What Changes
- Add cache-enabled wrapper around requests library
- Implement disk-based caching in `.cache/` directory
- Support configurable TTL (Time To Live) for cached responses
- Generate cache keys based on URL, HTTP method, and request parameters
- Store complete response objects using pickle serialization
- Provide simple `cache=True` parameter to enable caching per-request

## Impact
- Affected specs: `request-caching` (new capability)
- Affected code: New Python package/module wrapping requests
- Performance: Dramatically reduced network calls for repeated requests
- Storage: `.cache/` directory will grow with cached responses
