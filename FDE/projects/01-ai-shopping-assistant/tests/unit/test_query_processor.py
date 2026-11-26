"""Unit tests for query_processor — 意图分类 / 年龄价格检测 / 同义词扩展 / 关键词提取"""

import pytest

from app.rag.query_processor import (
    INTENT_AFTER_SALES,
    INTENT_CHITCHAT,
    INTENT_OFF_TOPIC,
    INTENT_ORDER,
    INTENT_PRODUCT,
    INTENT_PROMOTION,
    classify_intent,
    detect_age_intent,
    detect_price_intent,
    expand_query,
    extract_keywords,
    get_intent_response,
    needs_deepseek_agent,
)


class TestIntentClassification:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("推荐个适合5岁孩子的乐高", INTENT_PRODUCT),
            ("消防车多少钱", INTENT_PRODUCT),
            ("有没有便宜一点的", INTENT_PRODUCT),
            ("乐高星球大战系列有哪些", INTENT_PRODUCT),
            ("女孩喜欢什么乐高", INTENT_PRODUCT),
            ("哈利波特乐高套装", INTENT_PRODUCT),
            ("太空系列有什么好玩的", INTENT_PRODUCT),
            ("生日礼物推荐", INTENT_PRODUCT),
            ("最火的乐高推荐", INTENT_PRODUCT),
            ("城堡系列有什么新款的", INTENT_PRODUCT),
        ],
    )
    def test_product_inquiry(self, query, expected):
        assert classify_intent(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("你好", INTENT_CHITCHAT),
            ("嗨", INTENT_CHITCHAT),
            ("早上好", INTENT_CHITCHAT),
            ("谢谢你的推荐", INTENT_CHITCHAT),
            ("再见", INTENT_CHITCHAT),
            ("你是谁", INTENT_CHITCHAT),
            ("你叫什么名字", INTENT_CHITCHAT),
            ("你能干什么", INTENT_CHITCHAT),
            ("hello", INTENT_CHITCHAT),
            ("hi", INTENT_CHITCHAT),
        ],
    )
    def test_chitchat(self, query, expected):
        assert classify_intent(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("帮我写个Python代码", INTENT_OFF_TOPIC),
            ("今天股票涨了没", INTENT_OFF_TOPIC),
            ("你觉得特朗普怎么样", INTENT_OFF_TOPIC),
            ("我只想买苹果手机", INTENT_OFF_TOPIC),
            ("比特币怎么买", INTENT_OFF_TOPIC),
            ("Java和Python哪个好", INTENT_OFF_TOPIC),
            ("推荐一款手机", INTENT_OFF_TOPIC),
        ],
    )
    def test_off_topic(self, query, expected):
        assert classify_intent(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("我要退货", INTENT_AFTER_SALES),
            ("怎么换货", INTENT_AFTER_SALES),
            ("退款多久到账", INTENT_AFTER_SALES),
            ("少了一个零件怎么办", INTENT_AFTER_SALES),
            ("保修多久", INTENT_AFTER_SALES),
            ("我要投诉", INTENT_AFTER_SALES),
            ("申请售后工单", INTENT_AFTER_SALES),
            ("破损了可以换吗", INTENT_AFTER_SALES),
        ],
    )
    def test_after_sales(self, query, expected):
        assert classify_intent(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("查一下我的订单", INTENT_ORDER),
            ("订单号 ORD-123", INTENT_ORDER),
            ("我的消费记录", INTENT_ORDER),
            ("查询订单", INTENT_ORDER),
            ("查我的会员积分", INTENT_ORDER),
            ("会员等级怎么查", INTENT_ORDER),
        ],
    )
    def test_order_inquiry(self, query, expected):
        assert classify_intent(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("现在有什么活动", INTENT_PROMOTION),
            ("有没有打折", INTENT_PROMOTION),
            ("优惠券怎么领", INTENT_PROMOTION),
            ("满减活动有吗", INTENT_PROMOTION),
            ("有没有促销", INTENT_PROMOTION),
            ("特价商品有哪些", INTENT_PROMOTION),
        ],
    )
    def test_promotion(self, query, expected):
        assert classify_intent(query) == expected

    def test_empty_input_returns_chitchat(self):
        assert classify_intent("") == INTENT_CHITCHAT
        assert classify_intent(" ") == INTENT_CHITCHAT

    def test_short_input(self):
        assert classify_intent("嗯") == INTENT_CHITCHAT
        assert classify_intent("ok") == INTENT_CHITCHAT
        assert classify_intent("?",) == INTENT_CHITCHAT


class TestLocalVsRemoteRouting:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("乐高是什么", False),
            ("什么是乐高积木", False),
            ("怎么拼乐高", False),
            ("如何选乐高", False),
            ("新手怎么选乐高", False),
            ("乐高适合多大年龄的孩子", False),
            ("乐高有几个系列", False),
            ("乐高有哪些种类", False),
            ("为什么乐高这么贵", False),
            ("乐高有什么优点", False),
            ("乐高的缺点", False),
        ],
    )
    def test_local_ollama_simple_questions(self, query, expected):
        assert needs_deepseek_agent(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("我要退货", True),
            ("查订单 ORD-123", True),
            ("有什么优惠活动", True),
            ("推荐适合6岁孩子的乐高", True),
            ("8+岁的消防车", True),
            ("便宜一点的积木", True),
            ("昂贵的乐高推荐", True),
            ("推荐一款消防车", True),
            ("介绍一下太空系列", True),
            ("有没有警察局套装", True),
            ("消防车多少钱", True),
            ("哪款火箭适合孩子", True),
            ("买两件消防车多少钱", True),
            ("有没有乐高消防车", True),
        ],
    )
    def test_needs_agent_complex_queries(self, query, expected):
        assert needs_deepseek_agent(query) == expected

    def test_single_keyword_no_search_pattern(self):
        assert needs_deepseek_agent("消防") is False
        assert needs_deepseek_agent("赛车") is False
        assert needs_deepseek_agent("城堡") is False

    def test_lego_only_no_agent(self):
        assert needs_deepseek_agent("乐高") is False


class TestAgePriceDetection:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("适合5岁的乐高", 5),
            ("6岁孩子玩的", 6),
            ("8+岁可以玩", 8),
            ("12岁小朋友", 12),
            ("3岁入门", 3),
            ("10 岁孩子", 10),
        ],
    )
    def test_detect_age_intent(self, query, expected):
        assert detect_age_intent(query) == expected

    @pytest.mark.parametrize("query", ["乐高积木", "消防车", "价格便宜", "没有年龄信息"])
    def test_no_age_detected(self, query):
        assert detect_age_intent(query) is None

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("便宜一点的有吗", {"max": 20}),
            ("实惠的推荐", {"max": 30}),
            ("贵的不要", {"min": 80}),
            ("高端大气的", {"min": 80}),
            ("豪华套装", {"min": 100}),
            ("中级产品", {"min": 30, "max": 80}),
        ],
    )
    def test_detect_price_intent(self, query, expected):
        assert detect_price_intent(query) == expected

    @pytest.mark.parametrize("query", ["消防车", "太空火箭", "生日礼物"])
    def test_no_price_detected(self, query):
        assert detect_price_intent(query) is None


class TestSynonymExpansion:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("救火车在哪里", "救火车在哪里 消防 火车"),
            ("我想要警车", "我想要警车 警察"),
            ("工地积木", "工地积木 工程"),
            ("列车玩具", "列车玩具 火车"),
            ("客机模型", "客机模型 飞机"),
            ("宇宙探险", "宇宙探险 太空"),
            ("骑士城堡", "骑士城堡 城堡"),
            ("武士积木", "武士积木 忍者"),
            ("海贼船", "海贼船 海盗"),
            ("悟空套装", "悟空套装 孙悟空"),
            ("竞速跑道", "竞速跑道 赛车"),
        ],
    )
    def test_expand_synonyms(self, query, expected):
        assert expand_query(query) == expected

    @pytest.mark.parametrize("query", ["乐高积木", "价格查询", "你好"])
    def test_no_expansion_needed(self, query):
        assert expand_query(query) == query

    def test_multiple_synonyms_in_one_query(self):
        result = expand_query("警车和消防车")
        assert "警察" in result
        assert "消防" in result


class TestKeywordExtraction:
    def test_extracts_meaningful_keywords(self):
        result = extract_keywords("推荐消防车")
        assert "推荐消防车" in result or "消防车" in result

    def test_filters_stop_words(self):
        result = extract_keywords("我想买一个乐高")
        assert "想" not in result
        assert "买" not in result
        assert "一个" not in result

    def test_removes_single_char_words(self):
        result = extract_keywords("我的")
        assert "的" not in result


class TestIntentResponseDispatching:
    def test_chitchat_gets_template_reply(self):
        reply = get_intent_response(INTENT_CHITCHAT, "你好")
        assert reply is not None
        assert "小砖家" in reply

    def test_off_topic_gets_rejection(self):
        reply = get_intent_response(INTENT_OFF_TOPIC)
        assert reply is not None
        assert "只能回答" in reply

    def test_product_returns_none_for_agent_handling(self):
        assert get_intent_response(INTENT_PRODUCT, "推荐消防车") is None

    def test_after_sales_returns_none_for_agent_handling(self):
        assert get_intent_response(INTENT_AFTER_SALES, "我要退货") is None

    def test_order_returns_none_for_agent_handling(self):
        assert get_intent_response(INTENT_ORDER, "查订单") is None

    def test_promotion_returns_none_for_agent_handling(self):
        assert get_intent_response(INTENT_PROMOTION, "有什么活动") is None
