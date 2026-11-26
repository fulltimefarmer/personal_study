"""Unit tests for ConversationMemory — 两级记忆架构"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.memory import ConversationMemory


class TestConversationMemory:
    def test_init_defaults(self):
        mem = ConversationMemory()
        assert mem.session_id
        assert mem.max_recent == 10
        assert mem.max_total == 30
        assert mem.summary == ""
        assert mem.full_history == []

    def test_add_round(self):
        mem = ConversationMemory()
        mem.add_round("你好", "你好呀")
        assert len(mem.full_history) == 2
        assert isinstance(mem.full_history[0], HumanMessage)
        assert isinstance(mem.full_history[1], AIMessage)
        assert mem.full_history[0].content == "你好"
        assert mem.full_history[1].content == "你好呀"

    def test_get_context_no_summary(self):
        mem = ConversationMemory()
        mem.add_round("你好", "你好呀")
        mem.add_round("消防车推荐", "推荐这款...")
        context = mem.get_context()
        assert len(context) == 4

    def test_sliding_window_respects_max_recent(self):
        mem = ConversationMemory(max_recent=2)
        for i in range(10):
            mem.add_round(f"q{i}", f"a{i}")
        context = mem.get_context()
        assert len(context) <= 2

    def test_compression_triggers_on_threshold(self):
        mem = ConversationMemory(max_recent=2, max_total=4)
        messages = []
        for i in range(5):
            messages.append(HumanMessage(content=f"q{i}"))
            messages.append(AIMessage(content=f"a{i}"))
        mem.add_messages(messages)

        assert len(mem.full_history) <= 4

    def test_get_recent_user_messages(self):
        mem = ConversationMemory()
        mem.add_round("q1", "a1")
        mem.add_round("q2", "a2")
        mem.add_round("q3", "a3")
        user_msgs = mem.get_recent_user_messages(count=2)
        assert user_msgs == ["q2", "q3"]

    def test_clear(self):
        mem = ConversationMemory()
        mem.add_round("q1", "a1")
        mem.summary = "some summary"
        mem.clear()
        assert mem.full_history == []
        assert mem.summary == ""

    def test_add_message_single(self):
        mem = ConversationMemory()
        mem.add_message(HumanMessage(content="hi"))
        assert len(mem.full_history) == 1

    def test_messages_to_text(self):
        msgs = [HumanMessage(content="你好"), AIMessage(content="你好呀")]
        text = ConversationMemory._messages_to_text(msgs)
        assert "[用户] 你好" in text
        assert "[助手] 你好呀" in text

    def test_fallback_summary(self):
        msgs = [HumanMessage(content="q1"), HumanMessage(content="q2")]
        result = ConversationMemory._fallback_summary(msgs)
        assert "q1" in result
        assert "q2" in result

    def test_fallback_summary_empty(self):
        msgs = [AIMessage(content="")]
        result = ConversationMemory._fallback_summary(msgs)
        assert "对话记录" in result

    @patch("app.core.memory.create_llm")
    def test_summarize_with_llm(self, mock_create_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "用户问了关于乐高推荐的问题，倾向于消防车系列。"
        mock_create_llm.return_value = mock_llm

        mem = ConversationMemory()
        msgs = [
            HumanMessage(content="推荐消防车"),
            AIMessage(content="这里有一些消防车推荐"),
        ]
        summary = mem._summarize(msgs)
        assert "消防" in summary

    @patch("app.core.memory.create_llm")
    def test_summarize_fallback_on_llm_failure(self, mock_create_llm):
        mock_create_llm.side_effect = Exception("LLM unavailable")

        mem = ConversationMemory()
        msgs = [HumanMessage(content="推荐消防车")]
        summary = mem._summarize(msgs)
        assert "消防车" in summary
