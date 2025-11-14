## Context
The reqcache library currently uses a dual-parameter system (`cache` boolean + `cache_ttl`) which creates unnecessary API complexity. A TTL-only approach would be more intuitive: cache behavior is determined entirely by the TTL value, eliminating the boolean parameter entirely.

## Goals / Non-Goals
**Goals:**
- Simplify API by removing `cache` parameter completely
- Use TTL values to control caching behavior (0=disabled, -1=permanent, >0=seconds)
- Set default TTL to 1 day (86400 seconds) for caching by default
- Maintain all existing caching functionality with simpler interface
- Reduce API surface area and cognitive load

**Non-Goals:**
- Changing cache key generation logic
- Modifying storage format or location
- Adding global configuration complexity
- Changing cache management utilities

## Decisions
- **Decision**: Remove `cache` parameter entirely and use TTL-only control
  - **Rationale**: Simpler API, less cognitive overhead, more intuitive
  - **Alternative considered**: Keep both parameters - rejected as overly complex
  - **Alternative considered**: Use enum for cache modes - rejected as less flexible

- **Decision**: Use TTL semantics: 0=disabled, -1=permanent, >0=seconds
  - **Rationale**: Clear numerical mapping, standard TTL convention
  - **Alternative considered**: Use negative for disabled - rejected as confusing
  - **Alternative considered**: Use None for disabled - rejected as less explicit

- **Decision**: Remove `cache_dir` parameter from request functions
  - **Rationale**: Should be global configuration, not per-request
  - **Alternative considered**: Keep parameter - rejected for API simplicity

## Risks / Trade-offs
- **Major Breaking Change**: Complete API redesign
  - **Mitigation**: Version bump to 2.0.0, comprehensive migration guide
- **Learning Curve**: Users must learn new TTL-based control
  - **Mitigation**: Clear examples and documentation
- **Backward Compatibility**: No compatibility with existing code
  - **Mitigation**: Clean break better than confusing dual-API

## Migration Plan
1. Remove `cache` and `cache_dir` parameters from all HTTP functions
2. Update all function signatures to only accept `cache_ttl`
3. Set default `cache_ttl=86400` (1 day)
4. Update cache logic to handle TTL=0 (no cache) and TTL=-1 (permanent)
5. Version bump to 2.0.0 for major breaking change
6. Comprehensive migration guide and examples

## Open Questions
- Should we provide utility functions for common TTL values? (Decision: Yes, constants like TTL_PERMANENT, TTL_DISABLED)