"""Integration tests for memory — 多轮对话记忆验证"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)

from unittest.mock import MagicMock, patch

from app.core.memory import ConversationMemory, clear_memory, get_memory


class TestMemoryIntegration:
    def test_session_isolation(self):
        mem1 = get_memory("session_1")
        mem2 = get_memory("session_2")
        mem1.add_round("hello from 1", "hi 1")
        mem2.add_round("hello from 2", "hi 2")

        context1 = mem1.get_context()
        context2 = mem2.get_context()
        assert "hello from 1" in str(context1)
        assert "hello from 2" in str(context2)
        assert "hello from 2" not in str(context1)

        clear_memory("session_1")
        clear_memory("session_2")

    def test_get_memory_creates_once(self):
        mem1 = get_memory("test_session")
        mem2 = get_memory("test_session")
        assert mem1 is mem2
        clear_memory("test_session")

    def test_clear_memory_removes(self):
        mem = get_memory("temp_session")
        mem.add_round("q1", "a1")
        clear_memory("temp_session")
        mem2 = get_memory("temp_session")
        assert len(mem2.full_history) == 0

    @patch("app.core.memory.create_llm")
    def test_multiple_rounds_compress(self, mock_create_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "用户询问了多个乐高产品，偏好消防车和太空主题。"
        mock_create_llm.return_value = mock_llm

        mem = ConversationMemory(max_recent=2, max_total=6)
        for i in range(10):
            mem.add_round(f"Q{i}: 推荐乐高", f"A{i}: 推荐XXX")
        assert len(mem.full_history) <= 6

    def test_real_memory_session_flow(self):
        """模拟真实对话流"""
        mem = get_memory("integration_session")
        mem.add_round("你好", "你好呀，我是小砖家！")
        mem.add_round("推荐消防车", "推荐消防指挥车和市中心消防队...")
        mem.add_round("第一个多少钱", "消防指挥车是$59.99")
        context = mem.get_context()
        assert len(context) >= 6
        clear_memory("integration_session")

    def test_recent_user_messages_preserve_order(self):
        mem = ConversationMemory()
        mem.add_round("q1", "a1")
        mem.add_round("q2", "a2")
        mem.add_round("q3", "a3")
        user_msgs = mem.get_recent_user_messages(count=2)
        assert user_msgs == ["q2", "q3"]

    def test_add_messages_batch(self):
        mem = ConversationMemory()
        from langchain_core.messages import HumanMessage, AIMessage
        mem.add_messages([
            HumanMessage(content="q1"),
            AIMessage(content="a1"),
            HumanMessage(content="q2"),
            AIMessage(content="a2"),
        ])
        assert len(mem.full_history) == 4
