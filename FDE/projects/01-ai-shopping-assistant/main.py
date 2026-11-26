"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🧱  樂高智能导购助手 — 小砖家                            ║
║     LEGO Smart Shopping Assistant                            ║
║                                                              ║
║     一个基于 RAG（检索增强生成）的智能导购系统，帮助用户      ║
║     从乐高商品库中搜索、筛选、推荐合适的积木套装。            ║
║                                                              ║
║     架构特点：                                                ║
║     ├─ 双 RAG 模式：固定 RAG / Agentic RAG（自主决策）       ║
║     ├─ 意图路由：自动区分商品咨询 / 闲聊 / 无关话题           ║
║     ├─ 幻觉防控：来源标注 + 溯源校验 + 无结果兜底             ║
║     ├─ 对话记忆：滑动窗口 + 摘要压缩的两级记忆                ║
║     ├─ 向量检索：ChromaDB 语义搜索 + 属性过滤                 ║
║     ├─ Reflection：回答后反思修正（Generate→Reflect→Revise）  ║
║     ├─ Plan-and-Execute：复杂任务分解逐步执行                  ║
║     ├─ Multi-Agent：Supervisor + 子Agent 协作                 ║
║     └─ Structured Output：Pydantic 强制结构化输出              ║
║                                                              ║
║     技术栈：LangChain + ChromaDB + DeepSeek/Ollama + Loguru ║
║     LLM 模型：deepseek-v4-flash / qwen2.5:3b（可配置）      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

CLI 子命令：ingest / query / agent / compare / stats / eval / intent / memory / serve / reflection / plan / multi / quality

运行方式：
  python main.py query      # 固定 RAG 对话模式
  python main.py agent      # Agentic RAG 对话模式
  python main.py ingest     # 重建向量库
  python main.py stats      # 查看向量库统计
  python main.py reflection # 测试 Reflection（反思修正）模式
  python main.py plan       # 测试 Plan-and-Execute（任务分解）模式
  python main.py multi      # 测试 Multi-Agent（多Agent协作）模式
  python main.py quality    # RAGAS 质量评测
"""
import argparse
import time
import uuid
from pathlib import Path

from loguru import logger

from app.config import PROJECT_ROOT, settings
from app.core.logging import setup_logging

_SESSION_ID = f"cli_{uuid.uuid4().hex[:8]}"


def _enable_readline() -> None:
    """启用 CLI 行编辑；Windows 没有 GNU readline 时静默跳过。"""
    try:
        import readline  # noqa: F401
    except ImportError:
        pass


def _route_intent(query: str) -> str | None:
    """智能路由：依次判断意图→复杂度→选择合适的回答方式

    WHAT: 三层路由决策：
      1. 闲聊/无关 → 模板回复（零成本）
      2. 商品咨询但不需要工具 → 本地 Ollama 回答（免费）
      3. 商品咨询且需要工具 → 返回 None，由上游调用 DeepSeek Agent（付费）

    WHY:  最大化利用本地 Ollama，最小化 DeepSeek API 调用，节省费用。
           规则判断 μs 级，不影响用户体验。
    """
    from app.rag.query_processor import (
        answer_with_local_llm,
        classify_intent,
        get_intent_response,
        needs_deepseek_agent,
        INTENT_CHITCHAT,
        INTENT_OFF_TOPIC,
        INTENT_PRODUCT,
        INTENT_AFTER_SALES,
        INTENT_ORDER,
        INTENT_PROMOTION,
    )

    intent = classify_intent(query)

    if intent in (INTENT_CHITCHAT, INTENT_OFF_TOPIC):
        return get_intent_response(intent, query)

    if settings.use_local_for_simple and not needs_deepseek_agent(query, intent):
        logger.info(f"[router] 简单问题 → 本地 Ollama: {query!r}")
        return answer_with_local_llm(query)

    return None


# ═══ CLI入口: init_db ═══
def cmd_init_db():
    """初始化关系数据库（默认 SQLite）：创建商品表和库存表，导入 CSV 数据"""
    from scripts.init_db import seed_data
    seed_data(settings.product_csv_path)


# ═══ CLI入口: ingest ═══
def cmd_ingest():
    """重建向量库：从 CSV 产品数据中提取、嵌入、存入 ChromaDB（多粒度模式）"""
    from app.data.loader import ProductDataLoader
    from app.vector_store.chroma_store import ChromaStore

    logger.info("重建向量库（多粒度模式: 名称 + 描述 + 完整）...")
    store = ChromaStore()
    store.delete_collection()

    store2 = ChromaStore()
    loader = ProductDataLoader(settings.product_csv_path)
    docs = loader.build_embed_docs_multi_granularity()
    count = store2.add_documents(docs)
    # 记录当前 embedding provider，启动脚本据此判断是否需要重建，
    # 避免每次启动都重复向量化。
    marker = Path(PROJECT_ROOT) / "db" / f".ingest_{settings.embed_provider}"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(count), encoding="utf-8")
    logger.success(f"向量库重建完成，共 {count} 条文档")


# ═══ CLI入口: query ═══
def cmd_query():
    """交互式导购对话（固定 RAG 模式）：检索 + 生成同步执行"""
    _enable_readline()

    from app.rag.chain import RAGChain

    chain = RAGChain()

    print("=" * 60)
    print("  乐高导购助手 · 小砖家")
    print("  输入 /bye 退出，/search 仅检索，/intent 查看意图")
    print("=" * 60)

    while True:
        try:
            question = input("\n🧱 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() in ("/bye", "/exit", "/quit"):
            print("再见！")
            break

        if question.startswith("/search "):
            results = chain.search_only(question[len("/search "):])
            for i, r in enumerate(results, 1):
                meta = r["metadata"]
                print(
                    f"  {i}. {meta.get('name')} | "
                    f"{meta.get('series')} | "
                    f"${meta.get('price', 0):.2f} | "
                    f"匹配度: {r['score']:.2%}"
                )
            continue

        if question.startswith("/intent"):
            from app.rag.query_processor import classify_intent
            target = question[len("/intent"):].strip() or question.lstrip("/intent ")
            intent = classify_intent(target)
            print(f"  意图分类: {intent}")
            continue

        # ── 意图路由 ──
        routed = _route_intent(question)
        if routed:
            print(f"\n🧱 小砖家：{routed}")
            continue

        result = chain.query(question, k=4)
        print(f"\n🧱 小砖家：{result['answer']}")


# ═══ CLI入口: stats ═══
def cmd_stats():
    """查看向量库统计：商品总数、系列列表"""
    from app.vector_store.chroma_store import ChromaStore

    store = ChromaStore()
    logger.info(f"向量库商品总数: {store.count()}")
    series = store.list_series()
    logger.info(f"系列列表 ({len(series)} 个): {', '.join(series)}")


# ═══ CLI入口: eval ═══
def cmd_eval():
    """运行召回评测：测试检索准确率和召回率"""
    from scripts.eval_recall import run_evaluation

    run_evaluation()


# ═══ CLI入口: agent ═══
def cmd_agent():
    """Agentic RAG 模式：LLM 自主决定何时检索、用什么工具"""
    _enable_readline()

    from app.agent.graph import run_agent
    from app.core.memory import clear_memory

    session_id = _SESSION_ID
    print("=" * 60)
    print(f"  乐高导购助手 · 小砖家（Agent 模式）")
    print(f"  会话: {session_id}")
    print(f"  输入 /bye 退出，/clear 清空对话，/intent 查看意图")
    print("=" * 60)

    while True:
        try:
            question = input("\n🧱 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() in ("/bye", "/exit", "/quit"):
            print("再见！")
            break
        if question.lower() == "/clear":
            clear_memory(session_id)
            print("对话已清空。")
            continue

        # ── 意图路由 ──
        if not question.startswith("/"):
            routed = _route_intent(question)
            if routed:
                print(f"\n🧱 小砖家：{routed}")
                continue

        if question == "/intent":
            print("  请输入 /intent <问题> 来查看意图分类")
            continue
        if question.startswith("/intent "):
            from app.rag.query_processor import classify_intent
            target = question[len("/intent "):].strip()
            intent = classify_intent(target)
            print(f"  意图分类: {intent}")
            continue

        result = run_agent(question, session_id=session_id)

        # 打印工具调用过程
        if result["tool_calls_log"]:
            for tc in result["tool_calls_log"]:
                args_str = ", ".join(
                    f"{k}={v!r}" for k, v in tc["args"].items() if v
                )
                print(f"  ⚙  [{tc['name']}]({args_str})")

        # 打印幻觉防控警告
        guard = result.get("guardrails", {})
        if guard.get("warnings"):
            for w in guard["warnings"]:
                print(f"  ⚠  [guardrails] {w}")

        print(f"\n🧱 小砖家：{result['answer']}")


# ═══ CLI入口: compare ═══
def cmd_compare():
    """对比模式：同一问题用固定 RAG 和 Agentic RAG 分别回答"""
    question = input("请输入对比问题: ").strip()
    if not question:
        return

    from app.rag.query_processor import classify_intent, INTENT_PRODUCT

    intent = classify_intent(question)
    if intent != INTENT_PRODUCT:
        from app.rag.query_processor import get_intent_response
        routed = get_intent_response(intent, question)
        print(f"意图: {intent} → {routed}")
        return

    print(f"\n{'=' * 60}")
    print(f"  对比问题: {question}")
    print(f"  意图分类: {intent}")
    print(f"{'=' * 60}")

    # ── 固定 RAG ──
    print("\n── 固定 RAG 模式 ──")
    from app.rag.chain import RAGChain
    chain = RAGChain()
    t0 = time.time()
    rag_result = chain.query(question, k=4)
    rag_time = time.time() - t0

    from app.core.guardrails import apply_guardrails
    rag_guard = apply_guardrails(
        rag_result["answer"],
        [{"metadata": {"name": s["name"], "sku": s["sku"]}, "score": s["score"]}
         for s in rag_result["sources"]],
        question,
    )
    # 显示原始回答（不含来源标注的简短版）
    print(f"\n回答: {rag_result['answer'][:300]}...")
    print(f"幻觉防控: {'通过' if rag_guard['verified'] else '⚠ 有风险'}")
    if rag_guard["warnings"]:
        for w in rag_guard["warnings"]:
            print(f"  ⚠ {w}")
    print(f"\n来源 ({len(rag_result['sources'])} 条):")
    for s in rag_result["sources"]:
        print(f"  - {s['name']} ({s['score']:.1%})")
    print(f"\n耗时: {rag_time:.2f}s")

    # ── Agentic RAG ──
    print(f"\n{'─' * 60}")
    print("\n── Agentic RAG 模式 ──")
    from app.agent.graph import run_agent
    t0 = time.time()
    agent_result = run_agent(question)
    agent_time = time.time() - t0
    if agent_result["tool_calls_log"]:
        for tc in agent_result["tool_calls_log"]:
            args_str = ", ".join(
                f"{k}={v!r}" for k, v in tc["args"].items() if v
            )
            print(f"  ⚙  [{tc['name']}]({args_str})")
    guard = agent_result.get("guardrails", {})
    print(f"\n回答: {agent_result['answer'][:300]}...")
    print(f"幻觉防控: {'通过' if guard.get('verified') else '⚠ 有风险'}")
    if guard.get("warnings"):
        for w in guard["warnings"]:
            print(f"  ⚠ {w}")
    print(f"\n工具调用次数: {len(agent_result['tool_calls_log'])}")
    print(f"耗时: {agent_time:.2f}s")


# ═══ CLI入口: reflection ═══
def cmd_reflection():
    """测试 Reflection（反思修正）模式：生成 → 反思 → 修正循环"""
    _enable_readline()

    from app.agent.graph import run_agent
    from app.agent.reflection import apply_reflection

    session_id = _SESSION_ID
    print("=" * 60)
    print(f"  乐高导购助手 · 小砖家（Reflection 反思模式）")
    print(f"  流程: Agent生成 → 反思审阅 → 修正 → 输出")
    print(f"  输入 /bye 退出")
    print("=" * 60)

    while True:
        try:
            question = input("\n🧱 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() in ("/bye", "/exit", "/quit"):
            print("再见！")
            break

        routed = _route_intent(question)
        if routed:
            print(f"\n🧱 小砖家：{routed}")
            continue

        result = run_agent(question, session_id=session_id)
        raw_answer = result["answer"]
        sources_text = "\n".join(
            s.get("content", "") for s in result.get("sources", [])
        )

        if result["tool_calls_log"]:
            for tc in result["tool_calls_log"]:
                args_str = ", ".join(
                    f"{k}={v!r}" for k, v in tc["args"].items() if v
                )
                print(f"  ⚙  [{tc['name']}]({args_str})")

        refined_answer = apply_reflection(raw_answer, question, sources_text)
        print(f"\n🧱 小砖家：{refined_answer}")


# ═══ CLI入口: plan ═══
def cmd_plan():
    """测试 Plan-and-Execute（任务分解）模式"""
    from app.agent.planner import run_plan_and_execute

    print("=" * 60)
    print("  乐高导购助手 · 小砖家（Plan-and-Execute 模式）")
    print("  流程: 规划 → 逐步执行 → 汇总")
    print("  输入 /bye 退出")
    print("=" * 60)

    while True:
        try:
            question = input("\n🧱 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() in ("/bye", "/exit", "/quit"):
            print("再见！")
            break

        routed = _route_intent(question)
        if routed:
            print(f"\n🧱 小砖家：{routed}")
            continue

        answer = run_plan_and_execute(question)
        print(f"\n🧱 小砖家：{answer}")


# ═══ CLI入口: multi ═══
def cmd_multi():
    """测试 Multi-Agent（多Agent协作）模式"""
    from app.agent.multi_agent import run_multi_agent

    print("=" * 60)
    print("  乐高导购助手 · 小砖家（Multi-Agent 模式）")
    print("  Agent: Supervisor + 导购/售后/订单 子Agent")
    print("  输入 /bye 退出")
    print("=" * 60)

    history = []
    while True:
        try:
            question = input("\n🧱 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() in ("/bye", "/exit", "/quit"):
            print("再见！")
            break

        answer = run_multi_agent(question, history)
        from langchain_core.messages import AIMessage, HumanMessage
        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=answer))
        print(f"\n🧱 小砖家：{answer}")


# ═══ CLI入口: quality ═══
def cmd_quality():
    """运行 RAGAS 质量评测：Faithfulness + Relevance + Pairwise"""
    from scripts.eval_quality import run_full_evaluation
    run_full_evaluation()


# ═══ CLI入口: agent-switch ═══
def cmd_agent_switch_test():
    """运行 Agent 切换逻辑测试：本地/远程路由、多模态、网络搜索、人工介入等决策"""
    from scripts.test_agent_switching import run_all_tests
    success = run_all_tests()
    if not success:
        raise SystemExit(1)


# ═══ CLI入口: memory ═══
def cmd_memory_test():
    """测试对话记忆功能：验证滑动窗口 + 摘要压缩"""
    from app.core.memory import ConversationMemory

    print("=" * 60)
    print("  记忆管理测试")
    print("=" * 60)

    mem = ConversationMemory(max_recent=6, max_total=12)

    test_conversation = [
        ("你好，我想给孩子买乐高", "你好！孩子多大啦？有什么兴趣方向吗？"),
        ("孩子5岁，喜欢消防车", "推荐您看看城市系列的消防车，适合5岁以上。需要了解具体型号吗？"),
        ("有什么推荐的型号吗", "有LEGO City 消防指挥车等几款热门产品。"),
        ("买2件多少钱", "消防指挥车单价$39.99，两件总价$79.98。"),
        ("好的谢谢", "不客气！"),
        ("再推荐个适合7岁的", "这个年龄可以尝试科技系列了。"),
        ("有没有太空系列的", "当然有！太空系列有几款适合不同年龄的。"),
        ("帮我看看具体型号", "为您查看太空火箭发射中心详情。"),
    ]

    for i, (user, assistant) in enumerate(test_conversation, 1):
        mem.add_round(user, assistant)
        status = (
            f"[{len(mem.full_history)}条消息]"
            if not mem.summary else
            f"[压缩! {len(mem.full_history)}条消息] 摘要: {mem.summary[:60]}..."
        )
        print(f"  第{i}轮: {status}")

    print(f"\n最终状态: {len(mem.full_history)}条消息, 摘要长度: {len(mem.summary)}字")
    print(f"上下文消息数: {len(mem.get_context())}")


# ═══ CLI入口: serve ═══
def cmd_serve():
    """启动 FastAPI 服务（含 WebSocket 支持）"""
    import uvicorn

    from app.api.server import create_app

    app = create_app()
    logger.info("启动 FastAPI 服务 → http://localhost:8000")
    logger.info("WebSocket Chat  → ws://localhost:8000/ws/chat/{session_id}")
    logger.info("WebSocket Admin → ws://localhost:8000/ws/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ═══ CLI入口: intent ═══
def cmd_intent_test():
    """测试意图路由准确性：运行预设测试用例并统计准确率"""
    from app.rag.query_processor import classify_intent

    test_cases = [
        ("你好", "chitchat"),
        ("推荐个适合5岁孩子的乐高", "product_inquiry"),
        ("消防车多少钱", "product_inquiry"),
        ("谢谢你的推荐", "chitchat"),
        ("再见", "chitchat"),
        ("帮我写个Python代码", "off_topic"),
        ("今天股票涨了没", "off_topic"),
        ("有没有便宜一点的", "product_inquiry"),
        ("你是谁", "chitchat"),
        ("乐高星球大战系列有哪些", "product_inquiry"),
        ("帮我推荐一个礼物", "product_inquiry"),
        ("你能干什么", "chitchat"),
        ("你觉得特朗普怎么样", "off_topic"),
        ("太空系列有什么好玩的", "product_inquiry"),
        ("我只想买苹果手机", "off_topic"),
    ]

    print("=" * 60)
    print("  意图路由测试")
    print("=" * 60)

    correct = 0
    total = len(test_cases)
    for query, expected in test_cases:
        actual = classify_intent(query)
        ok = "✓" if actual == expected else "✗"
        if actual == expected:
            correct += 1
        print(f"  {ok} [{expected:20s}] {query:30s} → {actual}")

    print(f"\n准确率: {correct}/{total} ({correct/total:.1%})")


# ═══════════ 程序入口 ═══════════
def main():
    """
    WHAT：程序总入口 — 命令行参数解析 + 子命令路由分发
    WHY：  统一入口管理所有功能（ingest/query/agent/compare/stats/eval/...）
          让用户通过 `python main.py <command>` 调用不同功能
    HOW：  用 argparse 定义子命令 → 查分发表 dict dispatch 路由到对应函数
    """
    parser = argparse.ArgumentParser(description="乐高智能导购助手")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ingest", help="从 CSV 重建向量库")
    sub.add_parser("init-db", help="初始化关系数据库（默认 SQLite，商品表+库存表）")
    sub.add_parser("query", help="交互式导购对话（固定 RAG）")
    sub.add_parser("agent", help="交互式导购对话（Agentic RAG）")
    sub.add_parser("compare", help="对比固定 RAG vs Agentic RAG")
    sub.add_parser("stats", help="查看向量库统计")
    sub.add_parser("eval", help="运行召回评测")
    sub.add_parser("intent", help="意图路由测试")
    sub.add_parser("memory", help="记忆管理测试")
    sub.add_parser("reflection", help="Reflection 反思修正模式测试")
    sub.add_parser("plan", help="Plan-and-Execute 任务分解模式测试")
    sub.add_parser("multi", help="Multi-Agent 多Agent协作模式测试")
    sub.add_parser("quality", help="RAGAS 质量评测")
    sub.add_parser("agent-switch", help="Agent 切换逻辑测试")
    sub.add_parser("serve", help="启动 FastAPI 服务")

    args = parser.parse_args()
    setup_logging(settings.debug)

    dispatch = {
        "ingest": cmd_ingest,
        "init-db": cmd_init_db,
        "query": cmd_query,
        "agent": cmd_agent,
        "compare": cmd_compare,
        "stats": cmd_stats,
        "eval": cmd_eval,
        "intent": cmd_intent_test,
        "memory": cmd_memory_test,
        "reflection": cmd_reflection,
        "plan": cmd_plan,
        "multi": cmd_multi,
        "quality": cmd_quality,
        "agent-switch": cmd_agent_switch_test,
        "serve": cmd_serve,
    }

    if args.command in dispatch:
        dispatch[args.command]()
    else:
        parser.print_help()


# ═══════════════════════════════════════════════════════
#  🚀 程序启动点：当直接执行 main.py 时从这里开始
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
