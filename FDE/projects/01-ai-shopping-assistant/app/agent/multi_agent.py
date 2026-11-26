"""
Multi-Agent Collaboration — Supervisor 编排专业子 Agent
══════════════════════════════════════════════════════════

架构角色：
  单 Agent 架构把所有能力（导购+售后+订单+活动）塞进一个 LLM + prompt，
  面对复杂场景容易混乱（"该用哪个工具？先查售后还是先搜商品？"）。

  Multi-Agent 架构将职责拆分给多个专业子 Agent（如导购专家、
  售后专家、订单专家），由 Supervisor 统一决策路由到哪个子 Agent。

  面试考点：
  这是 LangGraph 中"监督者模式（Supervisor Pattern）"的标准实现，
  是 Agentic AI 架构演进的重要方向。

核心模式（Supervisor Pattern）：
  Supervisor（监督者）负责全局路由，每个 Worker（子 Agent）
  专注自己的领域。子 Agent 之间不直接通信，所有交互经过 Supervisor。

  类比企业中：Supervisor = 客服主管，子 Agent = 各个部门专员。
  主管听懂客户需求后，分配给对应专员处理，专员完成汇报给主管。

Graph 拓扑：
  START → supervisor → [路由]
                         ├─→ shopping（导购 Agent）
                         ├─→ aftersales（售后 Agent）
                         ├─→ order（订单会员 Agent）
                         └─→ END
  shopping/aftersales/order → supervisor（完成后回到 supervisor 决策）

面试中常见追问：
  Q: 为什么不直接给一个 Agent 更多工具而是拆成多个？
  A: (1) Prompt 太长会降低 LLM 对每个工具的注意力
     (2) 不同领域的工具不应该"污染"彼此的决策空间
     (3) 拆分后每个子 Agent 的 prompt 更聚焦、幻觉更少
     (4) 独立开发、单独优化、独立降级

  Q: 子 Agent 之间需要共享状态吗？
  A: 在本实现中通过 Supervisor 的状态中转。如果需要直接共享
     （如订单 Agent 需要知道售后的工单号），可以通过全局 State
     或 shared context 实现。LangGraph 的 StateGraph 天然支持
     这种跨节点状态共享。

  Q: 和 CrewAI/AutoGen 的多 Agent 有什么区别？
  A: CrewAI/AutoGen 是框架层封装，内部也是类似的编排逻辑。
     用 LangGraph 手写 Supervisor Pattern 更能展示对底层机制的
     理解，且可定制性更强。

与现有 ReAct Agent 的关系：
  本模块是示范性实现，展示多 Agent 架构模式。
  生产中可以：用 multi_agent 作为顶层路由器 → 下层的 shopping agent
  复用现有 graph.py 的 ReAct Agent。
"""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from app.config import create_llm
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from loguru import logger


class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str


SUPERVISOR_PROMPT = """你是一个客服主管，负责将用户请求路由给最合适的专业 Agent。

## 可用的子 Agent
1. **shopping** — 乐高商品导购，负责商品搜索、推荐、比价、价格计算
2. **aftersales** — 售后客服，负责退换货政策、工单创建、保修咨询
3. **order** — 订单会员，负责订单状态查询、物流跟踪、会员信息查询

## 路由规则
- 推荐商品/搜索/比价 → shopping
- 退换货/保修/工单/发货 → aftersales
- 订单状态/物流/会员/积分 → order
- 问候/感谢/再见/闲聊 → FINISH（你来直接回复）
- 问题超出以上范围 → FINISH（你来婉拒）
- 子 Agent 返回结果后，如果用户表示满意/感谢 → FINISH
- 子 Agent 返回结果后，如果用户继续追问相关问题 → 重新路由到对应 Agent

## 当前对话
{history}

请只回复一个词: shopping / aftersales / order / FINISH"""

SHOPPING_AGENT_PROMPT = """你是乐高导购专家"小砖家"。

## 职责
- 理解用户需求（年龄/预算/兴趣）
- 搜索推荐商品
- 解答商品相关问题

请基于对话历史回答用户的问题（简洁、友好）。

当前对话:
{history}"""

AFTERSALES_AGENT_PROMPT = """你是乐高售后客服专家。

## 职责
- 退换货政策咨询
- 创建售后工单
- 保修/缺件补发

请基于对话历史回答用户的问题。

当前对话:
{history}"""

ORDER_AGENT_PROMPT = """你是订单与会员服务专家。

## 职责
- 订单状态/物流查询
- 会员等级/积分查询
- 订单明细确认

请基于对话历史回答用户的问题。

当前对话:
{history}"""


def _supervisor_node(state: SupervisorState) -> dict:
    """
    WHAT: Supervisor 节点 — 决策将当前请求路由给哪个子 Agent

    WHY:  Supervisor 是多 Agent 架构的"大脑"，负责全局决策。
          - 根据对话历史和用户最新输入判断领域归属
          - 支持手递手切换（用户从导购问题转为售后问题时自动路由）
          - 支持终结判断（用户满意或超出能力时返回 FINISH）
    """
    llm = create_llm(temperature=0.1)

    history_text = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {str(m.content)[:200]}"
        for m in state["messages"][-6:]
    )

    prompt = SUPERVISOR_PROMPT.format(history=history_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    decision = str(response.content).strip().lower()

    logger.info(f"[supervisor] 路由决策: {decision}")
    return {"next_agent": decision}


def _shopping_agent_node(state: SupervisorState) -> dict:
    """
    WHAT: 导购子 Agent — 专注商品搜索与推荐

    WHY:  将导购逻辑独立出来，prompt 可以更加聚焦于商品知识，
          不会和售后政策、订单查询等无关内容混淆。

    HOW:  简化版直接用 LLM 回答（不含工具调用）。
          生产中可以替换为调用 graph.py 的 ReAct Agent。
    """
    llm = create_llm(temperature=0.5)
    history_text = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {str(m.content)[:300]}"
        for m in state["messages"][-6:]
    )
    prompt = SHOPPING_AGENT_PROMPT.format(history=history_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    logger.info("[shopping_agent] 导购 Agent 已回复")
    return {"messages": [AIMessage(content=str(response.content))]}


def _aftersales_agent_node(state: SupervisorState) -> dict:
    """售后子 Agent — 专注退换货/工单/保修"""
    llm = create_llm(temperature=0.3)
    history_text = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {str(m.content)[:300]}"
        for m in state["messages"][-6:]
    )
    prompt = AFTERSALES_AGENT_PROMPT.format(history=history_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    logger.info("[aftersales_agent] 售后 Agent 已回复")
    return {"messages": [AIMessage(content=str(response.content))]}


def _order_agent_node(state: SupervisorState) -> dict:
    """订单会员子 Agent — 专注订单/物流/积分"""
    llm = create_llm(temperature=0.3)
    history_text = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {str(m.content)[:300]}"
        for m in state["messages"][-6:]
    )
    prompt = ORDER_AGENT_PROMPT.format(history=history_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    logger.info("[order_agent] 订单 Agent 已回复")
    return {"messages": [AIMessage(content=str(response.content))]}


def _supervisor_should_continue(state: SupervisorState) -> Literal[
    "shopping", "aftersales", "order", END
]:
    """根据 Supervisor 的路由决策控制流"""
    agent = state.get("next_agent", "FINISH").lower()

    route_map = {
        "shopping": "shopping",
        "aftersales": "aftersales",
        "order": "order",
        "finish": END,
    }
    return route_map.get(agent, END)


def build_multi_agent_graph() -> CompiledStateGraph:
    """
    WHAT: 构建 Multi-Agent 图 — Supervisor + 3 个子 Agent

    WHY:  将多 Agent 模式封装为独立可复用的 Graph，
          可以作为现有架构的升级替代方案。

    HOW:  supervisor → [shopping|aftersales|order|END]
          shopping/aftersales/order → supervisor (返回继续决策)

    Graph 拓扑：
      START → supervisor → shopping → supervisor → FINISH → END
                              ↓ aftersales ↗        ↑ order ↗
    """
    builder = StateGraph(SupervisorState)

    builder.add_node("supervisor", _supervisor_node)
    builder.add_node("shopping", _shopping_agent_node)
    builder.add_node("aftersales", _aftersales_agent_node)
    builder.add_node("order", _order_agent_node)

    builder.set_entry_point("supervisor")

    builder.add_conditional_edges("supervisor", _supervisor_should_continue, {
        "shopping": "shopping",
        "aftersales": "aftersales",
        "order": "order",
        END: END,
    })

    builder.add_edge("shopping", "supervisor")
    builder.add_edge("aftersales", "supervisor")
    builder.add_edge("order", "supervisor")

    logger.info("[multi_agent] Multi-Agent Supervisor Graph 构建完成")
    return builder.compile()


_multi_agent_graph = build_multi_agent_graph()


def run_multi_agent(user_message: str, messages: list | None = None) -> str:
    """
    WHAT: Multi-Agent 入口 — 自动路由到专业子 Agent 处理

    Args:
        user_message: 用户输入
        messages: 历史消息列表（可选）

    Returns:
        str: 子 Agent 的回答
    """
    logger.info(f"[multi_agent] 收到请求: {user_message!r}")
    msgs = list(messages) if messages else []
    msgs.append(HumanMessage(content=user_message))

    initial_state: SupervisorState = {
        "messages": msgs,
        "next_agent": "",
    }
    result = _multi_agent_graph.invoke(initial_state)

    final_messages = result.get("messages", [])
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content:
            return str(msg.content)

    return "抱歉，暂时无法处理您的请求。"
