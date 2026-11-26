"""
RAG 质量评测 — RAGAS 指标 + LLM-as-Judge
════════════════════════════════════════════════

架构角色：
  eval_recall.py 只评测了检索召回（Hit Rate/MRR/Precision），
  缺少对生成质量的评测。本模块补充：

  1. RAGAS 风格指标：使用 LLM 自动评估 RAG 回答质量
     - Faithfulness（忠实度）：回答是否基于检索上下文
     - Answer Relevance（回答相关性）：回答是否切题
     - Context Precision（上下文精确度）：检索结果中有多少实际被使用

  2. LLM-as-Judge：用另一个 LLM 充当"考官"，对回答打分
     - 维度打分（准确性/完整性/有用性/格式规范性）
     - 配对对比（固定 RAG vs Agentic RAG 哪个更好）

  3. 综合评测报告：汇总统计 + 问题案例展示

面试考点：
  大模型应用的质量评估是面试中的高频话题。传统 NLP 指标
  (BLEU/ROUGE) 在大模型场景下失效，RAGAS 和 LLM-as-Judge
  是当前行业主流方案。

面试中常见追问：
  Q: 为什么不用 BLEU/ROUGE？
  A: BLEU 评测 n-gram 重叠，但大模型生成高度多样化，
     同样语义可以有完全不同的措辞。BLEU 低不代表质量差。
     大模型评估需要语义理解，LLM-as-Judge 是目前最有效方案。

  Q: LLM-as-Judge 有什么偏差？
  A: (1) 位置偏差（position bias）— 倾向于认为第一个选项更好
     (2) 长度偏差（verbosity bias）— 倾向于认为更长的回答更好
     (3) 自我偏好（self-preference）— 倾向于偏好自己的输出
     (4) 缓解方法：随机交换顺序、控制长度、用不同模型互评

  Q: RAGAS 的工作原理是什么？
  A: RAGAS 用 LLM 提取回答中的"陈述句"（claims），然后逐一检查
     每个 claim 是否能在检索上下文（context）中找到支撑。
     Faithfulness = 有支撑的 claims / 总 claims
"""
import json
import re
import time
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from app.config import create_llm, settings
from loguru import logger

FAITHFULNESS_PROMPT = """你是一个事实核查员。请检查以下 AI 回答中的每一条陈述，
判断是否能在检索结果中找到支撑。

## 用户问题
{question}

## AI 回答
{answer}

## 检索结果（回答的依据）
{context}

## 评估步骤
1. 将 AI 回答拆解为独立的陈述句（factual claims）
2. 对于每个陈述，检查在检索结果中是否有直接支撑
3. 统计：Supported (有支撑) / Unsupported (无支撑/幻觉) / Uncertain (不确定)

## 输出 JSON:
{{
  "claims": [
    {{"statement": "...", "verdict": "supported/unsupported/uncertain", "evidence": "..."}}
  ],
  "total_claims": N,
  "supported_claims": N,
  "faithfulness_score": 0.0-1.0,
  "summary": "一句话总结"
}}

只输出 JSON："""

RELEVANCE_PROMPT = """你是一个相关性评估员。请评估 AI 回答是否切中用户问题。

## 用户问题
{question}

## AI 回答
{answer}

## 评估维度
- 是否直接回答了用户的问题？
- 是否有跑题或答非所问的内容？
- 如果问了多个问题，是否都回答了？

## 输出 JSON:
{{
  "direct_answer": true/false,
  "off_topic_parts": ["..."],
  "completeness_score": 0.0-1.0,
  "relevance_score": 0.0-1.0,
  "summary": "一句话总结"
}}

只输出 JSON："""

JUDGE_PAIRWISE_PROMPT = """你是一个公正的评考官。请对比两个 AI 导购的回答，判断哪个更好。

## 用户问题
{question}

## 回答 A
{answer_a}

## 回答 B
{answer_b}

## 评估维度
1. 准确性：商品信息是否正确
2. 完整性：是否回答了用户的所有问题
3. 有用性：推荐理由是否具体、有说服力
4. 格式：是否清晰整洁、易于阅读

## 输出 JSON:
{{
  "winner": "A" / "B" / "tie",
  "score_a": {{"accuracy": X, "completeness": X, "helpfulness": X, "format": X}},
  "score_b": {{"accuracy": X, "completeness": X, "helpfulness": X, "format": X}},
  "reason": "详细说明为什么 A/B 更好"
}}

只输出 JSON："""


def _call_llm(prompt: str, temperature: float = 0.1) -> str:
    """调用 LLM 并返回文本内容"""
    llm = create_llm(temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    return str(response.content).strip()


def _parse_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON"""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.warning(f"JSON 解析失败: {text[:200]}")
        return {}


def evaluate_faithfulness(
    question: str, answer: str, context: str
) -> dict:
    """
    WHAT: 忠实度评估 — 回答中的陈述是否能从检索结果中找到源头

    WHY:  RAG 系统的核心质量指标。Faithfulness 直接衡量"编造"程度。
          Faithfulness=1.0 表示每句话都有检索源支撑。
    """
    prompt = FAITHFULNESS_PROMPT.format(
        question=question, answer=answer, context=context
    )
    result = _call_llm(prompt)
    return _parse_json(result)


def evaluate_relevance(question: str, answer: str) -> dict:
    """
    WHAT: 相关性评估 — 回答是否回答了用户的问题
    """
    prompt = RELEVANCE_PROMPT.format(question=question, answer=answer)
    result = _call_llm(prompt)
    return _parse_json(result)


def pairwise_comparison(
    question: str, answer_a: str, answer_b: str
) -> dict:
    """
    WHAT: 配对对比 — 两个回答哪个更好

    WHY:  用于对比固定 RAG vs Agentic RAG 的效果差异，
          用 LLM 代替人工做 A/B 选优。
    """
    prompt = JUDGE_PAIRWISE_PROMPT.format(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
    )
    result = _call_llm(prompt)
    return _parse_json(result)


def run_full_evaluation():
    """
    WHAT: 全量质量评测 — 运行 RAGAS 指标 + LLM-as-Judge

    HOW:  用预设的评测用例测试固定RAG和AgenticRAG的生成质量，
          分别评估 Faithfulness/Relevance，并做配对对比。
    """
    from app.agent.graph import run_agent
    from app.rag.chain import RAGChain

    test_cases = [
        {
            "id": "case1",
            "question": "推荐一个适合5岁孩子的消防车",
            "expected_intent": "product_inquiry",
        },
        {
            "id": "case2",
            "question": "星球大战系列有什么适合10岁的吗",
            "expected_intent": "product_inquiry",
        },
        {
            "id": "case3",
            "question": "帮我推荐5岁以下孩子玩的得宝系列",
            "expected_intent": "product_inquiry",
        },
        {
            "id": "case4",
            "question": "有没有50美元以下的太空主题乐高",
            "expected_intent": "product_inquiry",
        },
        {
            "id": "case5",
            "question": "城市系列和科技系列哪个更适合7岁孩子",
            "expected_intent": "product_inquiry",
        },
    ]

    chain = RAGChain()

    print("=" * 70)
    print("  RAG 质量评测 — Faithfulness + Relevance + Pairwise")
    print("=" * 70)

    results = []
    for tc in test_cases:
        qid = tc["id"]
        question = tc["question"]
        print(f"\n📋 [{qid}] {question}")

        # ── 固定 RAG ──
        t0 = time.time()
        rag_result = chain.query(question, k=4)
        rag_time = time.time() - t0
        rag_answer = rag_result["answer"]

        # 构建 context 文本
        rag_context = "\n".join(
            f"{s['name']} | 系列:{s.get('series','')} | ${s.get('price',0):.2f}"
            for s in rag_result.get("sources", [])
        )

        # ── Agentic RAG ──
        t0 = time.time()
        agent_result = run_agent(question)
        agent_time = time.time() - t0
        agent_answer = agent_result["answer"]

        agent_context = "\n".join(
            s.get("content", "") for s in agent_result.get("sources", [])
        )

        # ── 评测 ──
        print("  评估 Fixed RAG...")
        rag_faith = evaluate_faithfulness(question, rag_answer, rag_context)
        rag_rel = evaluate_relevance(question, rag_answer)

        print("  评估 Agentic RAG...")
        agent_faith = evaluate_faithfulness(
            question, agent_answer, agent_context
        )
        agent_rel = evaluate_relevance(question, agent_answer)

        print("  配对对比...")
        pairwise = pairwise_comparison(
            question, rag_answer, agent_answer
        )

        result = {
            "id": qid,
            "question": question,
            "fixed_rag": {
                "time": rag_time,
                "faithfulness": rag_faith.get("faithfulness_score"),
                "relevance": rag_rel.get("relevance_score"),
            },
            "agentic_rag": {
                "time": agent_time,
                "faithfulness": agent_faith.get("faithfulness_score"),
                "relevance": agent_rel.get("relevance_score"),
                "tool_calls": len(agent_result.get("tool_calls_log", [])),
            },
            "pairwise_winner": pairwise.get("winner", "unknown"),
            "pairwise_reason": pairwise.get("reason", ""),
        }
        results.append(result)

        # 打印简况
        print(f"  Fixed RAG:    Faith={rag_faith.get('faithfulness_score','?')}, "
              f"Relevance={rag_rel.get('relevance_score','?')}, Time={rag_time:.1f}s")
        print(f"  Agentic RAG:  Faith={agent_faith.get('faithfulness_score','?')}, "
              f"Relevance={agent_rel.get('relevance_score','?')}, Time={agent_time:.1f}s")
        print(f"  Pairwise:     Winner={pairwise.get('winner','?')}")

    # ── 汇总报告 ──
    print(f"\n{'=' * 70}")
    print("  汇总报告")
    print(f"{'=' * 70}")

    def safe_mean(vals, key):
        scores = [r[key].get(vals) for r in results if r[key].get(vals) is not None]
        return sum(scores) / len(scores) if scores else 0

    print(f"\n📊 固定 RAG 平均分数:")
    print(f"  Faithfulness: {safe_mean('fixed_rag', 'faithfulness'):.2f}")
    print(f"  Relevance:    {safe_mean('fixed_rag', 'relevance'):.2f}")
    print(f"  平均耗时:     {safe_mean('fixed_rag', 'time'):.1f}s")

    print(f"\n📊 Agentic RAG 平均分数:")
    print(f"  Faithfulness: {safe_mean('agentic_rag', 'faithfulness'):.2f}")
    print(f"  Relevance:    {safe_mean('agentic_rag', 'relevance'):.2f}")
    print(f"  平均耗时:     {safe_mean('agentic_rag', 'time'):.1f}s")

    winners = [r["pairwise_winner"] for r in results]
    a_wins = winners.count("A")
    b_wins = winners.count("B")
    ties = winners.count("tie")

    print(f"\n📊 配对对比结果 (A=Fixed RAG, B=Agentic RAG):")
    print(f"  A 更好: {a_wins}, B 更好: {b_wins}, 平手: {ties}")

    return results


if __name__ == "__main__":
    run_full_evaluation()
