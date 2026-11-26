"""Integration tests for graph_search tool — 需要 Neo4j 连通"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)

from app.agent.tools import graph_search, _format_graph_results


def _neo4j_available():
    try:
        from app.graph.graph_store import get_neo4j_store
        store = get_neo4j_store()
        health = store.health_check()
        return health["status"] == "connected" and health["node_count"] > 0
    except Exception:
        return False


pytestmark = pytest.mark.neo4j


@pytest.mark.skipif(not _neo4j_available(), reason="Neo4j not available or no data")
class TestGraphSearchIntegration:
    def test_recommend_by_sku(self):
        result = graph_search.invoke({"traversal_type": "recommend", "sku": "60374"})
        assert "知识图谱结果" in result
        assert "60374" not in result  # should not recommend itself

    def test_browse_by_series(self):
        result = graph_search.invoke(
            {"traversal_type": "browse", "keyword": "幻影忍者"}
        )
        assert "知识图谱结果" in result

    def test_browse_by_theme(self):
        result = graph_search.invoke(
            {"traversal_type": "browse", "keyword": "太空"}
        )
        assert "知识图谱结果" in result

    def test_browse_by_age_group(self):
        result = graph_search.invoke(
            {"traversal_type": "browse", "keyword": "5-7岁"}
        )
        assert "知识图谱结果" in result

    def test_browse_by_price_tier(self):
        result = graph_search.invoke(
            {"traversal_type": "browse", "keyword": "入门"}
        )
        assert "知识图谱结果" in result

    def test_upgrade(self):
        result = graph_search.invoke(
            {"traversal_type": "upgrade_downgrade", "sku": "60348",
             "direction": "up"}
        )
        assert "知识图谱结果" in result

    def test_downgrade(self):
        result = graph_search.invoke(
            {"traversal_type": "upgrade_downgrade", "sku": "60351",
             "direction": "down"}
        )
        assert "知识图谱结果" in result

    def test_cross_series_by_theme(self):
        result = graph_search.invoke(
            {"traversal_type": "cross_series", "theme": "太空"}
        )
        assert "知识图谱结果" in result

    def test_cross_series_by_theme_and_age(self):
        result = graph_search.invoke(
            {"traversal_type": "cross_series", "theme": "超级英雄", "age": 8}
        )
        assert "知识图谱结果" in result

    def test_nonexistent_sku_returns_empty(self):
        result = graph_search.invoke(
            {"traversal_type": "recommend", "sku": "NONEXIST"}
        )
        assert "未找到" in result


class TestGraphSearchFallback:
    def test_missing_sku_for_recommend(self):
        result = graph_search.invoke({"traversal_type": "recommend", "sku": ""})
        assert "请提供商品 SKU" in result

    def test_missing_keyword_for_browse(self):
        result = graph_search.invoke({"traversal_type": "browse", "keyword": ""})
        assert "请提供浏览关键词" in result

    def test_invalid_traversal_type(self):
        result = graph_search.invoke({"traversal_type": "invalid_type"})
        assert "不支持的查询类型" in result

    def test_graph_format_recommend(self, sample_graph_results):
        output = _format_graph_results(sample_graph_results, "recommend")
        assert "知识图谱结果（recommend）" in output

    def test_graph_format_empty(self):
        output = _format_graph_results([], "recommend")
        assert "recommend" in output
        assert output.endswith("：")


class TestGraphScenarioClassification:
    """验证哪些查询应触发 graph_search (规则层面)"""

    def _should_use_graph(self, query):
        keywords = [
            "搭配", "配套", "组合", "一起玩", "能和", "配合", "关联",
            "还有什么", "还有哪些", "还有别的",
            "别的系列", "其他系列", "不同系列", "跨系列", "有没有类似的",
            "除了",
            "便宜一点", "更便宜", "更贵", "更好的", "高端一点",
            "便宜替代", "升档", "降档", "太贵了", "预算不够",
            "系列有哪些", "主题有", "年龄段", "价位", "入门级别",
        ]
        return any(kw in query for kw in keywords)

    def test_pairing_queries_should_use_graph(self):
        assert self._should_use_graph("跟这个消防车搭配的还有什么")
        assert self._should_use_graph("有什么能和太空火箭一起玩的")
        assert self._should_use_graph("有没有配套的组件")

    def test_cross_series_queries_should_use_graph(self):
        assert self._should_use_graph("除了城市系列还有什么消防主题的")
        assert self._should_use_graph("别的系列有太空主题的吗")

    def test_upgrade_downgrade_queries_should_use_graph(self):
        assert self._should_use_graph("有没有类似的但便宜一点的")
        assert self._should_use_graph("想升级一下，有没有高端一点的")

    def test_browse_queries_should_use_graph(self):
        assert self._should_use_graph("幻影忍者系列有哪些产品")
        assert self._should_use_graph("超级英雄主题有什么好玩的")

    def test_semantic_queries_should_not_use_graph(self):
        assert not self._should_use_graph("推荐个适合5岁孩子的乐高")
        assert not self._should_use_graph("好玩的乐高")
        assert not self._should_use_graph("消防车")
        assert not self._should_use_graph("乐高是什么")
