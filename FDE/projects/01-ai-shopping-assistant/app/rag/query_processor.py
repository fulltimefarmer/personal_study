"""
查询预处理模块 — RAG Pipeline 的数据入口层
═══════════════════════════════════════════════

架构角色：
  本模块位于 RAG 管道的最前端，负责接收原始用户输入（自然语言查询），
  在向量检索之前完成所有预处理工作。下游的 RAGChain 和 Agent 依赖本模块的
  输出来决定检索策略（混合搜索 vs 普通搜索、是否需要价格/年龄过滤）。

核心能力：
  1. 同义词扩展 (expand_query)     — 将口语化表达映射到标准商品关键词
  2. 意图识别 (classify_intent)    — 区分商品咨询/闲聊/无效提问，路由到不同处理分支
  3. 参数提取 (detect_*)           — 从自然语言中结构化提取价格、年龄等筛选参数
  4. 复杂度判断 (needs_deepseek_agent) — 判断是否需要 DeepSeek Agent 还是本地 Ollama 即可
  5. 本地回答 (answer_with_local_llm)  — 简单问题用本地 Ollama 直接回复，节省 API 费用

设计理念：
  全部基于规则（关键词 + 正则），无需 LLM，保证毫秒级响应。
  作为 RAG 的"守门人"，本模块拦截无关查询，避免浪费 LLM Token。
"""
import re
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

SYNONYM_MAP = {
    "消防": ["消防车", "消防", "救火", "灭火"],
    "警察": ["警察", "警车", "警官", "警务", "警局"],
    "工程": ["工程车", "工程", "工地", "建筑", "建造", "施工"],
    "赛车": ["赛车", "跑车", "竞速", "F1", "赛车手"],
    "火车": ["火车", "列车", "铁路", "轨道", "高铁"],
    "飞机": ["飞机", "客机", "直升机", "战斗机", "喷气"],
    "太空": ["太空", "宇宙", "航天", "火箭", "空间站", "火星", "月球", "星际"],
    "城堡": ["城堡", "骑士", "王国", "中世纪"],
    "忍者": ["忍者", "武士", "武道", "功夫"],
    "海盗": ["海盗", "海贼", "宝藏", "沉船"],
    "孙悟空": ["孙悟空", "悟空", "西游", "神仙"],
    "赛车": ["赛车", "竞速", "跑道", "赛车场"],
}

PRICE_KEYWORDS = {
    "cheap": {"max": 20},
    "便宜": {"max": 20},
    "实惠": {"max": 30},
    "贵": {"min": 80},
    "高端": {"min": 80},
    "豪华": {"min": 100},
    "中级": {"min": 30, "max": 80},
}

AGE_PATTERN = re.compile(r"(\d+)\s*[岁\+]")
PRICE_PATTERN = re.compile(r"(\d+)\s*(美元|美金|刀|块|元)")


# ═══ 入口 ═══
def expand_query(query: str) -> str:
    """
    WHAT: 同义词扩展 — 将用户口语化表达关联到标准商品关键词

    WHY:  乐高商品官方描述与用户日常表达存在差异（如用户搜"消防"而非"消防车"）。
          直接检索会导致向量空间中的语义匹配不充分，召回率低。
          扩展后的查询同时携带原始口语表达与标准化关键词，在向量检索中
          形成更密集的语义锚点，显著提升召回覆盖率。

    HOW:  遍历 SYNONYM_MAP（关键词→别名列表映射表），
          若用户查询中包含任一别名，则将对应的主关键词追加到查询尾部。
          每个主关键词只追加一次，避免文本膨胀。
    """
    tokens = []
    for keyword, synonyms in SYNONYM_MAP.items():
        for syn in synonyms:
            if syn in query:
                tokens.append(keyword)
                break
    if tokens:
        return f"{query} {' '.join(tokens)}"
    return query


# ═══ 入口 ═══
def detect_price_intent(query: str) -> dict | None:
    """
    WHAT: 价格意图检测 — 从自然语言中提取结构化的价格过滤条件

    WHY:  用户输入如"便宜"、"豪华"、"中级"等模糊价格词，向量检索无法直接
          理解这些词对应的具体价格区间。将这些口语化价格词映射为结构化
          过滤条件（如 {"max": 20} 代表"便宜"），传递给 ChromaDB 的
          元数据过滤器，实现精确的价格范围筛选。

    HOW:  遍历 PRICE_KEYWORDS 字典（价格词→价格条件映射），
          返回第一个匹配的价格过滤字典。未检测到价格意图时返回 None。
    """
    for kw, cond in PRICE_KEYWORDS.items():
        if kw in query:
            return cond
    return None


# ═══ 入口 ═══
def detect_age_intent(query: str) -> int | None:
    """
    WHAT: 年龄意图检测 — 从用户查询中提取目标年龄

    WHY:  乐高套装都有 age_min 字段，用户常问"适合 6 岁孩子的"或"8+岁"。
          从自然语言中正则提取数字年龄，传递给 ChromaDB 元数据过滤，
          精准匹配合适年龄段的商品，避免推荐超龄或低龄商品。

    HOW:  使用正则 AGE_PATTERN = r"(\\d+)\\s*[岁+]" 匹配年龄表达
          （如 "6 岁"、"8+"），返回提取的数字作为年龄上限。
          未匹配时返回 None。
    """
    match = AGE_PATTERN.search(query)
    if match:
        return int(match.group(1))
    return None


def extract_keywords(query: str) -> List[str]:
    """
    WHAT: 关键词提取 — 从查询中提取有意义的实词

    WHY:  用户查询中有大量口语填充词（"我想买一个…"、"推荐一下…"），
          这些词对检索没有帮助反而引入噪音。抽取核心实词后可用于
          意图判断中的关键词计数（classify_intent 依赖此函数统计
          商品关键词命中数）。

    HOW:  先用正则 [\\u4e00-\\u9fff\\w]+ 提取所有中英文词，
          再过滤掉停用词列表和单字词，返回剩余关键词。
    """
    stop_words = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
        "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
        "想", "买", "推荐", "适合", "有没有", "什么", "怎么样",
    }
    words = re.findall(r"[\u4e00-\u9fff\w]+", query)
    return [w for w in words if w not in stop_words and len(w) > 1]


# ═══════════════════════════════════════════════════════
# 意图路由：商品咨询 / 闲聊 / 无效提问分流
# ═══════════════════════════════════════════════════════

# ── 售后工单关键词 ──
AFTER_SALES_KEYWORDS = [
    "退货", "换货", "退换", "退款", "保修", "售后", "维修",
    "缺件", "少零件", "少了一个", "少了一块", "少了个", "补发",
    "发货", "到货", "物流", "快递", "运输", "还没到", "什么时候到",
    "坏了", "损坏", "破损", "坏了怎么办", "质量问题",
    "工单", "申请售后", "客服", "投诉",
    "退钱", "退款多久", "怎么退货", "可以退吗", "能退吗",
]

# ── 订单会员关键词 ──
ORDER_KEYWORDS = [
    "订单", "订单号", "查订单", "我的订单", "订单状态",
    "买了什么", "买了啥", "购了什么", "消费记录",
    "会员", "积分", "VIP", "金卡", "银卡", "会员权益",
    "等级", "积分多少", "积分查询",
]

# ── 平台活动关键词 ──
PROMOTION_KEYWORDS = [
    "活动", "促销", "打折", "折扣", "优惠", "满减", "满送",
    "优惠券", "优惠卷", "抵用券", "特价", "秒杀", "限时",
    "有没有活动", "现在有活动吗", "什么时候活动", "打几折",
]
PRODUCT_KEYWORDS = [
    # 商品词
    "乐高", "积木", "套装", "型号", "系列", "新款", "推荐", "买",
    "价格", "多少钱", "预算", "便宜", "贵", "划算", "折扣",
    # 场景词
    "送", "礼物", "生日", "圣诞节", "儿童节",
    # 筛选词
    "年龄", "岁", "适合", "孩子", "小朋友", "男孩", "女孩",
    "消防", "警察", "赛车", "飞机", "火车", "太空", "火箭",
    "城堡", "城市", "建筑", "机械", "忍者", "海盗", "星球大战",
    "哈利波特", "漫威", "迪士尼", "马里奥", "得宝", "科技",
    # 商品属性词
    "颗粒", "拼装", "搭建", "零件", "难度", "入门", "高级",
]

# ── 闲聊关键词 ──
CHITCHAT_KEYWORDS = [
    "你好", "嗨", "早上好", "晚上好", "下午好", "hello", "hi",
    "谢谢", "感谢", "多谢", "不客气",
    "再见", "拜拜", "bye", "回头见", "下次见",
    "你叫什么", "你是谁", "做什么", "能干什么", "会什么",
    "今天天气", "心情", "怎么样", "好玩吗",
    "哈哈", "有意思", "有趣", "不错",
    "能帮我", "帮我", "请问",
]

# ── 无效提问关键词 ──
OFF_TOPIC_KEYWORDS = [
    "股票", "基金", "比特币", "投资",
    "政治", "选举", "政府", "法律", "法规", "特朗普", "拜登", "习近平",
    "医疗", "药品", "疾病", "医院", "医生",
    "代码", "编程", "python", "java", "前端", "写代码", "debug",
    "手机", "华为", "三星", "电脑", "笔记本", "买手机", "买电脑",
    "美女", "恋爱", "约会", "约吗",
    "骂", "傻", "垃圾", "废物",
    "汽车", "房产", "贷款", "保险",
]

# 强 off-topic 信号（即使有商品泛词也判为 off_topic）
STRONG_OFF_TOPIC = {
    "股票", "基金", "比特币", "政治", "选举", "特朗普", "拜登",
    "医疗", "药品", "疾病", "python", "java", "前端", "debug",
    "美女", "恋爱", "约会", "骂", "手机", "电脑",
}

INTENT_CHITCHAT = "chitchat"
INTENT_PRODUCT = "product_inquiry"
INTENT_OFF_TOPIC = "off_topic"
INTENT_AFTER_SALES = "after_sales"
INTENT_ORDER = "order_inquiry"
INTENT_PROMOTION = "promotion"


# ═══ 入口 ═══
def classify_intent(query: str) -> str:
    """
    WHAT: 意图分类器 — 将用户查询路由到不同的处理分支

    WHY:  不是所有用户输入都需要进入 RAG 检索 + LLM 生成的昂贵路径。
          闲聊（"你好"）和无关提问（"买手机"）应被快速拦截，
          节省 LLM Token 和响应延迟。
          本函数是 RAG 管道的"守门人"，确保只有商品咨询才触发完整检索流程。

    HOW:  基于关键词计数的优先级规则引擎（三步决策链）：
          1. 先检查 off_topic 关键词（政治/技术/违法等），命中即拦截
          2. 再检查 chitchat 关键词（问候/道别/自我介绍），命中就走预设回复
          3. 剩余默认判定为 product_inquiry — 进入 RAG 检索 + LLM 生成
          设计为纯规则引擎（零延迟、零幻觉风险），不依赖 LLM。

    Returns:
        "product_inquiry" | "chitchat" | "off_topic"
    """
    intent = _classify_intent(query)
    logger.info(f"[intent] {query!r} → {intent}")
    return intent


def _classify_intent(query: str) -> str:
    q = query.strip().lower()

    # 空输入 → 闲聊
    if not q:
        return INTENT_CHITCHAT

    # 极短输入 → 按关键词判断
    if len(q) <= 2:
        if q in ("你好", "嗨", "hi", "嗯", "谢", "好", "ok", "再见", "谢谢"):
            return INTENT_CHITCHAT
        if q in ("?", "？", "什么", "怎么"):
            return INTENT_CHITCHAT
        # 短词也可能是强 off-topic
        if any(kw in q for kw in STRONG_OFF_TOPIC):
            return INTENT_OFF_TOPIC
        return INTENT_PRODUCT

    # 短词问候（2-4字符）
    SHORT_CHITCHAT = ("谢谢", "再见", "拜拜", "多谢", "好的", "ok", "hello", "hi")
    if q in SHORT_CHITCHAT:
        return INTENT_CHITCHAT

    # ── 检查无效提问 ──
    off_topic_count = sum(1 for kw in OFF_TOPIC_KEYWORDS if kw in q)
    if off_topic_count >= 2:
        return INTENT_OFF_TOPIC
    # 强 off-topic 信号 → 直接拒绝
    if any(kw in q for kw in STRONG_OFF_TOPIC):
        return INTENT_OFF_TOPIC
    for kw in OFF_TOPIC_KEYWORDS:
        if kw in q and len(kw) >= 2:
            product_count = sum(1 for pk in PRODUCT_KEYWORDS if pk in q)
            if product_count == 0:
                return INTENT_OFF_TOPIC

    # ── 检查闲聊（以社交词开头优先） ──
    # 如果查询以社交词开头 → 闲聊
    if any(
        re.match(rf"^{kw}", q) for kw in
        ("谢谢", "感谢", "多谢", "不客气", "再见", "拜拜", "bye", "你好", "嗨", "hi", "hello")
    ):
        return INTENT_CHITCHAT

    chitchat_count = sum(1 for kw in CHITCHAT_KEYWORDS if kw in q)
    product_count = sum(1 for pk in PRODUCT_KEYWORDS if pk in q)
    if chitchat_count >= 2 and product_count == 0:
        return INTENT_CHITCHAT
    # 纯社交问候（全词匹配）
    if re.match(r"^(你好|嗨|hi|hello|早上好|晚上好|下午好|你是谁|你叫什么|你能|你会|介绍一下自己)[\s!！。.]*$", q):
        return INTENT_CHITCHAT
    # 询问助手能力（部分匹配）
    if re.search(r"(你是谁|你叫什么|能干什么|会干什么|介绍一下自己)", q):
        return INTENT_CHITCHAT

    # ── 检查售后工单 ──
    after_sales_count = sum(1 for kw in AFTER_SALES_KEYWORDS if kw in q)
    if after_sales_count >= 1:
        return INTENT_AFTER_SALES

    # ── 检查订单会员 ──
    order_count = sum(1 for kw in ORDER_KEYWORDS if kw in q)
    if order_count >= 1:
        return INTENT_ORDER

    # ── 检查平台活动 ──
    promotion_count = sum(1 for kw in PROMOTION_KEYWORDS if kw in q)
    if promotion_count >= 1:
        return INTENT_PROMOTION

    # ── 默认 → 商品咨询 ──
    return INTENT_PRODUCT


def get_intent_response(intent: str, query: str = "") -> str | None:
    """
    WHAT: 意图响应分发 — 根据分类结果返回预设回复或放行到 LLM/Agent

    WHY:  闲聊和无关提问不需要浪费 LLM Token，直接返回模板化应答即可。
           售后工单/订单/活动/商品咨询必须返回 None，让上游调用方知道需要
           使用 Agent + LLM 来处理。

    HOW:  chitchat/off_topic → 预设模板回复
          after_sales/order_inquiry/promotion/product_inquiry → None（走 Agent）
    """
    if intent == INTENT_CHITCHAT:
        return _chitchat_reply(query)
    if intent == INTENT_OFF_TOPIC:
        return _off_topic_reply()
    return None


def _chitchat_reply(query: str) -> str:
    """
    WHAT: 闲聊回复生成 — 为常见社交用语提供预设话术

    WHY:  问候/道别/感谢等场景无需 LLM，模板回复更快且体验一致。
          每个回复中都巧妙植入导购引导语，把闲聊转化为潜在的购物对话，
          提升转化率而不显得生硬。

    HOW:  按问候类型分分支匹配关键词，返回对应的预设回复模板。
    """
    q = query.strip()
    if any(w in q for w in ("你好", "嗨", "hi", "hello", "早上好", "晚上好", "下午好")):
        return (
            "你好呀！我是小砖家，乐高导购助手 🧱\n"
            "我可以帮你：\n"
            "  - 搜索各类乐高套装（告诉我想找什么题材）\n"
            "  - 按年龄/预算/系列筛选推荐\n"
            "  - 查看商品详情和价格\n"
            "  - 帮你算算买几件的总价\n\n"
            "有什么想看的吗？😊"
        )
    if any(w in q for w in ("谢谢", "感谢", "多谢")):
        return "不客气！还有什么想了解的乐高套装吗？随时问我～"
    if any(w in q for w in ("再见", "拜拜", "bye")):
        return "再见！欢迎再来，祝你拼装愉快 🧱✨"
    if any(w in q for w in ("你是谁", "你叫什么", "干什么的")):
        return (
            "我是「小砖家」，你的专属乐高导购助手！\n"
            "我可以根据你的需求推荐合适的乐高套装，也能帮你查价格、比型号。\n"
            "随便聊聊你想找什么样的乐高吧～"
        )
    return (
        "你好！我是小砖家 🧱 有什么乐高方面的问题吗？\n"
        "比如想找什么题材的套装？预算多少？给多大的孩子玩？"
    )


def _off_topic_reply() -> str:
    """
    WHAT: 拒绝回复 — 对所有非乐高相关问题的统一拒绝话术

    WHY:  明确告知用户自己的能力边界，同时友好地引导回乐高话题。
           直接拒绝比 LLM 自由发挥更安全（避免生成不当内容），
           且不需要消耗 Token，实现了防御式设计。

    HOW:  返回预设的拒绝文案模板，不含任何动态生成内容。
    """
    return (
        "抱歉，我是乐高积木导购助手，只能回答与乐高商品相关的问题哦～\n"
        "如果你对乐高套装感兴趣，不妨告诉我你的需求，我来帮你推荐！🧱"
    )


# ═══════════════════════════════════════════════════════════
# 复杂度判断 — 决定用本地 Ollama 还是 DeepSeek Agent
# ═══════════════════════════════════════════════════════════

LOOKUP_PATTERNS = [
    re.compile(p) for p in [
        # 明确要求搜索/查找/推荐（带商品上下文）
        r'(推荐|介绍|有没有|找(一)?[下个]|查(一)?[下看]|搜索|看看|显示|列出)',
        # 价格查询
        r'(多少|什么).*(钱|价格|价|预算)',
        # 选择/比较
        r'(哪个|哪款|哪套|什么).*(好|适合|推荐|值得)',
        # 需要查 SKU/详情
        r'SKU|型号|编号|配件号',
        # 计算需求
        r'买.*(件|个).*(多少钱|算算|算一下|总价|一共)',
        # 订单/售后/活动（即使语义上像商品咨询也需要 Agent）
        r'(订单|退[货换]|售后|保修|物流|快递|缺件|工单|会员|积分)',
    ]
]

LOOKUP_WEAK_PATTERNS = [
    re.compile(p) for p in [
        r'有没有.*乐高',
        r'(想看|看看|想要|想买|找找).*(乐高|积木)',
    ]
]

# 常识性问题模式 — 这类问题即使命中 product_keywords 也不需 Agent
GENERAL_KNOWLEDGE_PATTERNS = [
    re.compile(p) for p in [
        r'(什么是|是什么|啥是|什么叫).*乐高',
        r'乐高.*(是什么|是啥|怎么样)',
        r'(怎么|如何|怎样).*(拼|选|买|玩|搭|入门|开始|学习)',
        r'乐高.*(适合|推荐).*(几岁|多大|年龄|孩子|小朋友|宝宝)',
        r'(新手|入门|初学).*乐高',
        r'乐高.*(有|分为).*(哪些|几个|多少).*(系列|种类|类型|主题)',
        r'(为什么|为啥).*(乐高|积木).*(贵|便宜|火|流行|受欢迎)',
        r'(为什么|为啥)(.*)(乐高|积木)',
        r'乐高.*(为什么|为啥).*(贵|便宜)',
        r'乐高.*(好处|优点|作用|意义|价值|魅力|缺点|不足)',
        r'(积木|乐高).*(好处|优点|缺点|好处)',
    ]
]


def needs_deepseek_agent(query: str, intent: str | None = None) -> bool:
    """
    WHAT: 复杂度判断 — 启发式判断问题是否需要 DeepSeek Agent（工具调用）

    WHY:  不需要工具的问题（如"乐高是什么""乐高有几个系列"）用本地 Ollama
          就能回答，无需调用昂贵的 DeepSeek API。只有需要向量检索/过滤/计算
          等工具调用的问题才走 Agent 路径，节省 API 费用。

    HOW:  多级判断规则：
          1. 非商品意图（售后/订单/活动）→ 必定需要 Agent
          2. 商品意图 → 检查是否需要具体商品查找：
             a. 有年龄/价格筛选 → 需要 Agent
             b. 匹配明确查找模式 → 需要 Agent
             c. 命中 ≥3 个商品关键词 → 需要 Agent
          3. 都不满足 → 简单问题，本地 Ollama 即可
    """
    needs = _needs_deepseek_agent(query, intent)
    logger.info(f"[router] 需要 DeepSeek Agent: {needs} ← {query!r}")
    return needs


def _needs_deepseek_agent(query: str, intent: str | None = None) -> bool:
    if intent is None:
        intent = classify_intent(query)

    if intent in (INTENT_AFTER_SALES, INTENT_ORDER, INTENT_PROMOTION):
        return True

    if intent == INTENT_PRODUCT:
        for pattern in GENERAL_KNOWLEDGE_PATTERNS:
            if pattern.search(query):
                return False

        if detect_age_intent(query) is not None or detect_price_intent(query) is not None:
            return True

        for pat in LOOKUP_PATTERNS:
            if pat.search(query):
                return True

        weak_matches = sum(1 for pat in LOOKUP_WEAK_PATTERNS if pat.search(query))
        if weak_matches >= 1:
            return True

        product_hits = sum(1 for pk in PRODUCT_KEYWORDS if pk in query)
        if product_hits >= 4:
            return True

    return False


def answer_with_local_llm(query: str, temperature: float = 0.7) -> str:
    """
    WHAT: 本地回答 — 用本地 Ollama 模型直接回复简单问题

    WHY:  对于不需要工具调用的简单乐高问题（常识/入门/玩法），本地 LLM
          完全胜任，且零 API 费用。配合 system prompt 约束，避免编造商品信息。

    HOW:  使用 create_ollama_llm() 创建 ChatOllama 实例，注入简单的系统提示，
          直接 invoke 返回回复文本。异常时返回友好的错误提示。
    """
    from app.config import create_ollama_llm

    try:
        llm = create_ollama_llm(temperature=temperature)
        system_prompt = """你是一个专业的乐高积木导购助手"小砖家"。请用中文回答关于乐高积木的问题。

规则：
1. 语气友好热情，像一位乐高店员
2. 回答简洁有条理，不要冗长
3. 如果问题涉及具体商品推荐，建议用户提供年龄、预算、兴趣方向
4. 不要编造具体商品名称、SKU、价格，只介绍一般性知识
5. 可以介绍乐高系列分类、拼搭技巧、选购建议等常识内容"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]
        response = llm.invoke(messages)
        result = str(response.content).strip()
        logger.info(f"[local-llm] 本地模型回答长度: {len(result)}")
        return result
    except Exception as e:
        logger.warning(f"[local-llm] 本地模型调用失败: {e}，回退到预设回复")
        return (
            "你好！我是小砖家，乐高导购助手 🧱\n"
            "我可以帮你搜索各种乐高套装、按年龄和预算筛选推荐。\n"
            "告诉我你想找什么样的乐高吧～"
        )
