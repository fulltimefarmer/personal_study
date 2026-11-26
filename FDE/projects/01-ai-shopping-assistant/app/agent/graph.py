"""
LangGraph ReAct Agent 工作流 — 自主决策的多轮商品导购引擎
══════════════════════════════════════════════════════════════

架构角色：
  本模块使用 LangGraph 框架构建 ReAct Agent 图，是 Agentic RAG 的编排层。
  它定义了 Agent 的完整执行流程：节点（思考/行动）+ 边（条件分支/循环），
  将 LLM 推理能力与工具执行能力编排为可自我纠错的智能对话系统。

ReAct（Reasoning + Acting）循环原理：
  Agent 在"推理"和"行动"两个阶段之间交替进行：
  1. Reasoning（推理）: LLM 阅读对话历史 + 工具结果，判断需要什么信息，决定调用哪个工具
  2. Acting（行动）:   执行工具调用（搜索/查详情/计算），获取外部世界信息
  3. 工具结果反馈回 Reasoning，LLM 综合信息后判断：继续搜索 还是 输出最终答案
  循环持续直到 LLM 认为信息充足、无需再调用工具时自动结束。

Graph 拓扑结构：
  START → agent → [有 tool_calls?] → tools → agent → ... → [无 tool_calls] → END
                 ↘ [无 tool_calls] ──────────────────────────────→ END

StateGraph 核心 API：
  - add_node(name, func)           注册节点（对应 ReAct 的一个步骤）
  - add_edge(A, B)                 固定边：A 完成后总是进入 B
  - add_conditional_edges(A, ...)  条件边：根据路由函数返回值动态选择目标节点
  - set_entry_point(name)          指定图的起始节点
  - compile()                      将声明式定义编译为可执行的 CompiledStateGraph

条件边（conditional_edges）详解 — ReAct 循环的核心开关：
  条件边实现了 if/else 分支在图结构中的表达。通过 _should_continue 函数
  检查 LLM 输出是否包含 tool_calls，动态决定流向：
  - 有 tool_calls → 进入 "tools" 节点执行工具
  - 无 tool_calls → 进入 END，结束循环，最终状态返回给调用方

ToolNode 详解 — 工具自动执行器：
  ToolNode 是 LangGraph 内置的工具执行节点，负责：
  1. 从最后一条 AIMessage 中自动提取 tool_calls 列表（无需手动解析）
  2. 并行（非串行）执行每个 tool_call，调用对应的 @tool 函数
  3. 将每个工具调用的返回值封装为 ToolMessage，追加到 messages 列表
  开发者只需 add_node("tools", ToolNode(tools))，ToolNode 自动完成以上三步。

与固定 RAG 的关键区别：
  固定 RAG：检索 → 格式化 → 生成（一次调用，流程固定，无决策自由）
  Agentic RAG：LLM 自主决定是否检索、用哪种方式检索、是否多次检索、
              是否需要查看商品详情、是否需要计算价格 —— 灵活适应需求变化
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import List, Literal

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from app.config import create_llm, settings
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from loguru import logger

from app.agent.state import AgentState
from app.agent.tools import (
    analyze_image,
    calculate_price,
    check_inventory,
    create_service_ticket,
    filter_search,
    get_product_detail,
    graph_search,
    query_after_sales_policy,
    query_membership,
    query_order,
    search_promotions,
    semantic_search,
    transfer_to_human,
    web_search,
)

all_tools = [
    analyze_image,
    semantic_search,
    filter_search,
    get_product_detail,
    check_inventory,
    calculate_price,
    web_search,
    graph_search,
    query_after_sales_policy,
    create_service_ticket,
    query_order,
    query_membership,
    search_promotions,
    transfer_to_human,
]

# ── bind_tools 幕后原理 ─────────────────────────────────────
# LangChain 的 bind_tools() 遍历 @tool 装饰的函数，提取：
#   1. 函数名 → tool name
#   2. 参数名+类型注解 → JSON Schema properties
#   3. docstring → tool description
# 组装为 OpenAI Function Calling 格式注入每次 LLM 请求：
#   { "tools": [{ "type": "function", "function": { "name": "...", "parameters": {...} } }] }
# LLM 看到 tools 列表后，在需要时输出 tool_calls，格式为：
#   AIMessage(tool_calls=[{ "name": "filter_search", "args": { "query": "消防车", "max_price": 50 } }])
# 这就是 Agent 能"自己决定调用什么工具、传什么参数"的底层机制。
llm_with_tools = create_llm(temperature=0.3).bind_tools(all_tools)

SYSTEM_PROMPT = """你是一个专业的乐高积木智能导购与客服助手"小砖家"，具备商品导购、售后工单、订单查询、会员查询、活动搜索、图片识别等综合服务能力。

## 角色设定
- 你是一位在乐高旗舰店工作了 3 年的资深导购与客服
- 语气友好热情，像一位乐高店员与顾客面对面交流
- 用「你」称呼顾客，用「我」自称，使用「我们店」指代本店
- 回答简洁有条理，避免冗长的开场白

## 处理流程（按意图分支）

### 0. 图片识别
- 用户发送图片链接/URL 要求识别 → analyze_image
- 识别后根据结果进一步推荐类似商品（用 semantic_search/filter_search）
- 用户想知道"这是什么套装""帮我看看这个零件"→ analyze_image

### 1. 商品导购
- 先理解需求（年龄/预算/兴趣），不确定时主动确认
- 向量库有结果 → 直接推荐输出（系统已自动过滤缺货商品）
- 向量库无结果 → 使用 web_search 联网搜索补充
- 图片识别结果可以辅助商品推荐
- 工具选择：
  - 需求模糊 → semantic_search
  - 有明确条件（系列/预算/年龄）→ filter_search
  - 顾客对某商品感兴趣 → get_product_detail
  - 顾客问"买 N 件多少钱"→ calculate_price
  - 顾客发图片想识别/找类似 → analyze_image
  - 顾客问"有没有货""库存多少"→ check_inventory
  - **顾客问搭配/类似/跨系列/升档降档 → graph_search**
- **库存规则：搜索和推荐结果已经过滤掉缺货商品，不要再推荐缺货商品。**
   如果 get_product_detail 显示"暂时缺货"，应坦率告知用户并建议类似商品。

### graph_search 使用指南（知识图谱）
graph_search 利用商品关系图谱做结构化推荐，与语义搜索互补：
- **推荐搭配**: "跟这个消防车搭配的还有什么" → traversal_type="recommend", sku="60374"
- **浏览系列/主题**: "幻影忍者系列有哪些" → traversal_type="browse", keyword="幻影忍者"
- **价位升降**: "有没有类似的但便宜一点的" → traversal_type="upgrade_downgrade", sku="60351", direction="down"
- **跨系列发现**: "除了城市系列，还有什么太空主题" → traversal_type="cross_series", theme="太空"
- **年龄+主题**: "6岁男孩能玩什么超级英雄" → traversal_type="cross_series", theme="超级英雄", age=6

关键词对齐（browse/cross_series 的 keyword/theme 参数）：
- 系列：城市系列、好朋友系列、幻影忍者、超级赛车、哈利波特、星球大战、漫威、DC、迪士尼、得宝系列
- 主题：城市生活、紧急救援、太空、赛车、魔法、科幻、超级英雄、动物、启蒙、创意
- 年龄段：2-4岁、5-7岁、8-11岁、12-15岁、16岁以上
- 价位段：入门($0-25)、中档($25-60)、高端($60-150)、收藏($150+)

⚠ graph_search 返回结果可能包含缺货商品，需要你结合 get_product_detail 或 check_inventory 确认库存状态。

### 2. 售后工单
- 用户问退换货/保修/缺件/发货等政策 → query_after_sales_policy
- 用户要办理退换货/补发 → 先确认订单号+问题类型+描述
  - 信息不齐全 → 最多追问 2 轮，第 3 轮仍不齐 → transfer_to_human
  - 信息齐全 → create_service_ticket
- 政策咨询 → 直接回答政策内容

### 3. 订单会员查询
- 用户问订单状态/物流 → 先获取订单号 → query_order
- 用户问积分/会员等级 → 先获取手机号后四位 → query_membership
- 校验字段格式（订单号 ORD-xxxx、手机号格式）
- 格式不对 → 引导用户提供正确格式
- 查询失败 → 提示确认信息并建议人工

### 4. 平台活动
- 用户问优惠/打折/促销 → search_promotions
- 自动过滤已过期活动，只展示进行中的
- 活动信息不足时可联网补充

### 5. 业务外问题
- 非乐高相关问题 → transfer_to_human 转人工
- 用户明确要求转人工 → transfer_to_human
- 投诉/敏感操作 → transfer_to_human

## 输出格式
推荐商品时：
**🔥 为你推荐：**
1. **商品名称** — 系列名 | 年龄 X+ | $价格
   > 推荐理由：一句话说明为什么适合

## 严格规则
1. **绝不编造**商品名称、价格、订单等信息，一切以工具返回为准
2. 如果工具返回"未找到"，直接告知顾客，不要编造
3. 不要提及「向量库」「检索」「数据库」等技术术语
4. 价格使用美元（$）标注
5. 销售过程完成的最后一步输出"本轮结束，等待下一轮用户输入"
"""

# ─────────────────────────────────────────────────────────
# 节点 1：Agent 决策节点
# ─────────────────────────────────────────────────────────
# 这是 ReAct 的 "Reasoning" 部分。
# 将系统提示词 + 对话历史发给 LLM，LLM 返回：
#   AIMessage(content=..., tool_calls=[...])  如果决定调用工具
#   AIMessage(content=...)                     如果决定直接回复


def _agent_node(state: AgentState) -> dict:
    """
    WHAT: Agent 推理节点 — ReAct 循环的 Reasoning 阶段

    WHY:  这是整个 Agent 工作流的核心决策点。LLM 在此节点阅读完整的
          对话历史（包括用户消息、之前的工具调用结果、自身回复），
          综合所有可用信息后自主决策下一步行动。
          没有这个节点，Agent 就失去了"思考"能力，退化为固定 pipeline。

    HOW:  1. _ensure_system_prompt() 确保消息列表首条是 SystemMessage
             （仅在首次进入循环时注入，后续迭代复用已有的 SystemMessage）
          2. 将完整消息列表发给绑定了工具的 LLM (llm_with_tools.invoke)
          3. LLM 返回 AIMessage，可能包含：
             - tool_calls 列表 → Agent 决定调用工具（进入 Acting 阶段）
             - 纯文本 content  → Agent 决定直接回复用户（循环结束）
          4. 日志记录 LLM 的决策（调用了哪个工具 / 直接回复了什么），
             便于开发者调试。
    """
    messages = _ensure_system_prompt(state["messages"])
    logger.debug(f"[agent] msg 数: {len(messages)}")
    response = llm_with_tools.invoke(messages)

    # 日志：LLM 做出了什么决策？
    if isinstance(response, AIMessage) and response.tool_calls:
        tc_names = [tc["name"] for tc in response.tool_calls]
        logger.info(f"[agent] 决定调用工具: {tc_names}")
    else:
        content_preview = str(response.content)[:80] if response.content else "(空)"
        logger.info(f"[agent] 决定回复用户: {content_preview}...")

    return {"messages": [response]}


def _ensure_system_prompt(messages: List[BaseMessage]) -> list:
    """
    WHAT: System Prompt 注入 — 确保角色设定始终在对话上下文头部

    WHY:  ReAct 循环中 agent 节点会被反复调用（每轮工具执行后都回到 agent）。
          但 SystemMessage 只需在首次进入循环时注入一次，后续迭代中
          历史消息已经包含它。重复注入会导致 prompt 膨胀、浪费 Token，
          甚至可能让 LLM 对角色设定的注意力产生偏差。

    HOW:  检查消息列表首条是否为 SystemMessage 实例：
          是 → 直接返回原列表（已有 SystemMessage，跳过注入）
          否 → 在头部插入 SystemMessage 后返回（首次进入循环）
    """
    if messages and isinstance(messages[0], SystemMessage):
        return list(messages)
    return [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

# ─────────────────────────────────────────────────────────
# 节点 2：工具执行节点
# ─────────────────────────────────────────────────────────
# 这是 ReAct 的 "Acting" 部分。
# ToolNode 是 LangGraph 内置的工具执行器，其内部工作流程：
#
#   1. 从最后一条 AIMessage 提取 tool_calls 列表：
#      [{ "name": "filter_search", "args": {"query": "消防车", "max_price": 50}, "id": "call_xxx" }]
#
#   2. 在函数查找表中匹配工具名 → 调用对应函数：
#      tool_calls[0]["name"] = "filter_search" → 找到 @tool filter_search 函数
#
#   3. 并发执行所有 tool_call（ThreadPoolExecutor），大幅减少等待时间。
#      如果 LLM 一次决定调用 3 个工具，ToolNode 同时执行 3 个而不是逐个串行。
#
#   4. 将返回值封装为 ToolMessage，携带 tool_call_id 用于关联：
#      ToolMessage(content="搜索结果...", tool_call_id="call_xxx")
#
#   5. 返回 {"messages": [ToolMessage, ToolMessage, ...]}，
#      add_messages reducer 将它们追加到对话历史。

MAX_TOOL_CALLS = 5  # 防止无限循环的上限

_tool_node_inner = ToolNode(all_tools)


def _tool_node(state: AgentState, config=None) -> dict:
    """
    WHAT: 工具执行节点 — ReAct 循环的 Acting 阶段，内置安全阀与超时控制

    WHY:  Agent 可能陷入无限循环（LLM 反复调用工具而不给出最终回答），
           每次工具调用都消耗 LLM Token 和检索资源。通过 tool_call_count
           计数器限制每轮的最大工具调用次数（MAX_TOOL_CALLS=5），
           超过上限后强制注入终止消息，从源头切断死循环。
           同时通过线程超时机制防止单个工具执行时间过长阻塞整个 Agent 循环。

    HOW:  1. 检查 tool_call_count 是否超过 MAX_TOOL_CALLS(5)：
              超过 → 注入一条不含 tool_calls 的 AIMessage 强制结束循环
              未超过 → 在线程池中执行 ToolNode（LangGraph 内置工具执行器），
                       设置 tool_call_timeout 超时限制
           2. ToolNode 将每个工具返回值封装为 ToolMessage，追加到 messages
           3. 递增 tool_call_count 计数器
    """
    tc = state.get("tool_call_count", 0)
    if tc >= MAX_TOOL_CALLS:
        logger.warning(f"[agent] 工具调用次数已达上限 ({MAX_TOOL_CALLS})，强制结束")
        return {"messages": [AIMessage(content="已搜索到足够信息，现在为你推荐。")]}

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_tool_node_inner.invoke, state, config)
            result = future.result(timeout=settings.tool_call_timeout)
    except FutureTimeoutError:
        logger.error(f"[agent] 工具调用超时（>{settings.tool_call_timeout}s），跳过本次工具执行")
        return {
            "messages": [AIMessage(content="工具调用超时，请尝试简化问题或稍后重试。")],
            "tool_call_count": tc + 1,
        }

    executed_names = []
    if state.get("messages"):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            executed_names = [tc["name"] for tc in last.tool_calls]
    logger.info(f"[agent] 工具执行完成: {executed_names} (累计 {tc + 1}/{MAX_TOOL_CALLS})")

    return {
        "messages": result["messages"],
        "tool_call_count": tc + 1,
    }

# ─────────────────────────────────────────────────────────
# 条件路由：决定下一步
# ─────────────────────────────────────────────────────────
# 条件边函数返回字符串，graph 根据返回值将控制流导向对应节点。
# 这是 ReAct 循环的关键：tool_calls 存在 → 继续，否则 → 结束。


def _should_continue(state: AgentState) -> Literal["tools", END]:
    """
    WHAT: 条件路由函数 — 控制 ReAct 循环的继续或终止

    WHY:  这是条件边（conditional_edges）的路由逻辑核心。
          LangGraph 根据此函数的返回值决定控制流走向：
          有 tool_calls → 继续执行工具 → 回到 agent 推理
          无 tool_calls → Agent 已完成回答 → 结束执行
          没有这个开关，循环将永远无法终止。

    HOW:  检查消息列表最后一条：
          - 如果是 AIMessage 且包含 tool_calls 字段 → 返回 "tools"
            （LangGraph 路由到 tools 节点，继续 ReAct 循环）
          - 否则（纯文本回复 / 无消息 / 非 AIMessage）→ 返回 END
            （LangGraph 结束图的执行，最终状态返回给调用方）

    Returns:
        "tools" — 继续执行工具调用（进入 Acting 阶段）
        END    — 结束 Agent 执行（图终止，返回到 run_agent 提取结果）
    """
    messages = state["messages"]
    if not messages:
        return END

    last_msg = messages[-1]

    # 如果最后一条是 AIMessage 且有 tool_calls → 执行工具
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        logger.info(f"[agent] 路由: 有 {len(last_msg.tool_calls)} 个工具调用 → 进入 tools 节点")
        return "tools"
    logger.info("[agent] 路由: 无工具调用 → 结束 ReAct 循环")
    return END

# ─────────────────────────────────────────────────────────
# 组装 StateGraph
# ─────────────────────────────────────────────────────────


# ═══ 入口 ═══
def build_agent_graph() -> CompiledStateGraph:
    """
    WHAT: 构建 ReAct Agent 图 — 组装节点和边，返回编译后的可执行图

    WHY:  LangGraph 采用声明式图构建模式：先定义节点和边的拓扑结构，
          再 compile() 为可执行对象。分离构建和执行的好处是：
          同一张图可以多次执行（不同用户、不同会话复用），避免重复构建开销。
          模块加载时调用此函数一次，全局复用 _graph 实例。

    HOW:  七步构建过程：
          1. StateGraph(AgentState)        — 创建以 AgentState 为状态类型的图构建器
          2. add_node("agent", ...)        — 注册推理节点（ReAct 的 Reasoning）
          3. add_node("tools", ...)        — 注册工具执行节点（ReAct 的 Acting）
          4. set_entry_point("agent")      — 指定 agent 为图的起始节点
          5. add_conditional_edges(...)    — agent 输出 → _should_continue 判断路由
             → "tools"（继续循环） 或 END（结束）
          6. add_edge("tools", "agent")    — 工具执行完回到 agent（形成循环闭环）
          7. compile()                     — 编译为 CompiledStateGraph 可执行对象

    Returns:
        CompiledStateGraph: 编译后的图，支持 .invoke(state) 和 .stream(state) 调用
    """
    builder = StateGraph(AgentState)

    builder.add_node("agent", _agent_node)
    builder.add_node("tools", _tool_node)

    # 起始边：对话开始 → Agent 推理
    builder.set_entry_point("agent")

    # 条件边：Agent 输出 → 工具执行 或 直接结束
    builder.add_conditional_edges("agent", _should_continue)

    # 工具执行完 → 回到 Agent，让它基于工具结果继续推理
    builder.add_edge("tools", "agent")

    graph = builder.compile()
    logger.info("[agent] LangGraph ReAct 工作流构建完成")
    return graph


# ─────────────────────────────────────────────────────────
# 便捷封装：对外暴露简单 API
# ─────────────────────────────────────────────────────────

_graph = build_agent_graph()


# ═══ 入口 ═══
def run_agent(
    user_message: str,
    messages: list | None = None,
    session_id: str = "default",
    enable_reflection: bool = False,
) -> dict:
    """
    WHAT: Agent 执行入口 — 封装完整对话流程（记忆→执行→提取→防控→保存）

    WHY:  build_agent_graph() 构建的图只能直接 invoke，缺少生产环境所需的
          记忆管理、结果提取、幻觉防控、会话上下文的集成逻辑。
          run_agent() 是面向 API 层的高级封装，将图执行与业务需求粘合在一起，
          对外暴露一行式调用接口。

    HOW:  按标准 Agent 管道顺序执行八个步骤：
          1. 记忆加载 — 从 ConversationMemory 获取历史消息（多轮对话上下文）
          2. 状态构建 — 组装 AgentState（用户消息 + 历史 + 工具计数初始值）
          3. 图执行   — _graph.invoke(initial_state) 启动 ReAct 循环
          4. 回复提取 — 反向遍历 messages，取最后一条不含 tool_calls 的 AIMessage
          5. 工具日志 — 汇总本轮所有工具调用记录 [{name, args}]
          6. 来源提取 — 从 ToolMessage 中解析检索结果（SKU、匹配度等）
          7. 幻觉防控 — 如果 guardrails 开启，验证答案是否有商品来源支撑
          8. 记忆保存 — 将本轮问答对写入 ConversationMemory 供下轮对话使用

    Args:
        user_message: 用户当前输入
        messages:     历史消息列表（可选，优先于 session 记忆）
        session_id:   会话 ID（用于记忆管理）

    Returns:
        {
            "answer":          "最终回复文本",
            "messages":        [...],   # 完整消息历史（含中间工具调用）
            "tool_calls_log":  [...],   # 工具调用摘要 [{name, args}]
            "sources":         [...],   # 检索结果来源 [{content}]
            "guardrails":      {...},   # 幻觉防控结果 {verified, has_citations, ...}
            "reflection":      {...},   # 反思修正结果（仅 enable_reflection=True）
        }
    """
    from app.core.guardrails import apply_guardrails, no_result_response
    from app.core.memory import ConversationMemory, get_memory

    # ── 步骤1/8 记忆加载 ──
    if messages:
        context_messages = list(messages)
        logger.info(f"[agent] 步骤1 记忆加载: 使用传入历史 {len(context_messages)} 条")
    else:
        memory = get_memory(session_id)
        context_messages = memory.get_context()
        logger.info(f"[agent] 步骤1 记忆加载: 会话 {session_id} {len(context_messages)} 条")

    # ── 步骤2/8 状态构建 ──
    tool_count = sum(1 for m in context_messages if isinstance(m, ToolMessage))

    initial_state: AgentState = {
        "messages": context_messages + [{"role": "user", "content": user_message}],
        "search_results": [],
        "tool_call_count": tool_count,
    }
    logger.info(f"[agent] 步骤2 状态构建: 工具计数初始值 {tool_count}")

    # ── 步骤3/8 图执行 ──
    logger.info(f"[agent] 步骤3 图执行: 用户输入 {user_message!r}")
    final_state = _graph.invoke(initial_state)
    logger.info(f"[agent] 步骤3 图执行完成: 共 {len(final_state['messages'])} 条消息")

    # ── 步骤4/8 回复提取 ──
    answer = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            answer = str(msg.content)
            break
    logger.info(f"[agent] 步骤4 回复提取: {len(answer)} 字")

    # ── 步骤5/8 工具调用日志 ──
    tool_calls_log = []
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_log.append(
                    {"name": tc["name"], "args": tc.get("args", {})}
                )
    logger.info(f"[agent] 步骤5 工具调用: {len(tool_calls_log)} 次")

    # ── 步骤6/8 来源提取 ──
    sources = _extract_sources(final_state["messages"])
    logger.info(f"[agent] 步骤6 来源提取: {len(sources)} 条")

    # ── 步骤7/8 幻觉防控 ──
    if settings.guardrails_enabled:
        if not sources and tool_calls_log:
            answer = no_result_response(user_message)
            guardrails = {"verified": True, "has_citations": False, "warnings": []}
            logger.info("[agent] 步骤7 幻觉防控: 无来源 → 返回兜底话术")
        else:
            guardrails = apply_guardrails(answer, sources, user_message)
            answer = guardrails.pop("answer", answer)
            logger.info(
                f"[agent] 步骤7 幻觉防控: verified={guardrails.get('verified')}, "
                f"警告 {len(guardrails.get('warnings', []))} 条"
            )
    else:
        guardrails = {}
        logger.info("[agent] 步骤7 幻觉防控: 已禁用")

    # ── 步骤8/8 记忆保存 ──
    if not messages:
        memory = get_memory(session_id)
        memory.add_round(user_message, answer)
        logger.info(f"[memory] 会话 {session_id}: {len(memory.full_history)} 条消息")

    # ── Token 用量追踪 ──
    try:
        from app.core.token_tracker import get_token_tracker
        tracker = get_token_tracker()
        tracker.record(
            model=settings.deepseek_model,
            prompt=user_message + str(context_messages),
            completion=answer,
            session_id=session_id,
        )
        logger.debug(f"[token] 会话 {session_id} 用量已记录")
    except Exception:
        pass

    # ── Reflection 反思修正（可选）──
    reflection_result = None
    if enable_reflection:
        from app.agent.reflection import apply_reflection
        sources_text = "\n".join(
            s.get("content", "") for s in sources
        )
        answer = apply_reflection(answer, user_message, sources_text)
        reflection_result = {"applied": True}
        logger.info("[agent] Reflection 反思修正已应用")

    return {
        "answer": answer,
        "messages": final_state["messages"],
        "tool_calls_log": tool_calls_log,
        "sources": sources,
        "guardrails": guardrails,
        "reflection": reflection_result,
    }


def _extract_sources(messages: list) -> list:
    """
    WHAT: 来源提取 — 从混合消息历史中解析出检索到的商品信息

    WHY:  完整的消息历史包含 SystemMessage、HumanMessage、AIMessage
          （含 tool_calls）、ToolMessage 等多种类型，原始数据对前端不友好。
          需要从中筛选出"真正展示给用户看"的检索结果，
          用于前端来源展示和幻觉防控验证（确保 LLM 回答有据可查）。

    HOW:  遍历所有消息，筛选 ToolMessage 类型，再通过文本特征
          （含 "SKU:" 或 "匹配度"）识别出检索工具返回的消息，
          按行解析提取商品行（以数字开头的行）。
    """
    sources = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.content:
            content = str(msg.content)
            if "[SKU:" in content or "SKU:" in content or "匹配度" in content:
                lines = content.split("\n")
                for line in lines:
                    if line.strip() and line[0].isdigit():
                        sources.append({"content": line.strip()})
    return sources
