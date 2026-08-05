# 44. 设计特性开关/配置中心 (Design Feature Flag/Dynamic Config Service)

## 题目

设计一个特性开关 (Feature Flag) 与动态配置中心系统，类似 LaunchDarkly / Apollo / Nacos。支持实时开关控制、灰度发布、A/B 测试、动态配置推送。要求变更秒级生效、高可用、支持海量客户端。

## 需求澄清

### 功能性需求

1. **特性开关管理 (Feature Flag CRUD)**: 创建/编辑/删除/归档开关，定义开关名称、描述、类型
2. **开关评估 (Flag Evaluation)**: 客户端/服务端查询某个开关在当前上下文下的值 (boolean / string / number / JSON)
3. **灰度发布 (Gradual Rollout)**: 按百分比、用户组、地域、设备等维度逐步放量
4. **定向规则 (Targeting Rules)**: 支持基于用户属性（user_id, email, country, plan_type 等）的定向
5. **A/B 测试 (A/B Testing)**: 支持多变量实验，关联转化指标
6. **动态配置 (Dynamic Config)**: 支持非布尔类型配置的实时变更推送
7. **变更历史 (Change History)**: 完整的审计日志，记录谁在什么时间改了什么
8. **SDK 支持 (Multi-language SDK)**: Go/Java/Python/JS 等多语言 SDK

### 非功能性需求

1. **实时性 (Real-time)**: 变更推送延迟 < 1 秒（P99）
2. **高可用 (High Availability)**: 99.999%，开关服务不可用不影响业务
3. **高性能 (Performance)**: 评估延迟 < 1ms（SDK 本地），控制面 QPS 10K+
4. **可扩展性 (Scalability)**: 支持千万级客户端（包括移动端、服务端）
5. **容错性 (Fault Tolerance)**: SDK 离线时使用本地缓存，不阻塞业务
6. **一致性 (Consistency)**: 同一变更所有客户端在秒级内生效

### 容量估算

```
假设 1000 个微服务 + 1 亿移动端设备

开关总数: 10,000 个
每个开关平均 5 个定向规则
每个规则平均涉及 3 个条件

评估 QPS:
  1亿设备每 30 秒拉取一次 = 3.3M QPS (峰值)
  1000 微服务每 1 秒拉取一次 = 1K QPS
  总计 ~3.3M QPS (读)

管理操作 QPS: < 100 QPS (写)

存储估算:
  10,000 个开关 * (5KB 配置 + 规则) = 50MB
  版本快照 * 100 个版本 = 5GB (含审计日志)
  审计日志: 100 次变更/天 * 365 天 * 1KB = 36.5MB/年
```

## API设计

### REST API (控制面 - 管理平台)

```
# 项目管理
POST   /api/v1/projects                         创建项目
GET    /api/v1/projects/{project_id}            获取项目

# 开关管理
POST   /api/v1/projects/{project_id}/flags      创建开关
GET    /api/v1/projects/{project_id}/flags      列出开关
GET    /api/v1/flags/{flag_key}                 获取开关详情
PUT    /api/v1/flags/{flag_key}                 更新开关配置
DELETE /api/v1/flags/{flag_key}                 删除开关(软删除)
POST   /api/v1/flags/{flag_key}/archive         归档开关
POST   /api/v1/flags/{flag_key}/toggle         启用/禁用开关

# 定向规则
POST   /api/v1/flags/{flag_key}/targeting       创建/更新定向规则

# 变更管理
POST   /api/v1/flags/{flag_key}/release         发布变更
GET    /api/v1/flags/{flag_key}/history         变更历史
POST   /api/v1/flags/{flag_key}/rollback        回滚到指定版本

# SDK 数据拉取 (数据面)
GET    /api/v1/sdk/flags                        获取所有开启的开关 (全量)
GET    /api/v1/sdk/flags?since={version}        增量获取变更 (长轮询/SSE)
POST   /api/v1/sdk/evaluate                     批量评估开关 (服务端 SDK)
```

### SDK 接口设计

```java
// Java SDK 接口示例
public interface FeatureFlagClient {

    // 布尔开关
    boolean isEnabled(String flagKey, User user);
    boolean isEnabled(String flagKey, User user, boolean defaultValue);

    // 多变量开关
    String getStringValue(String flagKey, User user, String defaultValue);
    int getIntValue(String flagKey, User user, int defaultValue);
    double getDoubleValue(String flagKey, User user, double defaultValue);
    JsonNode getJsonValue(String flagKey, User user, JsonNode defaultValue);

    // 批量评估
    Map<String, FlagEvaluation> evaluateAll(User user);

    // 监听变更 (推送模式)
    void addFlagChangeListener(String flagKey, FlagChangeListener listener);
}
```

### 数据面 API 协议

```protobuf
// SDK 拉取开关数据的协议 (高效二进制)

message FlagDataRequest {
  string sdk_key = 1;           // SDK 密钥(用于项目识别)
  int64 since_version = 2;      // 增量拉取: 当前版本号
  string etag = 3;              // HTTP 缓存: ETag
}

message FlagDataResponse {
  int64 version = 1;                    // 当前数据版本号
  repeated Flag flags = 2;              // 开关列表
  bool full_sync = 3;                   // true: 全量, false: 增量
  int64 ttl_seconds = 4;                // 客户端本地缓存 TTL
}

message Flag {
  string key = 1;
  string name = 2;
  FlagType type = 3;                    // BOOLEAN / STRING / INT / DOUBLE / JSON
  bool enabled = 4;
  repeated Variation variations = 5;     // 多变量变体定义
  repeated TargetingRule rules = 6;     // 定向规则
  int64 fallthrough_value = 7;          // 默认匹配的变体索引
  int64 version = 8;
  bool archived = 9;
}

message Variation {
  int64 index = 1;
  string name = 2;
  string value = 3;              // 序列化后的值
}

message TargetingRule {
  int64 variation_index = 1;     // 匹配后返回的变体
  int32 rollout_percent = 2;     // 百分比放量 (0-10000, 万分之一精度)
  repeated Clause clauses = 3;   // 条件子句

  message Clause {
    string attribute = 1;        // 用户属性: email, country, plan...
    Operator op = 2;             // EQUAL / NOT_EQUAL / CONTAINS / IN / GREATER_THAN / REGEX...
    repeated string values = 3;
  }
}

enum Operator {
  EQUAL = 0;
  NOT_EQUAL = 1;
  CONTAINS = 2;
  IN = 3;
  GREATER_THAN = 4;
  LESS_THAN = 5;
  REGEX = 6;
  SEGMENT_MATCH = 7;
}
```

## 数据模型

### MySQL 核心表

```sql
-- 项目表
CREATE TABLE projects (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_key VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sdk_key VARCHAR(64) NOT NULL UNIQUE COMMENT 'SDK认证密钥',
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 开关定义表
CREATE TABLE feature_flags (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT NOT NULL,
    flag_key VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    flag_type ENUM('BOOLEAN','STRING','INT','DOUBLE','JSON') NOT NULL DEFAULT 'BOOLEAN',
    enabled TINYINT(1) NOT NULL DEFAULT 0,
    archived TINYINT(1) NOT NULL DEFAULT 0,
    version BIGINT NOT NULL DEFAULT 0 COMMENT '当前版本号，用于增量同步',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_project_flag (project_id, flag_key),
    INDEX idx_project_enabled (project_id, enabled, archived)
) ENGINE=InnoDB;

-- 变体定义表 (多变量开关)
CREATE TABLE flag_variations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    flag_id BIGINT NOT NULL,
    variation_index INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL COMMENT '序列化后的值',
    UNIQUE KEY uk_flag_index (flag_id, variation_index)
) ENGINE=InnoDB;

-- 定向规则表
CREATE TABLE targeting_rules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    flag_id BIGINT NOT NULL,
    rule_order INT NOT NULL DEFAULT 0 COMMENT '规则优先级(越小越优先)',
    variation_index INT NOT NULL COMMENT '匹配后返回的变体',
    rollout_percent INT NOT NULL DEFAULT 10000 COMMENT '万分比: 10000=100%',
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_flag_order (flag_id, rule_order)
) ENGINE=InnoDB;

-- 规则条件子句
CREATE TABLE rule_clauses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rule_id BIGINT NOT NULL,
    attribute VARCHAR(64) NOT NULL COMMENT '用户属性名',
    operator ENUM('EQUAL','NOT_EQUAL','CONTAINS','IN','GT','LT','GTE','LTE','REGEX','SEGMENT_MATCH') NOT NULL,
    values_json TEXT NOT NULL COMMENT 'JSON数组: ["value1","value2"]',
    INDEX idx_rule (rule_id)
) ENGINE=InnoDB;

-- 用户分组/标签表
CREATE TABLE user_segments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    segment_key VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255),
    description TEXT,
    rules_json TEXT NOT NULL COMMENT '分段规则JSON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 变更历史 / 审计日志
CREATE TABLE flag_change_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    flag_id BIGINT NOT NULL,
    operator_id VARCHAR(64) NOT NULL COMMENT '操作人',
    change_type VARCHAR(32) NOT NULL COMMENT 'CREATE/UPDATE/TOGGLE/ROLLBACK/ARCHIVE',
    previous_state JSON COMMENT '变更前状态',
    new_state JSON COMMENT '变更后状态',
    version BIGINT NOT NULL,
    release_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_flag_version (flag_id, version DESC),
    INDEX idx_operator (operator_id, created_at)
) ENGINE=InnoDB;
```

### Redis 数据结构

```
# 开关配置快照 (全量缓存)
# Key: project:flags:version
# Value: 当前全量配置版本号
GET project:flags:version -> 12345

# Key: project:flags:snapshot
# Value: 序列化的全量开关配置(protobuf/gzip压缩)
GET project:flags:snapshot -> <binary proto>

# 变更事件通道 (Pub/Sub)
PUBLISH project:flag_changed '{"flag_key":"new_feature","version":12346}'

# 增量变更日志 (Sorted Set, 保留最近1000条)
ZADD project:flag_changelog 12346 '{"flag_key":"...","action":"update",...}'
ZRANGEBYSCORE project:flag_changelog 12345 +inf  # 获取12345之后的所有变更
```

## 高层次架构

```
┌──────────────────────────────────────────────────────────────┐
│                     管理控制台 (Web UI)                        │
│   - 开关管理  - 规则配置  - 灰度发布  - A/B实验  - 审计日志    │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP/gRPC
              ┌───────────▼───────────┐
              │    Admin Service      │
              │  (控制面 - 管理操作)    │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
  │  MySQL    │    │  Redis    │    │  Kafka    │
  │ (持久化)   │    │ (缓存)    │    │ (变更事件) │
  └───────────┘    └─────┬─────┘    └─────┬─────┘
                         │                │
              ┌──────────▼────────────────▼──────────┐
              │         Sync / Delivery Service       │
              │   (数据面 - 配置同步与下发)              │
              │                                       │
              │  ┌──────────┐  ┌───────────────────┐  │
              │  │ Poll API │  │ Push (SSE/WS/      │  │
              │  │ (HTTP)   │  │  Long-Polling)     │  │
              │  └──────────┘  └───────────────────┘  │
              └──────────┬───────────────────────────┘
                         │
        ┌────────────────┼────────────────────────────┐
        │                │                            │
  ┌─────▼─────┐    ┌─────▼─────┐              ┌─────▼─────┐
  │ 移动端SDK  │    │ 后端服务SDK │              │  其他SDK   │
  │ (30s轮询)  │    │ (SSE/长轮询)│              │            │
  │           │    │           │              │            │
  │ ┌───────┐ │    │ ┌───────┐ │              │ ┌───────┐ │
  │ │L1 Cache│ │    │ │L1 Cache│ │              │ │L1 Cache│ │
  │ │(本地)  │ │    │ │(内存)  │ │              │ │(文件)  │ │
  │ └───────┘ │    │ └───────┘ │              │ └───────┘ │
  └───────────┘    └───────────┘              └───────────┘
```

### 核心流程

```
变更推送流程:

1. 管理员在控制台修改开关 -> Admin Service
2. Admin Service:
   a. 写入 MySQL (持久化)
   b. 刷新 Redis 缓存 (全量快照 + 版本号递增)
   c. 写入 Kafka 变更事件
3. Sync Service 从 Kafka 消费变更事件
4. Sync Service 更新内存中的全量快照
5. Sync Service 通过以下方式推送给客户端:
   - 服务端 SDK: SSE/Long-Polling 实时推送
   - 移动端 SDK: 标记数据版本过期, 下次轮询时获取增量

SDK 评估流程:

1. 应用调用: client.isEnabled("new_feature", user)
2. SDK 从本地内存缓存获取开关定义
3. 遍历定向规则(Targeting Rules):
   a. 按 rule_order 顺序匹配
   b. 对每个 Clause 检查用户属性:
      - user.email ENDS_WITH "@vip.com"  -> true
      - user.country IN ["CN","US"]      -> true
   c. 如果所有 Clauses 满足 -> 应用 rollout_percent
      - hash(user.key) % 10000 < rollout_percent -> 返回此变体
4. 如果没有规则匹配 -> 返回 fallthrough (默认值)
5. 返回评估结果 (true/false 或变体值)
```

## 核心深入

### 同步机制对比

#### 方案A: 定时轮询 (Polling)

```
SDK 每隔 N 秒 GET /sdk/flags?since={version}

优点: 简单, HTTP only, 防火墙友好
缺点: 延迟 >= 轮询间隔, 浪费带宽
适用: 移动端(30-60s 间隔), 对实时性要求不高的场景
```

#### 方案B: 长轮询 (Long Polling)

```
GET /sdk/flags?since={version}
Server hold 30s, 有变更立即返回, 无变更超时返回304

优点: 准实时, 无连接建立开销
缺点: 每个客户端一个 HTTP 连接
适用: 服务端 SDK
```

#### 方案C: SSE (Server-Sent Events)

```
GET /sdk/stream
Server 保持 HTTP 连接, 持续推送变更事件

优点: 标准协议, 浏览器原生支持, 自动重连
缺点: 单向推送(服务端->客户端)
适用: 服务端 SDK, 浏览器端
```

#### 方案D: WebSocket

```
双向通信, 全双工
优点: 最低延迟, 双向通信
缺点: 重连逻辑复杂, 需要特殊基础设施(网关支持)
```

**选型**: 多通道混合模式 ⭐

```
┌──────────────────────────────────────┐
│ 客户端类型        │ 同步方式          │
├──────────────────┼───────────────────┤
│ 移动端 App       │ 定时轮询 (30-60s) │
│ 后端微服务        │ SSE + 长轮询      │
│ 浏览器 JavaScript│ SSE               │
│ 边缘/IoT设备     │ 定时轮询 (60-120s)│
└──────────────────┴───────────────────┘
```

### 评估引擎核心算法

```python
class FlagEvaluator:
    """开关评估引擎 - SDK 核心"""

    def evaluate(self, flag: Flag, user: User) -> EvaluationResult:
        # 1. 开关未启用 -> 返回默认 off 值
        if not flag.enabled:
            return EvaluationResult(
                value=flag.get_off_variation_value(),
                reason="FLAG_DISABLED"
            )

        # 2. 遍历定向规则 (按优先级顺序)
        for rule in flag.targeting_rules:
            if not rule.is_active:
                continue

            if self._match_rule(rule, user):
                # 3. 规则匹配 -> 检查百分比放量
                if self._in_rollout(rule, user):
                    variation = flag.get_variation(rule.variation_index)
                    return EvaluationResult(
                        value=variation.value,
                        variation_index=rule.variation_index,
                        reason=f"RULE_MATCH:{rule.id}"
                    )

        # 4. 没有规则匹配 -> fallthrough
        variation = flag.get_variation(flag.fallthrough_variation_index)
        return EvaluationResult(
            value=variation.value,
            variation_index=flag.fallthrough_variation_index,
            reason="FALLTHROUGH"
        )

    def _match_rule(self, rule: TargetingRule, user: User) -> bool:
        """匹配规则: 所有子句必须满足 (AND 逻辑)"""
        for clause in rule.clauses:
            user_value = user.get_attribute(clause.attribute)
            if user_value is None:
                return False  # 缺失属性 -> 不匹配

            if not self._evaluate_clause(clause, user_value):
                return False
        return True

    def _evaluate_clause(self, clause, user_value) -> bool:
        """评估单个子句"""
        ops = {
            'EQUAL': lambda uv, cv: str(uv) == cv,
            'NOT_EQUAL': lambda uv, cv: str(uv) != cv,
            'CONTAINS': lambda uv, cv: cv in str(uv),
            'IN': lambda uv, cvs: str(uv) in cvs,
            'GT': lambda uv, cv: float(uv) > float(cv),
            'LT': lambda uv, cv: float(uv) < float(cv),
            'REGEX': lambda uv, cv: re.match(cv, str(uv)) is not None,
            'SEGMENT_MATCH': lambda uv, cv: self._check_segment(uv, cv),
        }
        op_func = ops.get(clause.operator)
        if not op_func:
            return False
        return op_func(user_value, clause.values[0] if len(clause.values) == 1 else clause.values)

    def _in_rollout(self, rule: TargetingRule, user: User) -> bool:
        """确定性地检查用户是否在百分比放量范围内"""
        if rule.rollout_percent >= 10000:
            return True  # 100% 放量

        # 计算哈希: hash(flag_key + user.key + rule.salt) % 10000
        hash_input = f"{rule.flag_key}:{user.key}:{rule.salt}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        bucket = hash_value % 10000

        return bucket < rule.rollout_percent
```

### 一致性哈希在百分比放量中的作用

```
百分比灰度放量的关键挑战:
  - 从 10% 放量到 20% 时，原来 10% 的用户应该继续在实验组
  - 不能因为百分比增大导致之前被选中的人被踢出

解决方案: 确定性分桶 (Deterministic Bucketing)

  hash(user.key + flag.salt) % 10000 = bucket

  放量 10%: bucket < 1000 的用户被选中
  放量 20%: bucket < 2000 的用户被选中
  -> 原来 10% 的用户 bucket 一定 < 1000 < 2000，继续保持
  -> 新增 10% 的用户 bucket 在 [1000, 2000) 之间

  关键: 百分比只能增大或保持不变，不能缩小（否则有人会被踢出）
```

### 本地缓存与容错机制

```java
public class FeatureFlagSDK {
    private final Map<String, Flag> flagCache = new ConcurrentHashMap<>();
    private final AtomicLong version = new AtomicLong(0);
    private volatile boolean initialized = false;

    public FeatureFlagSDK(SDKConfig config) {
        // 1. 尝试从本地文件加载缓存 (重启恢复)
        loadFromDiskCache();

        // 2. 异步初始化: 从服务器拉取全量数据
        syncFromServer();

        // 3. 启动定时同步
        scheduleSync();
    }

    private void loadFromDiskCache() {
        try {
            byte[] data = Files.readAllBytes(Paths.get("/tmp/flags_cache.bin"));
            FlagCache cache = deserialize(data);
            this.flagCache.putAll(cache.flags);
            this.version.set(cache.version);
            this.initialized = true;
        } catch (IOException e) {
            // 没有缓存文件，等待首次同步
            this.initialized = false;
        }
    }

    private void saveToDiskCache() {
        try {
            FlagCache cache = new FlagCache(flagCache, version.get());
            Files.write(Paths.get("/tmp/flags_cache.bin"), serialize(cache));
        } catch (IOException e) {
            log.warn("Failed to save disk cache", e);
        }
    }

    public boolean isEnabled(String flagKey, User user, boolean defaultValue) {
        Flag flag = flagCache.get(flagKey);

        if (flag == null) {
            // 开关不存在或尚未初始化 -> 返回默认值（不阻塞业务）
            log.warn("Flag {} not found, using default: {}", flagKey, defaultValue);
            return defaultValue;
        }

        try {
            return evaluator.evaluate(flag, user).getBooleanValue();
        } catch (Exception e) {
            // 评估异常 -> 返回默认值（宁可不生效，不能阻塞业务）
            log.error("Flag evaluation failed for {}", flagKey, e);
            return defaultValue;
        }
    }

    // 关键原则: SDK 是业务旁路逻辑，绝不能因为 SDK 异常导致业务不可用
}
```

### 增量同步优化

```python
# 服务端增量同步接口

@app.get("/api/v1/sdk/flags")
async def get_flags(sdk_key: str, since_version: int = 0):
    project = get_project_by_sdk_key(sdk_key)

    if since_version == 0:
        # 首次同步: 返回全量
        flags = get_all_active_flags(project.id)
        should_full_sync = True
    else:
        # 增量同步: 只返回变更的开关
        flags = get_flags_changed_since(project.id, since_version)
        should_full_sync = False

        # 检查是否需要全量同步 (版本差距太大)
        current_version = redis.get(f"project:{project.id}:flags:version")
        if current_version - since_version > 1000:
            flags = get_all_active_flags(project.id)
            should_full_sync = True

    response = FlagDataResponse(
        version=current_version,
        flags=flags,
        full_sync=should_full_sync,
        ttl_seconds=30  # 客户端缓存 30 秒
    )

    # CDN 缓存策略
    response.headers['Cache-Control'] = f'max-age={ttl_seconds}'
    response.headers['ETag'] = f'"{current_version}"'

    return response
```

## 扩展性与高可用

### Sync Service 的扩展

```
                      ┌──────────────────────┐
                      │    CDN / Edge Cache  │
                      │  (CloudFront/EdgeOne)│
                      │  Cache TTL: 5-10s    │
                      └──────────┬───────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
              │ Sync Svc 1│ │Sync 2 │ │ Sync Svc N│
              │(一致性哈希) │ │       │ │           │
              └─────┬─────┘ └───────┘ └─────┬─────┘
                    │                       │
                    │   Kafka Consumer      │
                    │   Group: sync-service │
                    │                       │
              ┌─────▼───────────────────────▼─────┐
              │          Kafka Cluster            │
              │   Topic: flag_change_events       │
              └───────────────────────────────────┘
```

### CDN 缓存策略

```
为什么用 CDN?

GET /sdk/flags HTTP 接口是幂等的、读多写少、数据变更不频繁
非常适合 CDN 缓存

缓存策略:
  CDN TTL: 10 秒 (配置变更后最多 10 秒全球生效)
  Cache Key: /sdk/flags?project={project_id}&version=0
  ETag: 数据版本号，支持条件请求 (304 Not Modified)

  Push/Purge: 紧急变更时主动清除 CDN 缓存
    POST /cdn/purge /sdk/flags?project={project_id}
```

### 多数据中心部署

```
┌────────────┐      ┌────────────┐      ┌────────────┐
│  DC-Asia   │      │  DC-US     │      │  DC-EU     │
│            │      │            │      │            │
│ MySQL(M)   │ ───► │ MySQL(R)   │ ───► │ MySQL(R)   │
│ Redis(M)   │      │ Redis(R)   │      │ Redis(R)   │
│ Sync Svc   │      │ Sync Svc   │      │ Sync Svc   │
│            │      │            │      │            │
│ 本地SDK───►│      │ 本地SDK───►│      │ 本地SDK───►│
└────────────┘      └────────────┘      └────────────┘

- 写操作只在主 DC (Asia)
- 其他 DC 通过 MySQL binlog 同步 + Redis replication
- 每个 DC 有本地 Sync Service，服务就近客户端
- DNS 就近路由: 亚洲用户 -> DC-Asia, 美国用户 -> DC-US
```

### 监控与告警

| 指标 | 说明 | 告警 |
|------|------|------|
| sync_service_qps | 同步服务请求量 | > 2x 基线 |
| sync_latency_p99 | 数据下发给客户端的延迟 | > 5s |
| flag_evaluation_error_rate | 开关评估失败率 | > 0.01% |
| flag_change_propagation_time | 变更推送到 99% 客户端的耗时 | > 30s |
| local_cache_hit_rate | SDK 本地缓存命中率 | < 95% |
| sync_service_availability | 同步服务可用性 | < 99.9% |
| admin_service_error_rate | 管理服务错误率 | > 1% |
| kafka_consumer_lag | Kafka 消费延迟 | > 10,000 |

## 总结

特性开关/配置中心的核心设计要点：

1. **架构分离**: 控制面（Admin Service）+ 数据面（Sync Service），读写分离，SQL/NoSQL 分离
2. **评估在客户端**: SDK 本地内存评估，延迟 < 1ms，架构上"去中心化"
3. **容错优先**: SDK 初始化和评估失败时返回默认值，绝不阻塞业务
4. **多通道同步**: 移动端轮询 + 服务端 SSE/长轮询，不同客户端不同策略
5. **确定性分桶**: hash(user.key + salt) % 10000，保证灰度用户不因放量调整被踢出
6. **增量同步**: 版本号机制 + 增量变更日志，减少数据传输量
7. **CDN 加速**: SDK 数据接口是幂等的，天然适合 CDN 缓存，大幅提升可用性和降低延迟
8. **完整审计**: 所有配置变更记录到变更历史表，支持 diff 对比和回滚
9. **数据最小化**: SDK 只获取当前项目需要的开关，过滤掉 archived 的开关

面试中面试官可能追问：如何保证灰度发布的一致性？如果一个用户从 10% 放量升级到 20%，如何确保之前 10% 的用户继续看到新功能？如何设计 "Kill Switch" 紧急关闭机制？
