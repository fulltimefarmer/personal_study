# 01 · AI Shopping Assistant

> 主项目推荐。基于 LEGO RAG 购物助手经历，升级成可评估、可上线、可复用的 FDE 项目。  
> 技术栈：**Python/FastAPI 后端 + Next.js 前端**。详细方案见 `../../06-FDE项目实战指南.docx` 第 3 章。

## 1. 业务背景

零售品牌希望在官网/会员端提供 AI 导购：根据用户问题推荐商品、解释卖点、对比 SKU、回答库存和促销。用户是消费者、客服和运营。

## 2. 为什么这个项目有竞争力

- 直接复用你 LEGO 的 RAG 经历，但把它升级成“可评估、可运营”的产品，而不是 Demo。
- 同时覆盖 AI FDE 的核心难点：商品数据、检索质量、引用、拒答、评估、成本、权限。
- 有明确业务指标：推荐准确率、转化率、客服工作量、P95、单次成本。
- 能讲“从数据管道到用户端”的端到端交付，而不是只调 API。

## 3. 目标与非目标

### 目标

- 自然语言导购与商品推荐
- 回答带商品引用（名称、价格、链接/ID）
- 可评估：召回、引用、拒答、延迟、成本
- 可私有化部署
- 有反馈和运营闭环

### 非目标

- 不做通用聊天机器人
- 不自动下单/支付
- 不承诺 100% 正确
- 第一版不做多模态

## 4. 用户与场景

| 用户 | 场景 | 痛点 |
|------|------|------|
| 消费者 | 问“适合 5 岁孩子的积木” | 商品多、不知道怎么选 |
| 客服 | 查卖点、库存、促销 | 知识分散、回答不一致 |
| 运营 | 维护推荐和话术 | 无法评估效果 |

## 5. 技术栈

### 后端

- Python 3.12+
- FastAPI + Pydantic v2
- SQLAlchemy 2 + Alembic
- PostgreSQL + pgvector 或 Milvus
- Redis（会话/缓存/限流）
- Celery / Arq（索引、评估）
- httpx（LLM/商品 API）
- pytest + pytest-asyncio + ruff
- uv / Docker

### 前端

- Next.js 15+（App Router）
- TypeScript
- Tailwind CSS
- TanStack Query
- Auth.js
- Playwright

### AI

- BGE / OpenAI embedding
- Qwen / GPT / 私有化模型
- 评估：Ragas / DeepEval 或自建脚本
- 可选：LangChain/LlamaIndex（不要过度封装）

## 6. 架构

```text
商品主数据/库存/促销/内容
        │ 批/实时同步
        ▼
Python ingestion -> 清洗/切分/Embedding -> pgvector/Milvus
        │
Next.js Chat UI -> FastAPI BFF -> 查询改写 -> 混合检索 -> 重排
        │                         │
        │                         └-> LLM -> 答案 + 商品引用
        ▼
反馈/评估/埋点/成本监控
```

## 7. 项目结构

```text
01-ai-shopping-assistant/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/                 # chat, products, feedback, admin
│   │   ├── core/                   # config, security, logging, deps
│   │   ├── domain/                 # 商品/会话/引用/评估
│   │   ├── models/                 # SQLAlchemy
│   │   ├── schemas/                # Pydantic
│   │   ├── repositories/           # DB/vector store
│   │   ├── integrations/           # LLM, embedding, 商品 API
│   │   ├── workers/                # 索引、评估、清理
│   │   └── evaluation/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/(chat)/page.tsx
│   ├── app/admin/eval/page.tsx
│   ├── components/                 # Chat, Citation, ProductCard
│   ├── lib/                        # api client, auth
│   ├── hooks/
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml
│   ├── k8s/
│   ├── helm/
│   └── .env.example
└── docs/
    ├── 01-discovery.docx
    ├── 02-architecture.docx
    └── 03-acceptance.docx
```

## 8. 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat` | 问题、会话、租户/用户 |
| GET | `/api/v1/products/{id}` | 商品详情/引用 |
| POST | `/api/v1/feedback` | 有用/无用/纠错 |
| POST | `/api/v1/admin/ingest` | 文档/商品索引 |
| GET | `/api/v1/admin/eval` | 评估报告 |
| GET | `/healthz` | 健康检查 |

## 9. 数据模型

| 表 | 关键字段 |
|----|----------|
| product | id, sku, name, brand, price, category, status |
| document | id, source, title, acl, updated_at |
| chunk | id, document_id, content, embedding, metadata |
| conversation | id, user_id, tenant_id, created_at |
| message | id, conversation_id, role, content, citations |
| feedback | message_id, rating, comment |
| eval_case | question, expected_answer, expected_docs |
| eval_run | run_id, metrics, model, prompt_version |

## 10. 实现步骤

### 阶段 1：项目初始化（2–3 天）

1. 建 `backend/`（uv + FastAPI + ruff + pytest）。
2. 建 `frontend/`（Next.js + TypeScript + Tailwind）。
3. 用 Docker Compose 起 Postgres（pgvector）和 Redis。
4. 建健康检查、配置、日志、错误处理。
5. 写 README 和 `.env.example`。

### 阶段 2：数据与索引（4–5 天）

1. 准备 20–50 个商品/FAQ 样例。
2. 解析、清洗、切分、embedding。
3. 写入 pgvector/Milvus，建索引。
4. 写一个检索脚本/top-k 接口。
5. 记录召回样例和失败。

### 阶段 3：RAG 问答（5–7 天）

1. 查询改写 + 混合检索。
2. Prompt 要求引用、结构化输出、拒答。
3. 接 LLM，处理超时/限流/重试。
4. 返回答案 + 商品引用。
5. Next.js Chat UI 接 API。

### 阶段 4：评估与权限（4–5 天）

1. 建 30 条评估集（可答/不可答/权限）。
2. 计算召回、引用准确、拒答、延迟、成本。
3. 加租户/渠道/门店权限过滤。
4. 加反馈和审计。
5. 输出评估报告。

### 阶段 5：生产化与 Demo（4–5 天）

1. Dockerfile + Compose 一键启动。
2. 加 Redis 缓存、限流、健康检查。
3. 加指标/日志/Trace。
4. 写 5 分钟 Demo 脚本。
5. 复盘并准备面试故事。

## 11. 里程碑

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | Discovery + 商品样例 + 评估问题 | 问题陈述、30 条评估集 |
| 2 | 清洗/切分/embedding/检索 | Top-K 检索可用 |
| 3 | RAG 回答 + 商品引用 | 端到端 Demo |
| 4 | 评估 + 权限 + 反馈 | 评估报告 |
| 5 | 部署 + Demo + 复盘 | Docker、监控、项目包 |

## 12. 验收标准

- [ ] 30 条评估问题，引用准确率 ≥ 80%
- [ ] 无答案/无商品时拒答或转人工
- [ ] 回答带商品名、价格、链接/ID
- [ ] 权限：不同渠道/门店看到不同商品
- [ ] P95 延迟和单次成本可接受
- [ ] 有失败分析和 Guardrails
- [ ] 前端可在移动端使用

## 13. 面试讲法

“我做过 LEGO 的 RAG 导购助手，覆盖 BGE + Milvus + Qwen。这个项目让我理解：AI FDE 的难点不是接模型，而是商品数据、检索质量、评估、引用和业务转化。”
