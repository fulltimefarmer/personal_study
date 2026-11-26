# 本地环境准备与排障（Windows 11 / macOS）

> 适用项目：`FDE/projects/01-ai-shopping-assistant`（乐高智能导购助手）  
> 检查时间：2026-11-26  
> 目标：不依赖生产级中间件，在本地把“前端 → FastAPI → 向量检索 → Ollama → 引用”完整跑通。

---

## 1. 当前机器检查结果

| 组件 | 状态 | 说明 |
|---|---|---|
| Windows | ✅ | Windows 11（`platform.release()` 显示 10，属于正常） |
| Python | ✅ | 由 uv 管理：`3.11.18` |
| uv | ✅ | `C:\Users\Administrator\.local\bin\uv.exe`，0.13.10 |
| Node.js | ✅ | `v24.18.0` |
| npm | ✅ | `11.16.0` |
| Ollama | ✅ | 0.40.18，已安装并运行在 `127.0.0.1:11434` |
| Ollama 模型 | ✅ | `qwen2.5:3b`、`bge-m3:latest` 已拉取 |
| SQLite | ✅ | Python 内置，默认数据库 `db/shopping_bot.sqlite3` |
| ChromaDB | ✅ | 本地持久化；首次 `ingest` 生成 375 条文档（仓库不提交生成物） |
| PostgreSQL | ✅ 可选 | 本机 PostgreSQL 18.6 运行在 5432，项目默认不需要 |
| pgvector | ❌ 可选 | 未安装；默认 Hash 向量不需要 |
| Redis | ❌ 可选 | 未安装；默认进程内 LRU 缓存 |
| Neo4j | ❌ 可选 | 未安装；`graph_search` 会自动回退向量检索 |
| Docker | ❌ 可选 | 未安装；本地模式不需要 |
| Git | ⚠️ 可选 | 当前终端 PATH 中无 git，但项目文件夹已存在 |

> 关键结论：**本地默认栈只需要 uv + Node.js + Ollama。**  
> PostgreSQL、pgvector、Redis、Neo4j、Docker 全部是可选增强，不影响项目启动。

---

## 2. 默认本地选型

| 能力 | 默认方案 | 是否需要额外安装 |
|---|---|---|
| 关系数据库 | SQLite | 否 |
| 向量库 | ChromaDB + 本地 Hash Embedding | 否 |
| 聊天 LLM | Ollama `qwen2.5:3b` | 是（Ollama） |
| 高质量 Embedding | Ollama `bge-m3` | 可选 |
| 缓存 | 进程内 LRU + TTL | 否 |
| 图数据库 | Neo4j | 可选 |
| 网络搜索 | Tavily | 可选 |
| 容器化 | Docker Compose | 可选 |

---

## 3. Windows 11 安装步骤

### 3.1 安装 uv

```powershell
winget install --id astral-sh.uv -e
```

如果 winget 安装后出现 `uv trampoline failed`、链接失效或 `uv` 不可用，改用官方脚本：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

重开终端验证：

```powershell
uv --version
uv python install 3.11
```

### 3.2 安装 Node.js

```powershell
winget install --id OpenJS.NodeJS.LTS -e
node --version
npm --version
```

### 3.3 安装 Ollama

```powershell
winget install --id Ollama.Ollama -e
```

安装后确认服务：

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

如果不可用，手动启动：

```powershell
ollama serve
```

拉取模型（另开终端）：

```powershell
ollama pull qwen2.5:3b
# 可选：更高质量的向量模型
ollama pull bge-m3:latest
```

### 3.4 初始化项目

```powershell
cd D:\git\personal_study\FDE\projects\01-ai-shopping-assistant

Copy-Item .env.example .env
uv sync --extra dev
uv run python scripts/init_db.py
uv run python main.py ingest
uv run python main.py serve
```

前端（另开两个终端）：

```powershell
cd public
npm ci
npm run dev
```

```powershell
cd admin
npm ci
npm run dev
```

或一键：

```powershell
.\start.ps1 local
```

### 3.5 访问

- 客户端：<http://localhost:3000>
- 客服端：<http://localhost:3001>
- API 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

---

## 4. macOS 安装步骤

```bash
# Homebrew 如未安装
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install uv node ollama
# 或 uv：curl -LsSf https://astral.sh/uv/install.sh | sh
```

启动 Ollama 并拉模型：

```bash
ollama serve
# 另开终端
ollama pull qwen2.5:3b
ollama pull bge-m3:latest   # 可选
```

初始化项目：

```bash
cd /path/to/01-ai-shopping-assistant
cp .env.example .env
uv sync --extra dev
uv run python scripts/init_db.py
uv run python main.py ingest
uv run python main.py serve
```

前端：

```bash
cd public && npm ci && npm run dev
cd admin  && npm ci && npm run dev
```

一键：

```bash
chmod +x start.sh
./start.sh local
```

---

## 5. 可选中间件

### 5.1 PostgreSQL

项目默认 SQLite，不需要 PostgreSQL。若要复用本机 PostgreSQL 18：

```sql
CREATE USER lego WITH PASSWORD 'lego123';
CREATE DATABASE shopping_bot OWNER lego;
```

`.env`：

```dotenv
DATABASE_URL=postgresql://lego:lego123@localhost:5432/shopping_bot
```

然后：

```powershell
uv run python scripts/init_db.py
```

### 5.2 pgvector

默认 Hash 向量不需要 pgvector。需要演练 pgvector 时推荐 Docker：

```powershell
docker run -d --name pgvector `
  -e POSTGRES_PASSWORD=postgres `
  -p 5433:5432 `
  pgvector/pgvector:pg18
```

```powershell
docker exec -it pgvector psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

> 当前代码的向量后端是 ChromaDB；pgvector 属于 L2 架构演进项，不是本地启动必需。

### 5.3 Neo4j

```powershell
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/password123 neo4j:latest
```

```powershell
uv run python scripts/build_knowledge_graph.py
uv run python scripts/test_graph_search.py
```

未启动 Neo4j 时，Agent 的 `graph_search` 工具会自动回退到 Chroma 语义检索。

### 5.4 Redis

当前使用进程内 LRU 缓存，不需要 Redis。需要时：

```powershell
winget install --id Memurai.MemuraiDeveloper -e
# 或 Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 5.5 Docker

```powershell
winget install --id Docker.DockerDesktop -e
wsl --install
```

Docker Desktop 需要 BIOS/UEFI 开启虚拟化。当前机器 WSL2 曾提示虚拟化未启用；如果 Docker 启动失败，先检查：

```powershell
wsl --status
```

`docker-compose.yml` 已将 PostgreSQL 映射到宿主机 **5433**，避免和本机 5432 冲突。

---

## 6. 环境自检

```powershell
uv run python scripts/verify_env.py
```

输出示例：

```text
[工具链]
  [OK]   uv         C:\Users\...\uv.EXE
  [OK]   node       D:\Program Files\nodejs\node.EXE
  [OK]   npm        D:\Program Files\nodejs\npm.CMD
  [OK]   ollama     C:\Users\...\ollama.EXE

[运行配置]
  LLM_PROVIDER   = auto
  EMBED_PROVIDER = hash
  DATABASE_URL   = sqlite:///./db/shopping_bot.sqlite3

[Ollama 模型]
  [OK]   qwen2.5:3b
  [OK]   bge-m3:latest

[数据与向量库]
  [OK]   CSV: .../files/products.csv
  [OK]   关系数据库可用，商品 125 条
  [OK]   向量库文档 375 条
```

---

## 7. 测试

```powershell
# 纯逻辑测试，不需要任何外部服务
uv run pytest tests/unit -q

# 环境/意图/Agent 切换
uv run python main.py intent
uv run python main.py agent-switch

# 前端构建
cd public; npm run build
cd admin;  npm run build
```

本地已验证：`236 passed`，两个前端 `npm run build` 成功。

---

## 8. 常见问题

| 现象 | 解决 |
|---|---|
| `python` 打开 Microsoft Store | 用 `uv run python ...`，不要依赖系统 python 别名 |
| `uv` 找不到 | 重开终端；确认 `C:\Users\<你>\.local\bin` 在 PATH；必要时用官方脚本重装 |
| `uv trampoline failed` | 删除 `.venv` 后 `uv sync --extra dev`；或重装 uv |
| `ollama` 连接失败 | `ollama serve`；确认 11434 端口 |
| 7B 模型报 ROCm/`gfx1100` 错误 | 使用 `qwen2.5:3b`；或让 Ollama 走 CPU |
| `bge-m3` embedding 报 400/连接重置 | 代码已改为原生 `/api/embed`，并默认 `num_gpu=0`；首次构建约 2–3 分钟 |
| 向量库为空 | `uv run python main.py ingest` |
| 商品列表为空/库存全缺 | `uv run python scripts/init_db.py` |
| 前端启动报 esbuild | `npm rebuild esbuild` 或 `npm approve-scripts esbuild` |
| 端口 5432 冲突 | 本机 PostgreSQL 占用；项目默认 SQLite，Docker Compose 用 5433 |
| 中文日志乱码 | Windows Terminal + `$env:PYTHONUTF8=1` |
| 浏览器 WS 连不上 | 前端走 Vite `/ws` 代理；确认后端 8000 已启动 |
| `npm ci` 很慢 | 使用国内镜像：`npm config set registry https://registry.npmmirror.com` |

---

## 9. 一句话总结

> 装好 **uv + Node.js + Ollama**，执行 `.\start.ps1 local`（Windows）或 `./start.sh local`（macOS）即可。  
> PostgreSQL、pgvector、Redis、Neo4j、Docker 都是后续按需升级项，不影响本地完整运行。
