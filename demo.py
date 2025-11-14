"""
Demo script for reqcache library

This script demonstrates the basic usage of reqcache.
"""

import time
import reqcache


def main():
    print("=== reqcache Demo ===\n")

    # Example 1: Basic caching
    print("1. Basic caching demonstration:")
    print("   Making first request to httpbin.org/uuid...")
    start = time.time()
    response1 = reqcache.get("https://httpbin.org/uuid", cache=True)
    elapsed1 = time.time() - start
    uuid1 = response1.json()["uuid"]
    print(f"   Response: {uuid1}")
    print(f"   Time: {elapsed1:.2f}s (network request)\n")

    print("   Making second request to same URL...")
    start = time.time()
    response2 = reqcache.get("https://httpbin.org/uuid", cache=True)
    elapsed2 = time.time() - start
    uuid2 = response2.json()["uuid"]
    print(f"   Response: {uuid2}")
    print(f"   Time: {elapsed2:.4f}s (from cache)")
    print(f"   Same UUID? {uuid1 == uuid2}")
    print(f"   Speed improvement: {elapsed1/elapsed2:.1f}x faster!\n")

    # Example 2: Custom TTL
    print("2. Custom TTL demonstration:")
    response = reqcache.get(
        "https://httpbin.org/delay/1",
        cache=True,
        cache_ttl=3600  # Cache for 1 hour
    )
    print(f"   Cached response with 1-hour TTL: {response.status_code}\n")

    # Example 3: POST requests
    print("3. POST request caching:")
    data = {"name": "Alice", "age": 30}
    response = reqcache.post(
        "https://httpbin.org/post",
        json=data,
        cache=True
    )
    print(f"   POST request cached: {response.status_code}")
    print(f"   Data sent: {data}\n")

    # Example 4: Cache management
    print("4. Cache management:")
    info = reqcache.get_cache_info()
    print(f"   Total cache files: {info['total_files']}")
    print(f"   Valid entries: {info['valid_entries']}")
    print(f"   Cache size: {info['total_size_mb']} MB")
    print(f"   Cache location: {info.get('cache_dir', '.cache')}\n")

    # Example 5: Clear cache
    print("5. Clearing cache:")
    deleted = reqcache.clear_cache()
    print(f"   Deleted {deleted} cache files")

    info_after = reqcache.get_cache_info()
    print(f"   Cache files remaining: {info_after['total_files']}\n")

    print("=== Demo Complete ===")
    print("Check the .cache/ directory to see cached responses!")


if __name__ == "__main__":
    main()
