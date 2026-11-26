"""
重排序器 — 融合检索结果二次精排

架构角色：向量检索后的精排层，位于初始召回和 LLM 生成之间。
粗排（ChromaDB 向量近似搜索）→ 重排（本模块）→ Top-K → LLM 生成。

为什么需要重排？
  向量检索使用 embedding 模型的语义相似度排序，但 embedding 模型
  是通用模型，不理解乐高领域特有的相关性判断标准。重排序用 LLM 的
  深度理解能力对候选集做精排，提升最终 top-k 的精准度。

策略选择：
  - LLM 逐条打分：用 LLM 对每个候选文档打分，最准确但较慢
  - LLM 批量排序：把所有候选给 LLM 让它排序，速度快但受上下文限制
  - 混合策略：候选数≤10 用批量排序，>10 用逐条打分（前 k*2 送 LLM 排序）

重排后的启发式增强（Score Boosting）：
  - 名称精确命中：如果商品名完全出现在 query 中，+15% 加成
  - 系列精确匹配：query 提到系列名且商品属于该系列，+10% 加成
  - 价格在合理区间：如果 query 提及价格词，符合预期的商品 +8% 加成
"""

from typing import List

from app.config import create_llm
from loguru import logger

_RERANK_SYSTEM = """你是一个搜索排序专家。你的任务是评估商品与用户搜索词的相关性。

对于每个候选商品，给出 [0.0, 1.0] 的相关性分数：
- 1.0 = 完全匹配（名称、描述与搜索意图高度一致）
- 0.7-0.9 = 高度相关（类型匹配但需微调）
- 0.4-0.6 = 部分相关（有交集但不是最优推荐）
- 0.1-0.3 = 弱相关（有关键词重合但方向不同）
- 0.0 = 完全无关

评分标准：
1. 商品名称是否包含搜索词中的核心概念
2. 商品描述是否匹配用户的需求场景（年龄、用途、兴趣）
3. 商品系列是否适合
4. 价格是否符合隐含预算预期

返回 JSON 格式：
{"scores": [{"id": index, "score": 0.XX, "reason": "简短理由(5字以内)"}, ...]}
只返回 JSON，不要其他内容。"""


class ReRanker:
    """二次重排序器 — LLM 精排层

    WHAT: 对向量检索召回的大候选集做 LLM 精排，输出最终 top-k。
    WHY:  粗排（embedding 语义相似度）的精度有限，LLM 的深度语义
          理解能捕获 embedding 模型漏掉的细微相关性。
    HOW:  两种策略：
          - 批量排序（候选≤10时）：一次性给 LLM 打分
          - 逐条打分（候选>10时）：分批次传给 LLM 评估

    分数融合：
      final_score = 0.60 * llm_score + 0.40 * vector_score
      向量分数提供"语义距离"的客观锚点，
      LLM 分数提供"领域理解"的主观判断。
    """

    def __init__(self):
        self._llm = create_llm(temperature=0.0)

    def rerank(
        self, query: str, candidates: List[dict], top_k: int = 4
    ) -> List[dict]:
        """重排候选集（主入口）

        WHAT: 对检索结果做 LLM 精排 + 分数融合。
        WHY:  提升最终返回给 LLM 生成的结果质量。
        HOW:  1. 候选>10 先截断（忽略尾部低质候选）
               2. LLM 批量打分
               3. LLM 分数与原始向量分数加权融合
               4. 按融合分数降序 → 截取 top_k

        Args:
            query: 用户原始查询（或改写后的查询）
            candidates: 候选集 [{"score": float, "content": str, "metadata": dict}, ...]
            top_k: 最终返回数量

        Returns:
            重排后的 top_k 候选集
        """
        n = len(candidates)
        if n <= top_k:
            return candidates
        if n > 20:
            candidates = candidates[:20]

        logger.info(f"[reranker] 候选 {n} → 截断 {len(candidates)} → 目标 top_{top_k}")

        try:
            llm_scores = self._batch_score(query, candidates)
        except Exception as e:
            logger.error(f"[reranker] LLM 打分失败: {e}，保持原始排序")
            return candidates[:top_k]

        fused = self._fuse_scores(candidates, llm_scores, query)
        fused.sort(key=lambda x: x["score"], reverse=True)

        logger.debug(
            f"[reranker] 重排完成: top1={fused[0]['metadata'].get('name', '?')} "
            f"(融合分={fused[0]['score']:.3f})"
        )
        return fused[:top_k]

    def _batch_score(self, query: str, candidates: List[dict]) -> List[float]:
        """LLM 批量打分"""
        items_text = []
        for i, c in enumerate(candidates):
            meta = c.get("metadata", {})
            items_text.append(
                f"{i}. 名称:{meta.get('name', '?')} | "
                f"系列:{meta.get('series', '?')} | "
                f"年龄:{meta.get('age_min', '?')}+ | "
                f"价格:${meta.get('price', 0):.2f} | "
                f"描述:{c.get('content', '')[:100]}"
            )

        prompt = (
            f"用户搜索: {query}\n\n"
            f"候选商品列表:\n" + "\n".join(items_text) +
            f"\n\n按相关性对以上 {len(candidates)} 个候选商品打分。"
        )

        from langchain_core.messages import HumanMessage, SystemMessage

        import json as _json

        messages = [
            SystemMessage(content=_RERANK_SYSTEM),
            HumanMessage(content=prompt),
        ]

        result = self._llm.invoke(messages)
        text = str(result.content).strip()

        try:
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = _json.loads(text)
            score_map = {}
            for item in data.get("scores", []):
                score_map[item["id"]] = float(item["score"])

            return [
                score_map.get(i, 0.5)
                for i in range(len(candidates))
            ]
        except Exception:
            return [0.5] * len(candidates)

    def _fuse_scores(
        self, candidates: List[dict], llm_scores: List[float], query: str
    ) -> List[dict]:
        """分数融合 + 启发式增强"""
        W_VECTOR = 0.40
        W_LLM = 0.60

        result = []
        for i, c in enumerate(candidates):
            vec_score = c.get("score", 0.5)
            llm_score = llm_scores[i] if i < len(llm_scores) else 0.5
            fused = W_LLM * llm_score + W_VECTOR * vec_score

            boost = self._heuristic_boost(query, c)
            fused = min(1.0, fused * (1.0 + boost))

            c = dict(c)
            c["rerank_detail"] = {
                "vector_score": round(vec_score, 4),
                "llm_score": round(llm_score, 4),
                "fused_score": round(fused, 4),
                "boost": round(boost, 4),
            }
            c["score"] = round(fused, 4)
            result.append(c)

        return result

    @staticmethod
    def _heuristic_boost(query: str, candidate: dict) -> float:
        """启发式分数加成"""
        boost = 0.0
        meta = candidate.get("metadata", {})
        name = meta.get("name", "")
        series = meta.get("series", "")

        if name and name in query:
            boost += 0.15

        if series and series in query:
            boost += 0.10

        q_lower = query.lower()
        if "便宜" in q_lower or "实惠" in q_lower or "便宜" in q_lower:
            price = meta.get("price", 0)
            if 0 < price <= 30:
                boost += 0.08

        return boost
