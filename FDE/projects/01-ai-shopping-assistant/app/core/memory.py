"""多轮对话记忆管理

═══════════════════════════════════════════════════════════
📦 架构角色：对话状态的持久化存储层
   本模块位于 app/core 基础设施层，为 RAG 链和 Agent
   提供"记住之前聊了什么"的能力。没有它，每次对话都
   是全新的开始，LLM 无法结合历史做出连贯推荐。
═══════════════════════════════════════════════════════════

两级记忆架构（滑动窗口 + 摘要压缩）：
  Level 1 — 滑动窗口（_recent）：
    保留最近 N 轮完整对话，确保即时上下文连贯。
    * 工作原理：只取 full_history 尾部 max_recent 条消息
    * 适用场景：最近的 2-3 轮对话细节（如"买2件多少钱"）
    * 类比：计算机的 L1 Cache — 速度快、容量小

  Level 2 — 摘要压缩（summary）：
    当消息总数超过 max_total 阈值时，将旧消息压缩为结构化摘要。
    * 触发条件：len(full_history) > max_total
    * 压缩策略：将前半部分旧消息调用 LLM 生成 2-3 句摘要
    * 摘要内容：用户偏好（年龄/预算/兴趣）、已讨论商品、用户反馈
    * 类比：计算机的 L2 Cache — 容量大、信息已提炼

  为什么需要两级而不是简单截断？
    - 纯截断会丢失重要偏好信息（如用户说过"孩子5岁"）
    - 纯摘要会丢失最近对话的细节精度
    - 两级结合 = 精度 + 容量，兼顾上下文质量和对话长度

设计考量：
  - 非侵入式：对上游调用方透明，get_context() 输出仍是标准消息列表
  - 可插拔：不依赖特定 LLM，可注入任意 ChatModel（摘要失败有 fallback）
  - 会话隔离：支持多 session_id，每个会话独立记忆空间
"""
import uuid
from typing import Dict, List, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.config import create_llm
from loguru import logger


# ═══ 入口 ═══
class ConversationMemory:
    """
    两级对话记忆（核心数据结构）

    ┌─────────────────────────────────────────────────┐
    │  完整对话历史 (full_history)                      │
    │  ┌──────────────────┬──────────────────────────┐ │
    │  │  摘要 (summary)   │  最近消息 (recent)        │ │
    │  │  → 旧消息压缩     │  → 最近 N 轮            │ │
    │  └──────────────────┴──────────────────────────┘ │
    └─────────────────────────────────────────────────┘

    触发条件：full_history 长度 > max_total 时，压缩前半部分。

    WHAT：一个对话会话的完整记忆容器
    WHY： 需要"记住"用户之前说过什么（年龄/预算/偏好），
          才能给出连贯、个性化的推荐，而非每次都是新对话
    HOW： 内部维护 full_history 列表 + summary 字符串，
         对外通过 get_context() 返回压缩后的消息列表，
         对 Agent/RAG 链完全透明
    """
    def __init__(
        self,
        session_id: str | None = None,
        max_recent: int = 10,
        max_total: int = 30,
    ):
        """
        WHAT：初始化一个对话记忆实例
        WHY：  每个会话需要一个独立的记忆空间
        HOW：  分配 UUID 短码作为 session_id，
               设定滑动窗口大小(max_recent)和压缩阈值(max_total)
        """
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.max_recent = max_recent
        self.max_total = max_total
        self.summary = ""
        self.full_history: List[BaseMessage] = []

    def add_round(self, user_text: str, assistant_text: str) -> None:
        """
        WHAT：记录一轮完整对话（用户提问 + 助手回答）
        WHY：  这是最常用的对外接口，封装了 HumanMessage + AIMessage 的创建
        HOW：  将 user_text → HumanMessage, assistant_text → AIMessage
               依次追加到 full_history，然后自动检查是否触发压缩
        """
        self.full_history.append(HumanMessage(content=user_text))
        self.full_history.append(AIMessage(content=assistant_text))
        self._maybe_compress()

    def add_message(self, message: BaseMessage) -> None:
        """
        WHAT：添加单条消息（用于 Agent 模式逐步记录）
        WHY：  Agent 模式下消息流是逐步产生的，不一定总是成对出现
        HOW：  直接追加到 full_history，触发压缩检查
        """
        self.full_history.append(message)
        self._maybe_compress()

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """
        WHAT：批量添加消息列表（用于一次性导入历史对话）
        WHY：  从文件/数据库恢复记忆时，需要高效批量写入
        HOW：  一次性 extend 全部消息，只做一次压缩检查
        """
        self.full_history.extend(messages)
        self._maybe_compress()

    def get_context(self) -> List[BaseMessage]:
        """
        WHAT：获取压缩后的上下文消息列表，供 LLM 调用
        WHY：  这是记忆模块的核心输出 — 上游只需调用此方法，
               无需关心内部是摘要还是滑动窗口
        HOW：  如果有 summary → 先插入 SystemMessage 摘要前缀，
               再追加最近 max_recent 条消息
        """
        result: List[BaseMessage] = []
        if self.summary:
            result.append(
                SystemMessage(
                    content=f"[历史对话摘要]\n{self.summary}\n\n"
                    f"以上是本次对话的过往摘要，请结合最新消息回复用户。"
                )
            )
        result.extend(self._recent_messages())
        return result

    def get_recent_user_messages(self, count: int = 5) -> List[str]:
        """
        WHAT：提取最近 N 条用户消息的纯文本内容
        WHY：  意图分析、上下文感知等场景只需要用户说了什么，不需要助手回复
        HOW：  从 recent 窗口过滤 HumanMessage，取后 count 条
        """
        recent = self._recent_messages()
        user_msgs = [
            m.content for m in recent
            if isinstance(m, HumanMessage) and m.content
        ]
        return user_msgs[-count:]

    def clear(self) -> None:
        """
        WHAT：清空当前会话的所有记忆数据
        WHY：  用户主动要求"重新开始"或切换话题时，需要抹掉历史
        HOW：  置空 summary 字符串，清空 full_history 列表
        """
        self.summary = ""
        self.full_history = []

    # ── 内部方法 ──────────────────────────────────────

    def _recent_messages(self) -> List[BaseMessage]:
        """
        WHAT：获取滑动窗口内的最近消息
        WHY：  滑动窗口保证 LLM 总能看到完整的最近几轮对话细节
        HOW：  Python 列表负索引切片 full_history[-max_recent:]
        """
        return self.full_history[-self.max_recent:]

    def _maybe_compress(self) -> None:
        """
        WHAT：触发条件检查 — 消息数超过 max_total 阈值时自动压缩
        WHY：  保持 full_history 长度可控，防止无限增长
        HOW：  计算 split 点（len - max_recent），前半部分送 LLM 摘要，
               后半部分保留为滑动窗口
        """
        if len(self.full_history) > self.max_total:
            split = max(0, len(self.full_history) - self.max_recent)
            old = self.full_history[:split]
            self.full_history = self.full_history[split:]
            if old:
                self.summary = self._summarize(old)

    def _summarize(self, messages: List[BaseMessage]) -> str:
        """
        WHAT：调用 LLM 将一批旧消息压缩为 2-3 句结构化摘要
        WHY：  旧消息不能丢弃（包含用户偏好），但原样保留太占 token
        HOW：  将消息列表转为 [角色] 文本格式，用 LLM + 摘要 prompt
                 生成摘要，失败时降级为 _fallback_summary
        """
        try:
            llm = create_llm(temperature=0.0)
            prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个对话摘要生成器。请将以下对话历史压缩为 2-3 句话的摘要，
重点记录：用户的需求偏好（年龄、预算、兴趣）、已讨论过的商品、用户的决定或反馈。
只输出摘要文本，不要包含任何格式标记或前缀。"""),
                ("human", "对话历史：\n{history}\n\n请生成摘要："),
            ])
            chain = prompt | llm | StrOutputParser()
            text = self._messages_to_text(messages)
            result = chain.invoke({"history": text})
            result = result.strip()
            logger.debug(f"[memory] 摘要完成: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"[memory] 摘要失败: {e}，使用截断策略")
            return self._fallback_summary(messages)

    @staticmethod
    def _messages_to_text(messages: List[BaseMessage]) -> str:
        """
        WHAT：将 LangChain BaseMessage 列表转为 [角色] 内容的纯文本
        WHY：  摘要 prompt 需要纯文本输入，不能直接传 message 对象
        HOW：  遍历消息，判断 isinstance 决定角色标签
        """
        lines = []
        for m in messages:
            role = "用户" if isinstance(m, HumanMessage) else (
                "助手" if isinstance(m, AIMessage) else "系统"
            )
            content = str(m.content) if m.content else "(工具调用)"
            lines.append(f"[{role}] {content}")
        return "\n".join(lines)

    @staticmethod
    def _fallback_summary(messages: List[BaseMessage]) -> str:
        """
        WHAT：LLM 不可用时的降级摘要策略（纯规则文本拼接）
        WHY：  不能让摘要失败导致整个对话崩溃，必须有兜底
        HOW：  提取最后 5 条用户消息，用 "；" 拼接为 "用户曾咨询：xxx"
        """
        user_msgs = [
            m.content for m in messages
            if isinstance(m, HumanMessage) and m.content
        ]
        if not user_msgs:
            return "(对话记录)"
        text = "；".join([str(m)[:120] for m in user_msgs[-5:]])
        return f"用户曾咨询：{text}"


# ── 全局会话管理 ─────────────────────────────────────

_sessions: Dict[str, ConversationMemory] = {}

# ═══ 入口 ═══
def get_memory(session_id: str = "default") -> ConversationMemory:
    """
    WHAT：全局会话记忆管理器 — 获取或创建指定 session 的记忆实例
    WHY：  多个 CLI 会话（或多个用户）需要隔离的记忆空间，
          但不想让每个调用方自己管理 dict 和生命周期
    HOW：  使用模块级 _sessions dict 做注册中心，
          不存在则新建 ConversationMemory，存在则直接返回
    """
    if session_id not in _sessions:
        _sessions[session_id] = ConversationMemory(session_id=session_id)
        logger.debug(f"[memory] 新建会话: {session_id}")
    return _sessions[session_id]


def clear_memory(session_id: str = "default") -> None:
    """清除指定会话记忆"""
    if session_id in _sessions:
        _sessions[session_id].clear()
        del _sessions[session_id]
        logger.info(f"[memory] 已清除会话: {session_id}")
