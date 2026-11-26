"""幻觉防控：来源标注、溯源校验、无结果兜底

═══════════════════════════════════════════════════════════
📦 架构角色：RAG 输出的质量控制层
   本模块是"生成结果的安全网关"，在所有 LLM 回答返回
   用户之前执行多重校验。它不修改业务逻辑，只做防御性
   的后处理，确保用户看到的信息是可信的。

   为什么需要？LLM 本质是预测下一个 token，不是数据库：
   - 它可能编造不存在的商品名、价格
   - 它可能把检索结果张冠李戴
   - 它可能在无检索结果时强行"推荐"
   - 它可能答非所问（偏离用户问题）
═══════════════════════════════════════════════════════════

四步防控流水线（apply_guardrails 内部执行顺序）：
  Step 1 — 无结果兜底（no-result check）：
   检索为空时检查回答是否"看起来像推荐"，
   如果像 → 添加警告前缀，提醒用户当前库中没有匹配商品。
   目的：防止 LLM 在无数据支撑时"编造推荐"。

  Step 2 — 溯源校验（verification）：
   从检索结果的 metadata 中提取商品名称列表，
   检查回答中提到的商品名是否都在这个列表中。
   不在列表中的 → 标记为 fabricated（疑似幻觉），记录警告。
   目的：确保每一个推荐的"名字"都有据可查。

  Step 3 — 来源标注（citations）：
   在回答末尾自动追加"📦 参考商品来源"区块，
   列出 Top 3 检索结果的 SKU、价格、匹配度。
   目的：增强透明度，让用户知道推荐依据。

  Step 4 — 相关性检查（relevance）：
   基于 query 和 answer 的关键词重叠度计算相关性分数，
   低于阈值（5%）且 query 长度≥3 → 标记为不相关。
   目的：拦截 LLM"自说自话""答非所问"的情况。

@tool 工具（用于 Agent 模式）：
  verify_product_claim — 验证某个商品声明是否来自检索结果
"""
from typing import Dict, List, Optional

from loguru import logger


# ═══ 入口 ═══
def apply_guardrails(
    answer: str,
    sources: List[Dict],
    query: str,
) -> Dict:
    """
    对 LLM 生成的回答应用四步幻觉防控策略。

    WHAT：RAG 回答的质量安全网关 — 输入原始回答，输出校验后的回答
    WHY：  LLM 本质是概率预测而非事实数据库，会在三个方向出错：
          (1) 编造不存在的商品名/价格（来源缺失）
          (2) 在检索为空时强行推荐（无数据支撑）
          (3) 答非所问（偏离用户问题）
          本函数四条防线分别对应这三类风险 + 透明化补充
    HOW：  依次执行四步流水线：
          Step1 无结果兜底 → Step2 溯源校验 → Step3 来源标注 → Step4 相关性检查

    Args:
        answer: LLM 原始回答文本
        sources: 检索结果列表 [{"metadata": {...}, "content": "...", "score": ...}, ...]
        query: 用户原始问题

    Returns:
        {
            "answer": str,          # 处理后的回答
            "verified": bool,       # 是否通过了溯源校验
            "has_citations": bool,  # 是否添加了来源标注
            "warnings": [str],      # 风险警告列表
            "sources_used": [str],  # 回答中实际引用的商品名称
        }
    """
    warnings: List[str] = []
    result = answer

    # 1. 无结果兜底
    if not sources:
        logger.warning("[guardrails] 检索结果为空，检查是否需要兜底")
        if _looks_like_recommendation(answer):
            warnings.append("检索为空但回答看起来像推荐，可能存在幻觉")
        result = _ensure_no_fabrication(result, sources)

    # 2. 溯源校验
    claimed_products = _extract_claimed_products(result, sources)
    fabricated = _check_fabrication(claimed_products, sources)
    if fabricated:
        warnings.append(
            f"回答中提到了未在检索结果中的商品: {', '.join(fabricated)}"
        )
        logger.warning(f"[guardrails] 疑似幻觉: {fabricated}")

    verified = len(fabricated) == 0

    # 3. 来源标注
    if sources:
        result = _add_citations(result, sources)
        has_citations = True
    else:
        has_citations = False

    # 4. 相关性检查
    if not _is_relevant(result, query):
        warnings.append("回答与问题相关性低")
        logger.warning("[guardrails] 回答可能与问题不相关")

    return {
        "answer": result,
        "verified": verified,
        "has_citations": has_citations,
        "warnings": warnings,
        "sources_used": list(claimed_products),
    }


def no_result_response(query: str) -> str:
    """
    WHAT：检索结果为空时的友好兜底回复生成器
    WHY：  不能让用户面对沉默或编造的推荐，
          需要引导用户调整搜索策略（换关键词、提供更多信息）
    HOW：  返回包含 3 条操作建议的模板文本
    """
    return (
        f'抱歉，我在商品库中没有找到与「{query}」完全匹配的乐高套装。\n\n'
        "建议您：\n"
        "1. 试试用不同的关键词描述（比如名称、颜色、题材）\n"
        "2. 告诉我孩子的年龄和预算，我来帮您推荐合适的系列\n"
        "3. 直接告诉我感兴趣的系列名称（如城市系列、科技系列、星球大战等）"
    )


def check_relevance(answer: str, query: str) -> float:
    """
    WHAT：计算回答与问题之间的相关性分数（0.0 ~ 1.0）
    WHY：  需要一个轻量级指标来快速判断 LLM 是否"答非所问"
    HOW：  将 query 和 answer 转为字符集合，计算 Jaccard 式重叠度：
          |query ∩ answer| / |query|
    """
    query_words = set(query)
    answer_words = set(answer)
    if not query_words:
        return 0.0
    overlap = query_words & answer_words
    return len(overlap) / len(query_words)


# ── 内部函数 ──────────────────────────────────────────

def _looks_like_recommendation(text: str) -> bool:
    """
    WHAT：判断一段文本是否"看起来像商品推荐"
    WHY：  无结果兜底需要区分 LLM 的两种回复：
          承认找不到（安全）vs 强行编造推荐（危险）
    HOW：  检查文本中是否包含推荐性关键词（推荐/建议/选择/这款...）
    """
    recommend_markers = [
        "推荐", "建议", "选择", "适合", "可以考虑", "这款", "价格",
        "年龄", "系列", "适用", "推荐", "不错",
    ]
    return any(marker in text for marker in recommend_markers)


def _ensure_no_fabrication(answer: str, sources: List[Dict]) -> str:
    """
    WHAT：确保无检索结果时不会给用户呈现编造的推荐
    WHY：  即使 LLM 编造了推荐内容，也可以在输出前插入免责声明
    HOW：  当 sources 为空且回答像推荐时，前置警告文本
    """
    if not sources and _looks_like_recommendation(answer):
        preamble = (
            "**注意：当前商品库中没有搜索到匹配的商品。**\n\n"
        )
        return preamble + answer
    return answer


def _extract_claimed_products(
    answer: str, sources: List[Dict]
) -> set:
    """
    WHAT：从回答中提取出实际引用的商品名称集合
    WHY：  溯源校验的前提 — 先知道 LLM 提到了哪些商品名
    HOW：  遍历 sources 的 metadata.name，检查哪些出现在 answer 文本中
    """
    if not sources:
        return set()
    source_products = {
        s.get("metadata", {}).get("name", "")
        for s in sources
        if s.get("metadata", {}).get("name")
    }
    claimed = set()
    for name in source_products:
        if name and name in answer:
            claimed.add(name)
    return claimed


def _check_fabrication(claimed: set, sources: List[Dict]) -> List[str]:
    """
    WHAT：检查声称引用的商品名是否真实存在于检索来源中
    WHY：  核心溯源逻辑 — claimed ∩ sources_names = 真实引用
          claimed - sources_names = 疑似幻觉
    HOW：  构造 sources 的名称集合，做差集运算
    """
    if not sources:
        return []
    source_names = {
        s.get("metadata", {}).get("name", "")
        for s in sources
    }
    fabricated = []
    for name in claimed:
        if name not in source_names:
            fabricated.append(name)
    return fabricated


def _add_citations(answer: str, sources: List[Dict]) -> str:
    """
    WHAT：在回答末尾自动追加"📦 参考商品来源"格式化区块
    WHY：  增强透明度，让用户知道这些推荐依据哪些检索结果
          — 同时防止重复添加（如果回答已包含"参考来源"字样则跳过）
    HOW：  取 Top 3 检索结果，列出 SKU、价格、匹配度
    """
    if not sources:
        return answer

    # 如果回答已经包含来源标记，不再重复添加
    if "参考来源" in answer or "来源：" in answer:
        return answer

    top_sources = sources[:3]
    lines = ["\n\n---\n📦 **参考商品来源**"]
    for i, s in enumerate(top_sources, 1):
        meta = s.get("metadata", {})
        name = meta.get("name", "未知")
        sku = meta.get("sku", "")
        price = meta.get("price", 0.0)
        score = s.get("score", 0)
        lines.append(
            f"{i}. **{name}** (SKU: {sku}) | ${price:.2f} | 匹配度 {score:.1%}"
        )
    return answer + "\n".join(lines)


def _is_relevant(answer: str, query: str) -> bool:
    """
    WHAT：快速判断回答是否与用户问题相关（轻量级，不调用 LLM）
    WHY：  拦截最严重的"答非所问"情况，但不过度严格
    HOW：  豁免规则：query<3字符 或 社交用语 → 自动 True
          否则调用 check_relevance() 计算字符重叠度，>5% 即为相关
    """
    q = query.replace(" ", "")
    if len(q) < 3:
        return True  # 太短不判断
    if "你好" in query or "谢谢" in query or "再见" in query:
        return True  # 社交用语
    score = check_relevance(answer, query)
    return score > 0.05
