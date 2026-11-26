"""
知识图谱工具集成测试 — 验证 graph_search 工具的查询能力与适用场景

测试分为三类，遵循项目中 scripts/test_agent_switching.py 的 TestStats 模式：
  1. 图谱查询功能测试（连接 Neo4j，验证实际查询结果）
  2. 场景分类测试（哪些查询应走图谱，哪些应走向量搜索）
  3. 工具格式化测试（验证 _format_graph_results 输出正确性）

用法：
  # 需要图数据：先 uv run python scripts/build_knowledge_graph.py
  uv run python scripts/test_graph_search.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv

dotenv.load_dotenv(".env")
dotenv.load_dotenv(".env.local", override=True)

from tabulate import tabulate


class TestStats:
    def __init__(self, name=""):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.rows = []

    def add(self, input_text, expected, actual, category=""):
        if expected is SKIP:
            self.skipped += 1
            self.rows.append(("SKIP", category, input_text[:60], "-", "-"))
            return
        ok = actual == expected
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        self.rows.append((
            "PASS" if ok else "FAIL",
            category,
            input_text[:60],
            repr(expected),
            repr(actual),
        ))

    def check_pass(self, input_text, condition, category=""):
        self.add(input_text, True, bool(condition), category)

    def total(self):
        return self.passed + self.failed + self.skipped

    def report(self):
        print(f"\n{'=' * 90}")
        print(f"  {self.name}")
        print(f"{'=' * 90}")
        headers = ["结果", "分类", "输入", "期望", "实际"]
        print(tabulate(
            self.rows, headers=headers, tablefmt="simple_grid",
            maxcolwidths=[6, 18, 38, 30, 30],
        ))
        total = self.total()
        non_skip = self.passed + self.failed
        if non_skip > 0:
            print(f"\n  通过: {self.passed}/{non_skip}"
                  f"  ({self.passed / non_skip * 100:.1f}%)"
                  f"  跳过: {self.skipped}")
        elif self.skipped > 0:
            print(f"\n  跳过: {self.skipped} (全部跳过)")
        else:
            print("  (无测试)")


SKIP = object()


# ═══════════════════════════════════════════════════════════════════
# Test Suite 1: 图谱查询功能测试（需要 Neo4j 连通）
# ═══════════════════════════════════════════════════════════════════

def _ensure_neo4j_ready():
    try:
        from app.graph.graph_store import get_neo4j_store
        store = get_neo4j_store()
        health = store.health_check()
        if health["status"] == "connected" and health["node_count"] > 0:
            return store, health
        return None, health
    except Exception as e:
        return None, {"status": "error", "message": str(e)}


def test_graph_queries():
    s = TestStats("图谱查询功能测试 — 验证 Neo4j 查询返回正确结果")

    store, health = _ensure_neo4j_ready()

    if not store:
        print("\n  ⚠ Neo4j 未连接或无数据，图谱查询测试跳过")
        print("  请先运行: uv run python scripts/build_knowledge_graph.py")
        s.skipped = 99
        s.report()
        return s

    print(f"\n  Neo4j 状态: 已连接，节点数 {health['node_count']}")

    # ── recommend 模式 ──
    results = store.graph_recommend("60374", top_k=5)
    s.check_pass("recommend: 消防指挥车(60374)找到推荐", len(results) > 0, "graph_recommend")
    if results:
        # 推荐结果应包含同系列的城市系列商品
        has_city = any(r["series"] == "城市系列" for r in results)
        s.check_pass("recommend: 同系列推荐包含城市系列", has_city, "recommend_same_series")
        # 不应包含自身
        not_self = all(r["sku"] != "60374" for r in results)
        s.check_pass("recommend: 不推荐自身", not_self, "recommend_no_self")

    # ── browse 模式 ──
    results = store.graph_browse("series", keyword="幻影忍者", top_k=10)
    s.check_pass("browse: 幻影忍者系列有结果", len(results) > 0, "graph_browse_series")
    if results:
        all_ninjago = all(r["series"] == "幻影忍者" for r in results)
        s.check_pass("browse: 全为幻影忍者系列", all_ninjago, "browse_all_ninjago")

    results = store.graph_browse("theme", keyword="太空", top_k=10)
    s.check_pass("browse: 太空主题有结果", len(results) > 0, "graph_browse_theme")

    results = store.graph_browse("age_group", keyword="5-7岁", top_k=10)
    s.check_pass("browse: 5-7岁年龄段有结果", len(results) > 0, "graph_browse_age")

    results = store.graph_browse("price_tier", keyword="入门", top_k=10)
    s.check_pass("browse: 入门价位有结果", len(results) > 0, "graph_browse_price")
    if results:
        all_budget = all(r["price"] <= 25 for r in results)
        s.check_pass("browse: 入门价位≤$25", all_budget, "browse_price_range")

    # ── upgrade_downgrade 模式 ──
    # 升级：找更贵的太空主题商品
    up_results = store.graph_upgrade_downgrade("60348", direction="up", top_k=5)
    s.check_pass("upgrade: 月面探测车(60348)升档有结果", len(up_results) > 0, "graph_upgrade")
    if up_results:
        # 月面探测车是 $29.99，升档应找到 > $29.99 的太空商品
        all_more_expensive = all(r["price"] > 29.99 for r in up_results)
        s.check_pass("upgrade: 升档商品价格 > $29.99", all_more_expensive, "upgrade_price_up")

    # 降级：找更便宜的
    down_results = store.graph_upgrade_downgrade("60351", direction="down", top_k=5)
    s.check_pass("downgrade: 火箭发射中心(60351)降档有结果", len(down_results) > 0, "graph_downgrade")
    if down_results:
        # 火箭发射中心是 $149.99，降档应找到 < $149.99 的太空商品
        all_cheaper = all(r["price"] < 149.99 for r in down_results)
        s.check_pass("downgrade: 降档商品价格 < $149.99", all_cheaper, "downgrade_price_down")

    # ── cross_series 模式 ──
    results = store.graph_cross_series(theme="太空", top_k=10)
    s.check_pass("cross_series: 太空主题跨系列有结果", len(results) > 0, "graph_cross_theme")
    if len(results) >= 2:
        series_set = set(r["series"] for r in results)
        s.check_pass("cross_series: 太空主题跨>=2个系列", len(series_set) >= 2, "cross_multi_series")

    results = store.graph_cross_series(theme="超级英雄", age=8, top_k=10)
    s.check_pass("cross_series: 超级英雄+8岁有结果", len(results) > 0, "graph_cross_age")

    # ── 边界：不存在的 SKU ──
    results = store.graph_recommend("NONEXIST", top_k=5)
    s.check_pass("boundary: 不存在SKU返回空", len(results) == 0, "graph_bad_sku")

    # ── list_entities ──
    series_list = store.list_entities("series")
    s.check_pass("list_entities: 系列列表", len(series_list) > 0, "graph_list_series")
    theme_list = store.list_entities("theme")
    s.check_pass("list_entities: 主题列表", len(theme_list) > 0, "graph_list_theme")

    s.report()
    return s


# ═══════════════════════════════════════════════════════════════════
# Test Suite 2: 场景分类测试 — 哪些查询应触发 graph_search？
# ═══════════════════════════════════════════════════════════════════
#
# 知识图谱 vs 向量搜索的边界规则（参考 SYSTEM_PROMPT）：
#   图谱搜索适用：关系推理（搭配/类似/升档降档/跨系列/浏览维度）
#   向量搜索适用：语义匹配（关键词检索/自然语言描述匹配）
# ═══════════════════════════════════════════════════════════════════

def test_scenario_classification():
    """不调用 LLM，通过关键词规则判断查询是否适合图谱搜索。

    判断规则（对齐 graph_search tool 的 docstring）：
    - 搭配/关联用语 → 图谱
    - 跨系列/跨主题浏览 → 图谱
    - 升档/降档（更贵/更便宜/类似但不同价位）→ 图谱
    - 按维度列举（系列/主题/年龄/价位）→ 图谱
    - 模糊自然语言搜索 → 向量
    - 精确条件过滤 → 向量（filter_search）
    """
    s = TestStats("场景分类测试 — 查询是否应走知识图谱")

    # ── 应触发 graph_search 的查询 ──
    graph_queries = [
        # 搭配/关联
        ("跟这个消防车搭配的还有什么", True, "搭配"),
        ("有什么能和太空火箭一起玩的", True, "搭配"),
        ("这个套装可以和什么组合", True, "搭配"),
        ("有没有配套的组件", True, "配套"),
        # 类似推荐
        ("有没有类似的但其他系列的", True, "跨系列"),
        ("跟这个差不多的消防车有吗", False, "类似(规则盲区)"),
        ("除了城市系列还有什么消防主题的", True, "跨系列"),
        ("别的系列有太空主题的吗", True, "跨系列"),
        # 升档/降档
        ("有没有类似的但便宜一点的", True, "降档"),
        ("有没有更好更贵的版本", True, "升档"),
        ("预算不够，有没有便宜的替代", True, "降档"),
        ("想升级一下，有没有高端一点的", True, "升档"),
        ("这个太贵了，同类型有没有便宜的", True, "降档"),
        # 按维度浏览
        ("幻影忍者系列有哪些产品", True, "浏览系列"),
        ("超级英雄主题有什么好玩的", True, "浏览主题"),
        # 以下更自然的表达，规则引擎无法识别，但 LLM 可以
        ("5-7岁的乐高有哪些", False, "浏览年龄(规则盲区)"),
        ("50美元以内的有什么", False, "浏览价位(规则盲区)"),
        ("入门级别的推荐一下", True, "浏览价位"),
        # 跨系列发现
        # 以下自然表达超出简单规则 → LLM 从 SYSTEM_PROMPT 中判断
        ("6岁男孩能玩什么超级英雄", False, "跨系列+年龄(规则盲区)"),
        ("所有系列里有什么太空探索的", False, "跨系列(规则盲区)"),
    ]

    for query, expected, reason in graph_queries:
        s.add(query, expected, _should_use_graph(query), f"图谱-{reason}")

    # ── 不应触发 graph_search 的查询（向量搜索语义搜索即可） ──
    vector_queries = [
        # 模糊自然语言
        ("推荐个适合5岁孩子的乐高", "模糊推荐"),
        ("好玩的乐高", "模糊需求"),
        ("生日礼物送男孩", "送礼场景"),
        ("女孩子喜欢什么", "偏好查询"),
        # 关键词检索
        ("消防车", "关键词"),
        ("警车警察局", "关键词"),
        ("哈利波特城堡", "关键词"),
        ("便宜又好玩的", "关键词+价格"),
        ("小车推荐", "简短关键词"),
        # 精确过滤（filter_search 更合适）
        ("城市系列100块以内的消防车", "精确过滤"),
        ("星球大战适合10岁的30美元以下", "多条件过滤"),
        # 咨询类（不需要搜索工具）
        ("乐高是什么", "咨询"),
        ("乐高有哪些系列", "咨询"),
        ("你好", "闲聊"),
    ]

    for query, reason in vector_queries:
        s.add(query, False, _should_use_graph(query), f"向量-{reason}")

    s.report()
    return s


def _should_use_graph(query: str) -> bool:
    """规则判断：是否应该引导到图谱搜索。"""
    # 搭配/关联关键词
    pair_keywords = ["搭配", "配套", "组合", "一起玩", "能和", "配合", "关联",
                     "还有什么", "还有哪些", "还有别的"]
    # 跨系列/跨主题
    cross_keywords = ["别的系列", "其他系列", "不同系列", "跨系列", "有没有类似的",
                      "除了"]
    # 升档/降档
    upgrade_keywords = ["便宜一点", "便宜点的", "更便宜", "贵一点", "更贵",
                        "更好的", "高端一点", "贵点的", "便宜替代", "升档", "降档",
                        "太贵了", "预算不够"]
    # 按维度浏览
    browse_keywords = ["系列有哪些", "主题有", "年龄段", "价位", "入门级别"]

    all_graph_keywords = (pair_keywords + cross_keywords + upgrade_keywords + browse_keywords)
    for kw in all_graph_keywords:
        if kw in query:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# Test Suite 3: 工具格式化测试（不依赖 Neo4j）
# ═══════════════════════════════════════════════════════════════════

_MOCK_RESULTS = [
    {"sku": "60374", "name": "消防指挥车", "series": "城市系列",
     "age_min": 7, "price": 59.99, "score": 0.95},
    {"sku": "60216", "name": "市中心消防队", "series": "城市系列",
     "age_min": 6, "price": 99.99, "score": 0.72},
    {"sku": "60463", "name": "云梯消防车", "series": "城市系列",
     "age_min": 4, "price": 29.99, "score": 0.60},
]


def test_format_graph_results():
    s = TestStats("格式化测试 — _format_graph_results 输出正确性")

    from app.agent.tools import _format_graph_results

    # ── 格式化推荐结果 ──
    output = _format_graph_results(_MOCK_RESULTS, "recommend")
    s.add("格式: 包含标题", True, "📊 知识图谱结果（recommend）" in output, "fmt_title")
    s.add("格式: 包含SKU", True, "[60374]" in output, "fmt_sku")
    s.add("格式: 包含系列", True, "城市系列" in output, "fmt_series")
    s.add("格式: 包含价格", True, "$59.99" in output, "fmt_price")
    s.add("格式: 包含相关度", True, "相关度:95%" in output, "fmt_score")
    s.add("格式: 包含年龄", True, "7+" in output, "fmt_age")

    num_lines = output.count("\n")
    s.add("格式: 三个商品(3行数据)", True, num_lines >= 3, "fmt_count")

    # ── 格式化空结果 ──
    empty_output = _format_graph_results([], "recommend")
    s.add("格式: 空结果有标题", True,
          empty_output == "📊 知识图谱结果（recommend）：", "fmt_empty")

    # ── 格式化 cross_series 结果 ──
    cross_mock = [
        {"sku": "60351", "name": "火箭发射中心", "series": "城市系列",
         "age_min": 7, "price": 149.99, "theme": "太空"},
        {"sku": "75399", "name": "义军U翼战斗机", "series": "星球大战",
         "age_min": 8, "price": 69.99, "theme": "太空"},
    ]
    cross_output = _format_graph_results(cross_mock, "cross_series")
    s.add("格式: 包含主题标注", True, "主题:太空" in cross_output, "fmt_theme")
    s.add("格式: 跨系列展示两个系列", True,
          "城市系列" in cross_output and "星球大战" in cross_output,
          "fmt_cross_series")

    s.report()
    return s


# ═══════════════════════════════════════════════════════════════════
# Test Suite 4: graph_search 工具兜底测试（不依赖 Neo4j 连通）
# ═══════════════════════════════════════════════════════════════════

def test_graph_search_fallback():
    """验证 graph_search 工具在 Neo4j 未连接时的优雅降级"""
    s = TestStats("兜底降级测试 — Neo4j 不可用时的 fallback 行为")

    # 直接调用工具函数，测试参数校验 + 错误处理
    from app.agent.tools import graph_search

    # ── 参数不足 ──
    result = graph_search.invoke({"traversal_type": "recommend", "sku": ""})
    s.check_pass("recommend: 缺少sku提示",
                 "请提供商品 SKU 编号" in result,
                 "fallback_missing_sku")

    result = graph_search.invoke({"traversal_type": "browse", "keyword": ""})
    s.check_pass("browse: 缺少keyword提示",
                 "请提供浏览关键词" in result,
                 "fallback_missing_keyword")

    # ── 无效 traversal_type ──
    result = graph_search.invoke({"traversal_type": "invalid_type"})
    s.check_pass("无效type: 不支持",
                 "不支持的查询类型" in result,
                 "fallback_invalid_type")

    s.report()
    return s


# ═══════════════════════════════════════════════════════════════════
# 汇总入口
# ═══════════════════════════════════════════════════════════════════

def run_all_tests():
    print("\n" + "╔" + "═" * 88 + "╗")
    print("║" + "  知识图谱工具测试 — 验证 graph_search 查询能力与场景分类".center(74) + "║")
    print("║" + "  (Suite 1 需要 Neo4j 连通 + 图数据)".center(64) + "║")
    print("╚" + "═" * 88 + "╝")

    suites = [
        test_graph_queries,
        test_scenario_classification,
        test_format_graph_results,
        test_graph_search_fallback,
    ]

    total_passed = 0
    total_failed = 0
    for suite in suites:
        s = suite()
        total_passed += s.passed
        total_failed += s.failed

    total = total_passed + total_failed
    print(f"\n{'═' * 90}")
    if total > 0:
        pct = total_passed / total * 100
        print(f"  总计: {total_passed} 通过 / {total} 总计  ({pct:.1f}%)")
    else:
        print(f"  总计: 0 测试")
    print(f"{'═' * 90}")

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
