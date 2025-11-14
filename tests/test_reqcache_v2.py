"""
Tests for reqcache library v2.0.0 - TTL-only API
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


@pytest.fixture(autouse=True)
def cleanup_cache():
    """Clean up cache directory before and after each test."""
    # Before test
    if Path(reqcache.DEFAULT_CACHE_DIR).exists():
        shutil.rmtree(reqcache.DEFAULT_CACHE_DIR)
    yield
    # After test
    if Path(reqcache.DEFAULT_CACHE_DIR).exists():
        shutil.rmtree(reqcache.DEFAULT_CACHE_DIR)


class TestTTLConstants:
    """Tests for TTL constants."""

    def test_ttl_constants_values(self):
        """Test TTL constant values."""
        assert reqcache.TTL_DISABLED == 0
        assert reqcache.TTL_PERMANENT == -1
        assert reqcache.TTL_ONE_DAY == 86400


class TestTTLValidation:
    """Tests for TTL parameter validation."""

    def test_invalid_ttl_negative_less_than_minus_one(self):
        """Test that TTL < -1 raises ValueError."""
        with pytest.raises(ValueError, match="cache_ttl must be -1, 0, or positive, got -2"):
            reqcache.get("https://example.com", cache_ttl=-2)

    def test_invalid_ttl_non_integer(self):
        """Test that non-integer TTL raises ValueError."""
        with pytest.raises(ValueError, match="cache_ttl must be an integer, got str"):
            reqcache.get("https://example.com", cache_ttl="invalid")

        with pytest.raises(ValueError, match="cache_ttl must be an integer, got float"):
            reqcache.get("https://example.com", cache_ttl=3.14)

    def test_valid_ttl_values(self):
        """Test that valid TTL values don't raise errors."""
        # These should not raise any errors
        reqcache.get("https://example.com", cache_ttl=reqcache.TTL_DISABLED)
        reqcache.get("https://example.com", cache_ttl=reqcache.TTL_PERMANENT)
        reqcache.get("https://example.com", cache_ttl=reqcache.TTL_ONE_DAY)
        reqcache.get("https://example.com", cache_ttl=3600)
        reqcache.get("https://example.com")  # Default TTL


class TestCacheDisabled:
    """Tests for cache disabled behavior (TTL=0)."""

    @patch('requests.request')
    def test_cache_disabled_no_cache_operations(self, mock_request):
        """Test that TTL=0 bypasses cache entirely."""
        mock_response = create_mock_response(text="test response")
        mock_request.return_value = mock_response

        # Make request with caching disabled
        response = reqcache.get("https://example.com", cache_ttl=reqcache.TTL_DISABLED)

        # Verify request was made
        mock_request.assert_called_once()

        # Verify cache directory was not created
        assert not Path(reqcache.DEFAULT_CACHE_DIR).exists()

    @patch('requests.request')
    def test_cache_disabled_multiple_calls(self, mock_request):
        """Test that disabled caching always makes network requests."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return create_mock_response(text=f"response {call_count}")

        mock_request.side_effect = side_effect

        # Make multiple requests with caching disabled
        response1 = reqcache.get("https://example.com", cache_ttl=0)
        response2 = reqcache.get("https://example.com", cache_ttl=0)

        # Both should make network requests
        assert call_count == 2
        assert response1.text == "response 1"
        assert response2.text == "response 2"


class TestCacheEnabled:
    """Tests for cache enabled behavior."""

    @patch('requests.request')
    def test_default_caching_enabled(self, mock_request):
        """Test that caching is enabled by default."""
        mock_response = create_mock_response(text="cached response")
        mock_request.return_value = mock_response

        # First request
        response1 = reqcache.get("https://example.com")
        assert response1.text == "cached response"
        assert mock_request.call_count == 1

        # Second request should use cache
        response2 = reqcache.get("https://example.com")
        assert response2.text == "cached response"
        assert mock_request.call_count == 1  # No additional calls

        # Verify cache directory was created
        assert Path(reqcache.DEFAULT_CACHE_DIR).exists()
        cache_files = list(Path(reqcache.DEFAULT_CACHE_DIR).glob("*.pkl"))
        assert len(cache_files) == 1

    @patch('requests.request')
    def test_custom_ttl_caching(self, mock_request):
        """Test caching with custom TTL."""
        mock_response = create_mock_response(text="cached response")
        mock_request.return_value = mock_response

        # Request with 1-hour TTL
        response = reqcache.get("https://example.com", cache_ttl=3600)
        assert response.text == "cached response"
        assert mock_request.call_count == 1

        # Second request should use cache
        response2 = reqcache.get("https://example.com", cache_ttl=3600)
        assert response2.text == "cached response"
        assert mock_request.call_count == 1

    @patch('requests.request')
    def test_permanent_caching(self, mock_request):
        """Test permanent caching (TTL=-1)."""
        mock_response = create_mock_response(text="permanent response")
        mock_request.return_value = mock_response

        # Request with permanent cache
        response1 = reqcache.get("https://example.com", cache_ttl=reqcache.TTL_PERMANENT)
        assert response1.text == "permanent response"
        assert mock_request.call_count == 1

        # Second request should use cache
        response2 = reqcache.get("https://example.com", cache_ttl=reqcache.TTL_PERMANENT)
        assert response2.text == "permanent response"
        assert mock_request.call_count == 1

        # Verify cache data has TTL=-1
        cache_files = list(Path(reqcache.DEFAULT_CACHE_DIR).glob("*.pkl"))
        assert len(cache_files) == 1

        with open(cache_files[0], 'rb') as f:
            cache_data = pickle.load(f)
        assert cache_data['ttl'] == reqcache.TTL_PERMANENT

    @patch('requests.request')
    def test_cache_expiration(self, mock_request):
        """Test that cache expires correctly."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return create_mock_response(text=f"response {call_count}")

        mock_request.side_effect = side_effect

        # Request with very short TTL (1 second)
        response1 = reqcache.get("https://example.com", cache_ttl=1)
        assert response1.text == "response 1"
        assert call_count == 1

        # Immediate second request should use cache
        response2 = reqcache.get("https://example.com", cache_ttl=1)
        assert response2.text == "response 1"
        assert call_count == 1

        # Wait for cache to expire
        time.sleep(1.1)

        # Next request should trigger new network request
        response3 = reqcache.get("https://example.com", cache_ttl=1)
        assert response3.text == "response 2"
        assert call_count == 2


class TestHTTPMethods:
    """Tests for all HTTP methods with TTL-only API."""

    @patch('requests.request')
    def test_all_http_methods_default_caching(self, mock_request):
        """Test that all HTTP methods use caching by default."""
        mock_response = create_mock_response(text="OK")
        mock_request.return_value = mock_response

        # Test all HTTP methods
        methods = [
            ('get', 'GET'),
            ('post', 'POST'),
            ('put', 'PUT'),
            ('delete', 'DELETE'),
            ('patch', 'PATCH'),
            ('head', 'HEAD'),
            ('options', 'OPTIONS')
        ]

        for method_name, http_method in methods:
            # Reset mock for each method
            mock_request.reset_mock()

            # Call the method
            method_func = getattr(reqcache, method_name)
            response = method_func("https://example.com")

            # Verify request was made
            mock_request.assert_called_once_with(http_method, "https://example.com")

            # Verify response
            assert response.text == "OK"

    @patch('requests.request')
    def test_http_methods_with_custom_ttl(self, mock_request):
        """Test HTTP methods with custom TTL values."""
        mock_response = create_mock_response(text="OK")
        mock_request.return_value = mock_response

        # Test POST with no caching
        reqcache.post("https://example.com", json={"test": "data"}, cache_ttl=0)

        # Verify request was made
        mock_request.assert_called_once_with(
            "POST",
            "https://example.com",
            json={"test": "data"}
        )

        # Test GET with custom TTL
        mock_request.reset_mock()
        reqcache.get("https://example.com", cache_ttl=7200)  # 2 hours

        # Verify request was made
        mock_request.assert_called_once_with("GET", "https://example.com")


class TestCacheUtilities:
    """Tests for cache utility functions."""

    def test_clear_cache_empty(self):
        """Test clearing empty cache."""
        result = reqcache.clear_cache()
        assert result == 0

    def test_clear_cache_with_files(self):
        """Test clearing cache with files."""
        with patch('requests.request') as mock_request:
            mock_response = create_mock_response(text="test")
            mock_request.return_value = mock_response

            # Create some cached entries
            reqcache.get("https://example.com/1")
            reqcache.get("https://example.com/2")

            # Verify cache files exist
            cache_files = list(Path(reqcache.DEFAULT_CACHE_DIR).glob("*.pkl"))
            assert len(cache_files) == 2

            # Clear cache
            result = reqcache.clear_cache()
            assert result == 2

            # Verify cache is empty
            cache_files = list(Path(reqcache.DEFAULT_CACHE_DIR).glob("*.pkl"))
            assert len(cache_files) == 0

    def test_get_cache_info_empty(self):
        """Test getting cache info for empty cache."""
        info = reqcache.get_cache_info()

        assert info['exists'] is False
        assert info['total_files'] == 0
        assert info['valid_entries'] == 0
        assert info['expired_entries'] == 0
        assert info['total_size_bytes'] == 0
        assert info['total_size_mb'] == 0

    @patch('requests.request')
    def test_get_cache_info_with_entries(self, mock_request):
        """Test getting cache info with entries."""
        mock_response = create_mock_response(text="test")
        mock_request.return_value = mock_response

        # Create cached entries
        reqcache.get("https://example.com/1", cache_ttl=3600)
        reqcache.get("https://example.com/2", cache_ttl=reqcache.TTL_PERMANENT)

        info = reqcache.get_cache_info()

        assert info['exists'] is True
        assert info['total_files'] == 2
        assert info['valid_entries'] == 2
        assert info['expired_entries'] == 0
        assert info['total_size_bytes'] > 0
        assert info['total_size_mb'] >= 0.0


class TestErrorHandling:
    """Tests for error handling."""

    @patch('requests.request')
    def test_http_error_cached(self, mock_request):
        """Test that HTTP errors are cached."""
        mock_response = create_mock_response(status_code=404, text="Not Found")
        mock_request.return_value = mock_response

        # First request
        response1 = reqcache.get("https://example.com/notfound")
        assert response1.status_code == 404
        assert mock_request.call_count == 1

        # Second request should use cache (even for 404)
        response2 = reqcache.get("https://example.com/notfound")
        assert response2.status_code == 404
        assert mock_request.call_count == 1

    @patch('requests.request')
    def test_network_error_not_cached(self, mock_request):
        """Test that network errors are not cached."""
        mock_request.side_effect = requests.RequestException("Network error")

        # Request should raise error
        with pytest.raises(requests.RequestException):
            reqcache.get("https://example.com")

        # Verify no cache files were created
        assert not Path(reqcache.DEFAULT_CACHE_DIR).exists()


class TestCacheKeyGeneration:
    """Tests for cache key generation (should still work)."""

    def test_different_urls_different_keys(self):
        """Different URLs should produce different cache keys."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/path1")
        key2 = reqcache._generate_cache_key("GET", "https://example.com/path2")
        assert key1 != key2

    def test_different_methods_different_keys(self):
        """Different HTTP methods should produce different cache keys."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/path")
        key2 = reqcache._generate_cache_key("POST", "https://example.com/path")
        assert key1 != key2

    def test_identical_requests_same_key(self):
        """Identical requests should produce same cache key."""
        key1 = reqcache._generate_cache_key("GET", "https://example.com/path", params={"a": "1"})
        key2 = reqcache._generate_cache_key("GET", "https://example.com/path", params={"a": "1"})
        assert key1 == key2