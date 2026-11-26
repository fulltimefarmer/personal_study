"""
Reflection / Self-Critique Agent — 回答后自我反思修正链
══════════════════════════════════════════════════════════

架构角色：
  在标准 ReAct Agent 回答之后，增加一个"反思"环节，让 LLM
  对自己的输出进行自评，发现不足之处并自动修正。

  面试考点：
  这是 LangGraph 中级常见的"Generate → Reflect → Revise"
  模式，区别于基础的 ReAct 循环。

核心思想：
  1. Generate（生成）：Agent 产出初步回答
  2. Reflect（反思）：LLM 以"审阅者"角色评估回答质量
     - 是否引用了来源中的信息？
     - 推荐理由是否具体？
     - 是否有更好的推荐策略？
     - 是否存在幻觉？
  3. Revise（修正）：如果反思发现问题，基于反思结果重新生成答案

面试中常见追问：
  Q: 为什么不在 prompt 里直接要求高质量，还要反思？
  A: LLM 在"生成"和"评判"两个角色中的表现差异很大。
     让同一个模型先写再评，比试图在生成阶段一次做对所有事情
     效果更好。类比：人类写文章也是先起草再修改。

  Q: Reflection 和 Guardrails 有什么区别？
  A: Guardrails 是确定性规则（字符匹配、关键词检查），
     Reflection 是 LLM 审查（语义理解、策略评估）。
     Guardrails 拦截硬错误（编造商品名），
     Reflection 提升软质量（推荐理由是否具体）。
     两者互补，不是替代关系。

  Q: 反思会不会增加太多延迟？
  A: 确实会增加 1-2 次 LLM 调用。生产中可以：
     - 只在答案质量要求高的场景使用
     - 用更小的模型做反思（如 3B 路由模型）
     - 让反思和初始生成并行进行

Graph 拓扑（添加到现有 ReAct 之后）：
  agent → tools ↔ agent → [输出] → reflect → [需修正?]
                                         ├─ 是 → revise → 输出
                                         └─ 否 → 输出
"""
from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage
from app.config import create_llm, settings
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

REFLECT_PROMPT = """你是一个严格的答案审阅者。请评估以下 AI 导购助手的回答是否合格。

## 评估维度
1. **信息准确性**：推荐的商品信息是否来自搜索结果？有没有编造？
2. **推荐质量**：推荐理由是否具体？有没有说明为什么适合用户？
3. **完整性**：是否回答了用户的所有问题？
4. **格式规范**：是否使用了规定的推荐格式？

## 判断标准
- 如果回答在上述维度都没有明显问题，回复 "APPROVED"
- 如果回答有需要改进的地方，回复 "NEEDS_REVISION: <具体问题和修改建议>"

## 待评估回答
用户问题: {question}

回答:
{answer}

搜索结果: {sources}

请评估并回复（只回复 APPROVED 或 NEEDS_REVISION: ...）："""

REVISE_PROMPT = """你是一个专业的乐高积木导购助手"小砖家"。

你之前的回答被审阅者指出了一些问题，请根据反馈修改你的回答。

## 审阅反馈
{critique}

## 原始回答
{answer}

## 用户问题
{question}

请重新生成改进后的回答（直接输出回答内容，不要提及"修改"或"反馈"）："""


class ReflectionState(TypedDict):
    question: str
    answer: str
    sources: str
    critique: str
    revision_count: int


def _reflect_node(state: ReflectionState) -> dict:
    """反思节点 — 审阅答案质量"""
    llm = create_llm(temperature=0.1)
    prompt = REFLECT_PROMPT.format(
        question=state["question"],
        answer=state["answer"],
        sources=state["sources"],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    critique = str(response.content).strip()
    logger.info(f"[reflection] 反思结果: {critique[:100]}...")
    return {"critique": critique}


def _revise_node(state: ReflectionState) -> dict:
    """修正节点 — 根据反馈重新生成"""
    llm = create_llm(temperature=0.5)
    prompt = REVISE_PROMPT.format(
        critique=state["critique"],
        answer=state["answer"],
        question=state["question"],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    revised = str(response.content).strip()
    logger.info(f"[reflection] 修正完成，长度: {len(revised)}")
    return {
        "answer": revised,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def _should_revise(state: ReflectionState) -> Literal["revise", END]:
    """判断是否需要修正"""
    critique = state.get("critique", "")
    rev_count = state.get("revision_count", 0)

    if "APPROVED" in critique.upper() and "NEEDS_REVISION" not in critique.upper():
        logger.info("[reflection] 回答通过审阅 ✓")
        return END

    if rev_count >= 2:
        logger.warning("[reflection] 已达到最大修正次数(2)，强制通过")
        return END

    logger.info(f"[reflection] 需要修正 (第{rev_count+1}次)")
    return "revise"


def build_reflection_graph() -> CompiledStateGraph:
    """
    WHAT: 构建 Reflection 图 — 生成→反思→（修正→反思）×N 循环

    WHY:  Reflection 是 Agentic AI 中的重要质量保障模式。
          - 基础 ReAct: Think → Act → Think → Act → Answer
          - + Reflection: Think → Act → ... → Answer → Reflect → Revise → Answer

    HOW:  StateGraph 三节点：
          reflect → [NEEDS_REVISION?]
                    ├─ 否 → END（输出通过审阅的答案）
                    └─ 是 → revise → reflect（修正后再次审阅，最多2轮）
    """
    builder = StateGraph(ReflectionState)
    builder.add_node("reflect", _reflect_node)
    builder.add_node("revise", _revise_node)

    builder.set_entry_point("reflect")
    builder.add_conditional_edges("reflect", _should_revise)
    builder.add_edge("revise", "reflect")

    logger.info("[reflection] Reflection Graph 构建完成")
    return builder.compile()


_reflection_graph = build_reflection_graph()


def apply_reflection(
    answer: str,
    question: str,
    sources: str,
) -> str:
    """
    WHAT: Reflection 入口 — 对答案进行反思 + 修正

    WHY:  将 Reflection 暴露为简单函数，方便在 run_agent() 或
          guardrails 之后调用，不改变现有的 ReAct 图结构。

    HOW:  构建状态 → 运行 reflection graph → 返回修正后的 answer

    Args:
        answer:   Agent 原始回答
        question: 用户问题
        sources:  检索来源文本

    Returns:
        str: 通过反思审阅的回答（可能是修正后的）
    """
    if not settings.guardrails_enabled:
        return answer

    logger.info("[reflection] 开始反思审阅...")
    initial_state: ReflectionState = {
        "question": question,
        "answer": answer,
        "sources": sources if sources else "（无检索结果）",
        "critique": "",
        "revision_count": 0,
    }

    result = _reflection_graph.invoke(initial_state)
    final_answer = result.get("answer", answer)

    if result.get("revision_count", 0) > 0:
        logger.info(
            f"[reflection] 经过 {result['revision_count']} 次修正"
        )

    return final_answer
