"""
Agent 状态定义 — ReAct 循环中的共享"黑板"数据结构
══════════════════════════════════════════════════════════

架构角色：
  AgentState 是 LangGraph ReAct 循环中所有节点共享的中央数据容器。
  每个节点（agent/tools）读取 State 中的信息做决策，执行完毕后
  返回部分更新 dict，LangGraph 自动将更新合并回 State。

  类比：如果把 Graph 看作流水线，AgentState 就是流水线上流转的"工件"，
  每个工位（节点）在上面添加自己的成果，然后传给下一个工位。

LangGraph 核心概念：
  StateGraph 中的 State 使用 TypedDict 定义，每一个节点函数接收 State
  并返回部分 State 更新。LangGraph 自动将节点返回值合并到当前状态中。

Annotated[list, add_messages] 的核心机制：
  这不是普通 list，而是带有 "reducer"（归约器）的特殊类型注解。
  当节点 return {"messages": [new_msg]} 时，new_msg 被**追加**到列表尾部，
  而不是替换整个列表 —— 这保证了对话历史的多轮累积。

  三个关键技术点的关系：
  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────────┐
  │  TypedDict   │  │    Annotated     │  │    add_messages     │
  │  定义字段结构 │+│  附加 reducer 元数据 │=│  字段追加而非替换    │
  └─────────────┘  └──────────────────┘  └─────────────────────┘

  - TypedDict:    定义固定字段名和类型的字典结构（类似轻量级 dataclass）
  - Annotated:    Python typing 的元数据装饰器，给类型附加上下文标注
  - add_messages: LangGraph 内置的消息归约器，控制 messages 字段的合并逻辑
                  它能正确处理 AIMessage、ToolMessage 的配对追加和去重

  为什么不用普通 dict？
  - 普通 dict 做节点间通信时，同名字段会被**替换**
  - 但对话历史需要**累加**（每条新消息都追加到历史）
  - Annotated[list, add_messages] 正是解决"替换 vs 追加"矛盾的机制
"""
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    WHAT: Agent 共享状态 — ReAct 循环中所有节点读写的中心数据结构

    WHY:  在 LangGraph 的多节点架构中，需要统一的状态容器让各节点协同工作。
          没有统一 State，节点间将无法传递信息：
          - Agent 节点往 State 写入 LLM 的推理结果（AIMessage，可能含 tool_calls）
          - Tools 节点往 State 写入工具执行结果（ToolMessage）
          - 条件路由读取最后一条消息，判断是否继续循环
          - 最终状态包含了完整对话历史，API 层可以提取回复和来源

    HOW:  使用 TypedDict 定义三个字段，其中 messages 使用
          Annotated[list, add_messages] 实现自动追加语义。

    Fields:
        messages        — 完整对话历史（含用户消息、AI回复、工具调用结果）
                          Annotated + add_messages 确保追加而非覆盖
                          这是 TypedDict + Annotated + add_messages 的核心应用

        search_results  — 当前轮次的商品检索结果缓存
                          避免同一轮中重复检索相同查询

        tool_call_count — 本轮工具调用计数，超过 MAX_TOOL_CALLS(5) 后
                          强制结束循环，防止 Agent 陷入无限循环
    """

    messages: Annotated[list, add_messages]
    search_results: list
    tool_call_count: int
