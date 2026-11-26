import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.agent.graph import run_agent
from app.api.schemas import SessionInfo
from app.api.ws_manager import ConversationEvent, manager
from app.config import settings
from app.core.memory import clear_memory

router = APIRouter()

# ── REST 健康检查 ──
@router.get("/health")
async def health():
    return {"status": "ok"}

# ── 获取所有会话列表 ──
@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions():
    return [
        SessionInfo(
            session_id=sid,
            created_at=manager._session_created_at.get(sid, ""),
            message_count=len(manager._sessions.get(sid, [])),
        )
        for sid in manager.get_session_ids()
    ]

# ── 获取指定会话消息 ──
@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    return manager.get_session_messages(session_id)

# ── 清空会话 ──
@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    clear_memory(session_id)
    manager._sessions.pop(session_id, None)
    manager._session_created_at.pop(session_id, None)
    return {"status": "deleted", "session_id": session_id}


# ── 客户端 WebSocket ──
@router.websocket("/ws/chat/{session_id}")
async def client_websocket(websocket: WebSocket, session_id: str):
    await manager.connect_client(websocket, session_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "无效的 JSON"})
                continue

            user_message = payload.get("message", "").strip()
            if not user_message:
                continue

            is_admin = payload.get("admin", False)
            logger.info(f"[ws] 收到消息: {user_message!r} (session={session_id}, admin={is_admin})")

            if is_admin:
                manager.add_message(
                    session_id, ConversationEvent.ROLE_ADMIN, user_message
                )

            manager.add_message(
                session_id, ConversationEvent.ROLE_CLIENT, user_message
            )

            await websocket.send_json(
                {"type": "status", "message": "thinking", "session_id": session_id}
            )

            loop = asyncio.get_event_loop()

            cached = await loop.run_in_executor(None, _check_cache, user_message)
            if cached:
                logger.info(f"[ws] 缓存命中: {user_message!r}")
                answer = cached
                tool_calls_log: list = []
                sources: list = []
                guardrails: dict = {}
            else:
                routed = await _route_or_delegate(loop, user_message, session_id)
                if routed:
                    logger.info(f"[ws] 本地路由命中: {user_message!r}")
                    answer = routed["answer"]
                    tool_calls_log = routed.get("tool_calls_log", [])
                    sources = routed.get("sources", [])
                    guardrails = routed.get("guardrails", {})
                else:
                    logger.info(f"[ws] 进入 Agent: {user_message!r}")
                    result = await _run_agent_safe(loop, user_message, session_id)
                    answer = result["answer"]
                    tool_calls_log = result.get("tool_calls_log", [])
                    sources = result.get("sources", [])
                    guardrails = result.get("guardrails", {})
                    await loop.run_in_executor(
                        None, _set_cache, user_message, answer
                    )

            manager.add_message(
                session_id,
                ConversationEvent.ROLE_AGENT,
                answer,
                {"tool_calls": tool_calls_log, "sources": sources},
            )

            await websocket.send_json(
                {
                    "type": "response",
                    "answer": answer,
                    "session_id": session_id,
                    "tool_calls_log": tool_calls_log,
                    "sources": sources,
                    "guardrails": guardrails,
                }
            )

    except WebSocketDisconnect:
        manager.disconnect_client(session_id)


# ── 客服端 WebSocket ──
@router.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket):
    await manager.connect_admin(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "无效的 JSON"})
                continue

            action = payload.get("action", "")
            session_id = payload.get("session_id", "")

            if action == "join_session":
                msgs = manager.get_session_messages(session_id)
                await websocket.send_json(
                    {"type": "session_history", "session_id": session_id, "messages": msgs}
                )

            elif action == "intervene":
                message = payload.get("message", "").strip()
                if not message or not session_id:
                    continue

                manager.add_message(
                    session_id, ConversationEvent.ROLE_ADMIN, message
                )
                manager.add_message(
                    session_id, ConversationEvent.ROLE_CLIENT, message
                )

                await websocket.send_json(
                    {
                        "type": "status",
                        "message": "intervening",
                        "session_id": session_id,
                    }
                )

                loop = asyncio.get_event_loop()

                routed = await _route_or_delegate(loop, message, session_id)
                if routed:
                    answer = routed["answer"]
                    tool_calls_log = routed.get("tool_calls_log", [])
                    sources = routed.get("sources", [])
                else:
                    result = await _run_agent_safe(loop, message, session_id)

                    answer = result["answer"]
                    tool_calls_log = result.get("tool_calls_log", [])
                    sources = result.get("sources", [])

                manager.add_message(
                    session_id,
                    ConversationEvent.ROLE_AGENT,
                    answer,
                    {"tool_calls": tool_calls_log, "sources": sources},
                )

                await websocket.send_json(
                    {
                        "type": "intervene_result",
                        "session_id": session_id,
                        "answer": answer,
                        "tool_calls_log": tool_calls_log,
                        "sources": sources,
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)


async def _run_agent_safe(loop, user_message: str, session_id: str) -> dict:
    """Agent 执行失败时返回可读降级回复，避免 WebSocket 直接断开。"""
    try:
        return await loop.run_in_executor(
            None, run_agent, user_message, None, session_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[ws] Agent 执行失败: {exc}")
        return {
            "answer": (
                "抱歉，当前本地/云端模型暂时不可用。\n"
                "请确认 Ollama 已启动并拉取 qwen2.5:3b，或配置 DEEPSEEK_API_KEY。\n"
                "商品检索和健康检查仍然可用。"
            ),
            "tool_calls_log": [],
            "sources": [],
            "guardrails": {},
        }


async def _route_or_delegate(loop, user_message: str, session_id: str) -> dict | None:
    """本地优先路由。

    返回 dict 表示已在本进程回答；返回 None 表示交给 Agent 处理。

    路由策略：
    1. 闲聊/无关问题 → 模板回复（零成本）
    2. 简单商品问题 → 本地 Ollama 常识回答
    3. 没有 DeepSeek Key 时的商品导购 → 固定 RAGChain
       （Qwen2.5-3B 的 ReAct 工具选择不稳定，固定 RAG 更可靠且有来源）
    4. 其余（售后/订单/活动/有 Key 的复杂问题）→ Agent
    """
    def _sync_route() -> dict | None:
        from app.config import has_deepseek_key
        from app.rag.query_processor import (
            answer_with_local_llm,
            classify_intent,
            get_intent_response,
            needs_deepseek_agent,
            INTENT_CHITCHAT,
            INTENT_OFF_TOPIC,
            INTENT_PRODUCT,
        )

        intent = classify_intent(user_message)

        if intent in (INTENT_CHITCHAT, INTENT_OFF_TOPIC):
            logger.info(f"[ws-router] {intent} → 模板回复")
            return {
                "answer": get_intent_response(intent, user_message) or "",
                "sources": [],
                "tool_calls_log": [],
                "guardrails": {},
            }

        if settings.use_local_for_simple and not needs_deepseek_agent(user_message, intent):
            logger.info(f"[ws-router] 简单问题 → 本地 Ollama: {user_message!r}")
            return {
                "answer": answer_with_local_llm(user_message),
                "sources": [],
                "tool_calls_log": [],
                "guardrails": {},
            }

        if intent == INTENT_PRODUCT and not has_deepseek_key():
            logger.info(f"[ws-router] 无 DeepSeek Key → 固定 RAG: {user_message!r}")
            from app.rag.chain import RAGChain

            result = RAGChain().query(user_message)
            return {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "tool_calls_log": [{"name": "rag_chain", "args": {"query": user_message}}],
                "guardrails": {},
            }

        return None

    return await loop.run_in_executor(None, _sync_route)


def _check_cache(query: str) -> str | None:
    """检查响应缓存"""
    try:
        from app.core.cache import get_query_cache
        return get_query_cache().get(query)
    except Exception:
        return None


def _set_cache(query: str, answer: str):
    """写入响应缓存"""
    try:
        from app.core.cache import get_query_cache
        get_query_cache().set(query, answer)
    except Exception:
        pass
