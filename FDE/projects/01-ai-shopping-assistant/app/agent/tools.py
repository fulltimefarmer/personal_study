"""
Agent 业务工具 — LLM 调用的能力函数集合
══════════════════════════════════════════

架构角色：
  工具函数是 Agent 与外部世界交互的唯一手段。LLM 不能直接操作数据库或
  做数学计算，必须通过工具调用来执行具体操作。本模块定义了导购助手的
  所有业务能力，包括商品搜索、订单查询、售后工单、会员查询、平台活动、
  转人工等。

工具分类：
  ┌─ 商品导购 ──── semantic_search / filter_search / get_product_detail / calculate_price
  ├─ 网络搜索 ──── web_search
  ├─ 售后工单 ──── query_after_sales_policy / create_service_ticket
  ├─ 订单会员 ──── query_order / query_membership
  ├─ 平台活动 ──── search_promotions
  └─ 人工兜底 ──── transfer_to_human
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool
from loguru import logger
from tavily import TavilyClient

from app.config import settings
from app.data.database import get_available_skus, get_inventory_batch
from app.vector_store.chroma_store import ChromaStore

_store = ChromaStore()
_tavily = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None


# ═══ 入口 ═══
@tool
def semantic_search(query: str) -> str:
    """
    WHAT: 语义搜索 — 纯自然语言理解检索，无结构化过滤

    WHY:  用户需求往往模糊（"好玩的"、"适合送人的"），无法转化为精确的
          筛选条件。语义搜索利用向量相似度匹配，在向量空间中自动找到
          语义相近的商品，适合作为兜底搜索策略或用户没有明确条件时
          的首选工具。

    HOW:  @tool 装饰器将本函数的签名和 docstring 生成 function calling schema，
          LLM 识别到模糊需求时输出 tool_call: semantic_search(query="...")。
          ToolNode 调用 ChromaDB 向量相似度搜索，返回 top 5 匹配商品。

    Args:
        query: 用户的需求描述，用自然语言即可
    """
    logger.info(f"[tool] semantic_search: {query!r}")
    results = _store.search(query, k=10)
    return _filter_and_format(results, top_k=5)


# ═══ 入口 ═══
@tool
def filter_search(
    query: str, series: str = "", max_price: float = 0, max_age: int = 0
) -> str:
    """
    WHAT: 过滤搜索 — 语义 + 结构化条件混合检索

    WHY:  当用户给出明确条件时（"100美元以下的消防车"、"适合 6 岁的城市系列"），
          纯语义搜索的召回不够精准。过滤搜索结合向量相似度 + 元数据过滤，
          在保证语义相关性的同时强制满足结构化约束，返回更精准的结果。

    HOW:  @tool 装饰器将函数签名（含类型注解）转为 JSON Schema，
          LLM 根据用户条件自动填充参数（如 max_price=100, query="消防车"）。
          执行时封装 ProductFilter → 调用 ChromaDB metadata filter → 返回过滤后的结果。
          不确定的参数传空值（空串 "", 0），ChromaDB 会忽略空过滤条件。

    关键原则：query 参数必不可少，用于语义匹配；
               其他参数用于硬性过滤，不确定的参数传空。

    Args:
        query:     搜索关键词（如 "消防车""火箭""警车"），不可为空
        series:    系列名（如 "城市系列""星球大战""得宝系列"），不确定传空串
        max_price: 预算上限（美元），不限制传 0
        max_age:   孩子年龄，返回此年龄及以下适用的商品，不确定传 0
    """
    logger.info(
        f"[tool] filter_search: query={query!r}, series={series!r}, "
        f"max_price={max_price}, max_age={max_age}"
    )
    from app.data.models import ProductFilter

    pf = ProductFilter(
        series=series if series else None,
        max_price=max_price if max_price > 0 else None,
        max_age=max_age if max_age > 0 else None,
    )
    # 同时做语义搜索 + 元数据过滤，取两倍结果去重
    results = _store.search(query, k=10, product_filter=pf)
    return _filter_and_format(results, top_k=5)


# ═══ 入口 ═══
@tool
def get_product_detail(sku: str) -> str:
    """
    WHAT: 商品详情查询 — 获取单个商品的完整信息

    WHY:  搜索结果只展示摘要信息（名称/系列/价格/匹配度），
          当用户对某个商品表现出兴趣时，LLM 需要更丰富的信息来生成
          有说服力的推荐理由。此工具提供商品的完整 metadata 和 content，
          让 LLM 言之有物而非泛泛而谈。

    HOW:  @tool 装饰器暴露 sku 参数的类型信息给 LLM。
          通过 SKU（商品唯一编号）精确查询 ChromaDB，返回名称、系列、
          年龄、价格、详细描述等完整字段。
          注意：LLM 必须从上一步搜索结果的 [SKU] 标记中提取 SKU，
          不能凭空编造编号。

    Args:
        sku: 商品编号，来自上一步搜索结果的 [SKU] 标记
    """
    logger.info(f"[tool] get_product_detail: sku={sku}")
    results = _store.get_by_ids([sku])
    if not results:
        return f"未找到 SKU 为 {sku} 的商品。"

    r = results[0]
    meta = r["metadata"]

    stock_str = ""
    try:
        from app.data.database import get_inventory
        qty = get_inventory(sku)
        if qty == 0:
            stock_str = "\n库存状态: ⚠ 暂时缺货"
        elif qty <= 5:
            stock_str = f"\n库存状态: 仅剩 {qty} 件，欲购从速！"
        else:
            stock_str = f"\n库存状态: 有货 ({qty} 件)"
    except Exception:
        pass

    return (
        f"商品名称: {meta.get('name')}\n"
        f"SKU: {meta.get('sku')}\n"
        f"系列: {meta.get('series')}\n"
        f"适用年龄: {meta.get('age_min')}+\n"
        f"价格: ${meta.get('price', 0):.2f}\n"
        f"详情: {r['content']}"
        f"{stock_str}"
    )


# ═══ 入口 ═══
@tool
def calculate_price(quantity: int, unit_price: float) -> str:
    """
    WHAT: 价格计算 — 批量购买总价估算

    WHY:  LLM 可以生成包含算术的文本，但用自然语言做计算不够精确且有
          幻觉风险（特别是大数值乘法）。将此操作封装为工具，
          用 Python 原生算术保证计算精度，结果是确定性的数学运算，
          不是语言模型的概率性猜测。

    HOW:  @tool 装饰器暴露 quantity(整数) 和 unit_price(浮点数) 参数类型。
          执行简单乘法 quantity * unit_price，返回格式化的总价文本。

    Args:
        quantity:   购买数量
        unit_price: 单价（美元）
    """
    total = quantity * unit_price
    logger.info(f"[tool] calculate_price: {quantity} x ${unit_price} = ${total}")
    return (
        f"{quantity} 件商品，单价 ${unit_price:.2f}，"
        f"总价 ${total:.2f}（不含税）"
    )


# ═══ 入口 ═══
@tool
def web_search(query: str) -> str:
    """
    WHAT: 网络搜索 — 当商品库中没有匹配结果时，从互联网搜索相关信息

    WHY:  用户可能询问乐高新款、行业趋势、拼装技巧等商品库中没有的信息。
          此工具作为商品库搜索的补充，帮助 Agent 回答超出本地商品库范围的问题。
          使用 Tavily 搜索引擎，结果更精准可靠。

    HOW:  调用 Tavily Search API，提取 top 5 结果摘要，
          格式化为简洁的搜索结果列表返回给 LLM。

    Args:
        query: 搜索关键词（支持中英文）
    """
    logger.info(f"[tool] web_search: {query!r}")

    if not _tavily:
        return "网络搜索未配置（需设置 TAVILY_API_KEY），请根据已有商品库信息回答。"

    try:
        response = _tavily.search(query=query, max_results=5, search_depth="basic")
        results = response.get("results", [])
        if not results:
            return "未找到相关的网络搜索结果。"

        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")
            lines.append(f"{i}. {title}\n   {content[:200]}\n   来源: {url}")

        search_results = "\n\n".join(lines)
        logger.debug(f"[tool] web_search 返回 {len(results)} 条结果")
        return (
            f"🌐 网络搜索结果（仅供参考，非本店商品）：\n\n{search_results}\n\n"
            "⚠ 以上为网络搜索结果，请以本店实际商品信息为准。"
        )
    except Exception as e:
        logger.error(f"[tool] web_search 失败: {e}")
        return f"网络搜索暂时不可用：{e}"


# ═══════════════════════════════════════════════════════
# 售后工单工具
# ═══════════════════════════════════════════════════════

_AFTER_SALES_POLICIES = {
    "退换货": "支持 7 天无理由退换货（未拆封），30 天质量问题换货。需保留原包装和小票。",
    "保修": "乐高积木终身质量保修（缺件/坏件免费补发）。请提供订单号和问题照片。",
    "退款": "退款将在收到退货后 3-5 个工作日内原路返回。使用优惠券的订单按比例退款。",
    "缺件补发": "请提供订单号和缺失零件编号，我们将免费补发，运输时间约 5-7 天。",
    "发货": "下单后 24 小时内发货，标准配送 3-5 天，加急配送 1-2 天。",
    "换货": "收到货 30 天内可申请换货（同型号或等价商品）。来回运费由我方承担。",
}

_SERVICE_TICKETS: dict[str, dict[str, Any]] = {}


@tool
def query_after_sales_policy(policy_type: str) -> str:
    """
    查询售后政策，用于回答用户的退换货、保修、退款、缺件补发、发货等问题。

    使用场景：
    - 用户问"能退货吗""怎么保修""发货要多久""少了一个零件怎么办"
    - 用户想了解退换货条件、流程、时效

    Args:
        policy_type: 政策类型（退换货 / 保修 / 退款 / 缺件补发 / 发货 / 换货）
    """
    logger.info(f"[tool] query_after_sales_policy: {policy_type!r}")
    for key, content in _AFTER_SALES_POLICIES.items():
        if key in policy_type:
            return f"📋 {key}政策：\n{content}"
    all_policies = "\n\n".join(
        f"• {k}：{v}" for k, v in _AFTER_SALES_POLICIES.items()
    )
    return f"未找到「{policy_type}」相关政策。以下是全部售后政策：\n\n{all_policies}"


@tool
def create_service_ticket(order_id: str, issue_type: str, description: str) -> str:
    """
    创建售后工单，用于帮用户办理退换货、申请缺件补发等售后业务。

    使用场景：
    - 用户明确要求退换货且提供了订单号
    - 用户需要申请缺件补发或保修

    重要：
    - 必须先问清楚订单号、问题类型和问题描述再创建工单
    - 信息不齐全时最多追问 2 轮，第 3 轮仍不齐全则建议转人工
    - 工单创建成功后告知用户预计处理时间

    Args:
        order_id: 订单号（如 ORD-20260001）
        issue_type: 问题类型（退换货 / 保修 / 缺件补发 / 换货）
        description: 问题描述
    """
    logger.info(
        f"[tool] create_service_ticket: order={order_id!r} "
        f"type={issue_type!r}"
    )
    ticket_id = f"TK-{uuid.uuid4().hex[:8].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "order_id": order_id.upper(),
        "issue_type": issue_type,
        "description": description,
        "status": "已受理",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _SERVICE_TICKETS[ticket_id] = ticket

    return (
        f"✅ 工单创建成功！\n"
        f"工单编号: {ticket_id}\n"
        f"订单号: {order_id.upper()}\n"
        f"问题类型: {issue_type}\n"
        f"状态: 已受理\n"
        f"预计处理时间: 1-2 个工作日\n"
        f"如需加急处理，可联系人工客服。"
    )


# ═══════════════════════════════════════════════════════
# 订单与会员查询工具
# ═══════════════════════════════════════════════════════

_MOCK_ORDERS = {
    "ORD-20260001": {
        "order_id": "ORD-20260001",
        "member": "张三",
        "phone": "138****5678",
        "items": [
            {"name": "乐高城市消防指挥车", "sku": "60321", "qty": 2, "price": 39.99},
            {"name": "乐高太空火箭发射中心", "sku": "60351", "qty": 1, "price": 59.99},
        ],
        "total": 139.97,
        "status": "已发货",
        "created_at": "2026-07-20",
    },
    "ORD-20260002": {
        "order_id": "ORD-20260002",
        "member": "李四",
        "phone": "139****1234",
        "items": [
            {"name": "乐高得宝消防局", "sku": "10903", "qty": 1, "price": 24.99},
        ],
        "total": 24.99,
        "status": "待发货",
        "created_at": "2026-07-28",
    },
}

_MOCK_MEMBERS = {
    "138****5678": {"member_id": "VIP001", "name": "张三", "level": "金卡", "points": 1280},
    "139****1234": {"member_id": "VIP002", "name": "李四", "level": "银卡", "points": 450},
}


@tool
def query_order(order_id: str) -> str:
    """
    查询订单信息，用于回答用户关于订单状态、商品明细、金额等问题。

    使用场景：
    - 用户问"我的订单到哪了""什么时候发货""我买了什么"
    - 用户提供了订单号想查详情

    注意：
    - 需要用户提供订单号才能查询
    - 如果用户不记得订单号，可引导提供手机号后四位或注册邮箱

    Args:
        order_id: 订单号（如 ORD-20260001）
    """
    logger.info(f"[tool] query_order: {order_id!r}")
    order = _MOCK_ORDERS.get(order_id.upper())
    if not order:
        return (
            f"未找到订单「{order_id}」，请确认订单号是否正确。\n"
            "如果忘记了订单号，可以提供注册手机号后四位，我帮您查找。"
        )
    items_text = "\n".join(
        f"  - {it['name']} (SKU:{it['sku']}) x{it['qty']} @ ${it['price']:.2f}"
        for it in order["items"]
    )
    return (
        f"📦 订单号: {order['order_id']}\n"
        f"会员: {order['member']}\n"
        f"状态: {order['status']}\n"
        f"下单时间: {order['created_at']}\n"
        f"商品明细:\n{items_text}\n"
        f"总金额: ${order['total']:.2f}\n"
        f"联系电话: {order['phone']}"
    )


@tool
def query_membership(phone: str) -> str:
    """
    查询会员信息，用于回答用户关于会员等级、积分、权益等问题。

    使用场景：
    - 用户问"我的积分多少""我是什么会员等级"
    - 用户想了解会员权益

    注意：
    - 需要用户提供注册手机号后四位来验证身份
    - 为了保护隐私，不会完整展示手机号

    Args:
        phone: 手机号（完整号码或后四位，如 "5678"）
    """
    logger.info(f"[tool] query_membership: {phone!r}")
    for key, member in _MOCK_MEMBERS.items():
        if phone in key:
            level_desc = {
                "金卡": "享 9 折优惠、免费加急配送、生日双倍积分",
                "银卡": "享 9.5 折优惠、满 $50 免运费",
            }
            return (
                f"👤 会员信息\n"
                f"会员编号: {member['member_id']}\n"
                f"姓名: {member['name']}\n"
                f"等级: {member['level']}\n"
                f"积分: {member['points']} 分\n"
                f"权益: {level_desc.get(member['level'], '暂无说明')}"
            )
    return "未找到该手机号对应的会员信息，请确认号码是否正确。"


# ═══════════════════════════════════════════════════════
# 平台活动工具
# ═══════════════════════════════════════════════════════

@tool
def search_promotions(query: str) -> str:
    """
    搜索平台当前活动，用于回答用户关于优惠、促销、打折等问题。

    使用场景：
    - 用户问"现在有什么优惠活动""打折吗""有没有满减"
    - 用户想知道当前有哪些促销

    实现方式：
    - 优先返回平台预置活动
    - 同时用 Tavily 联网搜索最新活动补充
    - 自动过滤已过期的活动

    Args:
        query: 活动搜索关键词（如 "优惠""打折""满减""促销"）
    """
    logger.info(f"[tool] search_promotions: {query!r}")
    now = datetime.now(timezone.utc)

    active_promotions = [
        {
            "name": "暑期大促",
            "desc": "全场乐高满 $99 减 $15，满 $199 减 $40",
            "end": "2026-08-31",
        },
        {
            "name": "新会员首单礼",
            "desc": "注册即送 $10 优惠券（满 $50 可用）",
            "end": "2026-12-31",
        },
        {
            "name": "城市系列特惠",
            "desc": "城市系列 8.5 折，部分爆款直降 20%",
            "end": "2026-08-15",
        },
    ]

    lines = ["🎉 当前活动："]
    active_count = 0
    for p in active_promotions:
        end_date = datetime.fromisoformat(p["end"]).replace(tzinfo=timezone.utc)
        if end_date >= now:
            active_count += 1
            lines.append(f"\n• **{p['name']}**（截至 {p['end']}）")
            lines.append(f"  {p['desc']}")

    if active_count == 0:
        lines.append("\n暂无进行中的活动。")

    if _tavily:
        try:
            response = _tavily.search(
                query=f"LEGO 促销 活动 优惠 {query} site:lego.com",
                max_results=3,
                search_depth="basic",
            )
            tavily_results = response.get("results", [])
            if tavily_results:
                lines.append("\n\n🌐 网络补充（可能包含最新活动）：")
                for r in tavily_results:
                    lines.append(f"\n• {r.get('title', '')}\n  {r.get('content', '')[:150]}")
        except Exception as e:
            logger.warning(f"[tool] search_promotions 联网失败: {e}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# 转人工工具
# ═══════════════════════════════════════════════════════

@tool
def transfer_to_human(reason: str) -> str:
    """
    转接人工客服，当问题超出机器人能力范围时使用。

    使用场景：
    - 业务外问题无法处理
    - 售后工单信息 3 轮追问仍不齐全
    - 用户明确要求转人工
    - 涉及退款/投诉等敏感操作需人工确认

    Args:
        reason: 转人工原因简述
    """
    logger.info(f"[tool] transfer_to_human: {reason!r}")
    return (
        "🔔 已为您转接人工客服，请稍候...\n\n"
        f"转接原因: {reason}\n"
        "预计等待时间: 约 1-3 分钟\n"
        "您也可以拨打客服热线 400-800-8888 直接联系人工客服。"
    )


# ═══════════════════════════════════════════════════════
# 图像识别工具
# ═══════════════════════════════════════════════════════


@tool
def analyze_image(image_url: str, question: str = "") -> str:
    """
    分析/识别图片中的乐高相关内容，用于帮用户识别乐高套装、零件、包装盒等。

    使用场景：
    - 用户上传了乐高产品包装盒照片，想知道是什么套装
    - 用户上传了拼好的乐高模型，想知道可能对应的套装编号
    - 用户上传了散落积木零件，想识别颜色/形状/用途
    - 用户想通过照片找到类似的乐高商品推荐

    Args:
        image_url: 图片的 URL 地址或 base64 data URL（如 http://... 或 data:image/...）
        question: 用户对图片的具体问题（如"这是什么套装""帮我推荐类似的"），
                  留空则做通用识别
    """
    logger.info(f"[tool] analyze_image: url={image_url[:80]}... question={question!r}")
    from app.vision.analyzer import analyze_image_base64

    prompt = (
        "请详细识别这张图片中与乐高有关的内容。"
        "如果是乐高产品包装盒，请识别套装名称、编号、系列、适用年龄、颗粒数。"
        "如果是乐高成品模型，请识别可能的套装或主题。"
        "如果是积木零件，请描述颜色、形状和可能的用途。"
        "请用中文回答，输出要结构化、信息完整。"
    )
    if question:
        prompt = f"用户问题: {question}\n\n请根据图片内容回答，用中文。"

    result = analyze_image_base64(image_url, prompt=prompt)
    return f"🖼️ 图片分析结果：\n\n{result}"


# ═══════════════════════════════════════════════════════
# 库存查询工具
# ═══════════════════════════════════════════════════════

@tool
def check_inventory(sku: str) -> str:
    """
    查询商品库存状态，用于回答用户关于"有没有货""库存多少"等问题。

    使用场景：
    - 用户问"这个还有货吗""库存充足吗"
    - 推荐商品前确认库存状态

    Args:
        sku: 商品编号，如 "60450"
    """
    logger.info(f"[tool] check_inventory: sku={sku}")
    try:
        from app.data.database import get_inventory
        qty = get_inventory(sku)
        if qty > 10:
            return f"SKU {sku}: 库存充足（{qty} 件），可放心购买。"
        elif qty > 0:
            return f"SKU {sku}: 库存紧张（仅剩 {qty} 件），建议尽快下单。"
        else:
            return f"SKU {sku}: ⚠ 暂时缺货，可登记到货通知。"
    except Exception as e:
        return f"库存查询失败: {e}"


# ═══════════════════════════════════════════════════════
# 知识图谱搜索工具
# ═══════════════════════════════════════════════════════

_GRAPH_SEARCH_DESCRIPTION = {
    "recommend": "根据某个商品的 SKU，在图谱中找到最相关/搭配的商品（同系列、同主题、同价位、同年龄段）",
    "browse": "按指定维度浏览商品：【系列】/【主题】/【年龄段】/【价位段】，需要提供 keyword",
    "upgrade_downgrade": "按价位升/降级：找到与指定商品主题相近但更贵(up)或更便宜(down)的替代品",
    "cross_series": "跨系列探索：在同一主题或年龄段下，发现不同系列的商品",
}


@tool
def graph_search(
    traversal_type: str,
    sku: str = "",
    keyword: str = "",
    direction: str = "up",
    theme: str = "",
    age: int = 0,
) -> str:
    """
    WHAT: 知识图谱搜索 — 基于乐高商品关系图谱的结构化推荐与探索

    WHY:  向量语义搜索能找到"描述相似"的商品，但无法理解结构化关系。
          知识图谱搜索利用图谱中的系列/主题/年龄段/价位段等关系，
          回答"推荐搭配""有没有类似的""更贵/更便宜的替代"等需要结构推理的问题。

    HOW:  根据 traversal_type 调用不同的图谱查询：
          - recommend: 图形相关性评分 → 综合同系列/同主题/同年龄/同价位打分
          - browse: 按维度遍历图谱（系列→商品、主题→系列→商品…）
          - upgrade_downgrade: 价位树遍历 → 找到更贵或更便宜的同类商品
          - cross_series: 跨图连通 → 同一主题下不同系列的商品发现

    使用场景：
    - 用户问"跟这个消防车搭配的还有什么" → recommend 模式
    - 用户问"幻影忍者系列有哪些" → browse + series 模式
    - 用户问"有没有类似的但便宜一点的" → upgrade_downgrade + down
    - 用户问"除了城市系列，还有什么太空主题的" → cross_series 模式
    - 用户问"6岁男孩能玩什么超级英雄" → cross_series 模式

    Args:
        traversal_type: 查询类型，可选值：recommend / browse / upgrade_downgrade / cross_series
        sku: 商品编号，recommend 和 upgrade_downgrade 模式需要，如 "60374"
        keyword: 浏览关键词，browse 模式需要，如系列名/主题名/年龄段/价位段
        direction: 升/降级方向，仅 upgrade_downgrade 模式有效，up=更贵，down=更便宜
        theme: 主题名，cross_series 模式用于过滤，如 "太空""超级英雄"
        age: 年龄，cross_series 模式用于过滤，如 6
    """
    logger.info(
        f"[tool] graph_search: type={traversal_type!r} sku={sku!r} "
        f"keyword={keyword!r} direction={direction!r} theme={theme!r} age={age}"
    )
    try:
        from app.graph.graph_store import get_neo4j_store

        store = get_neo4j_store()
    except Exception as e:
        logger.error(f"[tool] graph_search 初始化图谱连接失败: {e}")
        return (
            "知识图谱暂时不可用。请使用语义搜索工具(semantic_search/filter_search)"
            "代替。"
        )

    try:
        if traversal_type == "recommend":
            if not sku:
                return "请提供商品 SKU 编号（如 '60374'）以查找相关商品。"
            results = store.graph_recommend(sku, top_k=5)
            if not results:
                return f"未找到与 SKU {sku} 相关的商品推荐。"

        elif traversal_type == "browse":
            if not keyword:
                return "请提供浏览关键词（系列名/主题名/年龄段/价位段）。"
            found = False
            results = []
            for tt in ["series", "theme", "age_group", "price_tier"]:
                results = store.graph_browse(traversal_type=tt, keyword=keyword, top_k=10)
                if results:
                    found = True
                    break
            if not found:
                return f"未找到与「{keyword}」匹配的商品。可尝试：'城市系列'、'太空'、'5-7岁'、'入门'等。"
            results = results[:10]

        elif traversal_type == "upgrade_downgrade":
            if not sku:
                return "请提供商品 SKU 编号以查找升/降级替代。"
            results = store.graph_upgrade_downgrade(sku, direction=direction, top_k=5)
            label = "更贵" if direction == "up" else "更便宜"
            if not results:
                return f"未找到比 SKU {sku} {label}的替代商品。"

        elif traversal_type == "cross_series":
            results = store.graph_cross_series(theme=theme, age=age, top_k=10)
            if not results:
                return "未找到符合条件的跨系列商品。请尝试其他主题或放宽年龄限制。"

        else:
            return (
                f"不支持的查询类型「{traversal_type}」。"
                "可选：recommend / browse / upgrade_downgrade / cross_series"
            )

        if not results:
            return "未找到匹配的商品。请尝试其他条件。"

        return _format_graph_results(results, traversal_type)

    except Exception as e:
        # 本地开发没有启动 Neo4j 时，图谱工具不应让整个 Agent 失败。
        # 退化为向量检索，返回格式仍带 [SKU]/匹配度，供 Agent 和来源提取复用。
        logger.warning(f"[tool] graph_search 不可用，回退向量检索: {e}")
        fallback_query = keyword or theme or sku or "乐高 积木"
        try:
            fallback_results = _store.search(fallback_query, k=10)
            formatted = _filter_and_format(fallback_results, top_k=5)
            return f"（知识图谱未启用，已回退到语义检索）\n{formatted}"
        except Exception as fallback_error:  # noqa: BLE001
            logger.error(f"[tool] graph_search 回退也失败: {fallback_error}")
            return (
                "知识图谱和向量检索暂时不可用。请确认已执行 "
                "`python main.py ingest`，或启动 Neo4j 后重试。"
            )


def _format_graph_results(results: list, traversal_type: str) -> str:
    """格式化图谱查询结果为 LLM 可读文本"""
    lines = [f"📊 知识图谱结果（{traversal_type}）："]
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. [{r['sku']}] {r['name']} "
            f"| 系列:{r.get('series', '')} "
            f"| 年龄:{r.get('age_min', '')}+ "
            f"| ${r.get('price', 0):.2f}"
        )
        if "score" in r:
            lines[-1] += f" | 相关度:{r['score']:.0%}"
        if "theme" in r:
            lines[-1] += f" | 主题:{r['theme']}"
        if "match_key" in r:
            lines[-1] += f" | 匹配:{r['match_key']}"
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# 格式化工具
# ═══════════════════════════════════════════════════════

def _filter_in_stock(results: list) -> list:
    """
    WHAT: 库存过滤 — 从检索结果中剔除无库存的商品

    WHY:  导购助手不应向用户推荐缺货商品，避免「推荐了但买不到」的糟糕体验。
          在格式化展示前过滤掉 quantity=0 的 SKU，确保推荐的商品都可购买。
    """
    if not results:
        return results
    try:
        available_skus = get_available_skus()
        # 库存表尚未初始化时不要把所有商品都过滤掉；
        # 本地首次启动、只跑检索 Demo 的场景需要这个降级。
        if not available_skus:
            logger.warning("[tool] 库存表为空，跳过库存过滤（可运行 python scripts/init_db.py）")
            return results
        filtered = [r for r in results if r.get("metadata", {}).get("sku") in available_skus]
        removed = len(results) - len(filtered)
        if removed > 0:
            logger.info(f"[tool] 库存过滤: 剔除 {removed} 个缺货商品，保留 {len(filtered)} 个")
        return filtered
    except Exception:
        logger.warning("[tool] 库存查询失败，跳过库存过滤")
        return results


def _format_products(results: list) -> str:
    """
    WHAT: 商品列表格式化 — 将检索结果转为 LLM 可读的纯文本

    WHY:  ChromaDB 返回的 dict 列表不是 LLM 能直接理解的格式。
          格式化后每行包含 SKU（关键：LLM 用此值作为 get_product_detail
          的 sku 参数）、名称、系列、年龄、价格、匹配度，
          提供足够的结构化信息供 LLM 筛选和推荐。

    HOW:  遍历结果列表，逐行拼接待编号的格式化文本。
          空结果返回引导性提示（建议换词或放宽条件），
          帮助 LLM 给出合理的回应而非胡编乱造。
    """
    if not results:
        return "未找到匹配的商品。建议尝试更换搜索词或放宽筛选条件。"
    lines = []
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        lines.append(
            f"{i}. [{meta.get('sku')}] {meta.get('name')} "
            f"| 系列:{meta.get('series')} "
            f"| 年龄:{meta.get('age_min')}+ "
            f"| ${meta.get('price', 0):.2f} "
            f"| 匹配度:{r.get('score', 0):.1%}"
        )
    return "\n".join(lines)


def _filter_and_format(results: list, top_k: int | None = None) -> str:
    """WHAT: 库存过滤 + 格式化 — 搜索结果的统一后处理

    先通过库存过滤剔除缺货商品，再将剩余结果格式化为文本。
    这是 semantic_search 和 filter_search 的共用后处理管线。

    Args:
        results: 检索结果列表
        top_k: 截断数量，不传则取全部
    """
    filtered = _filter_in_stock(results)
    if top_k is not None:
        filtered = filtered[:top_k]
    return _format_products(filtered)
