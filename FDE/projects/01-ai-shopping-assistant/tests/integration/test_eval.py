"""Integration tests for evaluation modules — 召回评测"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)


def _chroma_has_data():
    try:
        from app.vector_store.chroma_store import ChromaStore
        return ChromaStore().count() > 0
    except Exception:
        return False


pytestmark = pytest.mark.vector


@pytest.mark.skipif(not _chroma_has_data(), reason="ChromaDB has no data")
class TestRecallEvaluation:
    def test_evaluate_basic(self):
        from scripts.eval_recall import evaluate
        from app.rag.chain import RAGChain

        chain = RAGChain()
        result = evaluate(chain, k=4)
        assert "hit_rate" in result
        assert "mrr" in result
        assert "precision" in result
        assert "details" in result
        assert result["total_cases"] > 0

    def test_eval_cases_cover_common_scenarios(self):
        from scripts.eval_recall import EVAL_CASES
        assert len(EVAL_CASES) > 0
        for case in EVAL_CASES:
            assert "query" in case
            assert "desc" in case
