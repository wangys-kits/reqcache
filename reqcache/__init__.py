"""
reqcache - A caching wrapper for Python requests library

This module provides TTL-based caching for HTTP requests.
Cached responses are stored in a local `.cache/` directory using pickle serialization.
Use cache_ttl parameter to control caching behavior:
- 0: No caching
- -1: Permanent caching
- >0: Cache for specified seconds (default: 86400)
"""

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, Union
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from requests import Response

__version__ = "1.0.0"
__all__ = [
    "get", "post", "put", "delete", "patch", "head", "options",
    "request", "clear_cache", "get_cache_info",
    "TTL_DISABLED", "TTL_PERMANENT", "TTL_ONE_DAY"
]

# TTL Constants
TTL_DISABLED = 0     # No caching
TTL_PERMANENT = -1   # Cache permanently
TTL_ONE_DAY = 86400  # 24 hours in seconds

# Default configuration
DEFAULT_CACHE_DIR = ".cache"
DEFAULT_TTL = TTL_ONE_DAY

# Thread lock for cache operations
_cache_lock = Lock()


def _generate_cache_key(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict, str, bytes]] = None,
    json_data: Optional[Dict] = None,
) -> str:
    """
    Generate a unique cache key based on request parameters.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        params: Query parameters
        data: Request body data
        json_data: JSON request body

    Returns:
        SHA256 hash of the cache key components
    """
    # Parse URL to normalize it
    parsed = urlparse(url)

    # Build normalized URL without query string
    normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Combine query parameters from URL and params argument
    url_params = parse_qs(parsed.query)
    if params:
        # Convert params to same format as parse_qs for consistency
        for key, value in params.items():
            if isinstance(value, list):
                url_params[key] = value
            else:
                url_params[key] = [str(value)]

    # Sort parameters for consistent hashing
    sorted_params = sorted(url_params.items())
    params_string = urlencode(sorted_params, doseq=True)

    # Hash request body if present
    body_hash = ""
    if json_data is not None:
        # Sort JSON keys for consistent hashing
        body_hash = hashlib.sha256(
            json.dumps(json_data, sort_keys=True).encode()
        ).hexdigest()
    elif data is not None:
        if isinstance(data, dict):
            body_hash = hashlib.sha256(
                urlencode(sorted(data.items())).encode()
            ).hexdigest()
        elif isinstance(data, bytes):
            body_hash = hashlib.sha256(data).hexdigest()
        elif isinstance(data, str):
            body_hash = hashlib.sha256(data.encode()).hexdigest()

    # Combine all components
    key_components = [
        method.upper(),
        normalized_url,
        params_string,
        body_hash,
    ]

    cache_key = "|".join(key_components)

    # Return SHA256 hash for filesystem-safe filename
    return hashlib.sha256(cache_key.encode()).hexdigest()


def _get_cache_path(cache_key: str) -> Path:
    """Get the file path for a cache key."""
    return Path(DEFAULT_CACHE_DIR) / f"{cache_key}.pkl"


def _ensure_cache_dir() -> None:
    """Create cache directory if it doesn't exist."""
    Path(DEFAULT_CACHE_DIR).mkdir(parents=True, exist_ok=True)


def _save_to_cache(
    cache_key: str,
    response: Response,
    ttl: int,
) -> None:
    """
    Save a response to cache with timestamp and TTL.

    Args:
        cache_key: Unique cache key
        response: Response object to cache
        ttl: Time to live in seconds (-1 for permanent)
    """
    # Skip saving if TTL is 0 (no caching)
    if ttl == TTL_DISABLED:
        return

    with _cache_lock:
        _ensure_cache_dir()

        cache_data = {
            "timestamp": time.time(),
            "ttl": ttl,
            "response": response,
        }

        cache_path = _get_cache_path(cache_key)
        with open(cache_path, "wb") as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)


def _load_from_cache(
    cache_key: str,
) -> Optional[Response]:
    """
    Load a response from cache if it exists and hasn't expired.

    Args:
        cache_key: Unique cache key

    Returns:
        Cached Response object if valid, None otherwise
    """
    cache_path = _get_cache_path(cache_key)

    if not cache_path.exists():
        return None

    try:
        with _cache_lock:
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)

        # Validate TTL
        timestamp = cache_data.get("timestamp", 0)
        ttl = cache_data.get("ttl", DEFAULT_TTL)

        # Check expiration (skip for permanent cache TTL=-1)
        if ttl != TTL_PERMANENT:
            if time.time() - timestamp > ttl:
                # Cache expired
                return None

        return cache_data.get("response")

    except (pickle.PickleError, OSError, KeyError):
        # Corrupted cache file or missing fields
        return None


def request(
    method: str,
    url: str,
    cache_ttl: int = DEFAULT_TTL,
    **kwargs
) -> Response:
    """
    Make an HTTP request with TTL-based caching control.

    Args:
        method: HTTP method
        url: Request URL
        cache_ttl: Cache time-to-live control:
                  - 0: No caching (passes through to requests)
                  - -1: Permanent caching (no expiration)
                  - >0: Cache for specified seconds (default: 86400)
        **kwargs: Additional arguments passed to requests.request()

    Returns:
        Response object (cached or fresh)
    """
    # Validate cache_ttl parameter
    if not isinstance(cache_ttl, int):
        raise ValueError(f"cache_ttl must be an integer, got {type(cache_ttl).__name__}")
    if cache_ttl < -1:
        raise ValueError(f"cache_ttl must be -1, 0, or positive, got {cache_ttl}")

    # If caching is disabled (TTL=0), pass through to requests
    if cache_ttl == TTL_DISABLED:
        return requests.request(method, url, **kwargs)

    # Generate cache key
    cache_key = _generate_cache_key(
        method=method,
        url=url,
        params=kwargs.get("params"),
        data=kwargs.get("data"),
        json_data=kwargs.get("json"),
    )

    # Try to load from cache
    cached_response = _load_from_cache(cache_key)
    if cached_response is not None:
        return cached_response

    # Cache miss - make actual request
    response = requests.request(method, url, **kwargs)

    # Save to cache
    _save_to_cache(cache_key, response, cache_ttl)

    return response


def get(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make a GET request with TTL-based caching control."""
    return request("GET", url, cache_ttl=cache_ttl, **kwargs)


def post(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make a POST request with TTL-based caching control."""
    return request("POST", url, cache_ttl=cache_ttl, **kwargs)


def put(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make a PUT request with TTL-based caching control."""
    return request("PUT", url, cache_ttl=cache_ttl, **kwargs)


def delete(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make a DELETE request with TTL-based caching control."""
    return request("DELETE", url, cache_ttl=cache_ttl, **kwargs)


def patch(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make a PATCH request with TTL-based caching control."""
    return request("PATCH", url, cache_ttl=cache_ttl, **kwargs)


def head(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make a HEAD request with TTL-based caching control."""
    return request("HEAD", url, cache_ttl=cache_ttl, **kwargs)


def options(url: str, cache_ttl: int = DEFAULT_TTL, **kwargs) -> Response:
    """Make an OPTIONS request with TTL-based caching control."""
    return request("OPTIONS", url, cache_ttl=cache_ttl, **kwargs)


def clear_cache() -> int:
    """
    Clear all cached responses.

    Returns:
        Number of cache files deleted
    """
    cache_path = Path(DEFAULT_CACHE_DIR)

    if not cache_path.exists():
        return 0

    count = 0
    with _cache_lock:
        for cache_file in cache_path.glob("*.pkl"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass

    return count


def get_cache_info() -> Dict[str, Any]:
    """
    Get information about the cache.

    Returns:
        Dictionary with cache statistics
    """
    cache_path = Path(DEFAULT_CACHE_DIR)

    if not cache_path.exists():
        return {
            "exists": False,
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "valid_entries": 0,
            "expired_entries": 0,
        }

    total_files = 0
    total_size = 0
    valid_entries = 0
    expired_entries = 0

    for cache_file in cache_path.glob("*.pkl"):
        total_files += 1
        try:
            total_size += cache_file.stat().st_size

            # Check if entry is valid
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)

            timestamp = cache_data.get("timestamp", 0)
            ttl = cache_data.get("ttl", DEFAULT_TTL)

            # Check expiration (skip for permanent cache TTL=-1)
            if ttl != TTL_PERMANENT:
                if time.time() - timestamp <= ttl:
                    valid_entries += 1
                else:
                    expired_entries += 1
            else:
                valid_entries += 1

        except (OSError, pickle.PickleError, KeyError):
            expired_entries += 1

    return {
        "exists": True,
        "cache_dir": str(cache_path.absolute()),
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
    }
