# 乐高智能导购助手 · 小砖家

> FDE 01 号项目：基于 **Agentic RAG** 的乐高商品智能导购与客服系统。  
> 支持商品导购、售后工单、订单查询、会员查询、平台活动等综合服务能力。125 款真实乐高商品数据，主推理支持 DeepSeek / 本地 Ollama，内置 **ChromaDB 向量检索**，可选 **Neo4j 知识图谱**。

本项目已从 `D:\git\ai_shopping_bot` 迁入 FDE 目录，并完成 **Windows 11 本地可运行性修复**：

- 修复 Windows 无 `readline` 导致 CLI 启动失败的问题；
- 默认数据库从 PostgreSQL 改为 **SQLite**，零中间件启动；
- 默认 Embedding 改为 **本地 Hash 向量**，无需先下载 bge-m3 即可跑通检索；
- 缺少 DeepSeek Key 时自动回退本地 Ollama，应用不会在 import 阶段崩溃；
- Neo4j 未启动时 `graph_search` 自动回退向量检索；
- 增加 Windows PowerShell / macOS Shell 一键启动脚本；
- 前端 WebSocket 改用 Vite 代理，不再硬编码 `localhost:8000`。

---

## 1. 技术栈

| 组件 | 本地默认 | 可选增强 | 说明 |
|---|---|---|---|
| 语言 / 包管理 | Python 3.11 + uv | — | `uv.lock` 锁定依赖 |
| 后端 | FastAPI + WebSocket + Uvicorn | — | REST + 实时推送 |
| Agent | LangGraph + LangChain | — | ReAct 状态图 + 14 个工具 |
| 向量库 | ChromaDB（本地持久化） | Milvus Lite | 嵌入式，零服务 |
| Embedding | 本地 Hash 向量（1024 维） | Ollama `bge-m3` | 默认离线可跑 |
| LLM | Ollama `qwen2.5:3b` | DeepSeek API | `LLM_PROVIDER=auto` 自动选择 |
| 关系数据库 | SQLite | PostgreSQL 16 | 商品 / 库存 |
| 图数据库 | 不启用（自动回退） | Neo4j | 知识图谱推荐 |
| 缓存 | 进程内 LRU + TTL | Redis | 查询缓存 |
| 前端 | Vue 3 + Vite | — | 客户端 3000 / 客服端 3001 |
| 网络搜索 | 关闭（未配置 Key） | Tavily API | 商品库外信息 |
| 部署 | 本地三进程 | Docker Compose | 生产可继续 K8s |

> 本地开发默认 **不需要** PostgreSQL、pgvector、Redis、Docker、Neo4j。  
> 只需要 **uv + Node.js + Ollama** 就能完整跑通“前端 → API → 检索 → LLM → 引用”。  
> 如果 Ollama 未启动，RAGChain 会自动降级为“检索结果直出”，仍然能看到商品和来源；启动 Ollama 后恢复自然语言回答。

---

## 2. 已实现能力

- 125 条乐高商品 CSV 数据，自动导入 SQLite；
- 商品多粒度向量化（名称 / 描述 / 完整），ChromaDB 检索；
- 意图分类：商品导购 / 售后 / 订单会员 / 活动 / 闲聊 / 业务外；
- 固定 RAG 与 Agentic RAG 双模式；
- 14 个业务工具：语义搜索、过滤搜索、商品详情、库存、比价、图谱、售后工单、订单、会员、活动、联网搜索、转人工等；
- 幻觉防控：来源校验、无结果兜底、引用标注；
- 两级记忆：滑动窗口 + 摘要压缩；
- Reflection、Plan-and-Execute、Multi-Agent、结构化输出实验模式；
- WebSocket 实时聊天 + 客服端会话监控/介入；
- 响应缓存、Token 统计、熔断/重试基础件；
- 单元测试 236 条，全部通过。

---

## 3. 项目结构

```text
01-ai-shopping-assistant/
├── app/
│   ├── config.py                 # 配置中心（.env、路径、LLM/Embedding 工厂）
│   ├── data/                     # CSV 加载、清洗、SQLAlchemy 模型、库存
│   ├── vector_store/             # VectorStoreBase + ChromaDB + Embedding 工厂
│   ├── graph/                    # Neo4j 知识图谱（可选）
│   ├── rag/                      # RAGChain、查询改写、重排、意图路由
│   ├── agent/                    # LangGraph ReAct、工具、Reflection、Planner、Multi-Agent
│   ├── api/                      # FastAPI 组装、REST/WS 路由、连接管理
│   ├── core/                     # 日志、异常、记忆、Guardrails、缓存、韧性、Token
│   └── vision/                   # 图片分析（可选）
├── public/                       # 客户端聊天前端（Vue 3 + Vite，3000）
├── admin/                        # 客服工作台（Vue 3 + Vite，3001）
├── files/products.csv            # 125 条乐高商品数据
├── db/                           # SQLite 与 ChromaDB 本地数据（运行时生成）
├── scripts/
│   ├── init_db.py                # 初始化商品/库存（幂等）
│   ├── verify_env.py             # 跨平台环境自检
│   ├── build_knowledge_graph.py  # Neo4j 图谱构建（可选）
│   ├── eval_recall.py            # 召回评测
│   ├── eval_quality.py           # LLM-as-Judge 质量评测
│   └── ...
├── tests/
│   ├── unit/                     # 纯逻辑测试（236 条）
│   └── integration/              # 需要 Chroma/LLM/Neo4j/DB 的集成测试
├── docs/
│   ├── FDE-project-plan.md       # 原 FDE 01 项目规划
│   └── FDE-src-plan.md           # 原 src 规划
├── main.py                       # CLI / FastAPI 入口
├── start.ps1 / start.bat         # Windows 11 一键启动
├── start.sh                      # macOS / Linux 一键启动
├── .env.example                  # 配置模板
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

---

## 4. 架构设计

```text
                         ┌──────────────────────────────┐
                         │        Vue 3 客户端 :3000     │
                         │   客服工作台 :3001            │
                         └──────────────┬───────────────┘
                                        │ WebSocket / REST
                         ┌──────────────▼───────────────┐
                         │      FastAPI  :8000           │
                         │  /health  /sessions  /ws/...  │
                         └──────────────┬───────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             │                          │                          │
   ┌─────────▼─────────┐      ┌─────────▼─────────┐      ┌─────────▼─────────┐
   │ 意图路由/本地优先  │      │  RAGChain          │      │  LangGraph Agent  │
   │ 规则引擎 μs 级     │      │ 检索→重排→生成     │      │ ReAct + 14 tools  │
   └─────────┬─────────┘      └─────────┬─────────┘      └─────────┬─────────┘
             │                          │                          │
             │              ┌───────────▼───────────┐              │
             │              │ ChromaDB 向量库        │              │
             │              │ Hash / bge-m3         │              │
             │              └───────────┬───────────┘              │
             │                          │                          │
             │              ┌───────────▼───────────┐              │
             │              │ SQLite / PostgreSQL   │              │
             │              │ 商品 + 库存            │              │
             │              └───────────────────────┘              │
             │                                                     │
             │              ┌───────────────────────┐              │
             └──────────────► Ollama qwen2.5:3b     ◄──────────────┘
                            │ 或 DeepSeek API       │
                            └───────────────────────┘
                                        │
                            ┌───────────▼───────────┐
                            │ Neo4j（可选）          │
                            │ 商品/系列/主题关系     │
                            └───────────────────────┘
```

### 请求链路（本地无 DeepSeek Key）

```text
用户输入
  ↓
意图分类（规则引擎）
  ├─ 闲聊 / 业务外 → 模板回复（0 Token）
  ├─ 简单商品问题 → 本地 Ollama 常识回答
  ├─ 商品导购 / 筛选 → 固定 RAGChain（检索 + 引用，稳定）
  └─ 售后 / 订单 / 活动 → Agent（Ollama + 工具）
  ↓
幻觉防控 / 来源标注 / 记忆写入
  ↓
WebSocket 返回 answer + sources + tool_calls_log
```

> 配置真实 `DEEPSEEK_API_KEY` 后，复杂商品问题会进入 Agentic RAG，由 DeepSeek 自主选择工具。

---

## 5. 快速开始

### 5.1 Windows 11（推荐）

#### 前置软件

| 软件 | 是否必须 | 安装命令 |
|---|---|---|
| uv | 必须 | `winget install --id astral-sh.uv -e` |
| Node.js 18+ | 必须（前端） | `winget install --id OpenJS.NodeJS.LTS -e` |
| Ollama | 聊天必须 | `winget install --id Ollama.Ollama -e` |
| Git | 可选 | `winget install --id Git.Git -e` |
| Docker Desktop | 可选 | `winget install --id Docker.DockerDesktop -e` |
| Neo4j | 可选 | Neo4j Desktop 或 Docker |
| PostgreSQL | 可选 | 本机已有 18.6，可复用 |

> 如果 `winget` 安装的 uv 出现 “uv trampoline failed” 或链接失效，改用官方脚本：
>
> ```powershell
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> ```
>
> 安装后重开终端，确保 `uv --version` 正常。

#### 第一次运行

```powershell
# 1. 进入项目
cd D:\git\personal_study\FDE\projects\01-ai-shopping-assistant

# 2. 启动 Ollama（安装后通常已在后台运行）
ollama serve
# 另开终端拉取模型
ollama pull qwen2.5:3b

# 3. 复制配置
Copy-Item .env.example .env

# 4. 安装 Python 依赖
uv sync --extra dev

# 5. 初始化 SQLite 商品/库存
uv run python scripts/init_db.py

# 6. 构建向量库（默认 Hash，秒级）
uv run python main.py ingest

# 7. 启动后端
uv run python main.py serve
```

再开两个终端启动前端：

```powershell
cd D:\git\personal_study\FDE\projects\01-ai-shopping-assistant\public
npm ci
npm run dev
```

```powershell
cd D:\git\personal_study\FDE\projects\01-ai-shopping-assistant\admin
npm ci
npm run dev
```

#### 一键启动

```powershell
.\start.ps1 local
# 或双击 start.bat
```

脚本会自动完成：复制 `.env` → `uv sync` → `npm ci` → 检查/拉取 Ollama 模型 → 初始化 SQLite → 构建向量库 → 打开三个服务窗口。

#### 访问地址

| 服务 | 地址 |
|---|---|
| 客户端聊天 | <http://localhost:3000> |
| 客服工作台 | <http://localhost:3001> |
| 后端 API | <http://localhost:8000> |
| Swagger | <http://localhost:8000/docs> |
| 健康检查 | <http://localhost:8000/health> |

---

### 5.2 macOS

#### 前置软件

```bash
# Homebrew（如未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install uv node ollama
# 或：curl -LsSf https://astral.sh/uv/install.sh | sh
# Node 也可从 https://nodejs.org 安装
# Ollama 也可从 https://ollama.com/download 安装
```

#### 第一次运行

```bash
cd /path/to/01-ai-shopping-assistant

# 1. 启动 Ollama 并拉取模型
ollama serve
# 另开终端
ollama pull qwen2.5:3b

# 2. 配置与依赖
cp .env.example .env
uv sync --extra dev

# 3. 初始化数据与向量库
uv run python scripts/init_db.py
uv run python main.py ingest

# 4. 启动后端
uv run python main.py serve
```

另开终端启动前端：

```bash
cd public && npm ci && npm run dev
```

```bash
cd admin && npm ci && npm run dev
```

一键启动：

```bash
chmod +x start.sh
./start.sh local
# 或 bash start.sh local
```

> macOS 若使用 zsh，`ollama serve` 可以放在单独终端；首次启动 Ollama 后模型会常驻。

---

### 5.3 零依赖 / 高质量模式切换

#### 默认模式（最稳）

```dotenv
LLM_PROVIDER=auto
EMBED_PROVIDER=hash
DATABASE_URL=sqlite:///./db/shopping_bot.sqlite3
```

- 不需要 PostgreSQL / pgvector / Redis / Neo4j / Docker；
- 只需要 Ollama 的 `qwen2.5:3b` 支持聊天；
- 检索质量是词法级语义，足够跑通链路和 Demo。

#### 使用 bge-m3 提升检索质量

```powershell
ollama pull bge-m3:latest
```

`.env`：

```dotenv
EMBED_PROVIDER=ollama
EMBED_MODEL=bge-m3:latest
```

然后必须重建向量库（集合名会自动带 `_ollama` 后缀，避免和 hash 向量混用）：

```powershell
uv run python main.py ingest
```

#### 使用 DeepSeek 云端模型

```dotenv
LLM_PROVIDER=auto
DEEPSEEK_API_KEY=sk-你的真实Key
DEEPSEEK_MODEL=deepseek-v4-flash
```

- 有有效 Key 时，复杂商品问题进入 Agentic RAG；
- 没有 Key 时自动回退 Ollama，不会启动失败。

#### 使用 PostgreSQL（可选）

```dotenv
DATABASE_URL=postgresql://lego:lego123@localhost:5432/shopping_bot
```

```powershell
uv run python scripts/init_db.py
```

> `docker-compose.yml` 把容器 PostgreSQL 映射到宿主机 **5433**，避免和本机 5432 冲突。

#### 使用 Neo4j（可选）

```powershell
# Docker
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:latest

# 构建图谱
uv run python scripts/build_knowledge_graph.py
uv run python scripts/test_graph_search.py
```

未启动 Neo4j 时，`graph_search` 会自动回退到向量检索，不会让 Agent 崩溃。

#### 使用 Redis（可选）

项目当前使用进程内 LRU 缓存，不依赖 Redis。需要多进程共享缓存时再接入。

---

## 6. 配置说明

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `auto` | `auto` / `ollama` / `deepseek` |
| `LLM_MODEL` | `qwen2.5:3b` | Ollama 对话模型 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 地址 |
| `DEEPSEEK_API_KEY` | 空 | 留空自动回退 Ollama |
| `EMBED_PROVIDER` | `hash` | `hash` / `ollama` |
| `EMBED_MODEL` | `bge-m3:latest` | `EMBED_PROVIDER=ollama` 时生效 |
| `EMBED_DIMENSIONS` | `1024` | Hash 向量维度 |
| `DATABASE_URL` | SQLite 文件 | 可切换 PostgreSQL |
| `CHROMA_PERSIST_DIR` | `./db/chroma` | 向量库目录 |
| `CHROMA_COLLECTION` | `lego_products` | 实际集合名会追加 `_<provider>` |
| `TOP_K` | `4` | 检索返回数量 |
| `NEO4J_*` | localhost | 可选图谱 |
| `TAVILY_API_KEY` | 空 | 可选联网搜索 |
| `DEBUG` | `true` | 调试日志 |
| `LLM_REQUEST_TIMEOUT` | `60` | LLM 超时秒数 |
| `TOOL_CALL_TIMEOUT` | `30` | 单工具超时秒数 |

配置优先级：环境变量 > `.env.local` > `.env` > 代码默认值。  
`.env` 与 `.env.local` 都已加入 `.gitignore`，不会提交敏感信息。

---

## 7. 验证与测试

### 7.1 环境自检

```powershell
uv run python scripts/verify_env.py
```

会检查 Python / uv / Node / Ollama / 模型 / CSV / 数据库 / 向量库。

### 7.2 单元测试

```powershell
uv run pytest tests/unit -q
```

当前结果：**236 passed**。

### 7.3 集成测试（需要外部服务）

```powershell
uv run pytest tests/integration -q
```

按需启动 Chroma / Ollama / Neo4j / PostgreSQL；未启动的服务相关用例会跳过或失败，属于预期。

### 7.4 快速冒烟

```powershell
# 后端健康
Invoke-RestMethod http://localhost:8000/health

# 意图路由
uv run python main.py intent

# Agent 切换逻辑
uv run python main.py agent-switch

# 向量库统计
uv run python main.py stats
```

本地已验证：

- `uv run pytest tests/unit -q` → 236 passed；
- `public` / `admin` 的 `npm run build` 均成功；
- `GET /health` → 200；
- WebSocket `推荐适合5岁孩子的消防车` → 返回答案 + 3 条商品来源；
- SQLite 125 条商品，ChromaDB 375 条文档。

---

## 8. API 与事件

| 类型 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/sessions` | 会话列表 |
| GET | `/sessions/{id}/messages` | 会话消息 |
| DELETE | `/sessions/{id}` | 清空会话 |
| WS | `/ws/chat/{session_id}` | 客户端聊天 |
| WS | `/ws/admin` | 客服端监控/介入 |

客户端发送：

```json
{ "message": "适合 5 岁孩子的消防车" }
```

服务端返回：

```json
{
  "type": "response",
  "answer": "...",
  "session_id": "...",
  "tool_calls_log": [{ "name": "rag_chain", "args": { "query": "..." } }],
  "sources": [
    { "sku": "60463", "name": "云梯消防车", "score": 0.53 }
  ],
  "guardrails": {}
}
```

> 开发环境前端通过 Vite 的 `/ws` 代理连接后端。生产构建时请由 Nginx/网关代理 `/ws`，或在构建前设置 `VITE_WS_URL=wss://your-domain/ws/chat`。

---

## 9. 继续架构 / 演进路线

### L1 · 本地 MVP（当前已完成）

- SQLite + ChromaDB + Hash Embedding；
- 固定 RAG + Agent 双模式；
- Vue 客户端 + 客服端；
- 本地 Ollama 推理；
- 单元测试、环境自检、一键启动。

### L2 · 数据与检索质量

1. `EMBED_PROVIDER=ollama` 切换 bge-m3，重建向量库；
2. 引入 pgvector 或 Milvus Lite，替换 JSON/Chroma 原型；
3. 增加商品数据增量同步、去重、版本化；
4. 补充 30–50 条评估集，计算 Recall@K、引用准确率、拒答率；
5. 对 `app/rag/reranker.py` 做 A/B：LLM 重排 vs 规则重排。

### L3 · Agent 与工具

1. 配置 DeepSeek Key，启用 Agentic RAG；
2. 完善订单/售后/活动的真实系统适配器；
3. 为工具增加权限、超时、幂等和审计；
4. 将 `app/agent/tools.py` 拆成 `tools/product.py`、`tools/order.py`、`tools/after_sales.py`；
5. 引入结构化输出和工具调用重试。

### L4 · 生产化

1. PostgreSQL 替代 SQLite，Alembic 管理迁移；
2. Redis 会话缓存、限流、分布式锁；
3. Celery / Arq 异步索引与评估；
4. 鉴权、租户隔离、审计日志；
5. Prometheus / OpenTelemetry / 结构化日志；
6. Docker Compose → K8s / Helm；
7. 私有化部署与离线模型包。

### 可扩展点

| 扩展点 | 位置 | 说明 |
|---|---|---|
| 向量后端 | `app/vector_store/base.py` | 实现 `VectorStoreBase` 即可替换 Chroma/Milvus/FAISS |
| Embedding | `app/vector_store/embeddings.py` | `HashEmbeddings` / `OllamaEmbeddings`，可加 OpenAI |
| LLM | `app/config.py:create_llm` | auto/ollama/deepseek，可加更多 provider |
| 工具 | `app/agent/tools.py` | `@tool` 装饰器注册新业务能力 |
| Prompt | `app/core/prompts.py` | 集中式 Prompt Registry |
| 记忆 | `app/core/memory.py` | 滑动窗口 + 摘要压缩 |
| 幻觉防控 | `app/core/guardrails.py` | 来源校验 / 拒答 / 标注 |
| 缓存 | `app/core/cache.py` | LRU + TTL，可替换 Redis |
| Trace/成本 | `app/core/token_tracker.py` | Token 统计与成本分析 |

---

## 10. 常见问题

| 现象 | 原因 / 解决 |
|---|---|
| `python` 打开 Microsoft Store | 使用 `uv run python ...`，或在 Windows“应用执行别名”关闭 python |
| `uv` 找不到 / 启动失败 | 优先用官方安装脚本；重开终端；确认 `uv --version` |
| `readline` 报错 | 已修复，Windows 自动跳过；旧版本请更新代码 |
| `ollama` 连接失败 | 运行 `ollama serve`；确认 `http://localhost:11434/api/tags` 可访问 |
| 7B 模型报 `rocblas ... gfx1100` | 当前机器 Ollama ROCm 兼容问题；使用 `qwen2.5:3b` 或设置 CPU 推理 |
| bge-m3 构建很慢 | 代码默认让 embedding 走 CPU（规避 AMD ROCm 特定 token 崩溃），375 条约 2–3 分钟 |
| 向量库为空 | `uv run python main.py ingest` |
| 找不到商品/库存全缺货 | `uv run python scripts/init_db.py` |
| 前端 `esbuild` 安装脚本被拦截 | `npm rebuild esbuild` 或 `npm approve-scripts esbuild` |
| 端口被占用 | 5432 是本机 PostgreSQL；Compose 已改用 5433 |
| 中文日志乱码 | 使用 Windows Terminal / PowerShell 7，设置 `$env:PYTHONUTF8=1` |
| `npm ci` 后 Vite 启动失败 | 删除 `node_modules` 后重新 `npm ci` |

更完整的 Windows 环境说明见 [`ENVIRONMENT-SETUP.md`](./ENVIRONMENT-SETUP.md)。

---

## 11. 与 FDE 01 规划的对应关系

原 FDE 规划文档已保留在 [`docs/FDE-project-plan.md`](./docs/FDE-project-plan.md)。当前实现与规划的对应：

| FDE 规划 | 当前实现 |
|---|---|
| 商品数据与索引 | `files/products.csv` → SQLite + ChromaDB |
| RAG 问答与引用 | `RAGChain` + `sources` + 前端展示 |
| Agent / 工具 | `app/agent` + 14 tools |
| 评估 | `scripts/eval_recall.py` / `eval_quality.py` / 集成测试 |
| 权限 | 待补：租户/渠道过滤 |
| 反馈与运营 | 待补：反馈 API + 评估看板 |
| 部署 | 本地脚本 + Docker Compose |
| 可观测性 | 日志 / Token 统计 / 健康检查，待接 Prometheus |

---

## 12. 说明

- 本项目用于学习与作品集展示，商品数据为样例数据，价格/库存为模拟值；
- 默认配置优先保证“任何环境能启动”，生产质量请按第 9 节逐步升级；
- 原始 `ai_shopping_bot` 的 `.git`、`node_modules`、`dist`、`db/chroma` 等生成物未复制，保持仓库干净。
