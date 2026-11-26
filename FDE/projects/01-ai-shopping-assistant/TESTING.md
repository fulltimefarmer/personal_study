# 测试用例运行指南

## 环境准备

```bash
# 安装运行 + 测试依赖（推荐）
uv sync --extra dev

# 环境自检
uv run python scripts/verify_env.py
```

> 默认使用 SQLite + Hash Embedding，单元测试不依赖 PostgreSQL / Ollama / Neo4j。

## 测试分类

| 分类 | 目录 | 特点 | 运行速度 |
|------|------|------|----------|
| **单元测试** | `tests/unit/` | 纯逻辑，无外部依赖（DB/LLM/网络） | 秒级 |
| **集成测试** | `tests/integration/` | 需要外部服务，验证完整调用链路 | 分钟级 |

---

## 一、Pytest 测试

### 1.1 运行全部单元测试

```bash
uv run pytest tests/unit/ -v
```

### 1.2 运行全部集成测试

```bash
uv run pytest tests/integration/ -v
```

### 1.3 运行全部测试

```bash
uv run pytest tests/ -v
```

### 1.4 按测试标记 (Marker) 筛选

```bash
# 只跑纯逻辑单元测试
uv run pytest -m unit

# 只跑集成测试
uv run pytest -m integration

# 只跑需要 Neo4j 的测试
uv run pytest -m neo4j

# 只跑需要 LLM API 的测试
uv run pytest -m llm

# 只跑需要 ChromaDB 的测试
uv run pytest -m vector

# 只跑需要 PostgreSQL 的测试
uv run pytest -m db

# 多标记组合：跑集成但不跑 LLM
uv run pytest -m "integration and not llm"
```

### 1.5 按文件名筛选

```bash
# 只跑某个模块
uv run pytest tests/unit/test_query_processor.py -v

# 只跑某个类
uv run pytest tests/unit/test_query_processor.py::TestIntentClassification -v

# 只跑某个方法
uv run pytest tests/unit/test_query_processor.py::TestIntentClassification::test_product_inquiry -v
```

### 1.6 按关键词筛选

```bash
# 只跑名称包含 "guardrails" 的测试
uv run pytest -k guardrails

# 只跑名称包含 "cache" 或 "memory" 的测试
uv run pytest -k "cache or memory"
```

### 1.7 常用选项

```bash
# 显示详细输出 + 缩短失败回溯
uv run pytest tests/ -v --tb=short

# 遇到第一个失败立即停止
uv run pytest tests/unit/ -x

# 失败时进入 pdb 调试
uv run pytest tests/unit/ --pdb

# 显示最慢的 10 个测试
uv run pytest tests/ --durations=10

# 安静模式（只显示结果摘要）
uv run pytest tests/unit/ -q
```

---

## 二、现有 CLI / 脚本测试

以下测试保留在 `scripts/` 目录下，独立运行：

### 2.1 Agent 切换逻辑测试（纯规则，不调 LLM）

```bash
uv run python scripts/test_agent_switching.py
```
覆盖：意图分类、本地 vs 远程路由、年龄/价格检测、同义词扩展、关键词提取、工具场景决策。

### 2.2 知识图谱搜索测试

```bash
# 先构建图数据（需要 Neo4j）
uv run python scripts/build_knowledge_graph.py

# 运行测试
uv run python scripts/test_graph_search.py
```

### 2.3 数据验证

```bash
uv run python scripts/test_data.py
```

### 2.4 Neo4j 连接测试

```bash
uv run python scripts/test_neo4j.py
```

### 2.5 召回评测

```bash
# 需要 ChromaDB 有数据
uv run python main.py eval
# 或直接运行脚本
uv run python scripts/eval_recall.py
```

### 2.6 生成质量评测（LLM-as-Judge）

```bash
# 需要 DeepSeek API
uv run python main.py quality
# 或直接运行脚本
uv run python scripts/eval_quality.py
```

### 2.7 环境验证

```bash
uv run python scripts/verify_env.py
```

---

## 三、各测试模块覆盖范围

### 单元测试 (`tests/unit/`)

| 文件 | 被测模块 | 测试数 | 覆盖内容 |
|------|----------|--------|----------|
| `test_query_processor.py` | `app/rag/query_processor.py` | ~110 | 7种意图分类、年龄/价格检测、同义词扩展、关键词提取、本地vs远程路由决策、意图响应分发 |
| `test_guardrails.py` | `app/core/guardrails.py` | 21 | 四步幻觉防控（空结果兜底、溯源校验、来源标注、相关性检查） |
| `test_memory.py` | `app/core/memory.py` | 12 | 对话记忆增删、滑动窗口、压缩触发、会话隔离、LLM摘要失败降级 |
| `test_cache.py` | `app/core/cache.py` | 12 | LRU淘汰、TTL过期、查询缓存归一化、线程安全 |
| `test_models.py` | `app/data/models.py` | 12 | Product构造/格式化、ProductFilter转Chroma过滤语法 |
| `test_resilience.py` | `app/core/resilience.py` | 12 | 熔断器状态机(CLOSED→OPEN→HALF_OPEN)、LLM韧性重试/降级 |
| `test_agent_tools.py` | `app/agent/tools.py` | 14 | 价格计算、商品列表格式化、图谱结果格式化、库存过滤 |
| `test_chroma_store_utils.py` | `app/vector_store/chroma_store.py` | 10 | L2距离转相似度、语义+年龄+价格三因子加权评分 |
| `test_data_loader.py` | `app/data/loader.py` | 8 | CSV解析、数据清洗、embed文档生成、多粒度文档 |

### 集成测试 (`tests/integration/`)

| 文件 | 覆盖链路 | 测试数 | 依赖服务 |
|------|----------|--------|----------|
| `test_graph_search.py` | graph_search → Neo4jStore → Neo4j | 18 | Neo4j |
| `test_vector_store.py` | ChromaStore 检索/过滤/CRUD | 13 | ChromaDB |
| `test_rag_pipeline.py` | 意图路由 → RAGChain → LLM生成 | 10 | ChromaDB + LLM |
| `test_agent_pipeline.py` | 完整 ReAct 循环 + 12个工具 | 20 | ChromaDB + LLM |
| `test_memory_integration.py` | 多轮对话记忆持久化 | 7 | 无（使用 Mock LLM） |
| `test_api.py` | FastAPI 端点 | 4 | 无 |
| `test_eval.py` | 召回评测 | 2 | ChromaDB |
