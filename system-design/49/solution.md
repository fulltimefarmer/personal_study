# 49. 设计API版本管理与废弃系统 (Design API Versioning & Deprecation System)

## 题目

设计一个API版本管理与废弃系统，管理微服务架构中API的版本生命周期。核心功能包括API版本定义、多版本并存路由、版本废弃策略管理、自动文档生成、以及客户端迁移追踪。类似Stripe/Google的API版本管理方案。

## 需求澄清

### 功能性需求

1. **API版本定义**: 定义API的版本号、变更内容、废弃日期
2. **多版本路由**: 根据请求中的版本号将流量路由到不同的服务版本
3. **版本日期管理**: 基于日期的版本标识 (如 2024-01-01)
4. **废弃策略管理 (Deprecation)**: 设置废弃日期、发送废弃通知、强制升级Deadline
5. **客户端追踪**: 追踪哪些客户端(API Key/App ID)在使用哪个版本
6. **变更日志 (Changelog)**: 自动生成版本之间的接口变更差异
7. **兼容性检测**: 检测API变更是否向后兼容 (Breaking Change Detection)
8. **灰度迁移**: 支持按客户/百分比从旧版本迁移到新版本
9. **自动文档**: 基于 API Schema (OpenAPI/Protobuf) 自动生成版本化文档

### 非功能性需求

1. **低延迟**: 版本路由/解析 < 1ms 额外开销
2. **高可用**: 版本管理服务不可用时，不影响已有路由规则
3. **可扩展性**: 支持数千个API端点，每个同时维护 2-3 个版本
4. **可审计性**: 所有版本变更有完整的审计日志

### 容量估算

```
假设:
  API 总端点: 2,000
  每个端点活跃版本: 2-3 个 (current, previous, deprecated)
  总活跃版本: ~6,000

日常 API 请求:
  总 QPS: 500K
  版本分布: v1(70%), v2(25%), v3(5%)
  
版本元数据存储:
  每个版本定义: ~5KB (schema + 路由规则 + 废弃策略)
  总大小: 6,000 × 5KB ≈ 30MB

API 文档:
  每个版本文档: ~100KB (渲染后的HTML)
  总大小: 6,000 × 100KB ≈ 600MB (CDN缓存)
```

## API设计 (元API - 管理API版本的API)

```protobuf
service APIVersionManagement {
  // API 定义管理
  rpc RegisterAPI(RegisterAPIRequest) returns (RegisterAPIResponse);
  rpc UpdateAPI(UpdateAPIRequest) returns (UpdateAPIResponse);

  // 版本管理
  rpc CreateVersion(CreateVersionRequest) returns (CreateVersionResponse);
  rpc DeprecateVersion(DeprecateVersionRequest) returns (DeprecateVersionResponse);
  rpc SunsetVersion(SunsetVersionRequest) returns (SunsetVersionResponse);

  // 查询
  rpc GetVersionInfo(GetVersionInfoRequest) returns (GetVersionInfoResponse);
  rpc ListVersions(ListVersionsRequest) returns (ListVersionsResponse);
  rpc GetChangelog(GetChangelogRequest) returns (GetChangelogResponse);
  rpc CheckCompatibility(CheckCompatibilityRequest) returns (CheckCompatibilityResponse);

  // 客户端追踪
  rpc TrackClientUsage(TrackClientUsageRequest) returns (TrackClientUsageResponse);
  rpc GetClientVersionDistribution(GetClientDistributionRequest) returns (GetClientDistributionResponse);
}

message CreateVersionRequest {
  string api_name = 1;           // "payment", "user", "order"
  string version = 2;            // "2024-06-15" (日期版本) 或 "v2" (语义化)
  string api_schema = 3;         // OpenAPI / Protobuf
  string previous_version = 4;   // 基于哪个版本创建
  repeated BreakingChange breaking_changes = 5;
}

message BreakingChange {
  string field_path = 1;         // 变更的字段路径
  ChangeType type = 2;           // FIELD_REMOVED / TYPE_CHANGED / REQUIRED_ADDED
  string description = 3;
  string migration_guide_url = 4;
}

message DeprecateVersionRequest {
  string api_name = 1;
  string version = 2;
  string deprecation_date = 3;   // 废弃公告日期
  string sunset_date = 4;        // 最终下线日期
  string replacement_version = 5; // 替代版本
  string deprecation_message = 6;
}

message CheckCompatibilityRequest {
  string api_name = 1;
  string old_version = 2;
  string new_version = 3;
}

message CheckCompatibilityResponse {
  bool is_backward_compatible = 1;
  repeated BreakingChange breaking_changes = 2;
}
```

### 版本标识方案

```
方案A: 语义化版本 (Semantic Versioning)
  格式: v{major}.{minor}.{patch}
  例: v1.2.3, v2.0.0
  路由: X-API-Version: v2

方案B: 日期版本 (Calendar Versioning) ⭐ 推荐
  格式: YYYY-MM-DD
  例: 2024-01-01, 2024-06-15
  路由: Stripe-Version: 2024-01-01
  优点: 直观体现时间线, 策略驱动

方案C: URL路径版本
  格式: /v1/payments, /v2/payments
  路由: URL解析
  缺点: URL膨胀, 不够灵活

方案D: Header + 日期
  格式: API-Version: 2024-06-15
  路由: 网关解析Header + 查版本映射表
  推荐用于内部API (解耦URL和版本)
```

## 数据模型

### MySQL 核心表

```sql
-- API 定义表
CREATE TABLE apis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_name VARCHAR(128) NOT NULL UNIQUE COMMENT '如: payment, user',
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_team VARCHAR(128) COMMENT '负责团队',
    api_type ENUM('REST','gRPC','GraphQL','WebSocket') NOT NULL,
    base_path VARCHAR(255) NOT NULL COMMENT '基本路径: /api/v1/payments',
    current_stable_version VARCHAR(32) COMMENT '当前稳定版本',
    status ENUM('ACTIVE','DEPRECATED','SUNSET') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- API 版本表
CREATE TABLE api_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_id BIGINT NOT NULL,
    version VARCHAR(32) NOT NULL,
    version_type ENUM('SEMVER','CALENDAR','CUSTOM') NOT NULL DEFAULT 'CALENDAR',
    schema_definition JSON NOT NULL COMMENT '完整的OpenAPI/Protobuf schema',
    previous_version VARCHAR(32) COMMENT '父版本',
    lifecycle_status ENUM('DRAFT','PREVIEW','STABLE','DEPRECATED','SUNSET') NOT NULL DEFAULT 'DRAFT',
    release_date DATE,
    deprecation_date DATE COMMENT '公告废弃日期',
    sunset_date DATE COMMENT '强制下线日期',
    deprecation_message TEXT,
    replacement_version VARCHAR(32),
    sunset_http_status INT DEFAULT 410 COMMENT '下线后的HTTP状态码',
    sunset_response_body JSON COMMENT '下线后的固定响应',
    changelog TEXT COMMENT '此版本相对于前一版本的变更说明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_api_version (api_id, version),
    INDEX idx_status_date (lifecycle_status, sunset_date)
) ENGINE=InnoDB;

-- 版本路由规则表
CREATE TABLE version_routing_rules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_id BIGINT NOT NULL,
    version VARCHAR(32) NOT NULL,
    route_type ENUM('HEADER','PATH','QUERY','DEFAULT') NOT NULL,
    match_pattern VARCHAR(128) COMMENT '匹配规则: header_name=value',
    target_service VARCHAR(255) NOT NULL COMMENT '目标服务名(K8s Service Name)',
    target_weight INT DEFAULT 100 COMMENT '流量权重(灰度)',
    priority INT DEFAULT 0 COMMENT '优先级(越小越高)',
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_api_version (api_id, version)
) ENGINE=InnoDB;

-- 版本变更日志
CREATE TABLE version_changelogs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_id BIGINT NOT NULL,
    from_version VARCHAR(32),
    to_version VARCHAR(32) NOT NULL,
    change_type ENUM('ADDED','MODIFIED','DEPRECATED','REMOVED','FIXED') NOT NULL,
    field_path VARCHAR(512) COMMENT '变更字段路径: response.data.payment_id',
    is_breaking TINYINT(1) DEFAULT 0 COMMENT '是否Breaking Change',
    description TEXT NOT NULL,
    migration_guide_url VARCHAR(512),
    operator VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_api_from_to (api_id, from_version, to_version)
) ENGINE=InnoDB;

-- 客户端使用追踪表
CREATE TABLE client_version_usage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_id BIGINT NOT NULL,
    client_id VARCHAR(128) NOT NULL COMMENT 'API Key / App ID',
    client_name VARCHAR(255),
    version_used VARCHAR(32) NOT NULL,
    request_count BIGINT DEFAULT 0 COMMENT '统计周期内的请求数',
    last_seen_at TIMESTAMP,
    stat_period VARCHAR(7) COMMENT '统计周期: 2024-01',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_client_version_period (client_id, api_id, version_used, stat_period),
    INDEX idx_api_version (api_id, version_used),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB;

-- 废弃通知记录
CREATE TABLE deprecation_notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_id BIGINT NOT NULL,
    version VARCHAR(32) NOT NULL,
    client_id VARCHAR(128),
    notification_channel ENUM('EMAIL','DASHBOARD','API_HEADER','WEBHOOK') NOT NULL,
    notification_content TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP COMMENT '客户端确认时间',
    INDEX idx_client_api (client_id, api_id)
) ENGINE=InnoDB;
```

### Redis 缓存结构

```
# 版本路由配置缓存 (热数据)
# Key: api:routing:{api_name}
# Type: Hash
# Fields: default_version, header_versions, url_versions

HSET api:routing:payment default_version "2024-06-15"
HSET api:routing:payment header_versions '{"API-Version:2024-01-01":{"target":"payment-svc-v1","status":"DEPRECATED"},"API-Version:2024-06-15":{"target":"payment-svc-v2","status":"STABLE"}}'

# 客户端版本缓存 (用于快速路由)
# Key: client:version:{client_id}:{api_name}
# Value: 使用的版本号
SET client:version:app_123:payment "2024-01-01"
EXPIRE client:version:app_123:payment 86400

# 版本生命周期事件
PUBLISH api:lifecycle:payment "{\"version\":\"2024-01-01\",\"action\":\"deprecated\",\"sunset\":\"2024-12-31\"}"
```

## 高层次架构

```
                         ┌──────────────────────────────┐
                         │      客户端 (SDK/调用方)       │
                         │  - API-Version: 2024-06-15   │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │        API Gateway            │
                         │  ┌─────────────────────────┐  │
                         │  │  版本解析与路由引擎       │  │
                         │  │                          │  │
                         │  │  1. 解析版本号           │  │
                         │  │  2. 查版本路由缓存        │  │
                         │  │  3. 检查生命周期状态      │  │
                         │  │  4. 路由到目标服务        │  │
                         │  │  5. 注入废弃警告Header   │  │
                         │  └────────────┬────────────┘  │
                         └───────────────┼───────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
┌───────▼────────┐              ┌───────▼────────┐              ┌───────▼────────┐
│ payment-svc-v1 │              │ payment-svc-v2 │              │ payment-svc-v3 │
│ Version:       │              │ Version:       │              │ Version:       │
│ 2024-01-01     │              │ 2024-06-15     │              │ 2024-12-01     │
│ Status:        │              │ Status:        │              │ Status:        │
│ DEPRECATED     │              │ STABLE         │              │ BETA           │
└────────────────┘              └────────────────┘              └────────────────┘
```

### 核心流程

```
请求处理流程:

1. 客户端请求到达: GET /api/payments/pay_123
   Headers: API-Version: 2024-01-01, Authorization: Bearer xxx

2. API Gateway 中间件:
   a. 认证 → 提取 client_id
   b. 版本解析:
      - 从 Header 提取版本号: 2024-01-01
      - 如果未指定 → 使用 client 的默认版本(从缓存/DB获取)
      - 如果client也未设置 → 使用API的current_stable_version
   c. 版本路由:
      - 查 Redis: api:routing:payment → header_versions
      - 找到: API-Version=2024-01-01 → payment-svc-v1
   d. 生命周期检查:
      - 状态 = DEPRECATED → 注入 Warning Header
      - 状态 = SUNSET → 返回 410 Gone + 迁移指南
   e. 转发请求到 payment-svc-v1
   f. 异步记录: 更新 client_version_usage (请求计数)
```

## 核心深入

### 版本路由策略详解

```python
class VersionRouter:
    """API 版本路由引擎"""

    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
        self.local_cache = {}  # 本地缓存，避免每次查Redis

    def resolve_target(self, api_name, request_version_header,
                        client_id=None) -> RouteResult:
        """解析目标服务"""

        # Step 1: 确定请求的版本号
        if request_version_header:
            version = request_version_header
        elif client_id:
            version = self._get_client_default_version(client_id, api_name)
        else:
            version = self._get_api_default_version(api_name)

        # Step 2: 查版本路由规则
        rules = self._get_routing_rules(api_name)

        # 精确匹配版本
        if version in rules['exact_versions']:
            rule = rules['exact_versions'][version]
        else:
            # 回退到默认版本
            rule = rules['default']

        # Step 3: 检查生命周期状态
        status = rule['lifecycle_status']

        warning_headers = {}
        if status == 'SUNSET':
            raise VersionSunsetException(
                http_status=rule.get('sunset_http_status', 410),
                sunset_date=rule['sunset_date'],
                replacement=rule.get('replacement_version'),
                message=rule.get('deprecation_message')
            )
        elif status == 'DEPRECATED':
            warning_headers = {
                'Warning': f'299 - "API version {version} is deprecated. '
                           f'Please migrate to {rule.get("replacement_version")}. '
                           f'Sunset date: {rule.get("sunset_date")}"',
                'Sunset': rule.get('sunset_date', ''),
                'Deprecation': 'true',
                'Link': f'</docs/migration/{api_name}>; rel="deprecation"'
            }

        return RouteResult(
            target_service=rule['target_service'],
            status=status,
            warning_headers=warning_headers,
            version=version
        )

    def _get_routing_rules(self, api_name):
        """获取路由规则(三级缓存)"""
        # L1: 本地内存缓存
        cache_key = f"api:routing:{api_name}"
        if cache_key in self.local_cache:
            return self.local_cache[cache_key]

        # L2: Redis
        rules_json = self.redis.get(cache_key)
        if rules_json:
            rules = json.loads(rules_json)
            self.local_cache[cache_key] = rules
            return rules

        # L3: MySQL
        rules = self._load_rules_from_db(api_name)
        self.redis.setex(cache_key, 300, json.dumps(rules))
        self.local_cache[cache_key] = rules
        return rules
```

### 废弃生命周期管理

```
版本生命周期状态机:

                    ┌─────────┐
                    │  DRAFT  │  内部开发中
                    └────┬────┘
                         │ 发布
                    ┌────▼────┐
                    │ PREVIEW │  公开预览(Beta)
                    └────┬────┘
                         │ 正式发布
                    ┌────▼────┐
                    │ STABLE  │  推荐使用的版本
                    └────┬────┘
                         │ 发布新版本 + 发布废弃公告
                    ┌────▼────┐
                    │DEPRECATE│  不再推荐, 发出废弃通知
                    │   D     │  响应中注入 Warning Header
                    └────┬────┘
                         │ 达到 sunset_date
                    ┌────▼────┐
                    │ SUNSET  │  完全下线
                    │         │  返回 410 Gone
                    └─────────┘
```

#### 废弃策略时间线

```
示例: payment API v2024-01-01 的废弃时间线

T-90天 (废弃公告日):
  ├── 状态变更为 DEPRECATED
  ├── 所有响应注入 Warning/Sunset Header
  ├── 发送邮件通知所有使用此版本的客户端
  ├── 管理控制台显示废弃横幅
  └── 监控 Dashboard 追踪迁移进度

T-60天:
  ├── 第二次提醒邮件
  └── 对未迁移的大客户进行电话/企业微信联系

T-30天:
  ├── 最终提醒
  ├── 速率限制: 限制此版本的请求速率(逐步降低)
  └── 随机注入延迟 (模拟不可用)

T+0天 (Sunset日):
  ├── 状态变更为 SUNSET
  ├── 所有请求返回 410 Gone
  └── 响应body包含迁移指南URL
```

### 兼容性检测引擎

```python
class CompatibilityChecker:
    """API 兼容性检测"""

    def check_backward_compatibility(self, old_schema, new_schema):
        """检查新版本是否向后兼容"""
        breaking_changes = []

        # 1. 检查字段删除
        removed_fields = self._find_removed_fields(old_schema, new_schema)
        for field in removed_fields:
            breaking_changes.append(BreakingChange(
                type='FIELD_REMOVED',
                field_path=field,
                description=f'字段 {field} 已被移除'
            ))

        # 2. 检查字段类型变更
        type_changes = self._find_type_changes(old_schema, new_schema)
        for field, (old_type, new_type) in type_changes.items():
            if not self._is_type_compatible(old_type, new_type):
                breaking_changes.append(BreakingChange(
                    type='TYPE_CHANGED',
                    field_path=field,
                    description=f'字段类型从 {old_type} 变为 {new_type}'
                ))

        # 3. 检查新增必填字段
        new_required = self._find_new_required_fields(old_schema, new_schema)
        for field in new_required:
            breaking_changes.append(BreakingChange(
                type='REQUIRED_ADDED',
                field_path=field,
                description=f'新增必填字段 {field}'
            ))

        # 4. 检查枚举值删除
        enum_changes = self._find_enum_changes(old_schema, new_schema)
        for field, removed_values in enum_changes.items():
            breaking_changes.append(BreakingChange(
                type='ENUM_VALUE_REMOVED',
                field_path=field,
                description=f'枚举值 {removed_values} 已移除'
            ))

        # 5. 检查URL路径变更
        if old_schema.get('path') != new_schema.get('path'):
            breaking_changes.append(BreakingChange(
                type='URL_CHANGED',
                field_path='__url__',
                description='API URL 路径变更'
            ))

        return CompatibilityResult(
            is_backward_compatible=len(breaking_changes) == 0,
            breaking_changes=breaking_changes
        )

    def _is_type_compatible(self, old_type, new_type):
        """类型兼容性矩阵"""
        compatible_pairs = {
            ('integer', 'number'): True,   # 放宽: int → float
            ('number', 'integer'): False,  # 收紧: float → int (Breaking!)
            ('string', 'number'): False,
            ('array<T>', 'array<U>'): self._is_type_compatible('T', 'U'),
        }
        return compatible_pairs.get((old_type, new_type), old_type == new_type)
```

### 向后兼容 vs 向前兼容

```
向后兼容 (Backward Compatible):
  新版本服务能处理旧版本客户端的请求
  客户端升级是可选的
  ✓ 添加新字段(可选)
  ✓ 添加新端点
  ✓ 放宽验证规则
  ✗ 删除字段
  ✗ 修改字段类型
  ✗ 修改URL路径

向前兼容 (Forward Compatible):
  旧版本服务能处理新版本客户端的请求
  服务端升级是可选的
  实现方式: 客户端只发送服务端能理解的字段
           (Protobuf默认支持, JSON需要服务端忽略未知字段)

推荐策略:
  ┌────────────────────────────────────────────────────────┐
  │ 只保证向后兼容 (Backward Compatible)                     │
  │ - 客户端侧升级是相对可控的                               │
  │ - 服务端升级前先发布新版本并存                            │
  │ - Breaking Change → 发新版本 + 废弃旧版本               │
  └────────────────────────────────────────────────────────┘
```

### 方案对比：版本策略

| 策略 | 实现方式 | 优点 | 缺点 |
|------|---------|------|------|
| 不做版本控制 | 直接修改API | 简单 | 无法兼容, 无法追踪 |
| URL版本 | /v1/ /v2/ | 直观, 易缓存 | URL膨胀, 不灵活 |
| Header版本 | API-Version头 | URL不变, 灵活 | 缓存需要包含Header |
| 日期版本 | 2024-06-15 | 时间线清晰 | 粒度粗(无法patch) |
| Stripe模式 | 日期+SDK固化 | 客户端可控 | 服务端要长期维护 |
| GraphQL | Schema字段 | 按需返回 | 版本在字段级过于细碎 |

**推荐**: Header + 日期版本 (内部API) 或 日期 + SDK固化 (对外API, Stripe模式)

## 扩展性与高可用

### 灰度迁移机制

```python
class GradualMigrationManager:
    """灰度迁移: 逐步将流量从旧版本切到新版本"""

    def route_with_migration(self, api_name, client_id, request_version):
        # 检查是否在迁移计划中
        migration = self.get_migration_plan(api_name)

        if migration and request_version == migration['from_version']:
            # 按百分比或客户端白名单决定是否使用新版本
            if self._should_migrate(client_id, migration):
                new_version = migration['to_version']
                # 记录"影子流量": 同时请求新旧版本, 对比响应
                if migration.get('shadow_mode'):
                    self._send_shadow_request(api_name, new_version, request)
                return self._route_to_version(api_name, new_version)

        return self._route_to_version(api_name, request_version)

    def _should_migrate(self, client_id, migration):
        """决定是否迁移"""
        # 白名单优先
        if client_id in migration.get('whitelist', []):
            return True
        # 黑名单跳过
        if client_id in migration.get('blacklist', []):
            return False
        # 百分比灰度
        percentage = migration.get('percentage', 0)
        if percentage >= 100:
            return True
        bucket = hash(client_id) % 100
        return bucket < percentage
```

### 自动废弃通知系统

```
通知渠道:
  ┌─────────────┐
  │ HTTP Header │  每次请求返回: Sunset + Deprecation + Warning
  └─────────────┘
  ┌─────────────┐
  │ Email       │  周期性发送(90/60/30天)给已注册客户端联系人
  └─────────────┘
  ┌─────────────┐
  │ Dashboard   │  管理控制台显示废弃提醒横幅
  └─────────────┘
  ┌─────────────┐
  │ Webhook     │  POST 到客户端注册的 Webhook URL
  └─────────────┘
  ┌─────────────┐
  │ SDK Warning │  SDK 日志中打印废弃警告
  └─────────────┘

Cron 调度:
  每天 00:00 检查所有 DEPRECATED 版本的 sunset_date
  距离 sunset_date:
    90天 → 第一轮通知
    60天 → 第二轮通知 + 升级为 WARNING 级别
    30天 → 最终通知 + 升级为 CRITICAL 级别
    7天  → 每日通知
    0天  → 自动切换为 SUNSET 状态
```

### 监控告警

| 指标 | 告警条件 |
|------|---------|
| 废弃版本使用比例 | 接近 sunset_date 但 >20% 仍在使用 |
| 版本路由延迟 | P99 > 5ms |
| 路由规则缓存命中率 | < 95% |
| 新版本错误率 | > 旧版本错误率 × 2 |
| 版本迁移速度 | 低于预期迁移曲线的 50% |

## 总结

1. **日期版本优于语义化**: Stripe/Google 的实践表明日期版本更直观、策略统一
2. **多版本并存**: 每个API维护 2-3 个活跃版本 (stable, deprecated, preview)
3. **三级路由缓存**: 本地内存 → Redis → MySQL, 路由解析 < 1ms
4. **结构化废弃流程**: 90天预告 → 响应Warning → 限流降级 → Sunset 410
5. **Breaking Change 定义**: 删除字段/修改类型/新增必填/改URL/删枚举值
6. **向后兼容优先**: 只要求向后兼容, Breaking Change 发新版本
7. **灰度迁移**: 按客户端百分比 + 白名单 + 影子流量逐步迁移
8. **客户端追踪**: 追踪每个客户端的版本使用, 为废弃决策提供数据支撑
9. **自动化通知**: 多通道(Header/Email/Dashboard/Webhook) + 时间线驱动
10. **兼容性检测**: Schema Diff 引擎自动检测Breaking Change

面试中可能追问: 如果必须做Breaking Change怎么办? 如何设计Stripe那样的"锁定"机制(客户端指定版本号后API永不变化)? GraphQL是否需要版本控制?
