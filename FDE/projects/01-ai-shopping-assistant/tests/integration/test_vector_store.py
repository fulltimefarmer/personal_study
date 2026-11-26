"""Integration tests for vector store — 需要 ChromaDB 有数据"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)

from app.vector_store.chroma_store import ChromaStore
from app.data.models import ProductFilter


def _chroma_has_data():
    try:
        store = ChromaStore()
        return store.count() > 0
    except Exception:
        return False


pytestmark = pytest.mark.vector


@pytest.mark.skipif(not _chroma_has_data(), reason="ChromaDB has no data")
class TestChromaStoreIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.store = ChromaStore()

    def test_store_has_documents(self):
        assert self.store.count() > 0

    def test_semantic_search(self):
        results = self.store.search("消防车", k=5)
        assert len(results) > 0
        for r in results:
            assert "score" in r
            assert "metadata" in r
            assert "content" in r

    def test_semantic_search_returns_sorted_by_score(self):
        results = self.store.search("消防车", k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_filtered_search_by_series(self):
        pf = ProductFilter(series="城市系列")
        results = self.store.search("消防", k=5, product_filter=pf)
        for r in results:
            assert r["metadata"]["series"] == "城市系列"

    def test_filtered_search_by_age(self):
        pf = ProductFilter(max_age=5)
        results = self.store.search("乐高", k=5, product_filter=pf)
        for r in results:
            assert r["metadata"]["age_min"] <= 5

    def test_filtered_search_by_price(self):
        pf = ProductFilter(max_price=30)
        results = self.store.search("乐高", k=5, product_filter=pf)
        for r in results:
            assert r["metadata"]["price"] <= 30

    def test_hybrid_search_with_age(self):
        results = self.store.search_hybrid("消防车", k=5, target_age=5)
        assert len(results) > 0
        for r in results:
            assert "detail" in r
            assert "semantic" in r["detail"]
            assert "age" in r["detail"]

    def test_hybrid_search_with_price_range(self):
        results = self.store.search_hybrid(
            "乐高", k=5, price_range={"min": 10, "max": 50}
        )
        assert len(results) > 0
        for r in results:
            assert "detail" in r
            assert "price" in r["detail"]

    def test_get_by_ids(self):
        results = self.store.search("消防车", k=1)
        if results:
            sku = results[0]["metadata"]["sku"]
            detail = self.store.get_by_ids([sku])
            assert len(detail) == 1
            assert detail[0]["id"] == sku

    def test_get_by_nonexistent_id(self):
        results = self.store.get_by_ids(["NONEXISTENT_SKU_99999"])
        assert results == []

    def test_list_series(self):
        series = self.store.list_series()
        assert len(series) > 0
        assert all(isinstance(s, str) for s in series)

    def test_count_positive(self):
        assert self.store.count() > 0
