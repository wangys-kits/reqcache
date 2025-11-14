"""
Tests for reqcache library
"""

import json
import os
import pickle
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest
import requests
from requests.models import Response
from requests.structures import CaseInsensitiveDict

import reqcache


def create_mock_response(status_code=200, text="", content=None, headers=None):
    """Create a real Response object for testing (can be pickled)."""
    response = Response()
    response.status_code = status_code
    response._content = content if content is not None else text.encode('utf-8')
    response.headers = CaseInsensitiveDict(headers or {})
    response.encoding = 'utf-8'
    response.url = "https://example.com/test"
    return response


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "test_cache"
    yield str(cache_dir)
    # Cleanup
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


class TestCacheKeyGeneration:
    """Tests for cache key generation logic."""

    def test_different_urls_different_keys(self):
        """Different URLs should produce different cache keys."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/path1")
        key2 = reqcache._generate_cache_key("GET", "https://example.com/path2")
        assert key1 != key2

    def test_different_methods_different_keys(self):
        """Different HTTP methods should produce different cache keys."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/data")
        key2 = reqcache._generate_cache_key("POST", "https://example.com/data")
        assert key1 != key2

    def test_different_params_different_keys(self):
        """Different query parameters should produce different cache keys."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/data", params={"a": "1"})
        key2 = reqcache._generate_cache_key("GET", "https://example.com/data", params={"a": "2"})
        assert key1 != key2

    def test_param_order_same_key(self):
        """Query parameters in different order should produce the same key."""
        key1 = reqcache._generate_cache_key(
            "GET", "https://example.com/data", params={"a": "1", "b": "2"}
        )
        key2 = reqcache._generate_cache_key(
            "GET", "https://example.com/data", params={"b": "2", "a": "1"}
        )
        assert key1 == key2

    def test_identical_requests_same_key(self):
        """Identical requests should produce the same cache key."""
        key1 = reqcache._generate_cache_key(
            "GET", "https://example.com/data?x=1", params={"a": "1"}
        )
        key2 = reqcache._generate_cache_key(
            "GET", "https://example.com/data?x=1", params={"a": "1"}
        )
        assert key1 == key2

    def test_different_post_data_different_keys(self):
        """Different POST data should produce different cache keys."""
        key1 = reqcache._generate_cache_key("POST", "https://example.com/api", data={"foo": "bar"})
        key2 = reqcache._generate_cache_key("POST", "https://example.com/api", data={"foo": "baz"})
        assert key1 != key2

    def test_json_data_affects_key(self):
        """JSON request body should affect cache key."""
        key1 = reqcache._generate_cache_key(
            "POST", "https://example.com/api", json_data={"foo": "bar"}
        )
        key2 = reqcache._generate_cache_key(
            "POST", "https://example.com/api", json_data={"foo": "baz"}
        )
        assert key1 != key2

    def test_url_params_normalized(self):
        """URL query parameters should be properly normalized."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/data?a=1&b=2")
        key2 = reqcache._generate_cache_key("GET", "https://example.com/data?b=2&a=1")
        assert key1 == key2


class TestCacheStorage:
    """Tests for cache storage and retrieval."""

    def test_cache_directory_created(self, temp_cache_dir):
        """Cache directory should be created automatically."""
        assert not Path(temp_cache_dir).exists()
        reqcache._ensure_cache_dir(temp_cache_dir)
        assert Path(temp_cache_dir).exists()

    def test_save_and_load_cache(self, temp_cache_dir):
        """Should be able to save and load responses from cache."""
        # Create real response
        mock_response = create_mock_response(
            status_code=200,
            text="test data",
            headers={"Content-Type": "text/plain"}
        )

        cache_key = "test_key_123"
        ttl = 3600

        # Save to cache
        reqcache._save_to_cache(cache_key, mock_response, ttl, temp_cache_dir)

        # Load from cache
        loaded_response = reqcache._load_from_cache(cache_key, temp_cache_dir)

        assert loaded_response is not None
        assert loaded_response.status_code == 200
        assert loaded_response.text == "test data"

    def test_cache_miss_returns_none(self, temp_cache_dir):
        """Non-existent cache entry should return None."""
        result = reqcache._load_from_cache("nonexistent_key", temp_cache_dir)
        assert result is None

    def test_expired_cache_returns_none(self, temp_cache_dir):
        """Expired cache entry should return None."""
        mock_response = create_mock_response(status_code=200)

        cache_key = "expired_key"
        ttl = -1  # Already expired

        reqcache._save_to_cache(cache_key, mock_response, ttl, temp_cache_dir)

        # Try to load expired cache
        result = reqcache._load_from_cache(cache_key, temp_cache_dir)
        assert result is None


class TestTTLValidation:
    """Tests for TTL expiration logic."""

    def test_valid_cache_within_ttl(self, temp_cache_dir):
        """Cache entry within TTL should be valid."""
        mock_response = create_mock_response(status_code=200)

        cache_key = "valid_key"
        ttl = 3600  # 1 hour

        reqcache._save_to_cache(cache_key, mock_response, ttl, temp_cache_dir)
        result = reqcache._load_from_cache(cache_key, temp_cache_dir)

        assert result is not None

    def test_cache_expires_after_ttl(self, temp_cache_dir):
        """Cache entry should expire after TTL."""
        mock_response = create_mock_response(status_code=200)

        cache_key = "expiring_key"
        ttl = 1  # 1 second

        reqcache._save_to_cache(cache_key, mock_response, ttl, temp_cache_dir)

        # Wait for expiration
        time.sleep(1.1)

        result = reqcache._load_from_cache(cache_key, temp_cache_dir)
        assert result is None

    def test_custom_ttl_per_request(self, temp_cache_dir):
        """Should support custom TTL per request."""
        mock_response = create_mock_response(status_code=200)

        # Short TTL
        cache_key1 = "short_ttl"
        reqcache._save_to_cache(cache_key1, mock_response, ttl=1, cache_dir=temp_cache_dir)

        # Long TTL
        cache_key2 = "long_ttl"
        reqcache._save_to_cache(cache_key2, mock_response, ttl=3600, cache_dir=temp_cache_dir)

        time.sleep(1.1)

        # Short TTL should be expired
        assert reqcache._load_from_cache(cache_key1, temp_cache_dir) is None

        # Long TTL should still be valid
        assert reqcache._load_from_cache(cache_key2, temp_cache_dir) is not None


class TestCacheEnabledRequests:
    """Tests for cache-enabled request functions."""

    @patch('reqcache.requests.request')
    def test_cache_disabled_by_default(self, mock_request, temp_cache_dir):
        """Requests should not be cached by default."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Make request without cache
        reqcache.get("https://example.com/data", cache_dir=temp_cache_dir)

        # Cache directory should not be created
        cache_files = list(Path(temp_cache_dir).glob("*.pkl")) if Path(temp_cache_dir).exists() else []
        assert len(cache_files) == 0

    @patch('reqcache.requests.request')
    def test_cache_enabled_stores_response(self, mock_request, temp_cache_dir):
        """Enabling cache should store the response."""
        mock_response = create_mock_response(status_code=200, text="cached data")
        mock_request.return_value = mock_response

        # Make cached request
        reqcache.get("https://example.com/data", cache=True, cache_dir=temp_cache_dir)

        # Cache file should exist
        cache_files = list(Path(temp_cache_dir).glob("*.pkl"))
        assert len(cache_files) == 1

    @patch('reqcache.requests.request')
    def test_cache_hit_no_network_request(self, mock_request, temp_cache_dir):
        """Cache hit should not make network request."""
        mock_response = create_mock_response(status_code=200, text="original data")
        mock_request.return_value = mock_response

        # First request
        response1 = reqcache.get("https://example.com/data", cache=True, cache_dir=temp_cache_dir)
        assert mock_request.call_count == 1

        # Second request should use cache
        response2 = reqcache.get("https://example.com/data", cache=True, cache_dir=temp_cache_dir)
        assert mock_request.call_count == 1  # No additional network call
        assert response2.text == "original data"

    @patch('reqcache.requests.request')
    def test_all_http_methods_supported(self, mock_request, temp_cache_dir):
        """All standard HTTP methods should be supported."""
        mock_response = create_mock_response(status_code=200)
        mock_request.return_value = mock_response

        methods = [
            reqcache.get,
            reqcache.post,
            reqcache.put,
            reqcache.delete,
            reqcache.patch,
            reqcache.head,
            reqcache.options,
        ]

        for method in methods:
            method("https://example.com/test", cache=True, cache_dir=temp_cache_dir)

        # Should have made all requests
        assert mock_request.call_count == len(methods)

    @patch('reqcache.requests.request')
    def test_request_params_preserved(self, mock_request, temp_cache_dir):
        """Request parameters should be passed through to requests library."""
        mock_response = create_mock_response(status_code=200)
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token"}
        timeout = 30
        params = {"key": "value"}

        reqcache.get(
            "https://example.com/api",
            cache=True,
            cache_dir=temp_cache_dir,
            headers=headers,
            timeout=timeout,
            params=params,
        )

        # Check that parameters were passed to requests.request
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["headers"] == headers
        assert call_kwargs["timeout"] == timeout
        assert call_kwargs["params"] == params


class TestCacheUtilities:
    """Tests for cache management utilities."""

    def test_clear_cache(self, temp_cache_dir):
        """clear_cache should delete all cache files."""
        # Create some cache files
        reqcache._ensure_cache_dir(temp_cache_dir)
        for i in range(5):
            cache_file = Path(temp_cache_dir) / f"test_{i}.pkl"
            cache_file.write_bytes(pickle.dumps({"test": i}))

        # Clear cache
        deleted_count = reqcache.clear_cache(temp_cache_dir)

        assert deleted_count == 5
        assert len(list(Path(temp_cache_dir).glob("*.pkl"))) == 0

    def test_clear_nonexistent_cache(self, temp_cache_dir):
        """Clearing non-existent cache should return 0."""
        deleted_count = reqcache.clear_cache(temp_cache_dir)
        assert deleted_count == 0

    def test_get_cache_info_empty(self, temp_cache_dir):
        """Cache info for non-existent cache."""
        info = reqcache.get_cache_info(temp_cache_dir)

        assert info["exists"] is False
        assert info["total_files"] == 0
        assert info["total_size_bytes"] == 0

    def test_get_cache_info_with_entries(self, temp_cache_dir):
        """Cache info should report statistics correctly."""
        mock_response = create_mock_response(status_code=200)

        # Create valid cache entries
        for i in range(3):
            reqcache._save_to_cache(f"key_{i}", mock_response, 3600, temp_cache_dir)

        # Create expired entry
        reqcache._save_to_cache("expired_key", mock_response, -1, temp_cache_dir)

        info = reqcache.get_cache_info(temp_cache_dir)

        assert info["exists"] is True
        assert info["total_files"] == 4
        assert info["valid_entries"] == 3
        assert info["expired_entries"] == 1
        assert info["total_size_bytes"] > 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('reqcache.requests.request')
    def test_empty_response_cached(self, mock_request, temp_cache_dir):
        """Empty responses should be cacheable."""
        mock_response = create_mock_response(status_code=204, text="")
        mock_request.return_value = mock_response

        response = reqcache.get("https://example.com/empty", cache=True, cache_dir=temp_cache_dir)

        assert response.status_code == 204
        assert response.text == ""

        # Should be in cache
        cache_files = list(Path(temp_cache_dir).glob("*.pkl"))
        assert len(cache_files) == 1

    @patch('reqcache.requests.request')
    def test_binary_response_cached(self, mock_request, temp_cache_dir):
        """Binary responses should be cacheable."""
        mock_response = create_mock_response(
            status_code=200,
            content=b"\x00\x01\x02\x03\xff"
        )
        mock_request.return_value = mock_response

        response = reqcache.get("https://example.com/binary", cache=True, cache_dir=temp_cache_dir)

        assert response.content == b"\x00\x01\x02\x03\xff"

    def test_corrupted_cache_file_ignored(self, temp_cache_dir):
        """Corrupted cache file should be treated as cache miss."""
        reqcache._ensure_cache_dir(temp_cache_dir)

        # Create corrupted cache file
        cache_file = Path(temp_cache_dir) / "corrupted.pkl"
        cache_file.write_bytes(b"not valid pickle data")

        # Should return None (cache miss)
        result = reqcache._load_from_cache("corrupted", temp_cache_dir)
        assert result is None

    @patch('reqcache.requests.request')
    def test_large_response_cached(self, mock_request, temp_cache_dir):
        """Large responses should be cacheable."""
        mock_response = create_mock_response(
            status_code=200,
            text="x" * 1000000  # 1MB of data
        )
        mock_request.return_value = mock_response

        response = reqcache.get("https://example.com/large", cache=True, cache_dir=temp_cache_dir)

        # Should be cached
        cached_response = reqcache.get(
            "https://example.com/large", cache=True, cache_dir=temp_cache_dir
        )
        assert len(cached_response.text) == 1000000
        assert mock_request.call_count == 1  # Only one network request

    @patch('reqcache.requests.request')
    def test_error_response_cached(self, mock_request, temp_cache_dir):
        """Error responses (4xx, 5xx) should also be cacheable."""
        mock_response = create_mock_response(status_code=404, text="Not Found")
        mock_request.return_value = mock_response

        response1 = reqcache.get("https://example.com/notfound", cache=True, cache_dir=temp_cache_dir)
        response2 = reqcache.get("https://example.com/notfound", cache=True, cache_dir=temp_cache_dir)

        assert response1.status_code == 404
        assert response2.status_code == 404
        assert mock_request.call_count == 1  # Cached


class TestIntegration:
    """Integration tests with real HTTP requests."""

    def test_real_request_with_httpbin(self, temp_cache_dir):
        """Test with real HTTP request to httpbin.org."""
        url = "https://httpbin.org/uuid"

        # First request
        response1 = reqcache.get(url, cache=True, cache_dir=temp_cache_dir)
        uuid1 = response1.json()["uuid"]

        # Second request should return cached response (same UUID)
        response2 = reqcache.get(url, cache=True, cache_dir=temp_cache_dir)
        uuid2 = response2.json()["uuid"]

        assert uuid1 == uuid2  # Same response from cache

        # Without cache, should get different UUID
        response3 = reqcache.get(url, cache=False)
        uuid3 = response3.json()["uuid"]

        assert uuid3 != uuid1  # Different response

    def test_cache_with_query_params(self, temp_cache_dir):
        """Test caching with query parameters."""
        base_url = "https://httpbin.org/get"

        # Different query params should be cached separately
        response1 = reqcache.get(
            base_url, params={"foo": "bar"}, cache=True, cache_dir=temp_cache_dir
        )
        response2 = reqcache.get(
            base_url, params={"foo": "baz"}, cache=True, cache_dir=temp_cache_dir
        )

        args1 = response1.json()["args"]
        args2 = response2.json()["args"]

        assert args1 == {"foo": "bar"}
        assert args2 == {"foo": "baz"}

        # Should have 2 cache files
        cache_files = list(Path(temp_cache_dir).glob("*.pkl"))
        assert len(cache_files) == 2
