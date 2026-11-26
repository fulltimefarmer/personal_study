# 🤖 Agentic RAG 学习规划 — 乐高智能导购助手

> 基于本项目的循序渐进式 AI 应用开发学习路线图。
> 每个阶段都标注了项目中的对应代码位置，便于边学边看。

---

## 学习前置条件

| 技能 | 要求 | 说明 |
|------|------|------|
| Python | 熟练 | 异步/类型注解/装饰器/Pydantic |
| 命令行 | 基础 | pip/uv 包管理、环境变量 |
| LLM 概念 | 了解 | 知道 prompt、token、temperature |

---

## 📅 第一阶段：基础 RAG 入门（第 1-2 周）

**目标**：理解 RAG（检索增强生成）的核心流程，跑通最简单的"检索→生成"管道。

### 1.1 环境搭建与项目结构

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 项目骨架 | `pyproject.toml` 依赖管理、CLI 入口 | `pyproject.toml`、`main.py:543-600` |
| 配置管理 | Pydantic Settings 单例模式、`.env` 加载 | `app/config.py:24-155` |
| 数据模型 | Pydantic BaseModel 定义 Product/ProductFilter | `app/data/models.py:18-109` |
| 日志系统 | Loguru 结构化日志配置 | `app/core/logging.py` |

**任务**：
- [ ] 运行 `python main.py stats` 查看向量库统计
- [ ] 阅读 `app/config.py`，画出配置流向图
- [ ] 理解 `pyproject.toml` 中的每个依赖是做什么的

### 1.2 数据摄取（ETL 管道）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| CSV 解析 | Markdown 格式 CSV 的手动解析 | `app/data/loader.py:42-75` |
| 数据清洗 | Pandas 去重/填充/类型转换 | `app/data/loader.py:80-106` |
| 文档嵌入 | **多粒度嵌入策略**（名称/描述/完整）| `app/data/loader.py:150-218` |
| 为什么多粒度 | 用户搜商品名→名称粒度精确命中；搜场景→描述粒度匹配 |

**任务**：
- [ ] 运行 `python main.py ingest` 重建向量库
- [ ] 阅读 `files/products.csv` 理解数据格式
- [ ] **思考**：为什么要给同一个商品生成 3 条不同粒度的文档？

### 1.3 Embedding 与向量存储

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| Embedding 模型 | OllamaEmbeddings 封装，bge-m3 模型 | `app/vector_store/embeddings.py:28-46` |
| ChromaDB 基础 | 集合创建、文档写入、持久化 | `app/vector_store/chroma_store.py:65-75` |
| 语义搜索 | `similarity_search_with_score()` L2 距离 | `app/vector_store/chroma_store.py:136-167` |
| L2 → 相似度 | `1/(1+L2)` 的数学原理 | `app/vector_store/chroma_store.py:262-290` |
| 混合搜索 | 语义(55%) + 年龄(20%) + 价格(25%) 加权 | `app/vector_store/chroma_store.py:170-210,292-408` |
| 可插拔设计 | VectorStoreBase 抽象基类 | `app/vector_store/base.py` |

**任务**：
- [ ] 运行 `python main.py search_only "消防车"` 体验纯检索
- [ ] **思考**：L2 距离是什么？为什么需要 `1/(1+L2)` 转换？
- [ ] **思考**：混合搜索的三因子权重为什么这样分配？

### 1.4 基础 RAG 链（LCEL）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **LCEL 管道** | `RunnablePassthrough \| Prompt \| LLM \| StrOutputParser` | `app/rag/chain.py:112-117` |
| ChatPromptTemplate | system/human 消息模板 | `app/rag/chain.py:60-65` |
| 文档格式化 | 检索结果→LLM 可读文本 | `app/rag/chain.py:68-93` |
| RAGChain.query() | 检索→格式化→生成的完整流程 | `app/rag/chain.py:176-210` |
| 流式生成 | `llm.stream()` 逐 token 输出 | `app/rag/chain.py:212-234` |

> **核心概念 — LangChain 管道 `|` 操作符**：
> ```python
> chain = (
>     {"context": ..., "question": ...}  # 输入准备
>     | prompt                           # 注入模板
>     | llm                              # 调用模型
>     | StrOutputParser()                # 解析输出
> )
> result = chain.invoke({"context": "...", "question": "..."})
> ```
> 每个 `|` 连接一个 Runnable，数据从左到右流动——这就是 LCEL（LangChain Expression Language）。

**任务**：
- [ ] 运行 `python main.py query` 体验 RAG 对话
- [ ] 对比 "固定 RAG" 和后续 "Agentic RAG" 的区别
- [ ] **思考**：`RunnablePassthrough` 做什么用的？

---

## 📅 第二阶段：Agentic RAG 核心（第 3-4 周）

**目标**：理解 LangGraph ReAct Agent 的工作原理，掌握 LLM 自主决策+工具调用。

### 2.1 LangGraph 核心概念

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **StateGraph 构建器** | `add_node` / `add_edge` / `add_conditional_edges` / `compile` | `app/agent/graph.py:333-371` |
| **AgentState** | TypedDict 定义状态字段 | `app/agent/state.py:43-71` |
| **Annotated + add_messages** | 消息列表的*追加*而非*替换*语义 | `app/agent/state.py:69` |
| 条件边（路由） | `_should_continue()` 根据 tool_calls 决策 | `app/agent/graph.py:296-325` |
| **ToolNode** | LangGraph 内置工具自动执行器（提取→调用→封装） | `app/agent/graph.py:248` |

> **核心概念 — Annotated[list, add_messages]**：
> 这是 LangGraph 最核心的机制之一。普通 dict 的同名字段会被*替换*，但对话历史需要*累加*。
> `add_messages` reducer 确保每次 `return {"messages": [new]}` 时，new 被追加到列表尾部。
> 三个技术的组合：`TypedDict`（定义结构）+ `Annotated`（附加元数据）+ `add_messages`（reducer 函数）。

**任务**：
- [ ] 阅读 `app/agent/state.py` 全文注释（已包含详细说明）
- [ ] 画出 ReAct Graph 的拓扑图：START → agent → [tool_calls?] → tools → agent → ... → END
- [ ] **思考**：如果 messages 字段不用 `Annotated[list, add_messages]` 而用普通 `list`，会发生什么？

### 2.2 ReAct 循环

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| ReAct 原理 | Reasoning ↔ Acting 交替循环 | `app/agent/graph.py:1-45`（文件头注释） |
| Agent 节点 | LLM 阅读历史→决策调用工具或回复 | `app/agent/graph.py:187-217` |
| 工具节点 | ToolNode 执行 + 超时 + 调用上限 | `app/agent/graph.py:251-287` |
| 安全阀 | `MAX_TOOL_CALLS=5` 防止无限循环 | `app/agent/graph.py:246,269-271` |
| run_agent 管道 | 记忆→执行→提取→防控→保存 八步流程 | `app/agent/graph.py:382-509` |

**任务**：
- [ ] 运行 `python main.py agent` 体验 Agentic RAG
- [ ] 观察终端输出的 `[agent] 决定调用工具` 和 `[tool]` 日志
- [ ] 运行 `python main.py compare` 对比固定 RAG vs Agentic RAG
- [ ] **思考**：为什么需要 MAX_TOOL_CALLS？没有它会怎样？

### 2.3 工具系统（@tool 装饰器）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **@tool 装饰器** | 函数签名→function calling schema 自动生成 | `app/agent/tools.py:36-55` |
| **bind_tools()** | 将工具列表绑定到 LLM | `app/agent/graph.py:91` |
| 语义搜索工具 | 纯向量相似度检索 | `app/agent/tools.py:36-56` |
| 过滤搜索工具 | 语义+结构化条件混合检索 | `app/agent/tools.py:59-97` |
| 商品详情工具 | 按 SKU 精确查询 | `app/agent/tools.py:102-149` |
| 价格计算工具 | 确定性算术（避免 LLM 幻觉） | `app/agent/tools.py:153-175` |
| 网络搜索工具 | Tavily API 联网兜底 | `app/agent/tools.py:179-221` |
| 售后/订单/会员工具 | 工单创建、订单查询、会员查询 | `app/agent/tools.py:227-411` |
| 活动搜索工具 | 平台促销查询 | `app/agent/tools.py:418-483` |
| 图片识别工具 | 多模态视觉分析 | `app/agent/tools.py:518-548` |
| 转人工工具 | 超出能力范围兜底 | `app/agent/tools.py:490-510` |
| 库存查询工具 | 实时库存状态 | `app/agent/tools.py:555-578` |
| 知识图谱工具 | 图谱关系推荐/浏览/升降级/跨系列 | `app/agent/tools.py:593-714` |

> **核心概念 — @tool 装饰器的魔法**：
> ```python
> @tool
> def filter_search(query: str, series: str = "", max_price: float = 0) -> str:
>     """搜索商品"""
> ```
> `@tool` 自动做两件事：
> 1. 从函数签名生成 JSON Schema（参数名/类型/默认值）
> 2. 从 docstring 提取工具描述
> LLM 看到 Schema 后决定何时调用、传什么参数。

**任务**：
- [ ] 数一数项目中共有多少个 @tool 函数
- [ ] **思考**：为什么 `calculate_price` 要封装为工具而不是让 LLM 自己算？
- [ ] **思考**：`filter_search` 的不确定参数为什么要传空值（`""`, `0`）？

### 2.4 意图路由系统

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 意图分类器 | 规则引擎 6 分类（商品/闲聊/无关/售后/订单/活动） | `app/rag/query_processor.py:223-311` |
| 三层路由 | 模板回复→本地 Ollama→DeepSeek Agent | `main.py:50-83`、`app/api/routes.py:208-231` |
| 复杂度判断 | 启发式判断是否需工具调用 | `app/rag/query_processor.py:431-473` |
| 同义词扩展 | 口语→标准关键词映射 | `app/rag/query_processor.py:57-78` |
| 查询改写 | 指代消解+上下文补全 | `app/rag/query_rewriter.py:58-137` |

> **核心概念 — 意图路由的成本优化**：
> ```
> 用户输入 → classify_intent()
>   ├─ 闲聊/无关 → 模板回复（零成本、<1ms）
>   ├─ 简单商品问题 → 本地 Ollama（免费、~1s）
>   └─ 复杂商品问题 → DeepSeek Agent（付费、~3-5s）
> ```
> 这种"逐渐升级"的路由策略是生产中控制 LLM 成本的经典模式。

**任务**：
- [ ] 运行 `python main.py intent` 测试意图分类准确率
- [ ] **思考**：为什么意图分类用规则引擎而不是 LLM？
- [ ] **思考**：查询改写（QueryRewriter）解决了什么问题？

---

## 📅 第三阶段：高级 Agent 模式（第 5-6 周）

**目标**：掌握 LangGraph 的三种进阶 Agent 模式。

### 3.1 Reflection（反思修正）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| Generate→Reflect→Revise | 三段式质量提升 | `app/agent/reflection.py:1-44`（文件头注释） |
| ReflectionState | 独立的反思状态 | `app/agent/reflection.py:92-97` |
| reflect/revise 节点 | 审阅 + 修正 | `app/agent/reflection.py:100-128` |
| 修正上限 | 最多 2 轮修正 | `app/agent/reflection.py:140-141` |

**任务**：
- [ ] 运行 `python main.py reflection` 体验反思模式
- [ ] **思考**：Reflection 和 Guardrails 有什么区别？
- [ ] **思考**：为什么修正不是无限循环？（答案在 `reflection.py:44-45」）

### 3.2 Plan-and-Execute（计划执行）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 三部曲 | Plan → Execute×N → Aggregate | `app/agent/planner.py:1-45`（文件头注释） |
| planner 节点 | LLM 生成 JSON 步骤列表 | `app/agent/planner.py:144-186` |
| executor 节点 | 按步骤调用工具→分析总结 | `app/agent/planner.py:189-252` |
| aggregator 节点 | 汇总各步骤→生成最终回答 | `app/agent/planner.py:255-270` |
| ReAct vs Plan | 灵活 vs 结构化的权衡 | `app/agent/planner.py:41-45` |

**任务**：
- [ ] 运行 `python main.py plan` 体验任务分解模式
- [ ] **思考**：什么场景适合 Plan-and-Execute 而不是 ReAct？
- [ ] **思考**：Plan-and-Execute 有什么缺点？

### 3.3 Multi-Agent（多 Agent 协作）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **Supervisor Pattern** | 监督者路由+子Agent执行 | `app/agent/multi_agent.py:1-48`（文件头注释） |
| supervisor 节点 | 决策路由到哪个子 Agent | `app/agent/multi_agent.py:128-149` |
| 三个子 Agent | shopping/aftersales/order | `app/agent/multi_agent.py:152-196` |
| Graph 拓扑 | supervisor→子Agent→supervisor 循环 | `app/agent/multi_agent.py:224-249` |

**任务**：
- [ ] 运行 `python main.py multi` 体验多 Agent 模式
- [ ] **思考**：为什么拆成多个 Agent 而不是一个 Agent+更多工具？
- [ ] **思考**：子 Agent 之间是否需要直接通信？

### 3.4 Structured Output（结构化输出）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| PydanticOutputParser | LangChain 内置格式化解析器 | `app/agent/structured.py:61-62,124` |
| 三步重试策略 | 直接JSON→清理提取→正则提取 | `app/agent/structured.py:130-151,153-203` |
| 三种方案对比 | Prompt要求→OutputParser→JSON Mode | `app/agent/structured.py:19-34` |

**任务**：
- [ ] 阅读 `app/agent/structured.py` 全文注释
- [ ] **思考**：为什么不用 `with_structured_output()`？
- [ ] **思考**：重试时为什么要在 prompt 中注入上次的错误信息？

---

## 📅 第四阶段：RAG 精调技术（第 7-8 周）

**目标**：掌握提升 RAG 检索精度的核心技术。

### 4.1 查询预处理

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 同义词扩展 | 口语→标准关键词的 SYNONYM_MAP | `app/rag/query_processor.py:27-40,57-78` |
| 年龄/价格检测 | 正则提取结构化过滤条件 | `app/rag/query_processor.py:82-116` |
| 查询改写（多轮） | 指代消解+LRU 缓存 | `app/rag/query_rewriter.py:58-137` |
| 关键词提取 | 去停用词后提取实词 | `app/rag/query_processor.py:119-138` |

### 4.2 结果重排序（Re-rank）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **粗排→精排** | 向量检索（粗排）→ LLM 打分（精排） | `app/rag/reranker.py:1-21` |
| LLM 批量打分 | 所有候选一次性给 LLM 评估 | `app/rag/reranker.py:110-157` |
| **分数融合** | `0.60×LLM + 0.40×vector` 加权 | `app/rag/reranker.py:159-185` |
| 启发式增强 | 名称命中+15% / 系列匹配+10% | `app/rag/reranker.py:188-207` |

> **核心概念 — 为什么需要 Re-rank？**
> Embedding 模型是通用的，不理解"乐高消防车"和"城市消防局"哪个更适合送礼。
> Re-rank 用 LLM 的深度语义理解能力对候选做精排，显著提升 top-k 精准度。
> 这是 RAG 精度的"最后一公里"优化。

**任务**：
- [ ] 对比 `RAGChain.query()` 和 `RAGChain.query_with_rerank()` 的差异
- [ ] **思考**：分数融合时为什么 LLM 权重 (0.60) > 向量权重 (0.40)？
- [ ] **思考**：启发式增强会不会引入偏见（如过度偏向名称匹配）？

### 4.3 高级检索

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 元数据过滤 | ChromaDB where 语法（$gte/$lte/$and） | `app/data/models.py:80-109` |
| 库存过滤 | 搜索结果自动剔除缺货商品 | `app/agent/tools.py:721-739` |
| SKU 去重 | 多粒度召回后按最高分去重 | `app/rag/chain.py:123-139` |

---

## 📅 第五阶段：生产级质量保障（第 9-10 周）

**目标**：掌握 AI 应用的生产化必备技术。

### 5.1 幻觉防控（Guardrails）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 四步防控管道 | 兜底→溯源→标注→相关性 | `app/core/guardrails.py:16-37,47-117` |
| 溯源校验 | 商品名是否在检索结果中 | `app/core/guardrails.py:203-220` |
| 来源标注 | 回答末尾追加引用 | `app/core/guardrails.py:223-248` |
| 相关性检查 | 回答与问题字符重叠度 | `app/core/guardrails.py:251-264` |

**任务**：
- [ ] **思考**：Guardrails 是"后置检测"，Structured Output 是"前置约束"，两者如何互补？

### 5.2 对话记忆管理

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **两级记忆架构** | 滑动窗口（L1）+ 摘要压缩（L2） | `app/core/memory.py:1-33` |
| 压缩触发 | `len(full_history) > max_total` | `app/core/memory.py:169-181` |
| LLM 摘要 | 将旧消息压缩为 2-3 句结构化摘要 | `app/core/memory.py:183-206` |
| 会话隔离 | 多 session_id 独立记忆空间 | `app/core/memory.py:243-264` |

> **为什么需要两级记忆？**
> - 纯截断：丢失用户偏好信息（"孩子5岁"）
> - 纯摘要：丢失最近对话细节
> - 两级结合：旧消息压缩为摘要保留偏好，新消息保留完整细节

**任务**：
- [ ] 运行 `python main.py memory` 观察记忆压缩过程
- [ ] **思考**：为什么不在每轮对话后都做摘要？

### 5.3 韧性工程（Resilience）

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **熔断器** | Closed→Open→Half-Open 状态机 | `app/core/resilience.py:53-113` |
| 指数退避重试 | 1s→2s→4s→...最多30s | `app/core/resilience.py:115-160` |
| **模型降级链** | DeepSeek→本地Ollama→模板回复 | `app/core/resilience.py:221-247` |
| 可重试错误判断 | Rate Limit/5xx 可重试，401/400 不可 | `app/core/resilience.py:170-179` |

**任务**：
- [ ] 阅读 `app/core/resilience.py` 了解熔断器状态机
- [ ] **思考**：为什么需要 Half-Open 状态而不是直接从 Open→Closed？

### 5.4 Token 成本管理

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| Token 估算 | 中文~1.5字符/token，英文~4字符/token | `app/core/token_tracker.py:76-83` |
| 成本计算 | 按模型定价计算费用 | `app/core/token_tracker.py:86-91` |
| 预算告警 | 日预算 80% 阈值告警 | `app/core/token_tracker.py:94-151` |
| 三层漏斗 | 路由拦截(50%+)→上下文压缩(30%)→模型选择(20%) | `app/core/token_tracker.py:33-37` |

### 5.5 查询缓存

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| LRU + TTL | 线程安全的精确匹配缓存 | `app/core/cache.py:44-110` |
| Semantic Cache 概念 | 向量相似度匹配的缓存 | `app/core/cache.py:1-30`（注释） |

---

## 📅 第六阶段：知识图谱（第 11-12 周）

**目标**：理解结构化知识与向量搜索的互补关系。

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| Neo4j 基础 | 图数据库连接与 Cypher 查询 | `app/graph/graph_store.py:12-41` |
| 图谱推荐 | 关系权重评分（系列40%+主题30%+年龄20%+价位10%） | `app/graph/graph_store.py:43-65` |
| 图谱浏览 | 按系列/主题/年龄/价位遍历 | `app/graph/graph_store.py:67-104` |
| 价位升降级 | 同主题价位树遍历 | `app/graph/graph_store.py:106-127` |
| 跨系列发现 | 同一主题下不同系列商品 | `app/graph/graph_store.py:129-149` |
| 图谱构建 | 125 商品→节点+关系的图构建脚本 | `scripts/build_knowledge_graph.py` |

> **向量搜索 vs 知识图谱**：
> - 向量搜索：「描述相似」→ 适合模糊需求（"好玩的消防车"）
> - 知识图谱：「结构推理」→ 适合明确关系（"同系列还有什么""更便宜的替代"）
> - 最佳实践：两者互补，不是替代

**任务**：
- [ ] **思考**：什么查询适合向量搜索，什么查询适合图谱搜索？
- [ ] **思考**：`graph_recommend` 中的 4 因子权重为什么这样分配？

---

## 📅 第七阶段：多模态与 API 服务（第 13-14 周）

**目标**：掌握多模态交互和 API 服务化。

### 7.1 多模态视觉

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| **LangChain 多模态消息** | `HumanMessage(content=[{text}, {image_url}])` | `app/vision/analyzer.py:136-141` |
| Base64 编码 | 本地图片→Data URL | `app/vision/analyzer.py:48-66` |
| 双通道设计 | DeepSeek API + 本地 Ollama qwen2.5vl | `app/vision/analyzer.py:83-151,174-237` |

> **核心概念 — 多模态消息格式**：
> ```python
> HumanMessage(content=[
>     {"type": "text", "text": "描述这张图片"},
>     {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
> ])
> ```
> `content` 可以是字符串（纯文本）或列表（多模态混合），LangChain 自动适配。

**任务**：
- [ ] 阅读 `app/vision/analyzer.py` 全文多模态注释
- [ ] **思考**：为什么 deepseek-v4-flash 可以通过 `ChatOpenAI` 调用？

### 7.2 FastAPI + WebSocket

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| FastAPI 应用工厂 | `create_app()` + CORS + 异常处理 | `app/api/server.py:9-24` |
| WebSocket 实时通信 | `ws/chat/{session_id}` | `app/api/routes.py:47-125` |
| 客服 WebSocket | `/ws/admin` 人工介入 | `app/api/routes.py:129-205` |
| 连接管理 | pub/sub 广播 + 会话追踪 | `app/api/ws_manager.py` |

**任务**：
- [ ] 运行 `python main.py serve` 启动 API 服务
- [ ] 查看 `http://localhost:8000/docs` Swagger 文档

---

## 📅 第八阶段：测试与评测（第 15-16 周）

**目标**：掌握 AI 应用的测试方法论。

### 8.1 单元测试

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 意图分类测试 | 15 个预设用例+准确率统计 | `tests/unit/test_query_processor.py` |
| 幻觉防控测试 | 溯源校验、相关性检查 | `tests/unit/test_guardrails.py` |
| 记忆管理测试 | 滑动窗口、摘要压缩 | `tests/unit/test_memory.py` |
| 缓存测试 | LRU + TTL | `tests/unit/test_cache.py` |
| 韧性测试 | CircuitBreaker 状态机 | `tests/unit/test_resilience.py` |
| 工具测试 | 价格计算、格式化 | `tests/unit/test_agent_tools.py` |

### 8.2 集成测试

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 向量库测试 | ChromaDB CRUD | `tests/integration/test_vector_store.py` |
| RAG 管道测试 | 意图→检索→生成集成 | `tests/integration/test_rag_pipeline.py` |
| Agent 管道测试 | ReAct 循环+12 工具 | `tests/integration/test_agent_pipeline.py` |
| API 测试 | FastAPI 端点 | `tests/integration/test_api.py` |

### 8.3 检索评测

| 主题 | 学习内容 | 代码位置 |
|------|----------|----------|
| 召回评测 | Hit Rate / MRR / Precision | `scripts/eval_recall.py` |
| RAGAS 质量评测 | Faithfulness / Relevance | `scripts/eval_quality.py` |

**任务**：
- [ ] 运行 `pytest tests/unit/ -v` 查看单元测试
- [ ] 运行 `python main.py eval` 运行召回评测
- [ ] 运行 `python main.py quality` 运行 RAGAS 评测

---

## 📊 技术栈速查表

| 层次 | 技术 | 项目中使用位置 |
|------|------|---------------|
| **LLM 调用** | LangChain ChatOpenAI / ChatOllama | `app/config.py:158-197` |
| **Agent 编排** | LangGraph StateGraph / ToolNode | `app/agent/graph.py` |
| **向量存储** | ChromaDB (langchain-chroma) | `app/vector_store/chroma_store.py` |
| **图数据库** | Neo4j (Cypher) | `app/graph/graph_store.py` |
| **关系数据库** | SQLAlchemy + PostgreSQL | `app/data/database.py` |
| **REST API** | FastAPI | `app/api/server.py` |
| **实时通信** | WebSocket | `app/api/routes.py` |
| **配置管理** | Pydantic Settings | `app/config.py` |
| **数据模型** | Pydantic BaseModel | `app/data/models.py` |
| **日志** | Loguru | `app/core/logging.py` |
| **评测** | RAGAS / 自定义 recall | `scripts/eval_*.py` |

---

## 🎯 学习检查清单

完成以下任务标志着你已经掌握了 Agentic RAG 开发的核心能力：

- [ ] 能解释 RAG 的完整流程（检索→格式化→生成）
- [ ] 能画出 LangGraph ReAct Agent 的节点-边拓扑图
- [ ] 能解释 `Annotated[list, add_messages]` 的作用
- [ ] 能编写自定义 @tool 函数
- [ ] 能实现意图路由的三层分发逻辑
- [ ] 能区分 ReAct / Reflection / Plan-and-Execute / Multi-Agent 四种模式
- [ ] 能解释分数融合的数学原理
- [ ] 能实现熔断器（CircuitBreaker）状态机
- [ ] 能设计两级对话记忆架构
- [ ] 能编写向量搜索+元数据过滤的混合检索
- [ ] 能区分向量搜索和知识图谱搜索的适用场景
- [ ] 能通过 WebSocket 实现实时 Agent 对话
- [ ] 能编写单元/集成/评测三层测试
- [ ] 能估算 LLM Token 成本并设计降本策略

---

## 📚 推荐阅读顺序

1. `README.md` — 项目总览
2. `app/config.py` — 配置中心（入门的第一个代码文件）
4. `app/data/loader.py` + `app/data/models.py` — 数据层
5. `app/vector_store/chroma_store.py` — 向量检索
6. `app/rag/chain.py` — 基础 RAG 链
7. `app/agent/state.py` + `app/agent/graph.py` — Agent 核心
8. `app/agent/tools.py` — 工具系统
9. `app/agent/reflection.py` → `planner.py` → `multi_agent.py` — 三种进阶模式
10. `app/core/` — 基础设施层
11. `app/vision/` + `app/graph/` — 多模态与知识图谱
12. `INTERVIEW.md` + `TESTING.md` — 面试与测试

---

> **持续更新**：本学习规划随项目演进持续更新。建议完成一个阶段后在对应 `[ ]` 前打 `[x]` 追踪进度。
