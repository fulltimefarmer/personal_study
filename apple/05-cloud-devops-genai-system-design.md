# 云/DevOps + GenAI/Agentic + 系统设计 深度问答 · Deep Q&A

> 说明：每题含中文题干、英文题干、中文答案、英文答案。本文件是本岗位（RAD 团队）的重点。
> Note: Each question has Chinese prompt, English prompt, Chinese answer, English answer. This file is the core for this RAD role.

---

# 第一部分 · Part 1：云基础设施 / DevOps

## CD-1. Docker 镜像(image)与容器(container)的区别？多阶段构建如何减小镜像？
**EN:** Docker image vs container? How does multi-stage build shrink images?

**中文答案：**
镜像是一套**只读、分层**的文件系统模板（代码、运行时、依赖）；容器是镜像的**运行实例**（加了可写层 + 进程/网络隔离）。减小体积：更小基础镜像(`alpine`/`distroless`)、**多阶段构建**（构建阶段与运行阶段分离，只拷贝产物）、合并 RUN 层、`.dockerignore`、只装生产依赖。

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY package*.json ./
RUN npm ci --omit=dev
CMD ["node", "dist/main.js"]
```

**English answer:**
An image is a **read-only, layered** filesystem template (code, runtime, deps); a container is a **running instance** of the image (writable layer + process/network isolation). Shrink: smaller base images (`alpine`/`distroless`), **multi-stage builds** (separate build vs runtime, copy only artifacts), merge RUN layers, `.dockerignore`, install only production deps.

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY package*.json ./
RUN npm ci --omit=dev
CMD ["node", "dist/main.js"]
```

---

## CD-2. Kubernetes 核心概念：Pod、Deployment、Service、Ingress、ConfigMap/Secret、HPA。
**EN:** Kubernetes core concepts: Pod, Deployment, Service, Ingress, ConfigMap/Secret, HPA.

**中文答案：**
- **Pod**：最小调度单元，一个或多个共享网络/存储的容器。
- **Deployment**：声明式管理副本数、滚动更新、回滚。
- **Service**：为 Pod 提供稳定虚拟 IP/DNS 与负载均衡。
- **Ingress**：HTTP(S) 路由入口，按域名/路径路由到 Service。
- **ConfigMap/Secret**：把配置/敏感信息与镜像解耦；Secret 存密钥（base64，生产配云 KMS/Secrets Manager）。
- **HPA**（HorizontalPodAutoscaler）：按 CPU/自定义指标自动扩缩容副本。

**English answer:**
- **Pod**: smallest schedulable unit; one or more containers sharing network/storage.
- **Deployment**: declaratively manages replicas, rolling updates, rollbacks.
- **Service**: stable virtual IP/DNS + load balancing for pods.
- **Ingress**: HTTP(S) entry routing to Services by host/path.
- **ConfigMap/Secret**: decouple config/secrets from images; Secret holds credentials (base64; use cloud KMS/Secrets Manager in prod).
- **HPA** (HorizontalPodAutoscaler): auto-scales replicas by CPU/custom metrics.

---

## CD-3. 描述针对本岗位（Angular + NestJS + AliCloud）的 CI/CD 流水线。
**EN:** Describe a CI/CD pipeline for Angular + NestJS on AliCloud.

**中文答案：**
1. **Trigger**：push/PR。
2. **Install & Cache**：`npm ci` + 依赖缓存。
3. **Lint & Test**：ESLint/Prettier；单元测试(Jest)；E2E(Playwright/Cypress)。
4. **Build**：Angular 生产构建 + NestJS 编译，产出 Docker 镜像（多阶段构建）。
5. **Security/QA**：依赖漏洞扫描(npm audit/Snyk)、镜像扫描(Trivy/阿里云 ACR)。
6. **Push**：镜像推送到阿里云容器镜像服务(ACR)。
7. **Deploy**：更新阿里云容器服务(ACK，即 K8s)或 ECS，滚动/蓝绿/金丝雀。
8. **Post-deploy**：健康检查、冒烟测试、监控告警(ARMS/云监控)。
9. **GenAI 增强**（本岗位亮点）：PR 阶段 agent 自动生成测试/审查、自动创建/修正 PR，human-in-the-loop 合并。

**English answer:**
1. **Trigger**: push/PR.
2. **Install & Cache**: `npm ci` + dependency cache.
3. **Lint & Test**: ESLint/Prettier; unit (Jest); E2E (Playwright/Cypress).
4. **Build**: Angular prod build + NestJS compile, produce Docker image (multi-stage).
5. **Security/QA**: dependency audit (npm audit/Snyx), image scanning (Trivy/Aliyun ACR).
6. **Push**: to Aliyun Container Registry (ACR).
7. **Deploy**: update Aliyun Container Service (ACK/K8s) or ECS, rolling/blue-green/canary.
8. **Post-deploy**: health checks, smoke tests, monitoring/alerting (ARMS/CloudMonitor).
9. **GenAI enhancement** (key for this role): agents auto-generate tests/reviews and create/fix PRs, human-in-the-loop merge.

---

## CD-4. 滚动更新、蓝绿部署、金丝雀发布的区别与取舍？
**EN:** Rolling update vs blue-green vs canary — differences and trade-offs?

**中文答案：**
- **滚动更新**：逐步替换旧实例，全程可用、无额外资源，但新旧版本短暂共存，回滚较慢。
- **蓝绿部署**：两套环境（蓝=旧、绿=新），切流量到绿，秒级回滚（切回蓝）；代价是双倍资源。
- **金丝雀**：小比例流量（如 5%）到新版本，观察指标逐步放量；风险最低、反馈最快，实现较复杂。
选择：低风险快速迭代 → 滚动；需秒级回滚的关键服务 → 蓝绿；大流量验证新特性 → 金丝雀。

**English answer:**
- **Rolling update**: gradually replaces old instances; always available, no extra resources, but old/new coexist briefly and rollback is slower.
- **Blue-green**: two environments (blue=old, green=new), switch traffic to green; instant rollback (switch back); costs double resources.
- **Canary**: a small % of traffic (e.g. 5%) to the new version, watch metrics, ramp up; lowest risk, fastest feedback, more complex.
Choice: rapid low-risk iteration → rolling; critical services needing instant rollback → blue-green; validating features at scale → canary.

---

## CD-5. 可观测性(observability)三支柱：日志、指标、追踪分别解决什么问题？
**EN:** Observability three pillars: logs, metrics, traces — what does each solve?

**中文答案：**
- **日志(logs)**：离散事件记录（错误栈、请求详情）——排查「具体发生了什么」。
- **指标(metrics)**：聚合数值（延迟、QPS、错误率、CPU）——观察趋势、告警、SLO。
- **追踪(tracing)**：一次请求跨服务的完整调用链（分布式追踪，trace ID 贯穿）——定位「哪个环节慢/失败」。
三者配合：指标发现问题 → 追踪定位链路 → 日志看细节。常用栈：Prometheus/Grafana + Loki/ELK + Jaeger/OpenTelemetry（阿里云 ARMS/链路追踪）。

**English answer:**
- **Logs**: discrete event records (error stacks, request details) — "what exactly happened".
- **Metrics**: aggregated numbers (latency, QPS, error rate, CPU) — trends, alerting, SLOs.
- **Traces**: a request's full call chain across services (distributed tracing, one trace ID) — "which step is slow/failing".
Together: metrics surface a problem → tracing pinpoints the path → logs give details. Common stack: Prometheus/Grafana + Loki/ELK + Jaeger/OpenTelemetry (Aliyun ARMS/distributed tracing).

---

## CD-6. 什么是 IaC（如 Terraform）？为什么用它管理 AliCloud 资源？
**EN:** What is IaC (e.g. Terraform)? Why manage AliCloud resources with it?

**中文答案：**
**IaC（基础设施即代码）**：用声明式代码定义云资源（VPC、ECS、RDS、ACK、SLB），版本化管理，可审查、可复现、可回滚。优势：消除手工控制台操作的人为错误；环境一致（dev/staging/prod 同一套代码不同参数）；`terraform plan` 预览变更、`apply` 幂等执行；`state` 记录真实状态。Terraform 有阿里云 Provider（`alicloud`），可统一管理 ASO 内部工具的云基础设施。

```hcl
resource "alicloud_db_instance" "main" {
  engine   = "PostgreSQL"
  instance_type = "pg.n4.small.1"
  ...
}
```

**English answer:**
**IaC (Infrastructure as Code)**: define cloud resources (VPC, ECS, RDS, ACK, SLB) with declarative code — versioned, reviewable, reproducible, rollback-able. Benefits: eliminates human error from manual console ops; consistent environments (dev/staging/prod same code, different params); `terraform plan` previews changes, `apply` is idempotent; `state` records reality. Terraform has an AliCloud provider (`alicloud`) to manage ASO internal-tool infra uniformly.

```hcl
resource "alicloud_db_instance" "main" {
  engine   = "PostgreSQL"
  instance_type = "pg.n4.small.1"
  ...
}
```

---

## CD-7. 如何管理密钥(secrets)？为什么不要把密钥写进代码或镜像？
**EN:** How to manage secrets? Why not hardcode them in code or images?

**中文答案：**
密钥（DB 密码、API key、token）写进代码/镜像 → 泄漏即泄露到 git 历史与镜像层，难以追溯与轮换。最佳实践：
- 分层：环境变量（非敏感）、云 KMS/Secrets Manager（阿里云 KMS/凭据管家）、K8s Secret（配合外部存储）。
- 注入时机：运行时注入而非构建期，避免进镜像层。
- 轮换：定期轮换 + 审计日志；最小权限原则。

**English answer:**
Secrets (DB passwords, API keys, tokens) hardcoded in code/images leak into git history and image layers, hard to trace and rotate. Best practices:
- Layering: env vars (non-sensitive), cloud KMS/Secrets Manager (Aliyun KMS/凭据管家), K8s Secret (backed by external store).
- Injection: at **runtime**, not build time, to keep them out of image layers.
- Rotation: periodic rotation + audit logs; least privilege.

---

# 第二部分 · Part 2：Generative AI / Agentic Workflows（本岗位重点）

## AI-1. 如何把 Generative AI 嵌入开发流水线（agentic workflow）？什么是 human-in-the-loop？
**EN:** How to embed GenAI into the dev pipeline (agentic workflow)? What is human-in-the-loop?

**中文答案：**
核心是「LLM 负责生成与推理，确定性代码负责校验与执行，人在关键节点审批」的**三明治结构**(LLM → 确定性代码 → LLM)。与 JD 直接对应的落地：
- **自动生成测试/样板代码**：输入 PR diff，agent 补测试与边界用例。
- **自动代码审查**：agent 先审（风格、安全隐患、潜在 bug），人复审。
- **自动创建/修正 PR**：agent 根据 issue/需求起草 PR，CI 跑测试，失败自动修复；通过后进入 **human-in-the-loop** 审批再合并。
- **RAG**：用团队内部文档/代码规范作上下文，提升生成质量与一致性。
- **human-in-the-loop**：高风险动作（合并、部署、写生产数据）前必须人工确认；AI 只做建议与草稿，保证质量、安全、可审计。

**English answer:**
The core is a **sandwich architecture** (LLM → deterministic code → LLM): LLMs generate/reason, deterministic code validates/executes, humans approve at critical gates. Directly matching this JD:
- **Auto-generate tests/boilerplate**: feed a PR diff, have an agent add tests and edge cases.
- **Automated code review**: an agent reviews first (style, security, bugs), humans re-review.
- **Auto create/fix PRs**: an agent drafts a PR from an issue/requirement; CI runs tests; on failure the agent auto-fixes; then **human-in-the-loop** approval before merge.
- **RAG**: use internal docs/coding standards as context for quality and consistency.
- **human-in-the-loop**: risky actions (merge, deploy, write prod data) require human confirmation; AI only proposes/drafts — ensuring quality, safety, auditability.

---

## AI-2. RAG 是什么？与微调(fine-tuning)相比，企业为何更常用 RAG？
**EN:** What is RAG? Why do enterprises prefer it over fine-tuning?

**中文答案：**
**RAG（检索增强生成）**：从外部知识库（向量库/搜索）检索相关片段，拼入 prompt，让 LLM 基于最新、可信资料生成并附引用。优点：知识实时更新、可控可追溯（可审计来源）、减少幻觉、无需重训、成本低。
**微调**：在特定数据上继续训练权重，适合「改变行为/风格/格式」而非「注入新知识」，成本高、更新慢、可能灾难性遗忘。
企业（尤其 Apple 强调隐私/合规）倾向 RAG：数据来源可控、更新快、易满足隐私与审计要求。

**English answer:**
**RAG (Retrieval-Augmented Generation)**: retrieve relevant snippets from an external knowledge base (vector DB/search) and prepend them to the prompt so the LLM generates from up-to-date, trusted sources with citations. Advantages: real-time updates, controllable/traceable (auditable), fewer hallucinations, no retraining, low cost.
**Fine-tuning**: continue training weights on specific data — suited to changing behavior/style/format rather than injecting knowledge; expensive, slow to update, risk of catastrophic forgetting.
Enterprises (Apple emphasizes privacy/compliance) prefer RAG: controllable sources, fast updates, easy privacy/audit compliance.

---

## AI-3. 生产部署 LLM 应用，如何做评估(evaluation)、防幻觉、保证隐私合规？
**EN:** How to evaluate, prevent hallucinations, and ensure privacy/compliance for production LLM apps?

**中文答案：**
- **评估**：构建 golden 数据集；自动化指标（准确率、忠实度/faithfulness、相关性、ROUGE/BLEU）+ **LLM-as-judge** + 人工抽检；A/B 测试；线上反馈闭环。
- **防幻觉**：RAG 提供可引用来源并约束「只根据给定资料回答」；结构化输出（JSON schema）；关键数值走确定性代码而非模型生成；高风险输出加校验与重试。
- **隐私合规**（契合 Apple）：数据最小化与脱敏（PII 打码）、私有化部署/专用通道、访问控制 + 审计日志、遵守 GDPR/个人信息保护法、敏感数据不进第三方模型、支持删除（被遗忘权）。

**English answer:**
- **Evaluation**: build a golden dataset; automated metrics (accuracy, faithfulness, relevance, ROUGE/BLEU) + **LLM-as-judge** + human spot checks; A/B testing; online feedback loop.
- **Prevent hallucination**: RAG supplies citable sources and constrains "answer only from provided material"; structured output (JSON schema); route critical numbers through deterministic code; validate/retry high-risk outputs.
- **Privacy/compliance** (fits Apple): data minimization & masking (PII redaction), private deployment/dedicated channels, access control + audit logs, GDPR/PIPL compliance, no sensitive data to third-party models, deletion (right to be forgotten).

---

## AI-4. 什么是 function calling / tool use？它如何让 agent 执行真实动作？
**EN:** What is function calling / tool use? How does it let agents perform real actions?

**中文答案：**
Function calling 是 LLM 按**预定义的 JSON schema** 输出「调用某个工具」的意图（工具名 + 参数），而不是直接生成动作。应用侧**确定性执行**该函数（查 DB、调 API、改状态），把结果回传给模型继续。这是「LLM 推理 + 确定性执行」的关键机制，也是 agentic workflow 的骨架：模型决定「调什么、传什么参」，代码负责「真正执行与安全校验」。

```ts
const tools = [{
  type: 'function',
  function: {
    name: 'get_order_status',
    description: '查询订单状态',
    parameters: { type: 'object', properties: { orderId: { type: 'string' } }, required: ['orderId'] },
  },
}];
```

**English answer:**
Function calling is when an LLM outputs the **intent to call a tool** (name + arguments) per a **predefined JSON schema**, instead of generating the action itself. The app side **deterministically executes** the function (query DB, call API, mutate state) and returns the result to the model to continue. This is the key "LLM reasoning + deterministic execution" mechanism and the skeleton of agentic workflows: the model decides "what to call with what args," code does the actual execution and safety checks.

```ts
const tools = [{
  type: 'function',
  function: {
    name: 'get_order_status',
    description: 'query order status',
    parameters: { type: 'object', properties: { orderId: { type: 'string' } }, required: ['orderId'] },
  },
}];
```

---

## AI-5. 向量数据库与 embeddings 在 RAG 中的作用？检索质量如何评估？
**EN:** Role of vector DB and embeddings in RAG? How to evaluate retrieval quality?

**中文答案：**
- **Embeddings**：把文本映射成向量，语义相近的文本向量距离近。RAG 把知识库 chunk 向量化入库，查询时把问题也向量化，用相似度（余弦/内积）检索 Top-K 相关片段。
- **向量库**：存储向量 + 支持 ANN（近似最近邻）检索（pgvector、Milvus、阿里云 OpenSearch/向量检索）。
- **检索质量评估**：命中率(hit rate)、MRR（平均倒数排名）、召回率/精确率；优化手段：chunk 大小与重叠、混合检索（向量 + 关键词 BM25）、重排序(reranker)、查询改写。

**English answer:**
- **Embeddings**: map text to vectors where semantically similar texts are close. RAG vectorizes knowledge-base chunks; at query time it vectorizes the question and retrieves Top-K similar chunks by similarity (cosine/inner product).
- **Vector DB**: stores vectors + ANN (approximate nearest neighbor) search (pgvector, Milvus, Aliyun OpenSearch/vector search).
- **Retrieval evaluation**: hit rate, MRR (mean reciprocal rank), recall/precision. Optimization: chunk size & overlap, hybrid search (vector + BM25 keyword), reranking, query rewriting.

---

## AI-6. agentic workflow 常见的编排方式：ReAct、规划器、多 agent 协作是什么？
**EN:** Common agent orchestration: ReAct, planners, multi-agent collaboration?

**中文答案：**
- **ReAct**（Reason + Act）：循环「思考 → 调用工具 → 观察结果 → 再思考」，直到完成任务——单 agent 的基础范式。
- **规划器(Planner)**：先制定步骤计划（plan-and-execute），再逐步执行，适合多步任务。
- **多 agent 协作**：多个专职 agent（如「编码 agent」「审查 agent」「测试 agent」）分工 + 结果传递，适合复杂流水线（如自动 PR：一个写代码、一个审、一个测）。
- 工程要点：明确的「停止条件」、失败重试与回退、人工审批点、可观测（记录每一步决策）。

**English answer:**
- **ReAct** (Reason + Act): loop "think → call tool → observe → think again" until done — the basic single-agent pattern.
- **Planner**: first produce a step plan (plan-and-execute), then execute step by step — for multi-step tasks.
- **Multi-agent**: specialized agents (e.g. coder, reviewer, tester) divide work and pass results — for complex pipelines (auto-PR: one writes, one reviews, one tests).
- Engineering essentials: clear stopping conditions, retry/fallback, human approval gates, observability (log every decision).

---

# 第三部分 · Part 3：系统设计

## SD-1. 设计 Apple Store Online 的「商品详情页 + 购物车 + 下单」系统（高层）。
**EN:** Design the "product detail + cart + checkout" system for Apple Store Online (high-level).

**中文答案：**
**需求**：浏览商品、库存/价格、购物车增删改、下单、高并发、低延迟、一致性。
**组件**：
- **前端**：Angular SPA + CDN；商品页 SEO 可 SSR。
- **网关/LB**：路由、限流、鉴权。
- **商品服务**：读多写少，Redis 缓存热点 + PostgreSQL 持久化；价格/库存独立服务。
- **购物车服务**：Redis（会话购物车，TTL）或 PG；乐观锁处理并发修改。
- **库存**：下单原子扣减（`UPDATE ... WHERE stock > 0`）防超卖；对账任务兜底。
- **订单服务**：订单 + 明细表，状态机；事务保证订单+库存一致，跨服务用 Saga/消息队列（RocketMQ）。
- **消息队列**：异步解耦（通知、发货）。
- **可观测**：日志、指标、追踪（ARMS）。
**关键权衡**：一致性 vs 可用性（下单最终一致 + 幂等）、缓存一致性（Cache Aside + TTL）、热点商品（本地缓存/预热）。

**English answer:**
**Requirements**: browse, inventory/price, cart CRUD, checkout, high concurrency, low latency, consistency.
**Components**:
- **Frontend**: Angular SPA + CDN; SSR for product SEO.
- **Gateway/LB**: routing, rate limiting, auth.
- **Product service**: read-heavy — Redis for hot products + PostgreSQL; separate price/inventory services.
- **Cart service**: Redis (session cart, TTL) or PG; optimistic locking for concurrent edits.
- **Inventory**: atomic deduction at order (`UPDATE ... WHERE stock > 0`) to prevent oversell; reconciliation job.
- **Order service**: order + items, state machine; transaction for order+inventory; Saga/message queue (RocketMQ) across services.
- **Message queue**: async decoupling (notifications, shipping).
- **Observability**: logs, metrics, tracing (ARMS).
**Key trade-offs**: consistency vs availability (eventual + idempotency), cache consistency (Cache Aside + TTL), hot products (local cache/prewarming).

---

## SD-2. 设计一个限流器(rate limiter)：算法、存储、分布式、返回策略。
**EN:** Design a rate limiter: algorithms, storage, distributed, response.

**中文答案：**
算法：**固定窗口**（简单、边界突刺）、**滑动窗口**（平滑）、**令牌桶**（允许突发，最常用）、**漏桶**（恒定流出、无突发）。
存储：单机内存；分布式用 Redis `INCR` + `EXPIRE`（原子）、或 `ZSET` 滑窗、Lua 脚本保证原子。
维度：用户/IP/API key/接口。
返回：超限返回 **429 + Retry-After**；多层限流（网关 + 服务）；降级与监控（当前 QPS、拒绝数）。

```lua
-- Redis 固定窗口限流（原子）
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
if c > tonumber(ARGV[2]) then return 0 else return 1 end
```

**English answer:**
Algorithms: **fixed window** (simple, boundary burst), **sliding window** (smooth), **token bucket** (allows bursts, most common), **leaky bucket** (constant outflow, no burst).
Storage: in-memory single node; distributed via Redis `INCR` + `EXPIRE` (atomic), `ZSET` sliding window, Lua for atomicity.
Dimensions: user/IP/API key/endpoint.
Response: **429 + Retry-After**; multi-layer (gateway + service); degradation & monitoring (current QPS, rejections).

```lua
-- Redis fixed-window rate limit (atomic)
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
if c > tonumber(ARGV[2]) then return 0 else return 1 end
```

---

## SD-3. 如何保证「下单」接口的幂等性与一致性？防超卖怎么做？
**EN:** How to ensure idempotency & consistency for "place order"? How to prevent overselling?

**中文答案：**
- **幂等**：客户端传唯一幂等键(Idempotency-Key/订单号)；服务端唯一索引或幂等表「先查后插」；重试/重复点击不产生重复订单；支付回调按交易号去重。
- **一致性**：订单 + 库存同一事务（单体）或 Saga + 补偿（微服务）；重试幂等；消息消费幂等（去重表）。
- **防超卖**：原子扣减 `UPDATE products SET stock = stock - 1 WHERE id = $1 AND stock > 0`，仅当影响行数 = 1 才算成功；或用乐观锁（版本号）。

```sql
UPDATE products SET stock = stock - 1
WHERE id = $1 AND stock > 0;  -- 返回影响行数为 1 才成功
```

**English answer:**
- **Idempotency**: client sends a unique idempotency key (Idempotency-Key / order no.); server uses a unique index or idempotency table ("check then insert"); retries/double-clicks don't duplicate; payment callbacks dedupe by transaction ID.
- **Consistency**: order + inventory in one transaction (monolith) or Saga + compensation (microservices); retries idempotent; consumers idempotent (dedup table).
- **Prevent oversell**: atomic deduction `UPDATE products SET stock = stock - 1 WHERE id = $1 AND stock > 0` — succeed only if 1 row affected; or optimistic locking (version).

```sql
UPDATE products SET stock = stock - 1
WHERE id = $1 AND stock > 0;  -- succeed only if 1 row affected
```

---

## SD-4. 什么是 CAP 定理？电商各场景如何取舍？
**EN:** What is CAP? Trade-offs across e-commerce scenarios?

**中文答案：**
CAP：分布式系统中一致性(C)、可用性(A)、分区容错(P)不可兼得；网络分区必然发生，故只能在 C 与 A 间取舍（P 必须满足）。
- **下单/支付**：倾向 **CP**——宁可暂时不可用，也不能超卖/重复扣款。
- **商品浏览/购物车**：倾向 **AP**——保证可访问，容忍短暂不一致，最终一致。
- 用**最终一致性 + 幂等 + 补偿**在 AP 上逼近业务正确性。

**English answer:**
CAP: in a distributed system you can't have all three of Consistency, Availability, and Partition tolerance; partitions inevitably occur, so you choose between C and A (P is mandatory).
- **Order/payment**: prefer **CP** — rather temporarily unavailable than oversell/double-charge.
- **Browsing/cart**: prefer **AP** — stay accessible, tolerate brief inconsistency, eventually consistent.
- Use **eventual consistency + idempotency + compensation** to approach correctness on AP.

---

## SD-5. 缓存策略：Cache Aside、Read/Write Through、Write Behind；缓存穿透/击穿/雪崩怎么解决？
**EN:** Caching strategies: Cache Aside, Read/Write Through, Write Behind; how to solve penetration/breakdown/avalanche?

**中文答案：**
- **Cache Aside**（最常用）：读未命中查 DB 再写缓存；更新时先更 DB 再删缓存（删比更新简单，避免双写不一致）。用 TTL 兜底。
- **Read/Write Through**：缓存层代理读写，应用只与缓存交互。
- **Write Behind**：先写缓存异步刷 DB，写入快但有丢失风险。
- **三灾**：
  - **穿透**（查不存在的数据）：布隆过滤器 + 空值缓存。
  - **击穿**（热点 key 过期瞬间）：互斥锁/`SETNX`、逻辑过期、永不过期+后台刷新。
  - **雪崩**（大量 key 同时过期/Redis 宕机）：过期时间加随机抖动、多级缓存、熔断降级、Redis 高可用（哨兵/集群）。

**English answer:**
- **Cache Aside** (most common): on miss, read DB then write cache; on update, update DB then delete cache (delete simpler than update, avoids dual-write inconsistency), with TTL as backstop.
- **Read/Write Through**: the cache layer proxies reads/writes; the app only talks to cache.
- **Write Behind**: write cache first, flush to DB async; fast writes but risk of loss.
- **Three hazards**:
  - **Penetration** (queries for non-existent data): Bloom filter + cache null values.
  - **Breakdown** (hot key expires): mutex/`SETNX`, logical expiry, never-expire + background refresh.
  - **Avalanche** (many keys expire together / Redis down): random TTL jitter, multi-level cache, circuit breaker, Redis HA (sentinel/cluster).

---

## SD-6. 消息队列(MQ)在电商中的作用？如何保证消息不丢、不重复、有序？
**EN:** Role of message queues in e-commerce? How to guarantee no loss, no duplication, ordering?

**中文答案：**
作用：**削峰**（秒杀流量缓冲）、**解耦**（下单后异步通知/发货/积分）、**异步**（耗时操作异步化）。
- **不丢**：生产端确认(ack)、MQ 持久化（broker 落盘 + 副本）、消费端手动 ack（处理完再确认）。
- **不重复**：消费幂等（唯一 ID + 去重表/唯一约束）；「至少一次」语义 + 幂等消费 = 恰好一次效果。
- **有序**：需要顺序的消息用同一分区/队列（按 key 路由，如订单号），单分区内有序；全局有序代价高，尽量避免。

**English answer:**
Role: **peak shaving** (buffer flash-sale traffic), **decoupling** (async notify/ship/points after order), **async** (offload slow ops).
- **No loss**: producer acks, broker persistence (disk + replicas), consumer manual ack (ack after processing).
- **No duplication**: idempotent consumption (unique ID + dedup table/unique constraint); "at-least-once" + idempotent consumers ≈ exactly-once.
- **Ordering**: route messages that need order to the same partition/queue (keyed by e.g. order no.); a single partition is ordered; global ordering is costly — avoid.

---

## SD-7. 如何设计「商品搜索/搜索联想(typeahead)」？（含 AI 增强与隐私）
**EN:** How to design product search / typeahead (with AI enhancement and privacy)?

**中文答案：**
- **联想(typeahead)**：前缀索引（Trie）或倒排索引 + 前缀查询；热门词缓存；每输入防抖 300ms 发请求；结果按热度/相关性排序；客户端本地缓存历史。
- **搜索**：倒排索引（Elasticsearch/阿里云 OpenSearch）+ 分词；相关性排序（BM25）；同义词/纠错。
- **AI 增强**：向量语义搜索（补关键词搜索的语义召回不足）+ RAG 生成购物建议。
- **隐私**（Apple 重点）：查询数据脱敏/匿名化、最小化存储、可删除、区分「设备端 vs 服务端」——敏感联想尽量本地(device) 计算，减少服务端日志。

**English answer:**
- **Typeahead**: prefix index (Trie) or inverted index + prefix query; cache hot terms; debounce 300ms per keystroke; rank by popularity/relevance; cache history client-side.
- **Search**: inverted index (Elasticsearch/Aliyun OpenSearch) + tokenization; relevance (BM25); synonyms/spell correction.
- **AI enhancement**: vector semantic search (fills keyword recall gaps) + RAG for shopping suggestions.
- **Privacy** (Apple's emphasis): redact/anonymize query data, minimize storage, support deletion, split device-side vs server-side — do sensitive suggestions on-device to reduce server logging.
