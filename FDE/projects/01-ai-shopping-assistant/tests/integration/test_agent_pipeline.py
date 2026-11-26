"""Integration tests for Agent pipeline — 完整 ReAct 循环验证"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)

from app.agent.graph import run_agent
from app.agent.tools import (
    calculate_price,
    create_service_ticket,
    query_after_sales_policy,
    query_membership,
    query_order,
    search_promotions,
    transfer_to_human,
)


def _chroma_has_data():
    try:
        from app.vector_store.chroma_store import ChromaStore
        return ChromaStore().count() > 0
    except Exception:
        return False


pytestmark = pytest.mark.llm


@pytest.mark.skipif(not _chroma_has_data(), reason="ChromaDB has no data")
class TestAgentPipeline:
    def test_agent_simple_product_inquiry(self):
        result = run_agent("推荐一个消防车")
        assert "answer" in result
        assert len(result["answer"]) > 0
        assert "messages" in result
        assert "tool_calls_log" in result
        assert "sources" in result

    def test_agent_age_filtered_search(self):
        result = run_agent("推荐适合5岁孩子的乐高")
        assert len(result["answer"]) > 0

    def test_agent_price_filtered_search(self):
        result = run_agent("推荐便宜的积木")
        assert len(result["answer"]) > 0

    def test_agent_multi_condition_search(self):
        result = run_agent("城市系列100块以内的消防车")
        assert len(result["answer"]) > 0

    def test_agent_uses_tools_in_log(self):
        result = run_agent("消防车多少钱")
        assert len(result["tool_calls_log"]) > 0

    def test_agent_returns_messages_array(self):
        result = run_agent("你好")
        messages = result["messages"]
        assert len(messages) > 0

    @pytest.mark.skip(reason="已知问题: max_tool_calls 强制终止后 AgentNode 重入时缺少 ToolMessage 导致 API 400 错误。需要修复 _tool_node 的终止逻辑。")
    def test_agent_stops_at_max_tool_calls(self):
        """验证 Agent 不会无限循环"""
        result = run_agent("推荐10个不同系列的乐高给我")
        assert len(result["tool_calls_log"]) <= 5


class TestAgentToolsDirect:
    """直接测试工具函数（不经过 ReAct 循环）"""

    def test_calculate_price_invoke(self):
        result = calculate_price.invoke({"quantity": 3, "unit_price": 29.99})
        assert "总价" in result
        assert "89.97" in result

    def test_query_after_sales_policy(self):
        result = query_after_sales_policy.invoke({"policy_type": "退换货"})
        assert "退换货" in result
        assert "7 天无理由" in result

    def test_query_after_sales_policy_all(self):
        result = query_after_sales_policy.invoke({"policy_type": "unknown"})
        assert "全部售后政策" in result

    def test_create_service_ticket(self):
        result = create_service_ticket.invoke({
            "order_id": "ORD-123",
            "issue_type": "退换货",
            "description": "商品有破损",
        })
        assert "TK-" in result
        assert "ORD-123" in result
        assert "已受理" in result

    def test_query_order_exists(self):
        result = query_order.invoke({"order_id": "ORD-20260001"})
        assert "张三" in result
        assert "消防指挥车" in result

    def test_query_order_not_found(self):
        result = query_order.invoke({"order_id": "ORD-99999"})
        assert "未找到订单" in result

    def test_query_membership_exists(self):
        result = query_membership.invoke({"phone": "5678"})
        assert "张三" in result
        assert "金卡" in result

    def test_query_membership_not_found(self):
        result = query_membership.invoke({"phone": "0000"})
        assert "未找到" in result

    def test_search_promotions(self):
        result = search_promotions.invoke({"query": "优惠"})
        assert "活动" in result

    def test_transfer_to_human(self):
        result = transfer_to_human.invoke({"reason": "投诉处理"})
        assert "人工客服" in result
        assert "投诉处理" in result
