from __future__ import annotations

from unittest import TestCase

from backend.app.infrastructure.repositories.transit_repository import LazyTrafficAccessCache


class LazyTrafficAccessCacheTests(TestCase):
    def test_builder_is_deferred_and_value_is_reused(self):
        calls = []
        value = {"station": {"h1": {"hospital_id": "h1"}}}

        def builder():
            calls.append("build")
            return value

        cache = LazyTrafficAccessCache(builder)
        self.assertEqual(calls, [])
        self.assertIs(cache.get(), value)
        self.assertIs(cache.get(), value)
        self.assertEqual(calls, ["build"])

    def test_clear_forces_a_single_rebuild_on_next_access(self):
        calls = []

        def builder():
            calls.append(len(calls) + 1)
            return {"generation": len(calls)}

        cache = LazyTrafficAccessCache(builder)
        first = cache.get()
        cache.clear()
        second = cache.get()
        self.assertEqual(first["generation"], 1)
        self.assertEqual(second["generation"], 2)
        self.assertEqual(calls, [1, 2])

    def test_cache_preserves_empty_maps(self):
        cache = LazyTrafficAccessCache(lambda: {"station": {}, "taxi": {}, "bike": {}})
        self.assertEqual(cache.get(), {"station": {}, "taxi": {}, "bike": {}})
