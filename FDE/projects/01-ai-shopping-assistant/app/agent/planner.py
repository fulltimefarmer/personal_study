"""
Plan-and-Execute Agent — 复杂查询的任务分解与逐步执行
══════════════════════════════════════════════════════════

架构角色：
  标准 ReAct Agent 对每一步都是"看一步走一步"，没有全局视野。
  当用户需求复杂时（如"帮我对比城市系列和科技系列在50-100美元
  区间的性价比，然后推荐最值得买的3款"），ReAct 容易遗漏或跑偏。

  Plan-and-Execute 先制定完整计划，再按计划逐步执行，最后汇总。

  面试考点：
  这是 LangGraph 中"先规划后执行"的经典模式，相比 ReAct 的
  优势在于结构化思维和可靠执行。

核心流程（三步法）：
  1. Plan（规划阶段）：LLM 分析用户需求，拆解为 3-5 个有序子任务，
     每个子任务指定需要调用的工具和参数。
  2. Execute（执行阶段）：按顺序执行每个子任务，收集中间结果。
     每个子步骤完成后将结果注入上下文，供后续步骤参考。
  3. Aggregate（汇总阶段）：将所有执行结果聚合，生成最终答案。

面试中常见追问：
  Q: 什么时候用 Plan-and-Execute 而不是 ReAct？
  A: 当任务有明显结构、需要多步骤协调时（对比分析、多条件筛选、
     枚举式探索）。简单单步任务用 ReAct 更高效。

  Q: Plan-and-Execute 有什么缺点？
  A: 计划是静态的，执行过程中如果发现新信息需要调整计划，
     需要实现 dynamic replanning（动态重规划），否则计划过时。
     另外初始规划就消耗了额外的 LLM 调用。

  Q: 和 LangChain 的 PlanAndExecuteAgentExecutor 有什么区别？
  A: 官方实现较复杂且抽象。本项目用 LangGraph 手写实现，
     更容易理解和定制，面试时可以展示对底层机制的理解。

Graph 拓扑：
  planner → executor(步骤1) → executor(步骤2) → ... → aggregator → END
                  ↑________重规划___________|

与 ReAct 的对比：
  ReAct:   思考→行动→思考→行动→...→回答（灵活但不可控）
  Plan:    计划→步骤1→步骤2→...→汇总（结构清晰但不够灵活）
  最佳实践：先用 Plan-and-Execute 处理结构化任务，
           再用 ReAct 处理灵活交互。
"""
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage
from app.config import create_llm, settings
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

PLAN_PROMPT = """你是一个任务规划专家。将用户的复杂导购需求拆解为有序执行步骤。

## 可用的工具
1. semantic_search(query) — 语义搜索商品
2. filter_search(query, series, max_price, max_age) — 条件筛选
3. get_product_detail(sku) — 查询商品详情
4. calculate_price(quantity, unit_price) — 计算价格

## 输出格式（纯 JSON 数组）
[
  {"step": 1, "action": "描述这一步要做什么", "tool": "工具名", "args": {参数}},
  {"step": 2, ...}
]

## 规则
- 步骤数 3-5 个，从理解需求到给出推荐全覆盖
- 参数根据用户需求指定，不确定的传空值
- 如果需要对多个候选做对比，先搜索再逐个查详情
- 只输出 JSON 数组，不要其他内容

用户需求: {question}

执行计划 (JSON):"""

EXECUTE_PROMPT = """你正在执行导购任务的第 {step_num}/{total_steps} 步。

## 当前步骤
{current_step}

## 已完成步骤的结果
{previous_results}

## 步骤执行结果
{step_result}

请完成这一步的分析，总结关键的发现（1-3句话）。如果结果不理想，可以建议调整后续策略："""

AGGREGATE_PROMPT = """你是一个专业的乐高积木导购助手"小砖家"。

## 用户原始需求
{question}

## 执行过程与结果
{execution_log}

请基于上述信息，生成最终的回答。要求：
1. 推荐格式用：**🔥 为你推荐：** 列表
2. 推荐理由具体，有数据支撑
3. 如果计划中有对比，明确给出对比结论
4. 价格使用美元（$）标注
5. 不要提及"计划""步骤""执行"等技术术语"""


class PlanStep(TypedDict):
    step: int
    action: str
    tool: str
    args: dict


class PlannerState(TypedDict):
    question: str
    plan: list  # List[PlanStep]
    current_step: int
    step_results: Annotated[list, add_messages]
    final_answer: str


_AVAILABLE_TOOLS = {}


def _init_tools():
    """延迟加载工具，避免循环导入"""
    if _AVAILABLE_TOOLS:
        return
    from app.agent.tools import (
        calculate_price,
        filter_search,
        get_product_detail,
        semantic_search,
    )

    for tool in [semantic_search, filter_search, get_product_detail, calculate_price]:
        _AVAILABLE_TOOLS[tool.name] = tool


def _plan_node(state: PlannerState) -> dict:
    """
    WHAT: 规划节点 — 将用户复杂需求拆解为有序执行步骤

    WHY:  ReAct "看一步走一步"对复杂任务容易遗漏。
          先规划再执行给 Agent 一个全局视图，提高可靠性。

    HOW:  LLM 分析需求 → 输出 JSON 步骤列表 → 解析为 PlanStep 列表
    """
    llm = create_llm(temperature=0.2)
    prompt = PLAN_PROMPT.format(question=state["question"])
    response = llm.invoke([HumanMessage(content=prompt)])
    content = str(response.content).strip()

    # 提取 JSON 数组（处理 LLM 可能输出 markdown 代码块的情况）
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        plan = json.loads(content)
        logger.info(f"[planner] 规划了 {len(plan)} 个步骤:")
        for step in plan:
            logger.info(f"  步骤{step['step']}: {step['action']}")
    except json.JSONDecodeError:
        logger.warning(f"[planner] JSON 解析失败，使用默认计划\n内容: {content[:200]}")
        plan = [
            {
                "step": 1,
                "action": "语义搜索相关商品",
                "tool": "semantic_search",
                "args": {"query": state["question"]},
            },
            {
                "step": 2,
                "action": "基于搜索结果推荐",
                "tool": "semantic_search",
                "args": {"query": state["question"]},
            },
        ]

    return {"plan": plan, "current_step": 0}


def _executor_node(state: PlannerState) -> dict:
    """
    WHAT: 执行节点 — 逐步执行计划中的每一个步骤

    WHY:  规划只是蓝图，需要实际调用工具获取数据，
          并且每个步骤的结果会影响后续步骤的分析。

    HOW:  取 plan[current_step]，调用对应工具，
          将结果传递给 LLM 分析总结。
    """
    _init_tools()
    step_idx = state["current_step"]
    plan = state["plan"]

    if step_idx >= len(plan):
        logger.warning("[planner] 步骤索引超出范围，跳过执行")
        return {"current_step": step_idx + 1}

    step = plan[step_idx]
    logger.info(f"[planner] 执行步骤 {step['step']}: {step['action']}")

    tool = _AVAILABLE_TOOLS.get(step["tool"])
    if not tool:
        result = f"工具 {step['tool']} 不可用"
        logger.warning(f"[planner] {result}")
    else:
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool.invoke, step["args"])
                result = future.result(timeout=settings.tool_call_timeout)
        except FutureTimeoutError:
            result = f"工具调用超时（>{settings.tool_call_timeout}s）: {step['tool']}"
            logger.error(f"[planner] 工具超时: {step['tool']}")
        except Exception as e:
            result = f"工具调用失败: {e}"
            logger.error(f"[planner] 工具错误: {e}")

    # 收集已完成步骤的结果
    prev_results = state.get("step_results", [])
    prev_text = "\n".join(
        str(r) for r in prev_results[-3:] if r
    ) if prev_results else "（无）"

    # 用 LLM 分析本步骤结果
    llm = create_llm(temperature=0.3)
    analysis_prompt = EXECUTE_PROMPT.format(
        step_num=step["step"],
        total_steps=len(plan),
        current_step=step["action"],
        previous_results=prev_text,
        step_result=result,
    )
    analysis = llm.invoke([HumanMessage(content=analysis_prompt)])

    step_summary = (
        f"步骤{step['step']}: {step['action']}\n"
        f"结果: {str(result)[:500]}\n"
        f"分析: {str(analysis.content)}"
    )

    return {
        "current_step": step_idx + 1,
        "step_results": [step_summary],
    }


def _aggregator_node(state: PlannerState) -> dict:
    """
    WHAT: 汇总节点 — 整合所有步骤结果，生成最终回答

    WHY:  执行结果是零散的步骤总结，需要整合为连贯的导购回答。
    """
    llm = create_llm(temperature=0.5)
    prompt = AGGREGATE_PROMPT.format(
        question=state["question"],
        execution_log="\n\n".join(
            str(r) for r in state.get("step_results", [])
        ),
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    logger.info(f"[planner] 汇总完成，长度: {len(str(response.content))}")
    return {"final_answer": str(response.content)}


def _should_continue_execute(state: PlannerState) -> Literal["execute", "aggregate"]:
    """判断是否继续执行下一步"""
    if state["current_step"] < len(state["plan"]):
        return "execute"
    return "aggregate"


def build_planner_graph() -> CompiledStateGraph:
    """
    WHAT: 构建 Plan-and-Execute 图

    HOW:  planner → executor → [还有步骤?]
                              ├─ 是 → executor（循环）
                              └─ 否 → aggregator → END
    """
    builder = StateGraph(PlannerState)

    builder.add_node("planner", _plan_node)
    builder.add_node("execute", _executor_node)
    builder.add_node("aggregate", _aggregator_node)

    builder.set_entry_point("planner")
    builder.add_edge("planner", "execute")
    builder.add_conditional_edges("execute", _should_continue_execute, {
        "execute": "execute",
        "aggregate": "aggregate",
    })
    builder.add_edge("aggregate", END)

    logger.info("[planner] Plan-and-Execute Graph 构建完成")
    return builder.compile()


_planner_graph = build_planner_graph()


def run_plan_and_execute(question: str) -> str:
    """
    WHAT: Plan-and-Execute 入口 — 一步调用完成整个规划→执行→汇总流程

    Args:
        question: 用户的复杂需求

    Returns:
        str: 汇总后的最终回答
    """
    logger.info(f"[planner] 开始 Plan-and-Execute，问题: {question!r}")
    initial_state: PlannerState = {
        "question": question,
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "final_answer": "",
    }
    result = _planner_graph.invoke(initial_state)
    return result.get("final_answer", "抱歉，处理您的需求时出现了问题。")
