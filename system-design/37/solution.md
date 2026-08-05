# 37. 设计代码部署/CI/CD 系统 (Code Deployment / CI/CD System)

## 题目

设计一个类似 GitHub Actions / Jenkins / GitLab CI 的持续集成和持续部署 (CI/CD) 系统，支持代码构建、测试、打包和部署的全流程自动化。

---

## 需求澄清

### 功能性需求

- 代码变更触发自动构建（Git push / PR / Tag）
- 支持多种语言和构建工具（Java, Go, Python, Node.js, Docker 等）
- 构建步骤可配置（Pipeline as Code: YAML）
- 并行执行多个构建步骤
- 测试报告和覆盖率统计
- 制品管理（构建产物: JAR, Docker Image, NPM Package 等）
- 多环境部署（dev, staging, production）
- 部署策略支持（滚动更新、蓝绿部署、金丝雀发布）
- 审批流程（手动批准后才能部署到生产环境）
- 构建历史查看、日志追踪
- 通知集成（Slack, Email, Webhook）

### 非功能性需求

| 指标 | 要求 |
|------|------|
| 可用性 | 99.9% |
| 构建启动延迟 | < 30s (从push到构建开始) |
| 构建吞吐 | 支持 1000+ 并发构建 |
| 扩展性 | Worker 动态扩缩容 |
| 安全性 | 构建环境隔离, Secrets管理 |
| 可追溯性 | 每次构建全链路可追踪 |

### 容量估算

假设：
- 每日代码提交次数：10000次
- 每次提交触发构建：平均2个pipeline
- 每日构建总数：20000次
- 平均构建时间：5分钟
- 峰值构建 QPS：~10 builds/min 并发
- 构建日志存储：每构建 500KB × 20000 = 10GB/天
- 制品存储：每构建 100MB × 20000 = 2TB/天

---

## 架构设计

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            Trigger Layer                                   │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │Webhook   │  │Manual    │  │Scheduled │  │API       │                │
│  │(Git Push)│  │(UI触发)  │  │(Cron)    │  │(外部集成)│                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│       │              │             │              │                       │
└───────┼──────────────┼─────────────┼──────────────┼───────────────────────┘
        │              │             │              │
        └──────────────┼─────────────┘              │
                       ▼                            │
┌──────────────────────────────────────────────────────────────────────────┐
│                        API Gateway + Auth                                 │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          CI/CD Core Services                              │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │   Pipeline Manager   │  │   Job Scheduler       │                     │
│  │                      │  │                      │                     │
│  │ - 解析 .ci.yml       │  │ - 分配Worker         │                     │
│  │ - 构建DAG依赖图      │  │ - 资源调度            │                     │
│  │ - 管理pipeline状态   │  │ - 优先级队列          │                     │
│  │ - 阶段间数据传递     │  │ - 超时管理            │                     │
│  └──────────┬───────────┘  └──────────┬───────────┘                     │
│             │                         │                                   │
│  ┌──────────▼─────────────────────────▼───────────┐                     │
│  │                 Message Queue (Kafka)           │                     │
│  │           job_events | log_streams              │                     │
│  └──────────────────────┬──────────────────────────┘                    │
│                         │                                                │
│  ┌──────────────────────▼──────────────────────────┐                    │
│  │               Log Aggregator                     │                    │
│  │         收集构建日志 → 持久化 → 实时流             │                    │
│  └─────────────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Execution Layer (Worker Pool)                     │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Worker 1    │  │  Worker 2    │  │  Worker N    │                  │
│  │              │  │              │  │              │                  │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │                  │
│  │ │Container │ │  │ │Container │ │  │ │Container │ │                  │
│  │ │ Builder  │ │  │ │ Builder  │ │  │ │ Builder  │ │                  │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │                  │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │                  │
│  │ │Container │ │  │ │Container │ │  │ │Container │ │                  │
│  │ │ Builder  │ │  │ │ Builder  │ │  │ │ Builder  │ │                  │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  Runner 环境:                                                             │
│  - Docker / Kubernetes Pod (每个Job一个隔离容器)                          │
│  - VM (更高隔离度，适合不可信代码)                                        │
│  - Serverless (无状态，按需创建)                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Storage & Infrastructure                           │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐           │
│  │PostgreSQL│  │  Redis   │  │ S3/Artifact │ │ Container    │           │
│  │构建/部署  │  │ 队列/缓存 │  │ Registry  │ │ Registry     │           │
│  │历史记录   │  │         │  │ (制品存储) │ │ (Docker Hub) │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. Pipeline 配置格式 (Pipeline as Code)

```yaml
# .ci.yml - Pipeline as Code
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 2 * * *"  # 每天凌晨2点

env:
  DOCKER_REGISTRY: registry.mycompany.com
  GO_VERSION: "1.21"

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      matrix:
        go: ["1.20", "1.21"]
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go }}
      
      - name: Cache Dependencies
        uses: actions/cache@v4
        with:
          path: ~/go/pkg/mod
          key: go-${{ matrix.go }}-${{ hashFiles('go.sum') }}
      
      - name: Run Tests
        run: go test -v -race -coverprofile=coverage.out ./...
      
      - name: Upload Coverage
        uses: upload-artifact@v4
        with:
          path: coverage.out
      
      - name: Upload Test Report
        if: always()
        uses: upload-artifact@v4
        with:
          name: test-report
          path: test-results/
  
  build:
    name: Build and Push
    needs: [test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Build Docker Image
        run: |
          docker build -t $DOCKER_REGISTRY/myapp:${{ github.sha }} .
          docker tag $DOCKER_REGISTRY/myapp:${{ github.sha }} \
                     $DOCKER_REGISTRY/myapp:latest
      
      - name: Push to Registry
        run: docker push $DOCKER_REGISTRY/myapp --all-tags
  
  deploy-staging:
    name: Deploy to Staging
    needs: [build]
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy
        run: |
          kubectl set image deployment/myapp \
            myapp=$DOCKER_REGISTRY/myapp:${{ github.sha }} \
            --namespace=staging
      
      - name: Health Check
        run: |
          for i in $(seq 1 30); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
              https://staging.myapp.com/health)
            if [ "$STATUS" = "200" ]; then exit 0; fi
            sleep 5
          done
          exit 1
  
  deploy-production:
    name: Deploy to Production
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    environment:
      name: production
      require_approval: true  # 需要手动审批
    steps:
      - name: Deploy (Canary)
        run: |
          kubectl set image deployment/myapp-canary \
            myapp=$DOCKER_REGISTRY/myapp:${{ github.sha }} \
            --namespace=production
      
      - name: Monitor Canary (10 min)
        run: ./scripts/monitor-canary.sh 600
      
      - name: Full Rollout
        if: success()
        run: |
          kubectl set image deployment/myapp \
            myapp=$DOCKER_REGISTRY/myapp:${{ github.sha }} \
            --namespace=production
```

### 2. DAG 依赖图调度

```
Pipeline DAG 示例:

              ┌──────────────┐
              │   Checkout   │
              └──────┬───────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Lint   │  │Unit Test│  │Build   │  ← 并行执行
    └───┬────┘  └───┬────┘  │(Go)    │
        │           │       └───┬────┘
        │           │           │
        └─────┬─────┘           │
              ▼                 │
        ┌──────────┐            │
        │Integration│            │
        │   Test    │            │
        └─────┬────┘            │
              │                 │
              └────────┬────────┘
                       ▼
                 ┌──────────┐
                 │  Build   │
                 │  Docker  │
                 └────┬─────┘
                      │
              ┌───────┴───────┐
              ▼               ▼
        ┌──────────┐   ┌──────────┐
        │  Deploy   │   │Security  │
        │  Staging  │   │  Scan    │
        └─────┬────┘   └──────────┘
              │
              ▼
        ┌──────────┐
        │  Deploy   │
        │Production │
        └──────────┘

DAG 调度器核心逻辑:
  1. 解析 needs/requires 依赖
  2. 拓扑排序确定执行顺序
  3. 无依赖的Job同时启动
  4. Job完成后检查下游依赖是否满足
  5. 满足即触发下游Job
```

### 3. Worker 调度器

```python
class JobScheduler:
    def __init__(self):
        self.pending_queue = PriorityQueue()  # 优先级队列
        self.running_jobs = {}
        self.worker_pool = WorkerPool()
    
    def schedule_job(self, pipeline_id, job_config):
        """
        调度单个Job到Worker执行
        """
        # 1. 资源需求匹配
        required_resources = job_config.resources  # {cpu: 2, memory: "4Gi"}
        worker = self.worker_pool.allocate(required_resources)
        
        if not worker:
            # 无可用Worker: 入队等待 + 触发扩容
            self.pending_queue.put(job_config, job_config.priority)
            self.trigger_scale_up()
            return
        
        # 2. 创建隔离执行环境
        executor = self.create_executor(worker, job_config)
        
        # 3. 注入Secrets和环境变量
        executor.inject_secrets(job_config.secrets)
        executor.inject_env(job_config.env)
        
        # 4. 运行Job
        execution = executor.run(job_config.steps)
        self.running_jobs[execution.id] = execution
        
        # 5. 监控超时
        self.schedule_timeout(execution.id, job_config.timeout_minutes * 60)
    
    def create_executor(self, worker, job_config):
        """创建隔离执行环境"""
        executor_type = job_config.get('runs-on', 'container')
        
        if executor_type == 'container':
            # Kubernetes Pod (推荐)
            pod_spec = {
                'apiVersion': 'v1',
                'kind': 'Pod',
                'spec': {
                    'containers': [{
                        'name': 'builder',
                        'image': job_config.image,
                        'resources': job_config.resources,
                        'volumeMounts': [
                            {'name': 'workspace', 'mountPath': '/workspace'},
                            {'name': 'docker-sock', 'mountPath': '/var/run/docker.sock'}
                        ]
                    }],
                    'volumes': [
                        {'name': 'workspace', 'emptyDir': {}},
                        {'name': 'docker-sock', 'hostPath': {'path': '/var/run/docker.sock'}}
                    ],
                    'restartPolicy': 'Never'
                }
            }
            return KubernetesExecutor(worker, pod_spec)
        
        elif executor_type == 'vm':
            # 虚拟机 (更高隔离度)
            return VMExecutor(worker, job_config)
        
        elif executor_type == 'self-hosted':
            # 自托管Runner
            return SelfHostedExecutor(worker, job_config)
```

### 4. 构建缓存策略

```
构建缓存层次:

L1: Docker Layer Cache (最快)
  ┌─────────────────────────────────┐
  │ FROM golang:1.21-alpine         │ ← Base layer (复用)
  │ COPY go.mod go.sum ./           │ ← 依赖层 (go.mod不变就复用)
  │ RUN go mod download             │ ← 只有依赖变了才重建
  │ COPY . .                        │ ← 源码层 (常变)
  │ RUN go build -o app             │ ← 构建层
  └─────────────────────────────────┘
  策略: 按变化频率排序Docker层, 不常变的放前面

L2: 依赖缓存 (Dependency Cache)
  - Go: ~/go/pkg/mod
  - Node: node_modules / .npm
  - Java: ~/.m2/repository
  - Python: pip cache
  
  实现: actions/cache → S3/分布式缓存服务
  Key: language-version-hash(dependency_files)
  例: go-1.21-${{ hashFiles('go.sum') }}

L3: 构建产物缓存 (Build Cache)
  - 编译中间文件 (.o, .class)
  - Docker buildx --cache-to/--cache-from
  - 远程缓存: 推送到Registry

L4: 工作空间缓存 (Workspace)
  - 同一Job的多个Step间共享workspace
  - 不同Job间通过Artifact传递
```

### 5. 部署策略

```
部署策略对比:

┌─────────────────────────────────────────────────────────────────────┐
│ 1. 滚动更新 (Rolling Update)                                       │
│   ┌──┬──┬──┬──┬──┐    ┌──┬──┬──┬──┬──┐                           │
│   │v1│v1│v1│v1│v1│ → │v2│v1│v1│v1│v1│ → ... → │v2│v2│v2│v2│v2│  │
│   └──┴──┴──┴──┴──┘    └──┴──┴──┴──┴──┘         └──┴──┴──┴──┴──┘  │
│   逐Pod替换，无停机                                                 │
│   缺点: 短时间内两个版本共存                                        │
│   回滚: 反向滚动更新                                                │
├─────────────────────────────────────────────────────────────────────┤
│ 2. 蓝绿部署 (Blue-Green)                                           │
│                                                                     │
│   当前:  ┌─────────┐    (Blue - active)                            │
│          │ v1 Pods │────用户流量                                   │
│          └─────────┘                                               │
│                                                                     │
│   部署:  ┌─────────┐    (Green - staging)                          │
│          │ v2 Pods │                                               │
│          └─────────┘                                               │
│                                                                     │
│   切换:  用户流量 ──→ Green (DNS/Service切换)                       │
│                                                                     │
│   优点: 瞬间切换，回滚极快                                          │
│   缺点: 需要双倍资源                                                │
├─────────────────────────────────────────────────────────────────────┤
│ 3. 金丝雀发布 (Canary Release)                                     │
│                                                                     │
│   ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐                                │
│   │v2│v1│v1│v1│v1│v1│v1│v1│v1│v1│  ← 10%流量到v2                 │
│   └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘                                │
│   监控v2: 错误率, 延迟, 无异常                                      │
│                                                                     │
│   → 逐步增加v2流量: 10% → 25% → 50% → 100%                        │
│   任意阶段异常 → 立即回滚到v1                                       │
│                                                                     │
│   优点: 小范围验证，风险可控                                        │
│   缺点: 部署周期长，需要精细流量控制                                 │
└─────────────────────────────────────────────────────────────────────┘

部署实现 (Kubernetes):
```yaml
# 金丝雀部署示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-canary
spec:
  replicas: 1  # 1/10 = 10% 流量
  selector:
    matchLabels:
      app: myapp
      version: canary
  template:
    metadata:
      labels:
        app: myapp
        version: canary
    spec:
      containers:
      - name: app
        image: registry.mycompany.com/myapp:v2.0.0

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-stable
spec:
  replicas: 9  # 9/10 = 90% 流量
  selector:
    matchLabels:
      app: myapp
      version: stable
  template:
    metadata:
      labels:
        app: myapp
        version: stable
    spec:
      containers:
      - name: app
        image: registry.mycompany.com/myapp:v1.9.0
```
```

### 6. Secrets 管理

```
Secrets 安全架构:

┌─────────────────────────────────────────────────────────────────────┐
│                      Secrets 生命周期                                │
│                                                                     │
│  存储:                                                              │
│    - Vault / AWS Secrets Manager / GCP Secret Manager              │
│    - 加密存储在数据库中 (AES-256-GCM)                                │
│    - 加密密钥由 KMS 管理                                            │
│                                                                     │
│  注入:                                                              │
│    Client Request: "Deploy to production"                          │
│         │                                                          │
│    ┌────▼─────────────────────────────────────────┐               │
│    │ 1. 验证: 用户是否有deploy:production权限       │               │
│    │ 2. 解密: 从Secrets Store获取并解密Credentials │               │
│    │ 3. 注入: 作为环境变量/TmpFS挂载到Builder容器    │               │
│    │ 4. 用完即毁: Job完成后Secrets从内存清除         │               │
│    │ 5. 审计: 记录谁在什么时候访问了什么Secret       │               │
│    └──────────────────────────────────────────────┘               │
│                                                                     │
│  日志脱敏:                                                          │
│    - 自动扫描构建日志, 匹配并遮蔽 Secrets                           │
│    - 正则模式: *** (替代明文)                                       │
│    - Jenkins 做法: maskPasswords() filter                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 7. 构建环境矩阵 (Matrix Build)

```
Matrix Build: 同一Job在不同环境下并行执行

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node: [16, 18, 20]
        exclude:
          - os: macos-latest
            node: 16
        include:
          - os: ubuntu-latest
            node: 20
            experimental: true

# 生成 3×3-1+1 = 9 个并行Job:
# 1. ubuntu + node16
# 2. ubuntu + node18
# 3. ubuntu + node20 (experimental)
# 4. macos + node18
# 5. macos + node20
# 6. windows + node16
# 7. windows + node18
# 8. windows + node20
```

### 8. 制品管理 (Artifact Management)

```
制品生命周期:

┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  构建产物 → Upload → Repository → Version → Promote → Deploy       │
│                                                                     │
│  制品仓库类型:                                                       │
│  ┌─────────────────┬────────────────────────────────────────────┐  │
│  │ 类型             │ 仓库                                       │  │
│  ├─────────────────┼────────────────────────────────────────────┤  │
│  │ Docker Image    │ Docker Hub / ECR / GCR / Harbor            │  │
│  │ Java JAR/WAR    │ Nexus / Artifactory / Maven Central        │  │
│  │ NPM Package     │ npmjs.org / Verdaccio                      │  │
│  │ Helm Chart      │ ChartMuseum / OCI Registry                 │  │
│  │ Generic Binary  │ S3 / GCS / Nexus Raw                       │  │
│  └─────────────────┴────────────────────────────────────────────┘  │
│                                                                     │
│  制品版本策略:                                                       │
│    - SemVer: v1.2.3                                                 │
│    - Git SHA: a1b2c3d (不可变, 可追溯)                              │
│    - 组合: v1.2.3-a1b2c3d                                          │
│                                                                     │
│  Promote 流程:                                                      │
│    Dev → QA → Staging → Production                                 │
│    每次Promote: 同一个Artifact, 只改变Label/Tag/元数据               │
│    (不可变基础设施原则)                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 数据模型

```sql
-- Pipeline 运行记录
CREATE TABLE pipeline_runs (
    id              UUID PRIMARY KEY,
    pipeline_name   VARCHAR(255) NOT NULL,
    trigger_type    VARCHAR(20) NOT NULL,   -- push, pr, manual, schedule
    trigger_ref     VARCHAR(255),           -- branch/tag name
    commit_sha      VARCHAR(40),
    status          VARCHAR(20) NOT NULL,   -- pending/running/success/failed/cancelled
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    duration_sec    INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pipeline_status ON pipeline_runs(status, created_at);

-- Job 运行记录
CREATE TABLE job_runs (
    id              UUID PRIMARY KEY,
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    job_name        VARCHAR(255) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    worker_id       VARCHAR(100),
    attempt         INTEGER DEFAULT 1,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    result          JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_run_pipeline ON job_runs(pipeline_run_id);

-- Step 运行记录
CREATE TABLE step_runs (
    id              UUID PRIMARY KEY,
    job_run_id      UUID NOT NULL REFERENCES job_runs(id),
    step_name       VARCHAR(255),
    step_index      INTEGER,
    status          VARCHAR(20),
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    duration_ms     INTEGER,
    exit_code       INTEGER,
    log_key         TEXT,               -- S3 key for logs
    output          JSONB               -- step outputs
);

-- 制品记录
CREATE TABLE artifacts (
    id              UUID PRIMARY KEY,
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    name            VARCHAR(255) NOT NULL,
    artifact_type   VARCHAR(50),        -- docker, jar, npm, generic
    storage_url     TEXT NOT NULL,      -- S3 URL or Registry URL
    version         VARCHAR(255),
    size_bytes      BIGINT,
    checksum_sha256 VARCHAR(64),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 部署记录
CREATE TABLE deployments (
    id              UUID PRIMARY KEY,
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    environment     VARCHAR(50) NOT NULL,  -- dev, staging, production
    strategy        VARCHAR(50),           -- rolling, blue-green, canary
    status          VARCHAR(20),
    approved_by     UUID,
    approved_at     TIMESTAMP,
    rollback_from   UUID,                  -- 回滚时指向之前的部署
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    metadata        JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 扩展性与高可用

### 1. Worker 动态扩缩容

```
Worker Pool 扩缩容策略:

┌─────────────────────────────────────────────────────────────────────┐
│                     Auto-Scaling Strategy                            │
│                                                                     │
│  扩缩容指标:                                                         │
│  ┌────────────────┬────────────────────────────────────────────┐   │
│  │ 指标             │ 阈值                                        │   │
│  ├────────────────┼────────────────────────────────────────────┤   │
│  │ Queue Depth     │ > 20 → Scale Up                           │   │
│  │ Idle Workers    │ > 5 for 10min → Scale Down                │   │
│  │ Avg Wait Time   │ > 60s → Scale Up                          │   │
│  │ Max Workers     │ 100 (硬上限, 防止雪崩)                      │   │
│  └────────────────┴────────────────────────────────────────────┘   │
│                                                                     │
│  扩容方案:                                                          │
│    1. Spot/Preemptible Instances: 低成本, 构建可用Spot              │
│    2. 预热池: 保持5～10个空闲Worker                                 │
│    3. 混合: 固定On-Demand + 弹性Spot                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. 故障处理

| 故障 | 处理 |
|------|------|
| Worker崩溃 | Job状态标记为failing, 自动重试(attempt+1) |
| 构建超时 | 60min硬超时(K8s activeDeadlineSeconds), kill Pod |
| 制品上传失败 | 重试3次, 指数退避, 最终标记失败 |
| Secrets获取失败 | Job不启动, 立即失败(安全优先) |
| 数据库故障 | 主从切换, 构建运行时缓存数据不丢失 |

### 3. 监控与审计

```
┌─────────────────────────────────────────────────────────────────────┐
│ 关键监控指标:                                                        │
│                                                                     │
│ 业务指标:                                                           │
│  - 构建成功率 (target > 95%)                                        │
│  - 平均构建时间 (趋势监控)                                           │
│  - 构建排队时间 P99 (< 60s)                                         │
│  - 部署频率 (DORA metric)                                           │
│                                                                     │
│ 系统指标:                                                           │
│  - Worker CPU/Mem/Disk 利用率                                       │
│  - Queue Depth                                                      │
│  - 制品存储使用量                                                   │
│                                                                     │
│ 安全审计:                                                           │
│  - Who triggered what deployment                                  │
│  - Who approved production release                                │
│  - Secrets access log                                             │
│  - 所有操作都有不可变审计日志                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| Pipeline | YAML配置 + DAG调度 + Matrix并行 |
| 执行环境 | 容器化(每个Job独立Pod) |
| 调度 | 优先级队列 + Worker Pool + 自动扩缩容 |
| 缓存 | Docker Layer → 依赖Cache → Build Cache |
| 部署 | 滚动/蓝绿/金丝雀 + 审批流程 |
| 安全 | Secrets加密 + 环境隔离 + 审计日志 |
| 制品 | 不可变版本 + Promote机制 + 多仓库支持 |

**关键设计权衡：**
1. **容器 vs VM:** 容器启动快、资源高效，适合可信代码；VM隔离度高，适合不可信PR
2. **Push vs Pull 日志:** Push(实时流)可实时查看，Pull(轮询)实现简单。CI/CD场景选择Push + WebSocket实时推送
3. **集中式 vs 分布式Worker:** 小团队用集中式(如GitHub-hosted runners)；大团队用自托管K8s Worker Pool
4. **制品策略:** 不可变(!important) + 跨环境Promote(同一Artifact, 环境改变只改配置)
