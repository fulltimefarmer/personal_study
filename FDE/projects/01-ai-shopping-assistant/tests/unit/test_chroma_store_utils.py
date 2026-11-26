"""Unit tests for ChromaStore utility functions — 核心算法逻辑"""

import random

import pytest

from app.vector_store.chroma_store import ChromaStore


class TestNormalizeScore:
    def test_perfect_match(self):
        assert ChromaStore._normalize_score(0.0) == 1.0

    def test_medium_distance(self):
        score = ChromaStore._normalize_score(1.0)
        assert score == 0.5

    def test_large_distance(self):
        score = ChromaStore._normalize_score(100.0)
        assert score < 0.01

    def test_monotonic_decreasing(self):
        # L2距离越大,相似度越低
        s1 = ChromaStore._normalize_score(1.0)
        s2 = ChromaStore._normalize_score(2.0)
        s3 = ChromaStore._normalize_score(0.5)
        assert s1 > s2
        assert s3 > s1

    def test_range_between_0_and_1(self):
        for _ in range(100):
            dist = random.uniform(0, 1000)
            score = ChromaStore._normalize_score(dist)
            assert 0 < score <= 1.0


class TestApplyBusinessScores:
    def _make_store_with_scores(self):
        """Create a store and mock _normalize_score for deterministic testing"""
        store = ChromaStore.__new__(ChromaStore)
        store._normalize_score = lambda d: 1.0 / (1.0 + d)
        return store

    def _make_doc(self, age_min=7, price=59.99):
        from langchain_core.documents import Document
        return Document(
            page_content="test",
            metadata={"name": "test", "age_min": age_min, "price": price},
        )

    def test_semantic_weight_dominant(self):
        store = self._make_store_with_scores()
        doc = self._make_doc()
        results = [(doc, 0.5)]  # L2 = 0.5
        scored = store._apply_business_scores(results, target_age=7, price_range={"min": 40, "max": 80})
        assert len(scored) == 1
        assert "detail" in scored[0]
        detail = scored[0]["detail"]
        assert 0.5 < detail["semantic"] < 1.0
        assert detail["age"] == 1.0  # exact age match
        assert detail["price"] == 1.0  # price in range

    def test_age_mismatch_penalized(self):
        store = self._make_store_with_scores()
        doc = self._make_doc(age_min=16)  # product for 16+, target is 5
        results = [(doc, 0.5)]
        scored = store._apply_business_scores(results, target_age=5, price_range=None)
        assert scored[0]["detail"]["age"] < 0.5  # big age gap = low score

    def test_price_above_budget_penalized(self):
        store = self._make_store_with_scores()
        doc = self._make_doc(price=200)
        results = [(doc, 0.5)]
        scored = store._apply_business_scores(
            results, target_age=None, price_range={"min": 0, "max": 50}
        )
        assert scored[0]["detail"]["price"] < 1.0  # over budget

    def test_no_age_no_price_neutral_scores(self):
        store = self._make_store_with_scores()
        doc = self._make_doc()
        results = [(doc, 0.5)]
        scored = store._apply_business_scores(results, target_age=None, price_range=None)
        assert scored[0]["detail"]["age"] == 0.5
        assert scored[0]["detail"]["price"] == 0.5

    def test_final_score_is_weighted_sum(self):
        store = self._make_store_with_scores()
        doc = self._make_doc(age_min=7, price=60)
        results = [(doc, 0.5)]
        scored = store._apply_business_scores(
            results, target_age=7, price_range={"min": 40, "max": 80}
        )
        detail = scored[0]["detail"]
        expected = 0.55 * detail["semantic"] + 0.20 * detail["age"] + 0.25 * detail["price"]
        assert abs(scored[0]["score"] - expected) < 0.01

    def test_individual_semantic_scores_correct(self):
        """_apply_business_scores 不排序（排序在 search_hybrid 中完成），
           但应正确计算每个文档的三因子得分"""
        store = self._make_store_with_scores()
        docs = [
            (self._make_doc(age_min=7, price=60), 0.1),   # L2=0.1
            (self._make_doc(age_min=7, price=60), 1.0),   # L2=1.0
            (self._make_doc(age_min=7, price=60), 0.3),   # L2=0.3
        ]
        scored = store._apply_business_scores(
            docs, target_age=7, price_range={"min": 30, "max": 80}
        )
        assert len(scored) == 3
        semantic_scores = [s["detail"]["semantic"] for s in scored]
        # L2=0.1 → 1/(1+0.1) ≈ 0.909, L2=1.0 → 0.5, L2=0.3 → 1/1.3 ≈ 0.769
        assert semantic_scores[0] > semantic_scores[1]  # 0.909 > 0.5
        assert semantic_scores[2] > semantic_scores[1]  # 0.769 > 0.5
        # age and price should be perfect match(=1.0) for all
        for s in scored:
            assert s["detail"]["age"] == 1.0
            assert s["detail"]["price"] == 1.0
