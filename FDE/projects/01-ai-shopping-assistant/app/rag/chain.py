"""
RAG 检索链模块 — 核心问答引擎
════════════════════════════════════

架构角色：
  本模块是 RAG（Retrieval-Augmented Generation）管道的核心执行层。
  它协调三个关键环节：向量检索 → 上下文格式化 → LLM 生成，
  将用户自然语言查询转化为包含真实商品信息的自然语言回复。

  与 agent/ 模块的关系：
  - RAGChain：固定流程（检索→格式化→生成），适合简单问答场景
  - Agent：   LLM 自主决策的多轮工具调用循环，适合复杂交互需求

核心入口：
  - RAGChain.query()         完整 RAG（检索 + 生成）
  - RAGChain.query_with_rerank()  完整 RAG + 重排序
  - RAGChain.search_only()   仅检索（用于召回评测）
  - RAGChain.stream()        流式生成（逐 token 输出，适合 SSE 推送）
"""
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from app.config import create_llm
from loguru import logger

from app.config import settings
from app.rag.query_processor import (
    detect_age_intent,
    detect_price_intent,
    expand_query,
)
from app.rag.query_rewriter import QueryRewriter
from app.rag.reranker import ReRanker
from app.vector_store.chroma_store import ChromaStore

RAG_SYSTEM_PROMPT = """你是一个专业的乐高积木导购助手，名叫"小砖家"。你的职责是根据商品库中的信息，帮助用户找到适合他们的乐高套装。

## 角色设定
- 用友好的语气，像一位热情的乐高店员一样与用户交流
- 用「你」称呼用户，用「我」自称

## 回复规范
1. 推荐商品时，使用以下格式清晰列出：

**推荐商品：**
1. **商品名称** (SKU: XXX)
   - 系列: XXX | 年龄: X岁+ | 价格: $XX.XX
   - 推荐理由：XXX

2. 优先推荐与用户需求最匹配的商品，并说明推荐理由
3. 如果用户没有明确需求，主动询问孩子的年龄、预算和兴趣方向
4. 回答中引用的商品信息必须来自下方"参考商品"列表，不得编造
5. 如果参考商品中没有相关信息，坦诚告知用户，并给出进一步询问的建议

参考商品：
{context}"""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", RAG_SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)


def _extractive_answer(question: str, docs: List[dict]) -> str:
    """无 LLM 时的兜底回答：直接把检索结果整理成可读文本。

    这样即使没有启动 Ollama，商品检索、引用和前端链路仍然可用。
    """
    if not docs:
        return (
            "抱歉，我暂时没有在商品库中找到匹配的乐高套装。\n"
            "可以尝试换一个关键词，或告诉我孩子的年龄、预算和兴趣方向。"
        )

    lines = [
        "（当前未连接 LLM，以下是商品库中的匹配结果）",
        f"问题：{question}",
        "",
        "**推荐商品：**",
    ]
    for index, doc in enumerate(docs, 1):
        meta = doc.get("metadata", {})
        lines.append(
            f"{index}. **{meta.get('name', 'N/A')}** "
            f"(SKU: {meta.get('sku', 'N/A')})\n"
            f"   - 系列：{meta.get('series', 'N/A')} | "
            f"年龄：{meta.get('age_min', 'N/A')}+ | "
            f"价格：${meta.get('price', 0):.2f} | "
            f"匹配度：{doc.get('score', 0):.1%}"
        )
    lines.append("\n连接 Ollama 或配置 DeepSeek 后可获得更自然的导购回答。")
    return "\n".join(lines)


def _format_docs(docs: List[dict]) -> str:
    """
    WHAT: 文档格式化 — 将向量检索结果转换为 LLM 可读的纯文本

    WHY:  ChromaDB 返回的是 dict 列表（metadata + content + score），
          而 LLM prompt 中的 {context} 占位符需要纯文本。
          必须将结构化数据序列化为人类可读格式，LLM 才能正确理解和引用。

    HOW:  遍历检索结果，逐条拼接为
          "序号. 名称 | 系列:XXX | 年龄:X+ | 价格:$XX | 匹配度:XX%" 格式。
          空结果返回警告占位文本，让 LLM 知晓检索无结果而非误以为缺少上下文。
    """
    if not docs:
        return "（暂无匹配商品）"
    lines = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get("metadata", {})
        score = doc.get("score", 0)
        lines.append(
            f"{i}. {meta.get('name', 'N/A')} "
            f"(SKU: {meta.get('sku', 'N/A')}) | "
            f"系列: {meta.get('series', 'N/A')} | "
            f"年龄: {meta.get('age_min', 'N/A')}+ | "
            f"价格: ${meta.get('price', 0):.2f} | "
            f"匹配度: {score:.2%}"
        )
    return "\n".join(lines)


class RAGChain:
    """
    WHAT: RAG 检索链 — 封装检索+生成的完整流程

    WHY:  将向量检索、上下文格式化、LLM 生成串联为一个可调用的管道对象。
           初始化时完成所有依赖注入（ChromaDB 连接、LLM 配置、LCEL 链构建），
           后续只需调用 query() 即可获得端到端回答，对外暴露简洁的 API。

    HOW:  使用 LangChain 的 LCEL（LangChain Expression Language）管道语法：
           {"context": ..., "question": ...} | prompt | llm | StrOutputParser()
           管道自动处理数据流转，从原始输入到最终文本输出的全过程。

    LCEL | 操作符深度解析（LangChain 核心概念）：
      LCEL 的 | 操作符本质是 "前一个组件的输出作为后一个组件的输入"。
      与 Unix pipe（ls | grep）类似，但处理的是结构化数据而非字节流：
      
      chain = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | RAG_PROMPT           # dict → ChatPromptValue（格式化后的提示）
        | self.llm             # ChatPromptValue → AIMessage（LLM 推理输出）
        | StrOutputParser()    # AIMessage → str（提取纯文本内容）
      )
      
      每一步的数据类型转换是 LangChain 框架自动处理的：
      - RunnablePassthrough: 原样透传输入（不做转换）
      - ChatPromptTemplate: dict → 格式化的提示模板字符串
      - ChatOpenAI.invoke(): 提示字符串 → AIMessage 对象
      - StrOutputParser: AIMessage.content → 纯文本字符串

      这个链式调用的核心优势：
      1. 声明式：代码结构即数据流向，可读性强
      2. 可组合：链可以嵌套（子链）和复用
      3. 可替换：任何组件（LLM/Prompt/Parser）可单独替换
      4. 自动批处理：invoke/batch/stream 三合一
    """

    def __init__(self, enable_rerank: bool = True) -> None:
        self.store = ChromaStore()
        self.llm = create_llm(temperature=0.7)
        self.chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )
        self.rewriter = QueryRewriter()
        self.reranker = ReRanker()
        self.enable_rerank = enable_rerank

    @staticmethod
    def _deduplicate_by_sku(results: List[dict]) -> List[dict]:
        """按 SKU 去重，保留每个 SKU 的最高分结果

        WHAT: 多粒度召回时同一 SKU 可能有多个文档（name/desc/full），
              去重后每个 SKU 只保留最高分的文档。
        WHY:  避免 LLM 在上下文中看到重复商品，
              同时用不同粒度中的最高分代表该商品的最佳匹配。
        HOW:  用 dict 以 SKU 为 key，遇重复时取 max score。
        """
        seen: dict[str, dict] = {}
        for r in results:
            sku = r.get("metadata", {}).get("sku", "")
            if not sku:
                continue
            if sku not in seen or r.get("score", 0) > seen[sku].get("score", 0):
                seen[sku] = r
        return sorted(seen.values(), key=lambda x: x.get("score", 0), reverse=True)

    def _retrieve(self, query: str, k: int | None = None) -> List[dict]:
        """
        WHAT: 向量检索 — 执行查询扩展 + 意图检测 + 自适应检索策略

        WHY:  单次裸查询的召回效果有限。通过三阶段预处理提升检索质量：
              1. 查询扩展：弥合口语与官方关键词的表达差距
              2. 意图检测：提取年龄/价格结构化过滤条件
              3. 自适应策略：有过滤条件时用混合搜索（语义+元数据过滤），
                 否则用纯语义搜索，实现按需优化。

        HOW:  先调用 query_processor 中的 expand_query、detect_age_intent、
              detect_price_intent 进行预处理，再根据是否有过滤条件
              选择 search_hybrid 或 search。结果通过 _format_docs 格式化。
        """
        expanded = expand_query(query)
        logger.debug(f"查询扩展: {query!r} → {expanded!r}")

        target_age = detect_age_intent(query)
        price_range = detect_price_intent(query)
        logger.debug(f"意图检测: age={target_age}, price={price_range}")

        if k is None:
            k = settings.top_k

        if target_age or price_range:
            results = self.store.search_hybrid(
                expanded, k=k, target_age=target_age, price_range=price_range
            )
        else:
            results = self.store.search(expanded, k=k)

        results = self._deduplicate_by_sku(results)
        return results[:k]

    # ═══ 入口 ═══
    def query(self, question: str, k: int | None = None) -> dict:
        """
        WHAT: 完整 RAG 查询 — 检索 + 生成，返回结构化答案

        WHY:  这是 RAGChain 最主要的对外接口。调用方只需传入问题文本，
          即可获得包含答案文本、商品来源列表的完整响应字典。
          返回 dict 而非纯文本，便于前端同时展示答案和引用来源。

        HOW:  三步管道：_retrieve → _format_docs → self.chain.invoke
              1. _retrieve() 执行向量检索，获取相关商品列表
              2. _format_docs() 将结果格式化为 LLM 上下文文本
              3. self.chain.invoke() 通过 LCEL 管道生成最终答案
              4. 将答案 + 商品来源打包为 dict 返回

        Returns:
            {"question": ..., "answer": ..., "sources": [{"sku":..., "name":..., "score":...}]}
        """
        docs = self._retrieve(question, k=k)
        context = _format_docs(docs)
        logger.debug(f"检索到 {len(docs)} 条结果，上下文长度: {len(context)} 字")

        try:
            answer = self.chain.invoke({"context": context, "question": question})
        except Exception as exc:  # noqa: BLE001
            # Ollama/DeepSeek 不可用时降级为“检索结果直出”，保证本地可运行。
            logger.warning(f"[rag] LLM 调用失败，使用检索结果兜底: {exc}")
            answer = _extractive_answer(question, docs)

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "sku": doc["metadata"].get("sku"),
                    "name": doc["metadata"].get("name"),
                    "score": doc.get("score", 0),
                }
                for doc in docs
            ],
        }

    def stream(self, question: str, k: int | None = None):
        """
        WHAT: 流式生成 — 逐 token 产出 LLM 回复

        WHY:  对于长回答（如推荐多个商品并逐一说明理由），全量生成延迟较高。
          流式输出让前端可以逐步渲染回答内容，用户能即时看到部分结果，
          显著提升交互体验的即时性。适合 SSE 推送场景。

        HOW:  使用 self.llm.stream() 代替 self.chain.invoke()，
          每次迭代 yield 一个 token 的文本片段。
          注意：stream 模式需提前手动格式化完整 prompt（RAG_PROMPT.format_messages），
          因为 LCEL 链的流式语义与 invoke 模式不同。

        Yields:
            str: 每次产出一个 token 的文本片段
        """
        docs = self._retrieve(question, k=k)
        context = _format_docs(docs)

        try:
            for chunk in self.llm.stream(
                RAG_PROMPT.format_messages(context=context, question=question)
            ):
                yield chunk.content
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[rag] 流式 LLM 调用失败，降级为检索结果: {exc}")
            yield _extractive_answer(question, docs)

    # ═══ 入口 ═══
    def search_only(self, query: str, k: int | None = None) -> List[dict]:
        """
        WHAT: 纯检索模式 — 只执行向量检索，不调用 LLM

        WHY:  在 RAG 系统开发和评测阶段，需要单独评估检索质量（召回率、
          精确率），而不关心 LLM 生成质量。此方法剥离了 LLM 调用，
          返回原始检索结果，可用于离线评测、结果调试和 A/B 测试。

        HOW:  直接调用 _retrieve() 返回 ChromaDB 原始检索结果列表，
          不经过 _format_docs() 格式化，也不经过 LLM 生成。

        Returns:
            List[dict]: ChromaDB 原生检索结果，每项含 metadata、content、score
        """
        return self._retrieve(query, k=k)

    # ═══ 入口 ═══ 带重排的检索
    def _retrieve_with_rerank(
        self,
        query: str,
        k: int | None = None,
        history: list | None = None,
    ) -> List[dict]:
        """带查询改写 + 重排序的高级检索管道

        WHAT: 完整的检索链：查询改写 → 查询扩展 → 意图检测 → 向量检索 → LLM 重排序
        WHY:  单次检索精度有限，通过流水线逐步提升结果质量：
              1. 改写解决指代问题
              2. 扩展解决同义词问题
              3. 意图提取结构化条件
              4. 重排用 LLM 甄别最相关候选
        HOW:  顺序调用 rewriter → expand → detect → search → rerank
        """
        if k is None:
            k = settings.top_k

        rewritten = self.rewriter.rewrite(query, history)

        expanded = expand_query(rewritten)
        logger.debug(f"查询扩展: {rewritten!r} → {expanded!r}")

        target_age = detect_age_intent(rewritten)
        price_range = detect_price_intent(rewritten)

        candidate_k = k * 3
        if target_age or price_range:
            results = self.store.search_hybrid(
                expanded, k=candidate_k, target_age=target_age, price_range=price_range
            )
        else:
            results = self.store.search(expanded, k=candidate_k)

        results = self._deduplicate_by_sku(results)

        if self.enable_rerank and len(results) > k:
            results = self.reranker.rerank(rewritten, results, top_k=k)

        return results

    # ═══ 入口 ═══
    def query_with_rerank(
        self,
        question: str,
        k: int | None = None,
        history: list | None = None,
    ) -> dict:
        """带改写+重排的完整 RAG 查询

        WHAT:  高级 RAG 管道 — 查询改写 + 意图检测 + 向量检索 + LLM 重排 + 生成
        WHY:   生产环境推荐使用此方法，相比基础 query() 提供更高的检索精度。
        HOW:   使用 _retrieve_with_rerank 获取精排候选 → _format_docs → LLM 生成
        """
        docs = self._retrieve_with_rerank(question, k=k, history=history)
        context = _format_docs(docs)
        logger.debug(f"检索+重排 → {len(docs)} 条结果")

        answer = self.chain.invoke({"context": context, "question": question})

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "sku": doc["metadata"].get("sku"),
                    "name": doc["metadata"].get("name"),
                    "score": doc.get("score", 0),
                    "rerank_detail": doc.get("rerank_detail"),
                }
                for doc in docs
            ],
        }
