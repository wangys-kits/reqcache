# request-caching Specification

## Purpose
TBD - created by archiving change add-request-caching. Update Purpose after archive.
## Requirements
### Requirement: Cache-Enabled Request Wrapper
The system SHALL provide a wrapper around Python's requests library that uses TTL-based cache control without boolean cache parameters.

#### Scenario: Default caching with one-day TTL
- **WHEN** a request is made without specifying cache_ttl parameter
- **THEN** the system caches for exactly 86400 seconds (24 hours)

#### Scenario: TTL-controlled caching
- **WHEN** a request specifies cache_ttl > 0
- **THEN** the system caches for the specified number of seconds

#### Scenario: Permanent caching
- **WHEN** a request specifies cache_ttl = -1
- **THEN** the system caches permanently without expiration

#### Scenario: Cache disabled
- **WHEN** a request specifies cache_ttl = 0
- **THEN** the request behaves exactly like standard requests library (no caching)

#### Scenario: Cache hit returns stored response
- **WHEN** a cached response exists and has not expired
- **THEN** the system returns the cached response without making a network request

#### Scenario: Cache miss triggers network request
- **WHEN** no cached response exists or cache has expired
- **THEN** the system makes a network request and stores the response in cache

### Requirement: Cache Key Generation
The system SHALL generate unique cache keys based on URL, HTTP method, and request parameters.

#### Scenario: Different URLs produce different keys
- **WHEN** requests are made to different URLs
- **THEN** each request uses a separate cache key and cache entry

#### Scenario: Different HTTP methods produce different keys
- **WHEN** GET and POST requests are made to the same URL
- **THEN** each method uses a separate cache key

#### Scenario: Different parameters produce different keys
- **WHEN** requests with different query parameters or request bodies are made
- **THEN** each parameter combination uses a separate cache key

#### Scenario: Identical requests produce same key
- **WHEN** multiple requests with same URL, method, and parameters are made
- **THEN** all requests share the same cache key and cache entry

### Requirement: Cache Storage Location
The system SHALL store cached responses in a `.cache/` directory within the current working directory.

#### Scenario: Cache directory created automatically
- **WHEN** the first cached request is made
- **THEN** the system creates `.cache/` directory if it does not exist

#### Scenario: Cache files organized by key hash
- **WHEN** responses are cached
- **THEN** each cache entry is stored as a separate file with filename derived from cache key hash

### Requirement: Cache Serialization Format
The system SHALL serialize complete response objects using Python's pickle format.

#### Scenario: Full response object preserved
- **WHEN** a response is cached
- **THEN** status code, headers, body, and other response attributes are preserved

#### Scenario: Cached response is identical to original
- **WHEN** a cached response is retrieved
- **THEN** it behaves identically to the original network response object

### Requirement: Configurable TTL (Time To Live)
The system SHALL handle TTL semantics including permanent caching and disabled caching.

#### Scenario: TTL zero disables caching
- **WHEN** cache_ttl = 0 is specified
- **THEN** no cache operations are performed

#### Scenario: TTL negative one enables permanent caching
- **WHEN** cache_ttl = -1 is specified
- **THEN** cached responses never expire

#### Scenario: Positive TTL creates timed cache
- **WHEN** cache_ttl > 0 is specified
- **THEN** cached responses expire after the specified seconds

#### Scenario: Cache timestamp validation with TTL
- **WHEN** checking cache validity
- **THEN** the system handles permanent cache (TTL=-1) and disabled cache (TTL=0) correctly

### Requirement: API Compatibility
The system SHALL provide a simplified API that only requires TTL parameter for cache control.

#### Scenario: No cache parameter in function signatures
- **WHEN** examining HTTP method function signatures
- **THEN** only cache_ttl parameter is present for cache control

#### Scenario: Consistent TTL behavior across methods
- **WHEN** using any HTTP method (GET, POST, PUT, etc.)
- **THEN** cache_ttl parameter behaves identically across all methods

#### Scenario: TTL validation
- **WHEN** invalid cache_ttl values are provided
- **THEN** the system raises appropriate validation errors

