"""Unit tests for agent tools — 纯逻辑工具函数（不需要外部服务）"""

from unittest.mock import MagicMock, patch

import pytest

from app.agent.tools import (
    _filter_in_stock,
    _format_graph_results,
    _format_products,
    calculate_price,
)


class TestCalculatePrice:
    def test_single_item(self):
        result = calculate_price.invoke({"quantity": 1, "unit_price": 29.99})
        assert "$29.99" in result
        assert "总价 $29.99" in result

    def test_multiple_items(self):
        result = calculate_price.invoke({"quantity": 3, "unit_price": 19.99})
        assert "总价 $59.97" in result

    def test_large_quantity(self):
        result = calculate_price.invoke({"quantity": 100, "unit_price": 1.50})
        assert "总价 $150.00" in result

    def test_zero_quantity(self):
        result = calculate_price.invoke({"quantity": 0, "unit_price": 10.00})
        assert "总价 $0.00" in result


class TestFormatProducts:
    def test_normal_results(self):
        results = [
            {
                "metadata": {
                    "sku": "60374", "name": "消防指挥车",
                    "series": "城市系列", "age_min": 7, "price": 59.99,
                },
                "score": 0.95,
            },
        ]
        output = _format_products(results)
        assert "60374" in output
        assert "消防指挥车" in output
        assert "城市系列" in output
        assert "95.0%" in output

    def test_empty_results(self):
        output = _format_products([])
        assert "未找到匹配的商品" in output

    def test_missing_metadata_fields(self):
        results = [
            {
                "metadata": {"sku": "001", "name": "test"},
                "score": 0.5,
            },
        ]
        output = _format_products(results)
        assert "[001]" in output
        assert "test" in output
        assert "$0.00" in output


class TestFormatGraphResults:
    def test_recommend_format(self, sample_graph_results):
        output = _format_graph_results(sample_graph_results, "recommend")
        assert "知识图谱结果（recommend）" in output
        assert "[60374]" in output
        assert "消防指挥车" in output
        assert "城市系列" in output
        assert "$59.99" in output
        assert "相关度:95%" in output
        assert "7+" in output

    def test_cross_series_format(self):
        results = [
            {"sku": "60351", "name": "火箭发射中心", "series": "城市系列",
             "age_min": 7, "price": 149.99, "theme": "太空"},
            {"sku": "75399", "name": "义军U翼战斗机", "series": "星球大战",
             "age_min": 8, "price": 69.99, "theme": "太空"},
        ]
        output = _format_graph_results(results, "cross_series")
        assert "主题:太空" in output
        assert "城市系列" in output
        assert "星球大战" in output

    def test_empty_results(self):
        output = _format_graph_results([], "recommend")
        assert "recommend" in output
        assert output.endswith("：")

    def test_browse_format(self, sample_graph_results):
        output = _format_graph_results(sample_graph_results, "browse")
        assert "知识图谱结果（browse）" in output


class TestFilterInStock:
    @patch("app.agent.tools.get_available_skus")
    def test_filters_out_of_stock(self, mock_get_skus):
        mock_get_skus.return_value = {"60374"}
        results = [
            {"metadata": {"sku": "60374", "name": "消防指挥车"}},
            {"metadata": {"sku": "99999", "name": "缺货商品"}},
        ]
        filtered = _filter_in_stock(results)
        assert len(filtered) == 1
        assert filtered[0]["metadata"]["sku"] == "60374"

    @patch("app.agent.tools.get_available_skus")
    def test_skip_on_error(self, mock_get_skus):
        mock_get_skus.side_effect = Exception("DB down")
        results = [{"metadata": {"sku": "001"}}]
        filtered = _filter_in_stock(results)
        assert filtered == results

    def test_empty_results(self):
        assert _filter_in_stock([]) == []
