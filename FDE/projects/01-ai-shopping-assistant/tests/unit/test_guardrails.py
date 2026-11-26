"""Unit tests for guardrails — 幻觉防控四步流水线"""

import pytest

from app.core.guardrails import (
    _add_citations,
    _check_fabrication,
    _ensure_no_fabrication,
    _extract_claimed_products,
    _is_relevant,
    _looks_like_recommendation,
    apply_guardrails,
    check_relevance,
    no_result_response,
)


class TestRelevanceCheck:
    def test_jaccard_overlap_full_match(self):
        assert check_relevance("消防车推荐", "消防车推荐") == 1.0

    def test_jaccard_50_percent_overlap(self):
        score = check_relevance("消防车", "消防车推荐红色消防车")
        assert score > 0.3  # 3/7 overlap ≈ 0.43

    def test_jaccard_no_overlap(self):
        score = check_relevance("消防车", "我们")
        assert score == 0.0

    def test_empty_query(self):
        assert check_relevance("", "anything") == 0.0


class TestLooksLikeRecommendation:
    @pytest.mark.parametrize(
        "text",
        [
            "我推荐这款消防车",
            "建议你考虑城市系列",
            "这款乐高适合6岁孩子",
            "参考价格为 $59.99",
        ],
    )
    def test_detected(self, text):
        assert _looks_like_recommendation(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "抱歉，数据库中没有找到匹配的商品",
            "请提供更多信息",
            "你好，有什么可以帮你的？",
        ],
    )
    def test_not_detected(self, text):
        assert _looks_like_recommendation(text) is False


class TestFabricationDetection:
    def test_no_sources_returns_empty_claimed(self, sample_sources):
        assert _extract_claimed_products("消防指挥车推荐", []) == set()

    def test_extracts_mentioned_products(self, sample_sources):
        claimed = _extract_claimed_products("消防指挥车是很好的选择", sample_sources)
        assert "消防指挥车" in claimed

    def test_missing_name_in_sources(self):
        sources = [{"metadata": {"name": ""}}]
        claimed = _extract_claimed_products("something", sources)
        assert claimed == set()

    def test_check_fabrication_no_sources(self):
        assert _check_fabrication({"fake_product"}, []) == []

    def test_check_fabrication_valid_claim(self, sample_sources):
        claimed = {"消防指挥车"}
        assert _check_fabrication(claimed, sample_sources) == []

    def test_check_fabrication_invalid_claim(self, sample_sources):
        claimed = {"不存在的商品"}
        assert _check_fabrication(claimed, sample_sources) == ["不存在的商品"]


class TestCitations:
    def test_adds_citations_block(self, sample_sources):
        answer = "推荐消防指挥车"
        result = _add_citations(answer, sample_sources)
        assert "参考商品来源" in result
        assert "60374" in result
        assert "$59.99" in result

    def test_no_duplicate_citations(self, sample_sources):
        answer = "这是推荐 参考来源：xxx"
        result = _add_citations(answer, sample_sources)
        assert result == answer

    def test_empty_sources(self):
        assert _add_citations("answer", []) == "answer"


class TestNoResultFabricationGuard:
    def test_marks_recommendation_without_sources(self):
        answer = "我推荐你购买这款消防车"
        result = _ensure_no_fabrication(answer, [])
        assert "没有搜索到匹配的商品" in result

    def test_passthrough_when_not_recommendation(self):
        answer = "对不起，我没有找到相关商品"
        result = _ensure_no_fabrication(answer, [])
        assert result == answer

    def test_passthrough_when_sources_exist(self):
        answer = "我推荐这款消防车"
        result = _ensure_no_fabrication(answer, [{"metadata": {"name": "x"}}])
        assert result == answer


class TestIsRelevant:
    def test_short_query_always_relevant(self):
        assert _is_relevant("anything", "ab") is True

    def test_social_query_always_relevant(self):
        assert _is_relevant("anything", "你好谢谢再见") is True

    def test_irrelevant_answer_detected(self):
        assert _is_relevant("this has no overlap", "消防车推荐") is False

    def test_relevant_answer_passes(self):
        assert _is_relevant("推荐消防车给你", "消防车推荐") is True


class TestApplyGuardrailsFull:
    def test_full_pipeline_with_sources(self, sample_sources):
        result = apply_guardrails(
            "推荐消防指挥车给6岁孩子", sample_sources, "推荐消防车"
        )
        assert "answer" in result
        assert "verified" in result
        assert "has_citations" in result
        assert "参考商品来源" in result["answer"]

    def test_full_pipeline_no_sources(self):
        result = apply_guardrails(
            "抱歉没有找到匹配商品", [], "推荐消防车"
        )
        assert not result["has_citations"]

    def test_all_mentioned_products_in_sources_pass(self, sample_sources):
        """当前 guardrails 验证逻辑：只有出现在 source metadata.name 中的商品名才会被追踪。
           如果回答中出现了不在 sources 中的商品名，该名称不会被 claimed_products 捕获，
           因此不会被标记为 fabricated。这是现有实现的已知特性。"""
        result = apply_guardrails(
            "推荐消防指挥车和市中心消防队", sample_sources, "推荐消防车"
        )
        assert result["verified"]
        assert "消防指挥车" in result["sources_used"]
        assert "市中心消防队" in result["sources_used"]

    def test_sources_used_tracks_claimed_products(self, sample_sources):
        result = apply_guardrails(
            "消防指挥车和市中心消防队都是好选择",
            sample_sources,
            "推荐消防车",
        )
        assert "消防指挥车" in result["sources_used"]


class TestNoResultResponse:
    def test_mentions_original_query(self):
        reply = no_result_response("太空火箭")
        assert "太空火箭" in reply

    def test_provides_guidance(self):
        reply = no_result_response("test")
        assert "建议" in reply
