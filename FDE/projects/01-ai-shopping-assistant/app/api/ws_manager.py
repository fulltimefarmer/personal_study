"""
WebSocket 连接管理器 — 实时对话推送与客服监控
════════════════════════════════════════════════════════

架构角色：
  在 AI 导购系统中，WebSocket 替代传统 HTTP 请求-响应模式提供：
  1. 客户端实时对话（无需轮询）
  2. 管理员实时监控（Pub/Sub 广播）
  3. 客服人工介入（intervene → Agent 代理回复）

LangChain/LangGraph 学习要点：
  本模块展示了如何在 AI 应用中将 LangChain/LangGraph Agent 与
  FastAPI WebSocket 集成。关键模式：
  - Agent 的同步 run_agent() 通过 run_in_executor 在线程池中执行
  - WebSocket 生命周期管理连接断开的清理
  - Pub/Sub 广播模式让多个 admin 同时监控会话

WebSocket vs HTTP 在 AI 应用中的选择：
  - HTTP: 适合单次请求（如健康检查、会话列表查询）
  - WebSocket: 适合多轮对话、流式输出、实时推送
  本项目 REST 端点（/health, /sessions）用 HTTP，
  对话通道（/ws/chat/{id}, /ws/admin）用 WebSocket。
"""
import asyncio
from datetime import datetime, timezone

from fastapi import WebSocket
from loguru import logger


class ConversationEvent:
    """对话事件角色常量 — 用于标记消息来源

    在 WebSocket 广播中，每条消息携带 role 字段标识发送者。
    LangChain 内部也有类似的角色概念（HumanMessage/AIMessage/SystemMessage/ToolMessage），
    这里的 role 是业务层的角色分类，与 LangChain 消息类型是不同抽象层。
    """
    ROLE_CLIENT = "client"   # 用户端发送的消息
    ROLE_AGENT = "agent"    # AI Agent 生成的回复
    ROLE_ADMIN = "admin"    # 客服人员介入的消息


class ConnectionManager:
    def __init__(self):
        self._client_connections: dict[str, WebSocket] = {}
        self._admin_connections: set[WebSocket] = set()
        self._sessions: dict[str, list[dict]] = {}
        self._session_created_at: dict[str, str] = {}

    def get_or_create_session(self, session_id: str) -> str:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            self._session_created_at[session_id] = datetime.now(
                timezone.utc
            ).isoformat()
        return session_id

    async def connect_client(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self._client_connections[session_id] = websocket
        self.get_or_create_session(session_id)
        logger.info(f"[ws] 客户端连接: {session_id}")

        history = self._sessions.get(session_id, [])
        if history:
            await websocket.send_json({"type": "history", "messages": history})

    def disconnect_client(self, session_id: str):
        self._client_connections.pop(session_id, None)
        logger.info(f"[ws] 客户端断开: {session_id}")

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self._admin_connections.add(websocket)
        logger.info(f"[ws] 客服端连接 (当前 {len(self._admin_connections)} 个)")

        sessions = [
            {
                "session_id": sid,
                "created_at": self._session_created_at.get(sid, ""),
                "message_count": len(msgs),
            }
            for sid, msgs in self._sessions.items()
        ]
        await websocket.send_json({"type": "session_list", "sessions": sessions})

    def disconnect_admin(self, websocket: WebSocket):
        self._admin_connections.discard(websocket)
        logger.info(
            f"[ws] 客服端断开 (剩余 {len(self._admin_connections)} 个)"
        )

    def add_message(
        self, session_id: str, role: str, content: str, extra: dict | None = None
    ):
        msg = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(extra or {}),
        }
        if session_id in self._sessions:
            self._sessions[session_id].append(msg)

        asyncio.create_task(self._broadcast(msg))

    async def _broadcast(self, msg: dict):
        disconnected: set[WebSocket] = set()
        payload = {"type": "conversation", "message": msg}

        for ws in self._admin_connections.copy():
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self._admin_connections.discard(ws)

    async def send_to_client(self, session_id: str, message: dict):
        ws = self._client_connections.get(session_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect_client(session_id)

    def get_session_ids(self) -> list[str]:
        return list(self._sessions.keys())

    def get_session_messages(self, session_id: str) -> list[dict]:
        return self._sessions.get(session_id, [])


manager = ConnectionManager()
