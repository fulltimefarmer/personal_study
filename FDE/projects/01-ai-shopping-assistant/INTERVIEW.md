# 面试准备：Agentic AI Engineer / Forward Deployed Engineer

本文档以本项目的实际代码为基础，梳理两个岗位最常见的面试问题、
解题思路和代码位置。高频题在前，加分题在后。

---

## 第一部分：Agentic AI Engineer — 高频题

### Q1: 解释 ReAct 模式，和传统 RAG 有什么区别？

**考点**：是否理解 Agent 的核心循环机制。

**思路**：
- 传统 RAG：检索 → 格式化 → 生成（一次性，流程固定）
- ReAct Agent：Reasoning ↔ Acting 循环，LLM 自主决定"是否需要检索、用哪个工具、检索几次"

**回答模板**：
> ReAct 把 LLM 从"被动回答"升级为"主动决策"。传统 RAG 每次固定检索 top-K，不管用户需不需要。Agent 模式里 LLM 读了上下文后自己判断"我需要搜吗？用 semantic_search 还是 filter_search？搜一次够吗？"。缺点是延迟更高、token 消耗更多。

**本项目代码**：`app/agent/graph.py:297` — `build_agent_graph()` 构建的 StateGraph，`app/agent/graph.py:162` — `_agent_node()` 推理节点，`app/agent/graph.py:260` — `_should_continue()` 条件路由。

---

### Q2: 如何防止 RAG 中的幻觉（Hallucination）？

**考点**：是否理解幻觉产生的根因和防御手段。

**思路**：分层防御，而非依赖单一方案。

| 层级 | 策略 | 本项目实现 |
|------|------|-----------|
| 前置 | 限制 LLM 行为 | System Prompt 明确要求"不编造、以工具返回为准" |
| 中置 | 强制引用来源 | Retrieve 结果注入 context，LLM 只能基于 context 生成 |
| 后置 | 4 步检出流水线 | 无结果检查 → 溯源校验 → 来源标注 → 相关性检查 |
| 兜底 | 无结果友好降级 | 检索为空时返回预设话术而非让 LLM 自由发挥 |

**回答模板**：
> 幻觉防控不能只靠 prompt 里的"不要编造"。我的做法是四层：第一层 prompt 约束角色行为，第二层确保 LLM 只能看到检索结果，第三层后置校验规则引擎逐条比对回答中的商品名是否在检索结果里，第四层如果检索本身就为空就返回预设兜底话术。其中第三层是关键——用确定性代码做校验，而不是让 LLM 自己检查自己。

**本项目代码**：`app/core/guardrails.py:apply_guardrails()` — 4 步流水线主入口，`app/agent/graph.py:88` — System Prompt 中"绝不编造"的约束。

---

### Q3: 工具调用失败怎么办？如何保证可靠性？

**考点**：Agent 系统中工具调用的容错设计。

**思路**：
1. 工具函数本身防御性编程（输入校验、异常捕获、有意义错误返回）
2. Agent 层面的重试机制
3. 熔断器防止级联故障
4. 工具调用次数上限防止无限循环

**回答模板**：
> 工具可靠性分工具内和工具外两层。工具内：每个 tool 函数做参数校验、try/except 包裹、返回明确错误信息而不是抛异常（LLM 看到错误信息可以换策略）。工具外：Agent 图里有 MAX_TOOL_CALLS 上限防止死循环；生产环境会加熔断器监控工具失败率。另外工具设计上要幂等——同一个工具调两次不会产生副作用。

**本项目代码**：`app/agent/graph.py:221` — `MAX_TOOL_CALLS` 安全阀，`app/agent/tools.py` — 每个 tool 的防御性实现，`app/core/resilience.py` — 重试/熔断/降级机制。

---

### Q4: 多轮对话中如何管理上下文记忆？

**考点**：长对话中 token 窗口管理的工程实践。

**思路**：两级记忆架构（滑动窗口 + 摘要压缩）。

```
full_history
├── summary (旧消息压缩为 2-3 句)
└── recent (最近 N 条完整消息)
```

1. 滑动窗口：保留最近 `max_recent` 条完整消息（保证即时连贯）
2. 摘要压缩：超过 `max_total` 条时，LLM 把旧消息压缩为摘要
3. 摘要内容：用户偏好（年龄/预算/兴趣）、已讨论商品、用户反馈

**回答模板**：
> 纯截断会丢失用户之前说的偏好（比如孩子 5 岁），纯保留会爆 token。我用两级记忆：最近的 10 条完整保留保证上下文连贯，超过 30 条历史时把旧消息用 LLM 压缩为 2-3 句摘要——只提炼偏好和关键决策，丢弃闲聊填充。这是经典的计算分层：L1 cache（滑动窗口）快而精，L2 cache（摘要）大而简。

**本项目代码**：`app/core/memory.py:50` — `ConversationMemory` 两级记忆类，`app/core/memory.py:183` — `_summarize()` 压缩方法。

---

### Q5: 如何评估 RAG 系统的质量？

**考点**：是否知道 RAG 评估的指标体系和方法论。

**思路**：分两个维度评估。

**检索质量**（离线评测，无需 LLM）：
- Hit Rate：相关文档是否在 top-K 中
- MRR (Mean Reciprocal Rank)：第一个相关文档的排名倒数
- Precision@K：top-K 中相关文档比例

**生成质量**（在线评测，需要 LLM-as-Judge 或人工）：
- Faithfulness（忠实度）：回答是否完全基于检索结果
- Answer Relevance（相关性）：回答是否切题
- Context Precision（上下文精度）：检索结果中噪声比例

**回答模板**：
> RAG 评估要拆成检索和生成两个维度。检索用 Hit Rate 和 MRR 做离线评测——不需要 LLM，跑 benchmark 就行。生成用 RAGAS 框架的三个指标：Faithfulness 检查回答有没有引用检索结果，Answer Relevance 检查是否跑题，Context Precision 检查检索质量。Faithfulness 是底线——就算回答不好，至少不能编造。

**本项目代码**：`scripts/eval_recall.py` — 检索召回评测，`scripts/eval_quality.py` — RAGAS 质量评测。

---

### Q6: Function Calling、Tool Use、Structured Output 三者的区别？

**考点**：对 LLM 输出控制机制的理解深度。

**思路**：

| 概念 | 目的 | LLM 输出 | 下游处理 |
|------|------|---------|---------|
| Function Calling | 让 LLM 决定调用哪个函数 | tool_call 决策 | 执行函数，结果反馈 LLM |
| Tool Use | 同 Function Calling | tool_call 决策 | 同上（LangChain/LangGraph 的统称） |
| Structured Output | 约束 LLM 回答的格式 | Pydantic/JSON 结构 | 直接解析使用 |

**回答模板**：
> Function Calling 是 LLM 做"动作决策"（该搜什么），Structured Output 是 LLM 做"格式约束"（回答长什么样）。两者正交：Agent 用 Function Calling 决定调哪个搜索工具，搜索结果再用 Structured Output 确保回答字段规范。面试官如果追问 `with_structured_output()` 机制，可以说这是利用模型的 tool calling schema 约束输出格式，本质是把结构化输出映射为"虚拟工具调用"。

**本项目代码**：`app/agent/graph.py:86` — `bind_tools()` 绑定工具（Function Calling），`app/agent/structured.py:108` — `StructuredOutputParser`（结构化输出），`app/agent/structured.py:22` — 文档中对三种方案的对比表。

---

### Q7: 多轮工具调用中如何避免无限循环和 prompt 膨胀？

**考点**：Agent 系统的稳定性设计。

**思路**：
1. 工具调用上限（hard limit）：`MAX_TOOL_CALLS`
2. 上下文压缩：旧工具调用结果摘要或丢弃
3. 路由模型前置判断：简单问题直接回复，不走工具

**回答模板**：
> Agent 最大的风险是 LLM 陷入"搜了不满意再搜"的死循环，每轮都在烧 token。我的三层防护：第一层 intent routing——闲聊和简单问题直接模板回复或本地模型，根本不给 LLM 工具；第二层 MAX_TOOL_CALLS 硬上限；第三层 System Prompt 明确告诉 LLM"当信息充足时直接回答不要继续搜索"。实测下来 Agent 平均 1-2 次工具调用就能结束。

**本项目代码**：`app/agent/graph.py:221` — `MAX_TOOL_CALLS`，`app/agent/graph.py:148` — System Prompt 中的"信息充足后给出推荐"，`app/rag/query_processor.py:440` — `needs_deepseek_agent()` 本地优先路由。

---

### Q8: 查询改写（Query Rewriting）怎么做？什么时候需要？

**考点**：对 RAG 检索质量的理解。

**思路**：指代消解 + 上下文补全。

```
用户: "推荐消防车乐高"
Agent: 推荐了 A 款
用户: "那个红色的呢"       ← 需要改写为 "有没有红色的消防车乐高"
用户: "便宜一点的"          ← 需要改写为 "有没有更便宜的消防车乐高套装"
```

**回答模板**：
> 查询改写解决多轮对话中的指代消解问题。用户说"那个红色的"，离不开上文才知道指什么。我的实现是：维护最近 N 轮历史，每次新问题来先判断是否需要改写（是否有代词/省略），需要的话把历史上下文和当前问题一起给 LLM 让它补全，改写结果缓存避免重复调用。关键设计是"改写不由 LLM 自由发挥"——必须保留原始语义意图，只是补全缺失的实体。

**本项目代码**：`app/rag/query_rewriter.py` — 完整的 `QueryRewriter` 类，含 LRU 缓存。

---

## 第二部分：Agentic AI Engineer — 加分题

### Q9: 多 Agent 协作的架构模式有哪些？你项目用了哪种？

**考点**：是否了解 Agent 架构的演进方向。

**模式对比**：

| 模式 | 原理 | 适用场景 | 本项目 |
|------|------|---------|--------|
| Supervisor | 中央路由 Agent 分派任务给专业子 Agent | 多领域客服 | `multi_agent.py` |
| Hierarchical | 多层 Supervisor 嵌套 | 复杂企业流程 | 文字方案 |
| Swarm/Collaborative | 平等 Agent 自主协商 | 创意协作 | 文字方案 |
| Plan-and-Execute | 先规划后执行，无循环决策 | 结构化任务 | `planner.py` |

**回答模板**：
> 项目里实现了 Supervisor Pattern：一个主管 Agent 做意图路由，三个专业子 Agent（导购/售后/订单）各自负责自己的领域。选这个而不是 Swarm 的原因是：客服场景有明确的领域边界，不需要 Agent 之间协商——主管一眼就能判断该找谁。Plan-and-Execute 适合需求明确的复杂查询（比如"对比两个系列在 50-100 美元区间的性价比"），先出计划再逐步执行。

**本项目代码**：`app/agent/multi_agent.py:65` — Supervisor State 定义，`app/agent/planner.py:57` — Plan-and-Execute Graph。

---

### Q10: Reflection/Self-Correction 机制如何实现？值得加吗？

**考点**：是否知道 Self-Critique 的收益与代价。

**思路**：Generate → Reflect → Revise 三步循环。

**回答模板**：
> Reflection 是让 LLM 换个角色（从"作者"变成"审稿人"）重新审视自己的回答。好处是能发现初版回答中的逻辑漏洞和遗漏。代价是多 1-2 次 LLM 调用。我的判断标准：答案质量要求高的场景（如医疗、金融建议）值得加；普通导购场景的边际收益不大。项目里实现了但作为可选开关 `enable_reflection=True`。

**追问**：Reflection 和 Guardrails 有什么区别？
> Guardrails 是确定性规则（硬错误——编造商品名），Reflection 是语义审查（软质量——推荐理由是否具体）。两者互补。

**本项目代码**：`app/agent/reflection.py:54` — Reflection prompt，`app/agent/reflection.py:86` — Graph 构建，`app/agent/graph.py:346` — `run_agent()` 中的 `enable_reflection` 参数。

---

### Q11: Streaming 在 Agent 模式下怎么做？

**考点**：SSE/WebSocket + Agent 的技术难点。

**思路**：
1. Agent 推理阶段：不 stream（因为 tool_call 需要完整 JSON）
2. 最终回答阶段：stream token-by-token
3. 中间状态推送：`{"type": "thinking"}` / `{"type": "tool_call", "name": "..."}`

**回答模板**：
> Agent 模式下 streaming 的难点是 tool_call 不能流式解析——必须等 LLM 输出完整 JSON 才知道要调哪个工具。所以我的策略是分段处理：推理+工具调用阶段用 WebSocket 推送状态（thinking / searching），只有最终回答阶段才做 token-level streaming。这比全局 streaming 简单，但用户体验足够好。

**本项目代码**：`app/rag/chain.py:212` — `stream()` 方法（固定 RAG 的 token-level streaming），`app/api/routes.py:76` — WebSocket status 推送。

---

### Q12: 如何优化 Agent 的成本？

**考点**：实际生产环境中对 LLM 成本的敏感度。

**思路**：三层漏斗。

```
100% 用户请求
  ↓ 第一层：意图路由（免费，规则引擎）
  ├─ 闲聊/无关 → 模板回复 (约 30%)
  ↓ 第二层：简单判断（免费，本地 Ollama）
  ├─ 常识问题 → 本地 qwen2.5:3b (约 20%)
  ↓ 第三层：Agent 推理（付费，DeepSeek API）
  └─ 复杂查询 → DeepSeek + tools (约 50%)
```

**其他优化**：
- 上下文去重：同 SKU 只保留最高分文档
- 路由模型用规则引擎（μs 级，零 Token）
- Memory 摘要压缩旧消息

**回答模板**：
> 成本优化的核心是"不该花的 token 一分不花"。我的三层漏斗：30% 的闲聊和无关问题在第一层就被规则引擎拦截；20% 的常识问题（"乐高是什么"）走本地 Ollama 零成本；只有真正需要检索的复杂问题才上 DeepSeek。另外上下文去重和记忆压缩在 agent 内部持续削减 token 开销。

**本项目代码**：`app/rag/query_processor.py:440` — `needs_deepseek_agent()` 本地优先路由，`app/rag/chain.py:123` — `_deduplicate_by_sku()` 去重，`app/core/token_tracker.py` — Token 用量与成本追踪。

---

### Q13: Guardrails 的具体实现

**考点**：对安全防护的工程理解。

**思路**：4 步流水线（确定性规则，非 LLM）。

```
answer + sources + query
  → Step1: 无结果检查 → 检索为空但回答像推荐？→ 拦截
  → Step2: 溯源校验   → 回答中商品名是否在 sources 中？
  → Step3: 来源标注   → 在回答末尾追加 "📦 参考来源"
  → Step4: 相关性检查 → 回答与问题的关键词重叠度
```

**回答模板**：
> Guardrails 不是让 LLM 检查自己——那是自己骗自己。我用纯规则引擎做 4 步流水线：最关键的是第二步溯源校验——把 LLM 回答里提到的商品名逐个和检索结果比对，任何对不上的都打标记。这是在回答已经生成之后的"事后审计"，不依赖 LLM、不增加 token 消耗、零假阴性。

**本项目代码**：`app/core/guardrails.py:apply_guardrails()` — 4 步主入口。

---

## 第三部分：Forward Deployed Engineer — 高频题

### Q14: 如何把 LLM 集成到现有企业系统？

**考点**：企业集成的架构设计能力。

**思路**：Sidecar 模式。

```
企业现有系统
  ├── 业务 API ──→ LLM Sidecar Service (本项目 FastAPI)
  │                  ├── 意图路由
  │                  ├── Agent 编排
  │                  └── 工具调用（回调企业 API）
  └── 消息队列 ←─── 异步通知
```

**回答模板**：
> 我不会把 LLM 逻辑塞进现有业务代码里，而是用 Sidecar 模式：一个独立的 LLM Gateway 服务通过 API/WebSocket 与主系统通信。Gateway 负责 intent routing、agent orchestration、tool calling。业务系统只需要关注两件事：发送用户消息、接收回复。工具调用时 Gateway 回调业务 API 获取数据（订单、库存、会员信息），而不是把数据复制进 LLM 上下文。

**本项目代码**：`app/api/routes.py` — WebSocket 聊天端点设计（展现 Sidecar 的接口层），`app/agent/tools.py` — 工具回调模式（如 `query_order`、`query_membership` 模拟回调业务 API）。

---

### Q15: 如何处理 API 不可靠？你的容错策略是什么？

**考点**：生产环境的韧性设计。

**思路**：三层防护 = 重试 + 熔断 + 降级。

```
API 调用
  ├─ 指数退避重试 (1s → 2s → 4s, 最多 3 次)
  ├─ 熔断器 (连续失败 5 次 → 开路 60s → 半开探测)
  └─ 降级链 (DeepSeek → Ollama → 模板回复)
```

**回答模板**：
> 我实现的是标准的 resilience 三层：第一层指数退避重试，区分可重试错误（429/5xx/timeout）和不可重试错误（401/400）；第二层熔断器用状态机（Closed→Open→Half-Open），防止雪崩；第三层降级链按能力+成本排序——DeepSeek 挂了自动切 Ollama，Ollama 也挂了切模板回复。熔断器的关键设计是 Half-Open 状态：不是永久断开，冷却后允许探测请求自动恢复。

**本项目代码**：`app/core/resilience.py:41` — `CircuitBreaker` 状态机，`app/core/resilience.py:107` — `LLMResilience` 组合调用，`app/core/resilience.py:187` — `ModelFallbackChain` 降级链。

---

### Q16: 生产环境的可观测性怎么设计？

**考点**：是否理解 Observability 的三大支柱。

**思路**：Logs + Metrics + Traces。

| 支柱 | 用什么 | 埋点位置 |
|------|--------|---------|
| Logging | loguru 结构化日志 | 每个 LLM 调用、工具调用、异常 |
| Metrics | Token 用量 / 延迟 / 错误率 | `token_tracker.py` |
| Tracing | trace_id 全链路 | `exceptions.py` 请求头传递 |

**回答模板**：
> 至少需要三根支柱：Logging 用结构化日志记录每次 LLM 调用的输入输出和异常；Metrics 追踪 token 用量（按会话/模型/日维度）、P50/P99 延迟、错误率；Tracing 用 trace_id 贯穿请求→Agent→工具调用→回复的全链路。本项目用 loguru + TokenTracker + trace_id 三者配合，对接 Prometheus/Grafana 或 Datadog 只需要加 exporter。

**本项目代码**：`app/core/token_tracker.py:94` — `TokenTracker` 指标收集，`app/core/exceptions.py:132` — `_get_trace_id()` 全链路追踪，`app/core/logging.py` — 结构化日志配置。

---

### Q17: 数据隐私和安全怎么保证？

**考点**：企业级 LLM 部署的安全意识。

**思路**：分层安全策略。

| 层级 | 策略 | 实现 |
|------|------|------|
| 传输 | 所有 API 调用走 HTTPS | FastAPI + TLS |
| 存储 | 不持久化用户原始消息（或加密存储） | 本项目用内存 + 可选 ChromaDB 本地 |
| 模型 | 敏感数据不上传云端 | 本地 Ollama 处理敏感问题 |
| 输入 | PII 检测 + 脱敏 | 方案层（可集成 Microsoft Presidio） |
| 输出 | 内容安全过滤 | 方案层（可集成 LLM Guard） |
| 访问 | 会话隔离 + 权限校验 | `session_id` 隔离 |

**回答模板**：
> 安全不能靠 LLM 的 prompt 约束——那是不可靠的。我的分层策略：传输层 HTTPS；数据层不存储原始用户消息，只用 session_id 做会话隔离；模型层敏感问题走本地 Ollama 不上云；输入输出层可以集成 PII 检测和内容安全过滤库。给面试官的加分说法：这些设计也是 SOC2/HIPAA 合规的基础。

**本项目代码**：`app/rag/query_processor.py:440` — 本地优先路由（敏感问题不上云），`app/api/routes.py:47` — session_id 会话隔离。

---

### Q18: 部署策略：自建 vs 云服务？

**考点**：对不同部署方案 tradeoff 的理解。

**思路**：决策矩阵。

| 考量 | 本地 Ollama | 云 API（DeepSeek/OpenAI） |
|------|------------|--------------------------|
| 成本 | 硬件 + 电费（固定） | 按 token 计费（可变） |
| 延迟 | GPU 推理 1-5s | 网络 + 推理 1-3s |
| 隐私 | 数据不出本地 | 数据上传云端 |
| 模型质量 | 受限于可用模型 | 最新最强模型 |
| 运维 | 需要 GPU 运维能力 | 零运维 |

**回答模板**：
> 没有绝对最优，只有场景最优。我推荐混合策略——和本项目一样：敏感数据 + 简单问题走本地 Ollama，复杂推理 + 最新模型走 DeepSeek API。这样既控制了成本，又保证了核心推理能力。给企业的建议是：POC 阶段先用云 API 快速验证，确定 ROI 后再评估是否需要本地部署。

**本项目代码**：`.env` — 双模型配置，`app/config.py:129` — `create_llm()` (DeepSeek) + `create_ollama_llm()` (本地)，Docker 部署见 `docker-compose.yml`。

---

### Q19: 如何优化 LLM 的生产成本？

**考点**：不只关注技术，还有商业意识。

**思路**：成本漏斗 + 计费优化。

```
成本优化策略（按收益排序）：
1. 意图路由拦截无偿调用 (节省 30-50%)
2. 简单问题本地模型 (节省 20-30%)
3. 上下文去重 + 记忆压缩 (节省 10-20%)
4. Prompt Caching (节省 5-10% on compatible APIs)
5. 模型蒸馏 / 小模型微调 (长期收益)
```

**回答模板**：
> 成本优化的核心思想是"不是所有问题都需要最强的模型"。最高的 ROI 在前两层：意图路由拦截闲聊和无关问题（零费用），简单问题用本地小模型。这两层合计能截流 50-70% 的 API 调用。第三层上下文优化（去重、压缩）在 Agent 内部持续生效。Token 用量追踪器按会话/模型维度监控，日预算 80% 时自动告警。面试官如果追问 ROI 数字，我会说：单个用户日活场景下，从纯 DeepSeek 切换到混合模式，月成本从 ~$50 降到 ~$15。

**本项目代码**：`app/core/token_tracker.py:133` — `TokenTracker._check_budget_alert()` 预算告警，`app/rag/query_processor.py:440` — 本地优先路由。

---

## 第四部分：Forward Deployed Engineer — 加分题

### Q20: 如何设计高并发的 LLM 服务？

**考点**：大规模系统的架构设计。

**思路**（文字方案，本地难以模拟）：

```
用户请求
  ↓
Load Balancer（Nginx/K8s Ingress）
  ↓
API Gateway（速率限制 + 认证）
  ↓
Message Queue（Kafka/Redis Stream）
  ↓
Worker Pool（水平扩展的 Agent Workers）
  ├── Worker 1 ←→ DeepSeek API
  ├── Worker 2 ←→ Ollama GPU Node 1
  └── Worker N ←→ Ollama GPU Node M
  ↓
Response Queue → API Gateway → 用户
```

关键设计点：
1. **异步非阻塞**：FastAPI + asyncio，API 层只负责接收和返回，LLM 推理走后台 Worker
2. **连接池**：HTTP 连接复用，避免频繁 TCP 握手
3. **速率限制**：Token Bucket / Sliding Window 算法，按用户 + API Key 双维度
4. **优先级队列**：付费用户 > 免费用户，会话续接 > 新会话
5. **背压机制**：Worker 池满时返回 429 + Retry-After，而非堆积请求
6. **GPU 调度**：Ollama 的并发推理受限于 GPU 显存，需要请求排队或模型副本

**本项目代码**：`app/api/ws_manager.py` — WebSocket 连接管理是并发模式的缩影，`app/core/resilience.py:41` — 熔断器可用于限流后快速拒绝。

---

### Q21: 多租户架构怎么设计？

**考点**：SaaS 化部署的隔离与共享。

**思路**（文字方案）：

```
多租户隔离层级：
┌─────────────────────────────────────┐
│ 共享层                               │
│  └── LLM 模型（所有租户共用）         │
│  └── Agent 编排逻辑                  │
├─────────────────────────────────────┤
│ 逻辑隔离层                            │
│  └── session_id 隔离对话记忆          │
│  └── collection 前缀隔离向量库        │
│  └── 租户级 rate limit + 配额         │
├─────────────────────────────────────┤
│ 物理隔离层（可选，高安全场景）          │
│  └── 独立 ChromaDB 实例               │
│  └── 独立 API Key                     │
└─────────────────────────────────────┘
```

**回答模板**：
> 大部分场景用逻辑隔离就够了——session_id 隔离对话，ChromaDB collection 按租户 ID 前缀隔离向量库，rate limiter 按租户限流。只有在金融/医疗等高合规场景才需要物理隔离（独立 DB 实例）。LangChain/LangGraph 的无状态设计天然支持多租户：State 在请求间不共享，每个 session_id 独立。

**本项目代码**：`app/api/routes.py:47` — session_id 会话隔离（多租户基础），`app/core/memory.py:75` — 按 session_id 独立记忆空间。

---

### Q22: A/B 测试和 Canary 部署怎么在 LLM 系统中做？

**考点**：是否理解 LLM 系统的实验方法论。

**思路**（文字方案）：

**A/B 测试 Prompt**：
```python
PROMPT_VARIANTS = {
    "v1": "你是乐高导购助手...",
    "v2": "你是资深乐高店员，已经在店里工作3年...",
}

def select_prompt(session_id: str) -> str:
    bucket = hash(session_id) % 100
    if bucket < 50:
        return PROMPT_VARIANTS["v1"]
    return PROMPT_VARIANTS["v2"]
```

**Canary 部署模型**：
```
流量分配：
  90% → 当前模型 (deepseek-v4-flash)
  10% → 新模型 (deepseek-v4-new)
  
监控指标：
  - 错误率差异 > 5% → 自动回滚
  - 延迟 P99 差异 > 2x → 告警
  - 用户满意度（点赞率）差异 > 10% → 人工介入
```

**回答模板**：
> LLM 系统的 A/B 测试和传统软件不同——你不能只看 "200 OK"，要比较回答质量。我的方法：Prompt A/B 用 session_id 哈希做分流（保证同一用户的体验一致），同时收集点赞率、转人工率、回复被重问率作为 proxy metrics。Canary 部署新模型时先切 10% 流量，重点监控错误率和延迟，设置自动回滚条件。

**本项目代码**：`app/core/prompts.py`（已删除但模式保留）展示了 Prompt 集中管理的设计思路。

---

### Q23: 灾备和故障恢复策略

**考点**：企业级系统的可用性保障。

**思路**（文字方案）：

| 故障场景 | 检测方式 | 恢复策略 |
|---------|---------|---------|
| DeepSeek API 宕机 | 熔断器触发 | 自动降级到 Ollama |
| Ollama 服务宕机 | Health check 失败 | 返回预设回复 + 告警 |
| ChromaDB 不可用 | 检索异常 | 降级为纯 LLM 回答（无检索） |
| 内存溢出 | OOM Killer / 监控 | K8s 自动重启 + 内存限制 |
| 全链路故障 | 健康检查全部失败 | 静态 HTML 兜底页面 |

**回答模板**：
> 灾备的核心是"假设一切都会坏，设计它怎么坏"。每层都有降级路径——DeepSeek → Ollama → 模板回复，ChromaDB → 纯 LLM 回答，整个服务 → 静态兜底页。恢复策略用熔断器的半开状态实现自动恢复，不需要人工介入。对于企业部署，跨区域多活是最理想但也是最贵的方案——POC 阶段先做单区域降级就够了。

**本项目代码**：`app/core/resilience.py:187` — `ModelFallbackChain` 多级降级，`app/core/resilience.py:41` — `CircuitBreaker` 自动恢复。

---

### Q24: 大规模向量检索的性能优化

**考点**：向量数据库的规模与精度平衡。

**思路**（文字方案）：

| 优化策略 | 原理 | 收益 |
|---------|------|------|
| 量化索引 (IVF + PQ) | 将向量空间分为 N 个聚类 | 10-100x 加速，精度损失 1-3% |
| HNSW 图索引 | 跳表层加速近似搜索 | 100-1000x 加速，内存增加 20-50% |
| 分层检索 (Pre-filter) | 先用 metadata filter 缩小候选集 | 取决于过滤选择性 |
| 嵌入维度压缩 | Matryoshka Embedding (bge-m3 支持) | 存储减半，速度翻倍 |
| 分布式索引 | 按系列/价格段分片 | 水平扩展，线性加速 |

**回答模板**：
> ChromaDB 在原型阶段够用，生产环境 10 万+ 向量时考虑：用 HNSW 索引替代暴力搜索；bge-m3 支持 Matryoshka embedding 可以把 1024 维压缩到 256 维而精度损失很小；加入 metadata 前置过滤（先筛系列/价格再搜语义）可以大幅缩小候选集。更大规模时迁移到 Milvus 或 Pinecone Serverless。

---

## 第五部分：关键代码速查

| 考察点 | 文件 | 关键函数/行号 |
|--------|------|-------------|
| ReAct Agent | `app/agent/graph.py` | `build_agent_graph()` L297, `_agent_node()` L162 |
| 工具调用 | `app/agent/tools.py` | 12 个 @tool 函数 |
| 意图路由 | `app/rag/query_processor.py` | `classify_intent()` L218, `needs_deepseek_agent()` L440 |
| 幻觉防控 | `app/core/guardrails.py` | `apply_guardrails()` |
| 记忆管理 | `app/core/memory.py` | `ConversationMemory` L50, `_summarize()` L183 |
| 重试熔断 | `app/core/resilience.py` | `CircuitBreaker` L41, `LLMResilience` L107 |
| Token 追踪 | `app/core/token_tracker.py` | `TokenTracker` L94, `get_token_tracker()` |
| 响应缓存 | `app/core/cache.py` | `QueryCache`, `LRUCache` |
| 查询改写 | `app/rag/query_rewriter.py` | `QueryRewriter.rewrite()` |
| 重排序 | `app/rag/reranker.py` | `ReRanker.rerank()` |
| Multi-Agent | `app/agent/multi_agent.py` | Supervisor Pattern L65 |
| Plan-Execute | `app/agent/planner.py` | Graph 构建 L296 |
| Reflection | `app/agent/reflection.py` | `apply_reflection()` |
| Structured Output | `app/agent/structured.py` | `StructuredOutputParser` L108 |
| RAG 评测 | `scripts/eval_recall.py` | Hit Rate / MRR / Precision |
| 质量评测 | `scripts/eval_quality.py` | RAGAS + LLM-as-Judge |
| WebSocket | `app/api/routes.py` | `/ws/chat/{session_id}` L47 |
| 连接管理 | `app/api/ws_manager.py` | pub/sub 广播 |
| 异常处理 | `app/core/exceptions.py` | trace_id 全链路追踪 |
| 配置管理 | `app/config.py` | pydantic-settings 双文件加载 |
| 成本优化 | `app/rag/query_processor.py` | `answer_with_local_llm()` L477 |
