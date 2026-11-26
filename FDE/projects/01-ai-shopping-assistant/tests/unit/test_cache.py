"""Unit tests for cache — LRUCache and QueryCache"""

import time

import pytest

from app.core.cache import LRUCache, QueryCache


class TestLRUCache:
    def test_get_set_basic(self):
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_returns_none(self):
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_expired_ttl(self):
        cache = LRUCache(max_size=10, ttl_seconds=0.001)
        cache.set("key1", "value1")
        time.sleep(0.005)
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_access_updates_lru_order(self):
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.get("a")
        cache.set("d", 4)
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_clear(self):
        cache = LRUCache(max_size=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert len(cache) == 0
        assert cache.get("a") is None

    def test_thread_safety_basic(self):
        import threading

        cache = LRUCache(max_size=100)
        results = []

        def worker(val):
            for _ in range(10):
                cache.set(f"k{val}", val)
                cache.get(f"k{val}")
            results.append(True)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert all(results)


class TestQueryCache:
    def test_hash_normalization(self):
        cache = QueryCache()
        cache.set("  推荐消防车  ", "result")
        assert cache.get("推荐消防车") == "result"
        assert cache.get("  推荐消防车  ") == "result"

    def test_hash_case_insensitive(self):
        cache = QueryCache()
        cache.set("Recommend LEGO", "result")
        assert cache.get("recommend lego") == "result"

    def test_cache_miss(self):
        cache = QueryCache()
        assert cache.get("missing") is None

    def test_cache_hit_after_set(self):
        cache = QueryCache()
        cache.set("推荐消防车", "result text")
        assert cache.get("推荐消防车") == "result text"

    def test_stats(self):
        cache = QueryCache(max_size=100)
        cache.set("q1", "a1")
        cache.set("q2", "a2")
        stats = cache.stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 100

    def test_clear(self):
        cache = QueryCache()
        cache.set("q1", "a1")
        cache.clear()
        assert cache.get("q1") is None
