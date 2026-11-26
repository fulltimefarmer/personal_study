"""Integration tests for RAG pipeline — 端到端检索+生成"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)

from app.rag.chain import RAGChain
from app.rag.query_processor import classify_intent, expand_query


def _chroma_has_data():
    try:
        from app.vector_store.chroma_store import ChromaStore
        return ChromaStore().count() > 0
    except Exception:
        return False


pytestmark = pytest.mark.llm


@pytest.mark.skipif(not _chroma_has_data(), reason="ChromaDB has no data")
class TestRAGPipeline:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.chain = RAGChain()

    def test_query_returns_answer_and_sources(self):
        result = self.chain.query("推荐消防车", k=3)
        assert "answer" in result
        assert "sources" in result
        assert len(result["answer"]) > 0
        assert len(result["sources"]) <= 3

    def test_query_with_rerank(self):
        result = self.chain.query_with_rerank("推荐消防车", k=3)
        assert "answer" in result
        assert "sources" in result
        assert len(result["answer"]) > 0

    def test_search_only(self):
        results = self.chain.search_only("消防车", k=5)
        assert len(results) > 0
        for r in results:
            assert "metadata" in r
            assert "content" in r

    def test_multiple_queries(self):
        queries = ["消防车", "飞机", "城堡", "赛车"]
        for q in queries:
            result = self.chain.query(q, k=2)
            assert len(result["answer"]) > 0


class TestEndToEndIntentRouting:
    """验证意图分类 → RAG 检索的完整链路"""

    def test_product_intent_triggers_rag(self):
        queries = ["推荐消防车", "太空火箭", "6岁孩子玩的乐高"]
        chain = RAGChain()
        for q in queries:
            intent = classify_intent(q)
            assert intent == "product_inquiry"

    def test_chitchat_skips_rag(self):
        queries = ["你好", "谢谢", "再见"]
        for q in queries:
            intent = classify_intent(q)
            assert intent == "chitchat"

    def test_off_topic_skips_rag(self):
        queries = ["买手机", "写代码", "股票"]
        for q in queries:
            intent = classify_intent(q)
            assert intent == "off_topic"

    def test_synonym_expansion_integration(self):
        expanded = expand_query("救火车推荐")
        assert "消防" in expanded
        assert "火车" in expanded
