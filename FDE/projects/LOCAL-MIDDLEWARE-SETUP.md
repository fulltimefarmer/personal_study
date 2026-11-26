# FDE 六项目 · 本地中间件安装指南（Windows 11 / macOS，不用 Docker）

> 依据：本目录 6 个项目的 README + 本机实测（2026-11-26）
> 目标：本地学习环境，能省则省；优先原生安装，单机内存占用控制在 1 GB 量级（不含本地大模型）。

---

## 0. 结论先行

1. 六个项目统一是 **Python/FastAPI 后端 + Next.js 前端**，中间件底座高度重合：**PostgreSQL + Redis**。
2. 真正"独有"的只有四个：
   - **03** 需要 **Kafka**（aiokafka）
   - **01** 需要 **Ollama**（本地 LLM + bge-m3 向量），**Neo4j** 仅知识图谱可选
   - **02 / 06** 需要 **pgvector**（PG 向量扩展）
   - **04** 需要 **OCR**（Tesseract 或 PaddleOCR）
   - **05** 名义上要 K8s / Keycloak，本地可以降级为 manifest 校验，不必真起集群
3. 本机现状（已核实）：

| 组件 | 状态 | 说明 |
|---|---|---|
| PostgreSQL 18.6 | ✅ 已装并运行 | `D:\Program Files\PostgreSQL\18`，服务 `postgresql-x64-18`，监听 0.0.0.0:5432 |
| pgvector | ❌ 缺 | PG 扩展目录里没有 `vector.control` |
| Redis | ❌ 缺 | 无 6379 服务 |
| Kafka | ❌ 缺 | — |
| Ollama | ❌ 缺 | — |
| Java | ✅ JDK 17 | `C:\Program Files\Java\jdk-17`，够跑 Kafka 4.x / Keycloak / Neo4j |
| Docker / WSL2 | ❌ 不可用 | `VirtualMachinePlatform` 启用失败（error 50），Docker Desktop 起不来 |
| uv / Git | ❌ 缺 | 项目 01 需要 uv；`winget` 可用 |

4. **最小启动集**：`PostgreSQL(+pgvector) + Redis 兼容服务`。Kafka、Ollama、Neo4j 按项目需要再装，不要一次性全上。

---

## 1. 六个项目依赖汇总

| 项目 | 代码状态 | 必装中间件 | 可选 / 可替代 | 本地最省方案 |
|---|---|---|---|---|
| 01 AI Shopping Assistant | 已有可运行代码（含 `.venv`、`uv.lock`、`docker-compose.yml`） | Ollama（本地 LLM）、ChromaDB | PostgreSQL、Neo4j、Tavily API | ChromaDB 是 pip 包（嵌入式，0 服务）；PG/Neo4j 全可不装 |
| 02 Field Ops Copilot | 骨架（仅 README + `src/README.md`） | PostgreSQL + pgvector、Redis | SQLite、MQTT/Kafka、对象存储 | PG+pgvector、Redis：Memurai/Garnet |
| 03 Order Exception Hub | 骨架 | PostgreSQL、Redis、**Kafka** | Celery/Arq | Kafka 用 KRaft 单机（唯一重负担） |
| 04 Document Intake Copilot | 骨架 | PostgreSQL、Redis、OCR | 对象存储 | Tesseract（轻）；MinIO 可选 |
| 05 Regulated Private Deployment | 骨架 | PostgreSQL、Redis | Keycloak、K8s、Harbor | 本地只做 `helm template` + `kubectl --dry-run`，不起集群 |
| 06 Incident Copilot | 骨架 | PostgreSQL + pgvector、Redis | Prometheus/Loki/Tempo | 可观测数据先 mock，后期只加 Prometheus |

> 提醒：02–06 目前只有 README 骨架，先把 01 跑通（它连零中间件模式都支持：SQLite + JSON 向量库 + Mock LLM），后面再按项目逐个补中间件，避免一开始就把 10 个服务全开。

---

## 2. 每类中间件的选型（省资源优先）

| 能力 | 推荐（Windows 11） | 推荐（macOS） | 为什么 |
|---|---|---|---|
| 关系库 | 复用已装的 **PostgreSQL 18 原生服务** | `brew install postgresql@18` 或 Postgres.app | 原生服务 80–150 MB；Docker 方案要先背 2–3 GB 底座 |
| 向量扩展 | **pgvector Windows 预编译包**（社区构建，免 MSVC 编译） | Postgres.app 自带；或 `brew install pgvector` | 免费，不用装 VS C++ Build Tools |
| 缓存/限流 | **Memurai Developer**（Redis 兼容，Windows 服务）或 **Garnet**（微软，MIT，最轻） | `brew install redis` | 二者都是原生进程，10–60 MB 级；Garnet 无许可限制 |
| 消息队列 | **Kafka 4.x KRaft 单机**（复用 JDK 17，堆压到 512 MB） | 官方 tar 包 KRaft，或 `brew install kafka` | Kafka 没有更轻的原生替代；Redpanda 只支持 Linux/WSL |
| 本地 LLM | **Ollama 原生 Windows 版** | `brew install ollama` 或官方 App | 原生直连 GPU；容器版在 Windows 上拿不到 GPU |
| 图数据库 | **Neo4j Desktop**（自带 JRE），或干脆不装 | `brew install neo4j` | 01 默认用 ChromaDB，图谱属加分项 |
| OCR | **Tesseract**（`UB-Mannheim.TesseractOCR`） | `brew install tesseract tesseract-lang` | 04 先跑通流程；PaddleOCR 体积大、模型下载多 |
| 对象存储 | 本地目录适配器 | 同 | 04/02 的对象存储接口可先用本地磁盘实现 |
| 可观测 | 先 mock；要真数据只加 **Prometheus 单 exe** | 同 | Loki/Tempo 对学习项目收益低 |

---

## 3. 资源对比：Docker Desktop vs 原生（粗略常驻内存）

| 组件 | Docker 方案 | 原生方案 | 备注 |
|---|---|---|---|
| Docker Desktop 底座本身 | 2–3 GB | 0 | WSL2 虚拟机常驻，这是最大头 |
| PostgreSQL | 100–200 MB（容器内） | 80–150 MB（服务） | 你已经有原生 PG，直接用 |
| Redis | 10–30 MB | Memurai ≈ 40 MB；Garnet ≈ 60–100 MB | 都远低于底座 |
| Kafka（KRaft 单机） | 1–1.5 GB | 500 MB–1 GB（`-Xmx512M`） | 仍然是最重的一个，只在做 03 时装 |
| Neo4j | 1–2 GB | Desktop ≈ 0.8–1.5 GB | 可选，先跳过 |
| Ollama | Windows 下 GPU 不可用/性能差 | 空闲 ≈ 50 MB，加载 3B 模型 ≈ 3–4 GB | 用完 `ollama stop` 释放 |
| pgvector | 镜像 ≈ 200 MB | 0（只是几个扩展文件） | — |
| **合计（开全部）** | **5–7 GB + 20 GB 磁盘** | **0.8–1.5 GB（不含模型）** | 结论：能原生就原生 |

---

## 4. Windows 11 安装步骤

### 4.1 前置工具（10 分钟）

```powershell
winget install --id astral-sh.uv -e
winget install --id Git.Git -e
# 装完重开 PowerShell
uv --version
```

### 4.2 PostgreSQL（已有，跳过安装，只建开发库）

```powershell
$psql = "D:\Program Files\PostgreSQL\18\bin\psql.exe"
$env:PGPASSWORD="<postgres 密码>"

& $psql -h 127.0.0.1 -U postgres -d postgres -c "CREATE USER fde WITH PASSWORD 'fde';"
& $psql -h 127.0.0.1 -U postgres -d postgres -c "CREATE DATABASE fde_dev OWNER fde;"
& $psql -h 127.0.0.1 -U postgres -d postgres -c "SELECT version();"
```

把 bin 目录加进当前会话 PATH（每次开新窗口都要，或写进 `$PROFILE`）：

```powershell
$env:Path += ";D:\Program Files\PostgreSQL\18\bin"
```

> 忘记 postgres 密码：见 `01-ai-shopping-assistant/ENVIRONMENT-SETUP.md` 第 5.3 节（改 `pg_hba.conf` 为 trust → 改密码 → 改回 scram-sha-256）。

### 4.3 pgvector（唯一需要"手动拷贝"的一步）

pgvector 官方没有 Windows 安装包，但社区有按 PG 大版本编好的预编译 zip，**选 PostgreSQL 18 那一版**即可，不用装 Visual Studio。

1. 打开 https://github.com/andreiramani/pgvector_pgsql_windows/releases
2. 找标题为 `pgvector v0.8.x for PostgreSQL 18, Microsoft Windows` 的 release，下载其 asset：`vector.v0.8.x-pg18.zip`
3. 解压到 `C:\temp\pgvector`，先看包里的 `readme.txt`
4. 拷贝文件（按包内 readme 为准，通用是这三类）：

```powershell
$pg = "D:\Program Files\PostgreSQL\18"
Copy-Item C:\temp\pgvector\vector.dll            "$pg\lib\" -Force
Copy-Item C:\temp\pgvector\vector.control        "$pg\share\extension\" -Force
Copy-Item C:\temp\pgvector\vector--*.sql         "$pg\share\extension\" -Force

Restart-Service postgresql-x64-18
```

5. 在目标库里启用扩展并验证：

```powershell
$psql = "D:\Program Files\PostgreSQL\18\bin\psql.exe"
$env:PGPASSWORD="fde"
& $psql -h 127.0.0.1 -U fde -d fde_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
& $psql -h 127.0.0.1 -U fde -d fde_dev -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
```

看到 `vector | 0.8.x` 就成功。**不想折腾时**：02/06 的骨架阶段可以先用 SQLite + 内存向量库，pgvector 留到实现检索层再开。

### 4.4 Redis 兼容服务（二选一）

**方案 A：Memurai Developer（推荐，装完就是 Windows 服务，命令兼容 Redis 7）**

```powershell
winget install --id Memurai.MemuraiDeveloper -e
Get-Service Memurai
Test-NetConnection 127.0.0.1 -Port 6379
```

**方案 B：Garnet（微软开源，MIT，无许可限制，最轻）**

```powershell
winget install --id Microsoft.Garnet.DN9 -e
# 新开窗口
GarnetServer --port 6379 --memory 256m
```

> 差异：Memurai 免费版仅限开发/测试（正好符合学习用途），兼容性最好；Garnet 完全开源但 Lua 脚本、部分数据结构命令覆盖有限。项目里只做缓存/会话/限流 → 两者都能用。

连接串：`redis://127.0.0.1:6379/0`

### 4.5 Kafka（只在做 03 时装）

Kafka 4.x 已经彻底去掉 ZooKeeper，单进程 combined 模式即可；broker 要求 Java 17（你已有）。Windows 版脚本在 `bin\windows` 下。

1. 下载：https://kafka.apache.org/downloads → 取 4.x 的 `kafka_2.13-4.x.x.tgz`，解压到 **短路径** `C:\kafka`（Windows 长路径容易炸）
2. 改 `C:\kafka\config\server.properties`，确认/修改这几项：

```properties
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@localhost:9093
listeners=PLAINTEXT://:9092,CONTROLLER://:9093
advertised.listeners=PLAINTEXT://localhost:9092
log.dirs=C:/kafka/data/kraft-combined-logs
```

> 默认 `log.dirs` 常是 `/tmp/...`，在 Windows 上必须改成上面的形式。

3. 格式化并启动（**每次格式化只能用一次集群 ID，重复格式化会丢消息**）：

```powershell
cd C:\kafka
.\bin\windows\kafka-storage.bat random-uuid
.\bin\windows\kafka-storage.bat format -t <上一步的UUID> -c .\config\server.properties

$env:KAFKA_HEAP_OPTS="-Xms256M -Xmx512M"
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

4. Windows 11 特有的坑：启动脚本会调用 `wmic` 算内存，而 Win11 已把它变成可选功能，报 `'wmic' 不是内部或外部命令` 时补装（管理员）：

```powershell
Add-WindowsCapability -Online -Name "WMIC~~~~"
```

5. 验证（另开一个窗口）：

```powershell
.\bin\windows\kafka-topics.bat --create --topic fde-orders --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092
```

连接：`localhost:9092`

### 4.6 Ollama（只在做 01 时装）

```powershell
winget install --id Ollama.Ollama -e
ollama --version

ollama pull qwen2.5:3b      # 约 2 GB，路由/简单问答
ollama pull bge-m3          # 约 1.2 GB，向量模型
ollama pull qwen2.5vl:3b    # 约 3 GB，图片理解，可选
```

省内存：用完释放显存

```powershell
ollama stop qwen2.5:3b
```

或设保活时间（系统环境变量）：`OLLAMA_KEEP_ALIVE=5m`。连接：`http://localhost:11434`

### 4.7 其他（按项目再装）

| 项目 | 组件 | 命令 |
|---|---|---|
| 01 | Neo4j（可选） | `winget install --id Neo4j.Neo4jDesktop -e`，建库后 `bolt://localhost:7687` |
| 04 | OCR | `winget install --id UB-Mannheim.TesseractOCR -e`，验证 `tesseract --version` |
| 04 | 对象存储（可选） | 下载 `minio.exe`（dl.min.io）→ `.\minio.exe server D:\data\minio --console-address ":9001"` |
| 06 | Prometheus（可选） | 下载单 exe（prometheus.io），`prometheus.exe --config.file=prometheus.yml` |
| 05 | K8s 校验 | 只装 `kubectl` + `helm`，用 `helm template` / `kubectl apply --dry-run=client` 验证清单，**不起真集群** |
| 05 | Keycloak（可选） | 下载 keycloak zip（需 Java 17），`bin\kc.bat start-dev`，端口 8080 |

---

## 5. macOS 安装步骤（同一套选型）

```bash
# 基础工具
brew install uv git node

# PostgreSQL 18
brew install postgresql@18
brew services start postgresql@18
export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"
createdb fde_dev

# pgvector：两条路
# ① 最省事：装 Postgres.app（自带 pgvector）
# ② 用 Homebrew 版：brew install pgvector（针对 brew 的 postgresql 版本编译，与 @18 不一致时用 PG_CONFIG 指向 @18 手动 make）

# Redis
brew install redis
brew services start redis

# Kafka（做 03 才需要）
brew install kafka
# 配置文件在 /opt/homebrew/etc/kafka/server.properties，KRaft 命令同名（.sh）：
# kafka-storage random-uuid
# kafka-storage format -t <uuid> -c /opt/homebrew/etc/kafka/server.properties

# Ollama
brew install ollama
brew services start ollama

# 可选
brew install neo4j              # 01 图谱，需要 Java 21
brew install tesseract tesseract-lang   # 04 OCR
```

验证统一用：

```bash
pg_isready -h 127.0.0.1 -p 5432
redis-cli ping            # 返回 PONG
kafka-topics --list --bootstrap-server localhost:9092
curl http://localhost:11434/api/tags
```

> Mac 上磁盘/内存更紧张（M4 16G）时，把 Kafka 和 Ollama 排到最后，或用 `ollama stop` 即用即停。

---

## 6. 端口与环境变量对照

| 服务 | 端口 | `.env` 典型值 |
|---|---|---|
| PostgreSQL | 5432 | `DATABASE_URL=postgresql+asyncpg://fde:fde@127.0.0.1:5432/fde_dev` |
| Redis | 6379 | `REDIS_URL=redis://127.0.0.1:6379/0` |
| Kafka | 9092（controller 9093） | `KAFKA_BOOTSTRAP_SERVERS=localhost:9092` |
| Ollama | 11434 | `OLLAMA_BASE_URL=http://localhost:11434` |
| Neo4j | 7687 / 7474 | `NEO4J_URI=bolt://localhost:7687` |
| MinIO | 9000 / 9001 | `S3_ENDPOINT=http://localhost:9000` |
| 后端 | 8000 | — |
| 前端 | 3000 / 3001 | — |
| Grafana | **3300**（默认 3000 会和前端撞车） | — |

---

## 7. 施工顺序建议（别一次全装）

1. **第 0 天**：`uv` + Git，把 01 用零中间件模式跑通（SQLite + JSON 向量 + Mock LLM），确认 `http://127.0.0.1:8000/docs` 能开。
2. **第 2 天**：PG 建 `fde_dev` 库 → 切 `DATABASE_URL`，跑通持久化。这一天顺手把 **pgvector** 装上（约 20 分钟），后面 02/06 直接可用。
3. **第 3 天**：Redis（Memurai 一条命令），给 02–05 的会话/限流做准备。
4. **做 03 那周**：再装 Kafka（唯一的重负担），并接受它占 0.5–1 GB。
5. **做 01 那周**：装 Ollama + 拉模型；Neo4j 只在要讲"知识图谱"故事时开。
6. **05 / 06**：K8s 与可观测优先用"清单校验 + mock"，本地不追真集群。

---

## 8. 常见坑

| 现象 | 处理 |
|---|---|
| `wsl --install` 报 error 50 | 先关"内存完整性"、确认 BIOS 虚拟化；本机已确认不可用 → 全程走原生安装 |
| pgvector 拷贝后 `CREATE EXTENSION` 报 could not open extension control file | 文件放错目录：`.control`/`.sql` 进 `share\extension`，`vector.dll` 进 `lib` |
| pgvector 报版本不兼容 | 必须选 `pg18` 的 asset，别用 pg17 的 |
| psql 卡住不动 | 在等密码输入，改用 `$env:PGPASSWORD` 再调用 |
| Kafka 报 `wmic 不是命令` | `Add-WindowsCapability -Online -Name "WMIC~~~~"` |
| Kafka 启动后立刻退出 | 看 `log.dirs` 是否还是 `/tmp/...`；改成 `C:/kafka/data/kraft-combined-logs` |
| Kafka 重启后消息丢了 | 重复执行了 `kafka-storage format`，重新格式化会清空日志目录 |
| Ollama 拉模型很慢 | 国内网络；可先只拉 `qwen2.5:3b` 验证链路 |
| 3000 端口冲突 | 前端与 Grafana 都用 3000，Grafana 改 3300 |

---

## 9. 参考

- Kafka 4.0 官方发布说明（KRaft 默认、broker 需 Java 17）：https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/
- KRaft 单机 combined 模式文档：https://kafka.apache.org/41/operations/kraft/
- pgvector Windows 预编译（社区，含 PG18 分版本 zip）：https://github.com/andreiramani/pgvector_pgsql_windows
- pgvector 官方安装说明（Windows 编译方式）：https://github.com/pgvector/pgvector
- Kafka Windows 下 WMIC 缺失的处理：https://blog.csdn.net/General_zy/article/details/147168532
