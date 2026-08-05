# 33. 设计任务调度系统 / Cron 服务 (Job Scheduler / Cron Service)

## 题目

设计一个分布式任务调度系统，支持定时任务（Cron 表达式）、延迟任务、工作流任务编排，具备高可用和精确执行保障。类似 Quartz、Airflow、Google Cloud Scheduler。

---

## 需求澄清

### 功能性需求 (Functional Requirements)

- 支持 Cron 表达式定时调度（秒级精度）
- 支持一次性延迟任务（delay task）
- 支持任务依赖编排（DAG 工作流）
- 任务执行历史记录和状态查询
- 任务失败重试（可配置重试次数和间隔）
- 任务超时控制和中止
- 任务执行日志查看
- 支持多种任务类型（HTTP 回调、Shell 脚本、消息推送）
- 任务优先级管理
- 任务并发控制（避免同一任务重复执行）

### 非功能性需求 (Non-functional Requirements)

| 指标 | 要求 |
|------|------|
| 可用性 | 99.99%（任务不丢失、不重复） |
| 精确性 | 定时触发偏差 < 1秒 |
| 延迟 | 延迟任务触发偏差 < 100ms |
| 扩展性 | 支持百万级任务注册 |
| 吞吐 | 支持 10,000+ 任务/秒的执行 |
| 持久性 | 任务状态持久化，重启不丢失 |

### 容量估算 (Capacity Estimation)

假设：
- 总注册任务：100万
- 活跃调度任务（每小时有触发）：10万
- 高峰触发 QPS：1000 tasks/s
- 平均任务执行时间：500ms
- 任务执行日志保留：30天
- 每任务日志 size：约 2KB

**存储估算：**
- 任务定义存储：100万 × 2KB ≈ 2GB
- 执行历史存储：1000/s × 86400 × 30 × 2KB ≈ 5TB
- 总存储需求：约 6TB

---

## API 设计

### 任务管理 API

```
# 创建定时任务
POST /api/v1/jobs
{
  "name": "daily-report",
  "type": "http",                    # http | shell | kafka | grpc
  "schedule": "0 0 8 * * ?",        # Cron表达式: 每天8点
  "timezone": "Asia/Shanghai",
  "config": {
    "url": "https://report.internal/api/generate",
    "method": "POST",
    "headers": { "Authorization": "Bearer xxx" },
    "body": { "type": "daily" },
    "timeout_ms": 300000,            # 5分钟超时
    "retry": {
      "max_attempts": 3,
      "backoff": "exponential",      # fixed | exponential | linear
      "initial_interval_ms": 1000,
      "max_interval_ms": 60000
    }
  },
  "tags": ["report", "production"],
  "enabled": true
}

# 创建延迟任务（一次性）
POST /api/v1/jobs/delayed
{
  "name": "send-verification-sms",
  "type": "http",
  "trigger_at": "2024-01-15T10:35:00Z",  # 精确触发时间
  "config": {
    "url": "https://notification.internal/api/sms",
    "method": "POST",
    "body": { "phone": "+8613800138000", "code": "123456" }
  }
}

# 创建 DAG 工作流
POST /api/v1/jobs/workflow
{
  "name": "etl-pipeline",
  "schedule": "0 0 2 * * ?",
  "dag": {
    "tasks": [
      { "id": "extract",  "type": "http", "config": {...} },
      { "id": "transform","type": "http", "config": {...}, 
        "depends_on": ["extract"] },
      { "id": "load",     "type": "http", "config": {...},
        "depends_on": ["transform"] },
      { "id": "validate", "type": "http", "config": {...},
        "depends_on": ["load"] },
      { "id": "notify",   "type": "http", "config": {...},
        "depends_on": ["validate"], 
        "trigger_rule": "all_success" }  # all_success | all_done | one_failed
    ]
  }
}

# 查询任务列表
GET /api/v1/jobs?status=active&tags=production&page=1&size=20

# 获取任务详情
GET /api/v1/jobs/:jobId

# 更新任务
PUT /api/v1/jobs/:jobId

# 暂停/恢复任务
POST /api/v1/jobs/:jobId/pause
POST /api/v1/jobs/:jobId/resume

# 立即触发任务（手动执行）
POST /api/v1/jobs/:jobId/trigger

# 查询执行历史
GET /api/v1/jobs/:jobId/executions?from=2024-01-01&to=2024-01-15&status=failed

# 中止正在运行的任务
POST /api/v1/jobs/:jobId/executions/:executionId/cancel
```

### 回调 API（任务执行器注册）

```
# Worker 注册
POST /api/v1/workers/register
{
  "worker_id": "worker-01",
  "capacity": 10,            # 最大并发执行数
  "supported_types": ["http", "shell"],
  "tags": ["production", "us-east-1"],
  "heartbeat_interval_ms": 10000
}

# Worker 心跳
POST /api/v1/workers/:workerId/heartbeat
{
  "running_jobs": ["exec-123", "exec-456"],
  "cpu_usage": 0.45,
  "memory_usage": 0.60
}

# 任务执行状态回调
POST /api/v1/executions/:executionId/status
{
  "status": "running" | "success" | "failed",
  "result": { "exit_code": 0, "output": "...", "duration_ms": 1234 },
  "error": { "message": "...", "stack_trace": "..." }
}
```

---

## 数据模型

### 核心表结构

```sql
-- 任务定义表
CREATE TABLE jobs (
    id              VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(50) NOT NULL,       -- http, shell, kafka, grpc
    schedule        VARCHAR(100),               -- cron表达式, NULL表示一次性任务
    timezone        VARCHAR(50) DEFAULT 'UTC',
    trigger_at      TIMESTAMP,                  -- 延迟任务触发时间
    next_fire_time  TIMESTAMP,                  -- 下次触发时间(由scheduler计算)
    config          JSONB NOT NULL,             -- 任务配置
    retry_config    JSONB,                      -- 重试配置
    timeout_ms      INTEGER DEFAULT 300000,
    priority        INTEGER DEFAULT 0,          -- 优先级(越大越高)
    enabled         BOOLEAN DEFAULT TRUE,
    tags            TEXT[],                     -- PostgreSQL数组: 标签
    created_by      VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_next_fire ON jobs(next_fire_time) WHERE enabled = TRUE;
CREATE INDEX idx_jobs_enabled ON jobs(enabled);
CREATE INDEX idx_jobs_tags ON jobs USING GIN(tags);

-- 任务执行记录表
CREATE TABLE executions (
    id              VARCHAR(64) PRIMARY KEY,    -- execution id
    job_id          VARCHAR(64) NOT NULL REFERENCES jobs(id),
    trigger_type    VARCHAR(20) NOT NULL,       -- scheduled | manual | retry | delayed
    status          VARCHAR(20) NOT NULL,       -- pending | running | success | failed | timeout | cancelled
    attempt         INTEGER DEFAULT 1,          -- 第几次尝试
    worker_id       VARCHAR(100),               -- 执行worker ID
    scheduled_at    TIMESTAMP NOT NULL,         -- 计划执行时间
    started_at      TIMESTAMP,                  -- 实际开始时间
    completed_at    TIMESTAMP,                  -- 完成时间
    duration_ms     INTEGER,                    -- 执行耗时
    result          JSONB,                      -- 执行结果
    error_message   TEXT,                       -- 错误信息
    next_retry_at   TIMESTAMP,                  -- 下次重试时间
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_executions_job ON executions(job_id, scheduled_at DESC);
CREATE INDEX idx_executions_status ON executions(status) WHERE status IN ('running', 'pending');
CREATE INDEX idx_executions_next_retry ON executions(next_retry_at) WHERE status = 'failed';

-- Worker注册表
CREATE TABLE workers (
    id              VARCHAR(100) PRIMARY KEY,
    status          VARCHAR(20) DEFAULT 'active',  -- active | busy | draining | offline
    capacity        INTEGER NOT NULL,
    running_count   INTEGER DEFAULT 0,
    supported_types TEXT[],
    tags            TEXT[],
    hostname        VARCHAR(255),
    last_heartbeat  TIMESTAMP,
    registered_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_workers_heartbeat ON workers(last_heartbeat);

-- DAG工作流定义
CREATE TABLE workflows (
    id              VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    schedule        VARCHAR(100),
    dag_definition  JSONB NOT NULL,    -- DAG结构定义
    status          VARCHAR(20) DEFAULT 'active',
    next_fire_time  TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- DAG任务运行实例
CREATE TABLE workflow_runs (
    id              VARCHAR(64) PRIMARY KEY,
    workflow_id     VARCHAR(64) NOT NULL,
    trigger_type    VARCHAR(20) NOT NULL,
    status          VARCHAR(20) NOT NULL,  -- running | success | failed
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    dag_snapshot    JSONB NOT NULL,        -- 本次运行的DAG快照(含状态)
    created_at      TIMESTAMP DEFAULT NOW()
);
```

### Cron 表达式解析

```python
# Cron 表达式: 秒 分 时 日 月 周
# 示例: "0 30 9 * * ?" = 每天9:30:00执行

class CronParser:
    FIELD_NAMES = ['second', 'minute', 'hour', 'day', 'month', 'weekday']
    FIELD_RANGES = {
        'second':  (0, 59),
        'minute':  (0, 59),
        'hour':    (0, 23),
        'day':     (1, 31),
        'month':   (1, 12),
        'weekday': (0, 6),   # 0=Sunday
    }
    
    def next_fire_time(self, cron_expr, from_time):
        """计算下一次触发时间"""
        fields = cron_expr.split()
        parsed = [self._parse_field(f, name) 
                  for f, name in zip(fields, self.FIELD_NAMES)]
        
        current = from_time + timedelta(seconds=1)
        # 从秒开始逐级匹配, 不匹配则进位
        for attempt in range(366 * 24 * 3600):  # 最多找一年
            if self._matches_all(current, parsed):
                return current
            current = self._increment(current, parsed)
        return None
    
    def _parse_field(self, field, name):
        """解析单个域: * | 1,2,3 | 1-5 | */5 | 1/5"""
        min_val, max_val = self.FIELD_RANGES[name]
        values = set()
        
        for part in field.split(','):
            if part == '*':
                values.update(range(min_val, max_val + 1))
            elif '/' in part:
                range_part, step = part.split('/')
                step = int(step)
                if range_part == '*':
                    values.update(range(min_val, max_val + 1, step))
                else:
                    start, end = map(int, range_part.split('-'))
                    values.update(range(start, end + 1, step))
            elif '-' in part:
                start, end = map(int, part.split('-'))
                values.update(range(start, end + 1))
            else:
                values.add(int(part))
        
        return sorted(values)
```

---

## 高层次架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            API Layer (REST)                               │
│                     Job CRUD, 触发, 查询, 管理                            │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Scheduler Cluster                                │
│                                                                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────────┐  │
│  │  Scheduler Node 1  │  │  Scheduler Node 2  │  │  Scheduler Node 3 │  │
│  │  (Leader)           │  │  (Standby)         │  │  (Standby)        │  │
│  │                    │  │                    │  │                    │  │
│  │ ┌────────────────┐ │  │ ┌────────────────┐ │  │ ┌────────────────┐ │  │
│  │ │ Time Wheel    │ │  │ │ Time Wheel    │ │  │ │ Time Wheel    │ │  │
│  │ │ (内存)        │ │  │ │ (空闲)        │ │  │ │ (空闲)        │ │  │
│  │ └────────────────┘ │  │ └────────────────┘ │  │ └────────────────┘ │  │
│  │ ┌────────────────┐ │  │                    │  │                    │  │
│  │ │ Cron Scanner  │ │  │                    │  │                    │  │
│  │ │ (定期扫描DB)   │ │  │                    │  │                    │  │
│  │ └────────────────┘ │  │                    │  │                    │  │
│  │ ┌────────────────┐ │  │                    │  │                    │  │
│  │ │ Dispatcher    │ │  │                    │  │                    │  │
│  │ │ (分发任务)     │ │  │                    │  │                    │  │
│  │ └────────────────┘ │  │                    │  │                    │  │
│  └────────────────────┘  └────────────────────┘  └───────────────────┘  │
│            │                                                            │
└────────────┼────────────────────────────────────────────────────────────┘
             │
             │  Leader Election via: ZooKeeper / etcd / Raft
             │
             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Task Queue (Message Broker)                      │
│                                                                          │
│              ┌───────────────────────────────────────┐                   │
│              │          Redis / Kafka                 │                   │
│              │                                       │                   │
│              │  优先级队列 (Redis Sorted Set):        │                   │
│              │  Key: "task:queue"                    │                   │
│              │  Score: priority + scheduled_time     │                   │
│              │                                       │                   │
│              │  延迟队列 (Redis ZSet):                │                   │
│              │  Key: "task:delayed"                  │                   │
│              │  Score: trigger_timestamp             │                   │
│              │                                       │                   │
│              │  就绪队列 (Redis List):                │                   │
│              │  Key: "task:ready"                    │                   │
│              └───────────────────────────────────────┘                   │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           Worker Cluster                                  │
│                                                                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐              │
│  │  Worker Node 1│   │  Worker Node 2│   │  Worker Node 3│              │
│  │               │   │               │   │               │              │
│  │ Pull Task ────│   │ Pull Task ────│   │ Pull Task ────│              │
│  │ Execute ──────│   │ Execute ──────│   │ Execute ──────│              │
│  │ Report Status │   │ Report Status │   │ Report Status │              │
│  └───────────────┘   └───────────────┘   └───────────────┘              │
│                                                                          │
│  Worker类型:                                                             │
│  - HTTP Worker: 发送HTTP请求执行任务                                      │
│  - Shell Worker: 执行Shell脚本                                           │
│  - Kafka Worker: 发送Kafka消息                                           │
│  - gRPC Worker: 调用gRPC服务                                             │
│  - Custom Worker: 自定义执行逻辑                                         │
└──────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Storage Layer                                    │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │   PostgreSQL          │  │   Redis               │                     │
│  │  - jobs定义           │  │  - 任务队列            │                     │
│  │  - executions历史     │  │  - 延迟队列            │                     │
│  │  - workers注册        │  │  - 分布式锁            │                     │
│  │  - workflows定义      │  │  - 计数器/限流         │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │  ZooKeeper / etcd (Leader Election + 配置中心)        │               │
│  └──────────────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. 时间轮算法 (Timing Wheel)

时间轮是高效延迟任务调度核心数据结构，O(1) 插入和触发复杂度。

```
时间轮结构:

                    ┌───┬───┬───┬───┬───┬───┬───┬───┐
        slot[0] ──►│   │   │   │   │   │   │   │   │
        slot[1] ──►│   │   │   │   │   │   │   │   │
        slot[2] ──►│ T1│ T2│   │   │   │   │   │   │
        ...        │   │   │   │   │   │   │   │   │
        slot[59]──►│   │   │   │   │   │   │   │   │
                    └───┴───┴───┴───┴───┴───┴───┴───┘
                    ←──── 60个槽, 每个槽1秒 ────→

层级时间轮 (Hierarchical Timing Wheel):
  秒轮 (60 slots × 1s)  → 60秒范围
  分轮 (60 slots × 1min) → 60分钟范围
  时轮 (24 slots × 1h)  → 24小时范围

  当秒轮走完一圈(60秒), 从分轮降级一个槽到秒轮
  当分轮走完一圈(60分钟), 从时轮降级一个槽到分轮
```

**时间轮实现伪代码：**

```python
class TimingWheel:
    def __init__(self, tick_ms, wheel_size):
        self.tick_ms = tick_ms        # 每格时间 (ms)
        self.wheel_size = wheel_size  # 格子数量
        self.current_index = 0
        self.slots = [[] for _ in range(wheel_size)]
    
    def add_task(self, task, delay_ms):
        """添加延迟任务 O(1)"""
        slot_index = (self.current_index + delay_ms // self.tick_ms) % self.wheel_size
        rounds = delay_ms // (self.tick_ms * self.wheel_size)
        self.slots[slot_index].append((rounds, task))
    
    def tick(self):
        """时间推进一格"""
        slot = self.slots[self.current_index]
        ready_tasks = []
        remaining = []
        
        for rounds, task in slot:
            if rounds <= 0:
                ready_tasks.append(task)  # 该执行了
            else:
                remaining.append((rounds - 1, task))  # 还需等待
        
        self.slots[self.current_index] = remaining
        self.current_index = (self.current_index + 1) % self.wheel_size
        return ready_tasks


# 层级时间轮
class HierarchicalTimingWheel:
    def __init__(self):
        self.second_wheel = TimingWheel(tick_ms=1000, wheel_size=60)   # 1分钟
        self.minute_wheel = TimingWheel(tick_ms=60000, wheel_size=60)  # 1小时
        self.hour_wheel = TimingWheel(tick_ms=3600000, wheel_size=24)  # 1天
    
    def add_task(self, task, delay_ms):
        if delay_ms < 60000:
            self.second_wheel.add_task(task, delay_ms)
        elif delay_ms < 3600000:
            self.minute_wheel.add_task(task, delay_ms)
        else:
            self.hour_wheel.add_task(task, delay_ms)
    
    def tick(self):
        """每1秒tick一次"""
        ready = self.second_wheel.tick()
        
        if self.second_wheel.current_index == 0:  # 秒轮转了一圈
            cascade = self.minute_wheel.tick()
            for rounds, task in cascade:
                # 降级到秒轮
                self.second_wheel.slots[0].append((rounds, task))
        
        if self.minute_wheel.current_index == 0:   # 分轮转了一圈
            cascade = self.hour_wheel.tick()
            for rounds, task in cascade:
                self.minute_wheel.slots[0].append((rounds, task))
        
        return ready
```

### 2. Leader Election 与高可用

```
Leader选举方案对比:

┌──────────────┬─────────────────────┬─────────────────────┐
│   方案        │       优点          │       缺点           │
├──────────────┼─────────────────────┼─────────────────────┤
│ ZooKeeper    │ 成熟, 自带Session   │ 额外运维组件         │
│              │ Watch, 临时节点      │ 性能一般            │
├──────────────┼─────────────────────┼─────────────────────┤
│ etcd         │ Raft协议, 强一致    │ 需要独立部署         │
│              │ 性能优于ZK          │                     │
├──────────────┼─────────────────────┼─────────────────────┤
│ Redis 分布式锁│ 轻量, 多数公司已有   │ Redlock有争议        │
│ (Redlock)    │                     │ 不保证绝对安全       │
├──────────────┼─────────────────────┼─────────────────────┤
│ 数据库悲观锁  │ 无额外组件          │ 性能差, 高负载不行    │
│ SELECT FOR   │ 实现简单            │ 需要处理锁过期        │
│ UPDATE       │                     │                     │
└──────────────┴─────────────────────┴─────────────────────┘
```

**Leader 故障切换流程：**

```
正常状态:
  Server-1 (Leader)  ── 持有锁 ──┐
  Server-2 (Standby)              │    ZooKeeper
  Server-3 (Standby)              │   ┌──────────┐
                                  ├──>│ /lock    │ (临时节点, Server-1创建)
                                  │   └──────────┘

Server-1 宕机:
  1. ZooKeeper Session 过期 → 临时节点 /lock 自动删除
  2. Server-2 watch 到节点删除事件
  3. Server-2 尝试创建 /lock (ZooKeeper写操作, 原子性保证)
  4. Server-2 创建成功 → 成为新Leader
  5. Server-2 加载未完成的任务状态, 接管调度
```

### 3. 防止重复执行

这是分布式调度最难的问题之一：

```python
# 方案1: 数据库乐观锁
def acquire_job(job_id, expected_next_fire):
    """使用乐观锁防止重复调度"""
    result = db.execute("""
        UPDATE jobs 
        SET next_fire_time = calculate_next_fire(schedule, timezone, NOW()),
            updated_at = NOW()
        WHERE id = %s 
          AND enabled = TRUE 
          AND next_fire_time <= NOW()
          AND next_fire_time = %s  -- 乐观锁: 检查是否被其他进程修改
        RETURNING id
    """, [job_id, expected_next_fire])
    return result.rowcount > 0

# 方案2: Redis 分布式锁
def dispatch_with_lock(job_id, execution_id):
    lock_key = f"job:lock:{job_id}"
    lock_value = execution_id
    lock_ttl = 300  # 5分钟, 超过最大任务执行时间
    
    # SET NX EX 是原子操作
    acquired = redis.set(lock_key, lock_value, nx=True, ex=lock_ttl)
    if not acquired:
        return False  # 其他进程已调度
    
    try:
        # 执行调度逻辑
        push_to_queue(job_id, execution_id)
    finally:
        # 释放锁 (需要Lua脚本保证原子性)
        redis.eval("""
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
        """, 1, lock_key, lock_value)

# 方案3: 数据库分片 + 单线程调度
# 将任务按 job_id hash 分片, 每个分片由一个线程/进程负责
# 通过分区实现并行, 每个分区内天然串行, 避免分布式锁
```

### 4. 大规模 Cron 扫描优化

```
问题: 100万任务, 每秒扫描一次数据库找需要触发的任务 → 开销巨大

解决方案: 多层过滤策略

Layer 1: 时间分桶 (Time Bucketing)
预计算每个任务的 next_fire_time, 放入对应分钟桶

  时间桶: "tasks:2024-01-15-10:30" → Set{job1, job2, ...}

  扫描逻辑 (每分钟执行):
    current_bucket = f"tasks:{now.strftime('%Y-%m-%d-%H:%M')}"
    job_ids = redis.smembers(current_bucket)
    对每个 job_id 进行检查和调度

Layer 2: 二次校验 (避免时钟漂移)
  对桶中的每个任务, 重新计算 next_fire_time 确认确实该执行

Layer 3: 快速过滤
  预编译 cron 表达式, 跳过明显不匹配的任务
```

**时间分桶预加载流程：**

```python
class BucketScheduler:
    def __init__(self):
        self.prefetch_window = 5  # 提前预加载未来5分钟的桶
    
    def preload_future_buckets(self):
        """后台线程定期运行"""
        now = datetime.now()
        
        # 扫描DB中 next_fire_time 在未来窗口内的任务
        window_end = now + timedelta(minutes=self.prefetch_window)
        tasks = db.query("""
            SELECT id, next_fire_time 
            FROM jobs 
            WHERE enabled = TRUE 
              AND next_fire_time <= %s
              AND (next_bucket IS NULL OR next_bucket < %s)
        """, [window_end, now])
        
        for task in tasks:
            bucket_key = self.get_bucket_key(task.next_fire_time)
            redis.sadd(bucket_key, task.id)
            db.update_next_bucket(task.id, bucket_key)
    
    def dispatch_current_bucket(self):
        """每分钟触发一次"""
        bucket_key = self.get_bucket_key(datetime.now())
        job_ids = redis.smembers(bucket_key)
        
        for job_id in job_ids:
            job = cache.get_or_load(job_id)
            # 二次确认: 精确计算 next_fire_time
            if job.next_fire_time <= datetime.now():
                self.dispatch(job)
            
            # 计算下次触发时间并放入对应桶
            job.next_fire_time = self.calc_next_fire(job)
            next_bucket = self.get_bucket_key(job.next_fire_time)
            redis.sadd(next_bucket, job.id)
        
        redis.delete(bucket_key)  # 清理当前桶
```

### 5. 任务执行与重试策略

```python
class TaskExecutor:
    def execute(self, execution):
        attempt = 0
        max_attempts = execution.retry_max_attempts
        
        while attempt < max_attempts:
            try:
                start_time = time.time()
                
                # 执行任务 (带超时)
                result = self.run_with_timeout(
                    execution.job.type,
                    execution.job.config,
                    execution.job.timeout_ms
                )
                
                elapsed = (time.time() - start_time) * 1000
                
                # 上报成功
                self.report_result(execution.id, 'success', {
                    'duration_ms': elapsed,
                    'output': result,
                    'attempt': attempt + 1
                })
                return
                
            except TimeoutError:
                self.report_result(execution.id, 'timeout', {
                    'attempt': attempt + 1,
                    'error': f'Execution exceeded {execution.job.timeout_ms}ms'
                })
                
            except Exception as e:
                attempt += 1
                if attempt >= max_attempts:
                    self.report_result(execution.id, 'failed', {
                        'attempt': attempt,
                        'error': str(e),
                        'stack_trace': traceback.format_exc()
                    })
                    return
                
                # 计算退避延迟
                delay = self.calculate_backoff(
                    execution.job.retry_config, attempt
                )
                
                # 安排重试 (通过延迟队列)
                self.schedule_retry(execution, delay)
                return
    
    def calculate_backoff(self, retry_config, attempt):
        """退避策略"""
        base = retry_config['initial_interval_ms']
        max_delay = retry_config.get('max_interval_ms', 60000)
        
        strategy = retry_config.get('backoff', 'exponential')
        
        if strategy == 'fixed':
            return base
        elif strategy == 'linear':
            return min(base * attempt, max_delay)
        elif strategy == 'exponential':
            delay = base * (2 ** (attempt - 1))
            # 添加随机抖动避免惊群效应
            jitter = random.uniform(0, delay * 0.1)
            return min(delay + jitter, max_delay)
    
    def run_with_timeout(self, task_type, config, timeout_ms):
        """带超时的任务执行"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._execute_inner, task_type, config)
            try:
                return future.result(timeout=timeout_ms / 1000)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise TimeoutError()
```

### 6. DAG 工作流调度

```
DAG 工作流示例:

         ┌─────────┐
         │ extract │ (从DB提取数据)
         └────┬────┘
              │
              ▼
         ┌─────────┐
         │transform│ (数据转换)
         └────┬────┘
         ┌────┴────┐
         │         │
         ▼         ▼
    ┌────────┐ ┌────────┐
    │ load   │ │backup  │ (并行执行)
    │ (DB)   │ │ (S3)   │
    └───┬────┘ └───┬────┘
        │          │
        └────┬─────┘
             │
             ▼
        ┌─────────┐
        │validate │ (数据校验)
        └────┬────┘
             │
             ▼
        ┌─────────┐
        │ notify  │ (通知)
        └─────────┘
```

```python
class DAGExecutor:
    def __init__(self, dag):
        self.graph = self.build_graph(dag)  # 邻接表
        self.in_degree = self.calc_in_degrees()
        self.task_status = {task: 'pending' for task in dag.tasks}
        self.completed = set()
    
    def execute(self):
        """拓扑排序执行DAG"""
        ready_queue = [
            task for task, deg in self.in_degree.items() 
            if deg == 0
        ]
        
        while ready_queue:
            # 并行执行所有就绪任务
            futures = {}
            with ThreadPoolExecutor(max_workers=len(ready_queue)) as pool:
                for task in ready_queue:
                    futures[pool.submit(self.run_task, task)] = task
            
            ready_queue = []
            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    self.task_status[task] = 'success'
                    self.completed.add(task)
                    
                    # 检查下游任务是否就绪
                    for downstream in self.graph.get(task, []):
                        self.in_degree[downstream] -= 1
                        if (self.in_degree[downstream] == 0 and
                            self.all_upstream_success(downstream)):
                            ready_queue.append(downstream)
                            
                except Exception:
                    self.task_status[task] = 'failed'
                    # trigger_rule 处理: all_success / all_done / one_failed
                    if task.trigger_rule == 'all_success':
                        # 下游任务全部标记为upstream_failed
                        self.cascade_failure(task)
```

---

## 扩展性与高可用

### 1. Scheduler 水平扩展

```
分片策略:

方法1: 一致性哈希 (推荐)
  - 将 job_id hash 到不同的 Scheduler 实例
  - 每个 Scheduler 只负责自己的分片
  - Leader Election 仅用于协调分片分配, 不承担所有调度

方法2: 分区表
  - jobs_0, jobs_1, jobs_2, ..., jobs_N
  - 每个 Scheduler 固定负责几个分区
  - 增减 Scheduler 时重新分配分区

一致性哈希实现:
  Hash Ring:  0 ─── 2^32 ─── 0
              │     │      │
              S1   S3     S2
              
  job_id "abc" → hash("abc") = 1.2×10^9
  顺时针找到下一个节点 S3
  ∴ S3 负责调度 job "abc"
```

### 2. Worker 动态扩缩容

```
Worker Pool 管理:

                    ┌──────────────┐
                    │    Queue     │ ← 任务队列深度
                    │   Depth: 0   │   作为扩缩容信号
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │Worker 1│  │Worker 2│  │Worker 3│
         │ slots: │  │ slots: │  │ slots: │
         │  5/10  │  │  2/10  │  │  8/10  │
         └────────┘  └────────┘  └────────┘

扩缩容策略:
  - Queue Depth > capacity × 2 持续1分钟 → Scale Up (+1 worker)
  - All Workers idle > 5分钟 → Scale Down (-1 worker)
  - 任务等待时间 P99 > 30s → 紧急扩容
```

### 3. 故障处理矩阵

| 故障场景 | 影响 | 恢复策略 |
|----------|------|----------|
| Scheduler 宕机 | 该分片任务暂时不被调度 | 一致性哈希自动转移到其他 Scheduler |
| Worker 宕机 | 该 Worker 上的执行中断 | 心跳超时(30s)后任务重新分配 |
| 数据库故障 | 任务定义不可见 | 主从切换 + 读cache |
| Redis 故障 | 延迟队列不可用 | Sentinel 自动 failover |
| 网络分区 | Leader可能脑裂 | 基于epoch fencing token防止双主 |

### 4. 监控与运维

```
Dashboard 指标:
┌─────────────────────────────────────────────────────────────┐
│ 调度层                                                        │
│  - 活跃任务数, 每分钟触发数                                    │
│  - 调度延迟 (scheduled_at vs actual trigger time)             │
│  - 调度跳过率 (任务因锁竞争未能触发)                            │
├─────────────────────────────────────────────────────────────┤
│ 执行层                                                        │
│  - Worker 数量, 负载, 心跳                                     │
│  - 队列深度, 任务等待时间                                       │
│  - 成功率, 失败率, 重试率                                       │
│  - P50/P95/P99 执行延迟                                       │
├─────────────────────────────────────────────────────────────┤
│ 告警                                                          │
│  - 调度跳过率 > 1% → 可能需要扩容 Scheduler                     │
│  - 任务失败率 > 5% → 可能是下游故障                             │
│  - Worker 心跳丢失 > 30s → Worker 可能宕机                     │
│  - 延迟队列堆积 > 10000 → 执行能力不足                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 核心算法 | 层级时间轮 (O(1) 插入/触发) + Cron 预计算 |
| 分片策略 | 一致性哈希 + 时间分桶 |
| 高可用 | Leader Election (etcd) + 分片重分配 |
| 防重复 | 乐观锁 + 分布式锁 + 分片串行执行 |
| 重试策略 | 指数退避 + 随机抖动 |
| 工作流 | DAG 拓扑排序 + trigger_rule 灵活编排 |
| 存储 | PostgreSQL(定义+历史) + Redis(队列+锁) + etcd(选举) |

**CAP 取舍：** 选择 CP 模型。调度系统的核心要求是**精确执行一次**（exactly-once），不能重复触发也不能漏触发。因此优先保证一致性——Leader 选举确保只有写入数据库的操作才会被调度；如果发生网络分区导致无法选举 Leader，宁可暂停调度也不能重复调度。

**关键设计权衡：**
1. **Leader-Scheduler vs 分片-Scheduler：** 初期可用 Leader 模式（简单），规模化后切换到分片模式（可扩展）
2. **时间轮 vs 数据库轮询：** 时间轮适合大规模延迟任务（O(1)触发），数据库轮询适合小规模 Cron 任务
3. **Push (Scheduler下发) vs Pull (Worker拉取)：** Pull 模式更适合 Worker 异构场景，Worker 可根据自身负载自主拉取
