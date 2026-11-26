"""
查询改写器 — 指代消解与上下文补全

架构角色：RAG 管道的前置处理器，负责在向量检索前将用户的不完整/含糊
查询改写为包含完整上下文的明确查询。

典型场景：
  "那个红色的呢"  →  "有没有红色的城市系列消防车"
  "便宜一点的"    →  "有没有更便宜的消防车套装"
  "还有别的吗"    →  "还有什么其他类似的消防车套装推荐"

工作原理：
  1. 维护最近 N 轮对话历史作为上下文
  2. 用轻量级 LLM 判断是否需要改写 + 执行改写
  3. 缓存改写结果避免重复 LLM 调用（相似查询）
"""

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.config import create_llm
from loguru import logger

REWRITE_SYSTEM_PROMPT = """你是一个查询改写专家。你的任务是对用户的购物查询进行指代消解和上下文补全。

## 改写规则
1. 如果用户的查询是完整的（包含具体的商品特征描述），直接返回原查询
2. 如果用户使用了指代词（"那个""这个""它""上面那个""红色的"），根据对话历史补全
3. 如果用户说"还有别的吗""换一个""类似的有吗"，保留原兴趣方向并加上"其他类似"
4. 如果用户说"便宜一点的""贵一点的"，在原条件下添加价格调整
5. 改写后用自然语言描述，不要太生硬
6. 只输出改写后的查询文本，不要加任何解释

## 关键原则
- 改写后应为完整的新查询，可独立执行向量检索
- 保留用户的核心兴趣方向（题材、年龄、预算等）
- 不要添加用户未提及的限制条件
"""

_rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", REWRITE_SYSTEM_PROMPT),
    ("human", "对话历史：\n{history}\n\n用户最新输入：{query}\n\n改写后的查询："),
])

_COREFERENCE_MARKERS = [
    "那个", "这个", "它", "上面", "前面", "刚刚", "刚才",
    "还有别的", "还有其他", "换一个", "换一种", "类似的",
    "便宜一点", "便宜些", "贵一点", "贵些", "更便宜", "更贵",
    "有没有类似", "还有其他吗", "别的呢", "另外的",
    "红色的", "蓝色的", "黄色的", "绿色的", "黑色的", "白色的",
    "大一点的", "小一点的", "小套", "大套",
]

_REWRITE_CACHE: dict[str, str] = {}
_CACHE_MAX_SIZE = 100


class QueryRewriter:
    """查询改写器 — 指代消解 + 上下文补全

    WHAT: 接收用户查询和对话历史，判断是否需要改写，
          必要时调用 LLM 做指代消解补全。
    WHY:  多轮对话中用户经常使用指代词和省略表达，
          向量检索无法理解"那个"指代什么，需要在上游改写。
    HOW:  先用规则检测改写必要性（核心词匹配），
          命中后用轻量 LLM 生成改写后查询。

    LCEL 管道示例（LangChain 学习要点）：
      self._chain = _rewrite_prompt | self._llm | StrOutputParser()
      
      这条链与 RAGChain 中的链结构相同，但用途不同：
      - RAGChain 的链：检索上下文 + 用户问题 → 最终回答
      - QueryRewriter 的链：对话历史 + 用户查询 → 改写后的查询
      
      核心模式：同一套 LCEL 管道语法可以组装出不同功能链路。
      掌握 LCEL 后，任何 "输入→处理→输出" 的流程都能用链式表达。

    缓存策略说明：
      高频改写（相同查询反复出现）用 LRU 缓存避免重复调用 LLM。
      这是生产环境降本的常见手法——缓存命中时零 API 调用。
    """

    def __init__(self):
        self._llm = create_llm(temperature=0.0)
        self._chain = _rewrite_prompt | self._llm | StrOutputParser()

    def needs_rewrite(self, query: str) -> bool:
        """检测查询是否需要改写（规则判断，不调用 LLM）

        WHAT: 用关键词匹配判断用户是否使用了指代或省略表达。
        WHY:  避免每条查询都调用 LLM，保存计算资源。
        HOW:  检查查询中是否包含指代/省略标记词。
        """
        q = query.strip()
        if len(q) <= 3:
            return q in ("还有吗", "别的呢", "换一个", "还有呢")
        for marker in _COREFERENCE_MARKERS:
            if marker in q:
                return True
        return False

    def rewrite(
        self, query: str, history: list[BaseMessage] | None = None
    ) -> str:
        """改写查询（主入口）

        WHAT: 将可能含指代/省略的用户查询转为完整查询。
        WHY:  多轮对话 RAG 的关键前置步骤，提升检索召回率。
        HOW:  1. 规则判断是否需要改写
               2. 需要 → LLM 改写（带缓存）
               3. 不需要 → 原样返回

        Args:
            query: 用户原始查询
            history: 对话历史消息列表

        Returns:
            改写后的完整查询（或原查询）
        """
        q = query.strip()
        if not q:
            return q

        if not self.needs_rewrite(q):
            return q

        cache_key = q[:80]
        if cache_key in _REWRITE_CACHE:
            logger.debug(f"[rewriter] 缓存命中: {q!r}")
            return _REWRITE_CACHE[cache_key]

        history_text = _format_history(history) if history else "（无历史）"

        try:
            rewritten = self._chain.invoke({
                "history": history_text,
                "query": q,
            }).strip()
            if not rewritten:
                logger.warning(f"[rewriter] LLM 返回空结果，使用原查询")
                return q

            if rewritten != q:
                logger.info(f"[rewriter] 改写: {q!r} → {rewritten!r}")

            _cache_rewrite(cache_key, rewritten)
            return rewritten

        except Exception as e:
            logger.error(f"[rewriter] 改写失败: {e}")
            return q


def _format_history(messages: list[BaseMessage]) -> str:
    """格式化对话历史为可读文本"""
    lines = []
    for msg in messages[-6:]:
        role = "用户" if msg.__class__.__name__ == "HumanMessage" else "助手"
        content = str(msg.content)[:200] if msg.content else ""
        lines.append(f"[{role}] {content}")
    return "\n".join(lines) if lines else "（无历史）"


def _cache_rewrite(key: str, value: str):
    if len(_REWRITE_CACHE) >= _CACHE_MAX_SIZE:
        _REWRITE_CACHE.pop(next(iter(_REWRITE_CACHE)))
    _REWRITE_CACHE[key] = value
