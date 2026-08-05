# 设计CDN内容分发网络 (Design Content Delivery Network)

## 题目

设计一个全球内容分发网络(CDN)系统，类似 Cloudflare / Akamai / AWS CloudFront，支持静态和动态内容的全球低延迟分发、缓存、安全防护。

## 需求澄清

### 功能性需求

1. **内容缓存与分发**: 将源站内容缓存到边缘节点，用户就近访问
2. **缓存策略**: 支持TTL、Cache-Control、自定义缓存规则
3. **缓存清除 (Purge/Invalidate)**: 支持主动清除/失效缓存内容
4. **HTTPS 支持**: 边缘节点提供SSL/TLS终结 (SSL Termination)
5. **动态内容加速**: 对不可缓存动态请求，优化回源路径
6. **源站保护**: 隐藏源站IP，防止DDoS攻击
7. **访问控制**: IP黑白名单、Referer防盗链、Token鉴权、WAF(Web应用防火墙)
8. **流量统计与分析**: 实时带宽、请求数、缓存命中率、错误率
9. **自定义域名**: 支持客户绑定自己的域名

### 非功能性需求

- **低延迟**: 全球 < 100ms 首字节时间(TTFB)
- **高可用**: 99.99% (边缘节点多路冗)
- **高吞吐**: 单节点 > 10 Gbps, 全局 > 100 Tbps
- **高并发**: 单节点 > 100万 并发连接
- **快速失效**: 缓存清除 < 5秒 全球生效
- **弹性扩展**: 应对流量突增 (热门事件、DDoS)

### 容量估算

```
假设:
- 客户域名: 100万
- 边缘节点: 200 个 (全球主要城市)
- 日均PV: 1000亿
- 缓存命中率: 90%
- 平均内容大小: 200 KB (图片/JS/CSS/视频片段等)

QPS估算:
- 日均QPS = 1000亿 / 86400 ≈ 115万 QPS (平均)
- 峰值QPS ≈ 115万 × 5(高峰) ≈ 575万 QPS
- 其中缓存命中90% → 回源 QPS ≈ 57.5万 QPS

带宽估算:
- 日均流量: 1000亿 × 200KB = 20 PB/天
- 平均带宽: 20PB / 86400s ≈ 1.85 Tbps
- 峰值带宽: 1.85 Tbps × 5 ≈ 9.25 Tbps

存储估算 (每边缘节点缓存):
- 热内容(最近1小时): 1.85Tbps/8 × 3600s × 10% ≈ 83 TB (全部节点)
- 每节点: 83TB / 200 ≈ 415 GB
- SSD 容量: 2 TB/节点 (有余量)
```

## API设计

```protobuf
// ============ 配置管理 API (CDN控制台) ============

// 创建加速域名
// POST /api/v1/domains
message CreateDomainRequest {
  string domain = 1;                     // "cdn.example.com"
  string origin = 2;                     // "origin.example.com" 或 S3 bucket
  OriginProtocol origin_protocol = 3;     // HTTP, HTTPS, FOLLOW (跟随请求)
  int32 origin_port = 4;
  bool https_enabled = 5;
  string ssl_certificate_id = 6;         // 客户上传的证书ID
  repeated CacheRule cache_rules = 7;
  repeated AccessRule access_rules = 8;
}

message CacheRule {
  string path_pattern = 1;               // "*.jpg", "/images/*", "/api/*"
  int64 ttl_seconds = 2;                 // 缓存时间, 0=不缓存
  CacheBehavior behavior = 3;            // CACHE, BYPASS, ORIGIN_ONLY
  repeated string query_string_keys = 4; // 区分缓存的查询参数
  repeated string cookie_keys = 5;       // 区分缓存的Cookie
}

enum CacheBehavior {
  CACHE = 0;                             // 默认缓存
  BYPASS = 1;                            // 不缓存, 直接回源
  ORIGIN_ONLY = 2;                       // 遵循源站 Cache-Control
}

message AccessRule {
  string path_pattern = 1;
  repeated string allowed_ips = 2;       // IP白名单
  repeated string blocked_ips = 3;       // IP黑名单
  repeated string allowed_referers = 4;  // 防盗链白名单
  string token_auth_key = 5;             // URL Token鉴权密钥
  bool waf_enabled = 6;                  // 是否启用WAF
}

// ============ 缓存管理 API ============

// 缓存清除
// POST /api/v1/purge
message PurgeRequest {
  oneof target {
    string single_url = 1;               // 单个URL
    string prefix = 2;                   // 前缀匹配 "https://cdn.example.com/images/*"
    string host = 3;                     // 整个域名
    repeated string urls = 4;            // 批量URL
  }
  PurgeType type = 5;                    // INVALIDATE (软失效) / DELETE (硬删除)
}

enum PurgeType {
  INVALIDATE = 0;                        // 标记失效, 下次请求回源
  DELETE = 1;                            // 立即删除缓存文件
}

message PurgeResponse {
  string purge_id = 1;
  PurgeStatus status = 2;
}

// 查询缓存清除状态
// GET /api/v1/purge/{purge_id}
message PurgeStatus {
  string purge_id = 1;
  string status = 2;                     // "pending", "in_progress", "completed", "failed"
  int32 completed_nodes = 3;
  int32 total_nodes = 4;
}

// ============ 实时统计 API ============
// GET /api/v1/stats/realtime?domain=cdn.example.com&metric=bandwidth,requests,cache_hit_ratio

message RealtimeStats {
  string domain = 1;
  int64 timestamp_ms = 2;
  int64 bandwidth_bps = 3;               // 当前带宽(bps)
  int64 requests_per_second = 4;         // 当前QPS
  double cache_hit_ratio = 5;            // 缓存命中率 0-1
  map<int, int64> status_codes = 6;      // {200: 12345, 404: 23, 502: 5}
  map<string, int64> edge_bandwidth = 7; // {"LAX": 1000000, "LHR": 500000}
}
```

## 数据模型

### CDN 配置存储 (MySQL / PostgreSQL)

```sql
-- 域名配置表
CREATE TABLE cdn_domains (
    domain_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    domain_name VARCHAR(255) NOT NULL UNIQUE,
    origin_address VARCHAR(500) NOT NULL,     -- 源站地址
    origin_protocol ENUM('http','https','follow') DEFAULT 'https',
    origin_port INT DEFAULT 443,
    status ENUM('active','suspended','deleted') DEFAULT 'active',
    https_enabled BOOLEAN DEFAULT TRUE,
    ssl_certificate_id VARCHAR(64),
    ssl_certificate_path VARCHAR(500),        -- S3路径/Nginx cert路径
    ipv6_enabled BOOLEAN DEFAULT TRUE,
    http2_enabled BOOLEAN DEFAULT TRUE,
    quic_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer (customer_id),
    INDEX idx_status (status)
);

-- 缓存规则表
CREATE TABLE cache_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    domain_id VARCHAR(64) NOT NULL,
    path_pattern VARCHAR(500) NOT NULL,
    priority INT NOT NULL DEFAULT 0,         -- 优先级, 数值越大越优先
    ttl_seconds INT NOT NULL,                -- -1 = 不缓存, 0 = 源站决定
    behavior ENUM('cache','bypass','origin_only') DEFAULT 'cache',
    query_string_keys JSON,                  -- ["v","t"] 只保留指定参数
    cookie_keys JSON,
    status ENUM('active','disabled') DEFAULT 'active',
    INDEX idx_domain (domain_id)
);

-- 访问控制规则表
CREATE TABLE access_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    domain_id VARCHAR(64) NOT NULL,
    path_pattern VARCHAR(500) NOT NULL,
    priority INT NOT NULL DEFAULT 0,
    rule_type ENUM('ip_whitelist','ip_blacklist','referer','token_auth','geo_block','waf'),
    rule_config JSON NOT NULL,               -- {"ips":[], "key":"", "country_codes":[]}
    status ENUM('active','disabled') DEFAULT 'active',
    INDEX idx_domain (domain_id)
);

-- 缓存清除任务表
CREATE TABLE purge_tasks (
    purge_id VARCHAR(64) PRIMARY KEY,
    domain_id VARCHAR(64) NOT NULL,
    target_type ENUM('url','prefix','host','batch'),
    target_value TEXT NOT NULL,
    status ENUM('pending','in_progress','completed','failed') DEFAULT 'pending',
    completed_nodes INT DEFAULT 0,
    total_nodes INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_status (status)
);

-- 流量统计表 (T+1聚合)
CREATE TABLE traffic_stats_hourly (
    stat_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    domain_id VARCHAR(64) NOT NULL,
    edge_node VARCHAR(64) NOT NULL,           -- "LAX-01", "LHR-01"
    stat_hour TIMESTAMP NOT NULL,
    total_requests BIGINT DEFAULT 0,
    cache_hits BIGINT DEFAULT 0,
    cache_misses BIGINT DEFAULT 0,
    bandwidth_bytes BIGINT DEFAULT 0,         -- 出流量
    origin_bandwidth_bytes BIGINT DEFAULT 0,  -- 回源流量
    status_2xx BIGINT DEFAULT 0,
    status_3xx BIGINT DEFAULT 0,
    status_4xx BIGINT DEFAULT 0,
    status_5xx BIGINT DEFAULT 0,
    INDEX idx_domain_hour (domain_id, stat_hour),
    INDEX idx_node_hour (edge_node, stat_hour)
) ENGINE=InnoDB;
```

## 高层次架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CDN 全球架构                                      │
│                                                                         │
│                        ┌──────────────────┐                              │
│                        │   CDN 控制台      │                              │
│                        │  (Web Console)    │                              │
│                        └────────┬─────────┘                              │
│                                 │                                        │
│                        ┌────────▼─────────┐                              │
│                        │  Configuration    │                              │
│                        │  Center (主控)    │                              │
│                        └────────┬─────────┘                              │
│                                 │                                        │
│              ┌──────────────────┼──────────────────┐                     │
│              │                  │                  │                     │
│              ▼                  ▼                  ▼                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐            │
│  │   北美区域       │ │   欧洲区域       │ │   亚太区域       │            │
│  │  (PoP Cluster)  │ │  (PoP Cluster)  │ │  (PoP Cluster)  │            │
│  │                 │ │                 │ │                 │            │
│  │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │            │
│  │  │ 边缘节点   │  │ │  │ 边缘节点   │  │ │  │ 边缘节点   │  │            │
│  │  │ LAX × 4   │  │ │  │ LHR × 4   │  │ │  │ NRT × 4   │  │            │
│  │  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │            │
│  │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │            │
│  │  │ 边缘节点   │  │ │  │ 边缘节点   │  │ │  │ 边缘节点   │  │            │
│  │  │ SJC × 4   │  │ │  │ AMS × 4   │  │ │  │ SIN × 4   │  │            │
│  │  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │            │
│  │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │            │
│  │  │ 边缘节点   │  │ │  │ 边缘节点   │  │ │  │ 边缘节点   │  │            │
│  │  │ IAD × 4   │  │ │  │ FRA × 4   │  │ │  │ HKG × 4   │  │            │
│  │  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │            │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘            │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      中间层 (Shield / Mid-Tier)                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │  │
│  │  │ Shield North    │  │ Shield Europe   │  │ Shield Asia     │   │  │
│  │  │ America         │  │                 │  │                 │   │  │
│  │  │ 减少回源压力     │  │ 缓存父层        │  │                 │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│                      回源请求 (仅Cache Miss)                              │
│                                 │                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        客户源站 (Origin)                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │ Customer A   │  │ S3 Bucket    │  │ Customer B   │            │  │
│  │  │ Nginx/ALB    │  │ (静态网站)    │  │ K8s Ingress  │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 请求处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    单个边缘节点处理流程                            │
│                                                                 │
│  客户端请求                                                      │
│     │                                                           │
│     ▼                                                           │
│  ┌────────────────┐                                              │
│  │   DNS解析      │  GeoDNS → 最近PoP → IP Anycast           │
│  │   到达边缘节点  │                                              │
│  └───────┬────────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────┐                                              │
│  │ L4 LB (BGP/    │  DDoS防护 → SYN Proxy → 清洗                 │
│  │  Anycast)      │                                              │
│  └───────┬────────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────┐                                              │
│  │ Nginx/ATS/     │  SSL Termination → HTTP/2 → WebSocket      │
│  │ Varnish        │  WAF 规则检查                                │
│  └───────┬────────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────┐    ┌────────────────────┐                    │
│  │  缓存查找       │───►│ Cache Hit (90%)     │──→ 直接返回      │
│  │  (SSD/RAM)     │    └────────────────────┘                    │
│  │                │                                              │
│  │                │    ┌────────────────────┐                    │
│  │                │───►│ Cache Miss (10%)    │                    │
│  └───────┬────────┘    └─────────┬──────────┘                    │
│          │                       │                                │
│          │                       ▼                                │
│          │            ┌────────────────────┐                      │
│          │            │  父缓存层查询       │                      │
│          │            │  (Shield/Mid-Tier) │──→ Hit → 返回       │
│          │            └─────────┬──────────┘                      │
│          │                      │ Miss                            │
│          │                      ▼                                 │
│          │            ┌────────────────────┐                      │
│          │            │  回源请求           │                      │
│          │            │  Origin Shield      │                      │
│          │            │  合并并发回源        │                      │
│          │            │  (Request Coalescing)│                     │
│          │            └─────────┬──────────┘                      │
│          │                      │                                 │
│          │                      ▼                                 │
│          │            ┌────────────────────┐                      │
│          │            │  客户源站           │                      │
│          │            └────────────────────┘                      │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────┐                                              │
│  │  日志/指标上报  │  → Kafka → 日志系统 / 仪表盘                  │
│  └────────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 核心深入

### 1. 缓存策略与LRU/LFU

```
┌────────────────────────────────────────────────────────────────┐
│                    缓存淘汰策略                                  │
│                                                                │
│  缓存存储层次:                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  L1: RAM (Nginx in-memory cache / Varnish malloc)        │  │
│  │       容量: 32-128 GB/节点                                │  │
│  │       对象: 超热点内容 (图标, CSS, JS)                     │  │
│  │       TTL: 根据 Cache-Control, 默认短TTL                  │  │
│  │                                                          │  │
│  │  L2: SSD/NVMe (Nginx proxy_cache / ATS disk cache)       │  │
│  │       容量: 2-8 TB/节点                                    │  │
│  │       对象: 温热内容 (图片, 视频片段, HTML)                 │  │
│  │       淘汰算法: 分段LRU (Segmented LRU)                    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  分段 LRU (Segmented LRU) 算法:                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  ┌──────────────────┐     ┌──────────────────┐           │  │
│  │  │  Protected (热)   │     │  Probation (温)   │           │  │
│  │  │  ─────────────── │     │  ─────────────── │           │  │
│  │  │  被访问过2次以上   │     │  被访问过1次       │           │  │
│  │  │  容量: 80%        │     │  容量: 20%        │           │  │
│  │  └────────┬─────────┘     └────────┬─────────┘           │  │
│  │           │                        │                      │  │
│  │           │    首次访问             │                      │  │
│  │   对象  ──┼────────────────────────►│                      │  │
│  │           │                        │                      │  │
│  │           │     再次访问             │                      │  │
│  │           │◄────────────────────────│                      │  │
│  │           │                        │                      │  │
│  │  淘汰: 从Protected队尾移到Probation头部                     │  │
│  │         Probation满 → 淘汰 Probation队尾                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  TTL 与 LRU 的关系:                                             │
│  - TTL 为主: Cache-Control: max-age=3600 → 1小时后必过期        │
│  - LRU 为辅: 缓存满了, 即使TTL未到也淘汰冷数据                   │
│  - 预取 (Prefetch): 预测热点内容提前缓存                         │
└────────────────────────────────────────────────────────────────┘
```

### 2. GeoDNS 与路由策略

```
┌────────────────────────────────────────────────────────────────┐
│                  全球流量调度 (GSLB)                             │
│                                                                │
│  GeoDNS 原理:                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  用户 DNS 请求: "cdn.example.com"                         │  │
│  │     │                                                    │  │
│  │     ▼                                                    │  │
│  │  ┌───────────────────────────────────────┐               │  │
│  │  │         GeoDNS Server                 │               │  │
│  │  │  (根据请求来源IP查GeoIP数据库)          │               │  │
│  │  │                                       │               │  │
│  │  │  IP来自 东京 → 返回 NRT节点 IP         │               │  │
│  │  │  IP来自 伦敦 → 返回 LHR节点 IP         │               │  │
│  │  │  IP来自 纽约 → 返回 EWR节点 IP         │               │  │
│  │  └───────────────────────────────────────┘               │  │
│  │                                                          │  │
│  │  进阶策略:                                                 │  │
│  │  1. Geo + Latency: 测速+地理位置综合判断                   │  │
│  │  2. Geo + Health: 节点不健康时自动切换                     │  │
│  │  3. Geo + Capacity: 节点过载时分摊到其他节点               │  │
│  │  4. Geo + Cost: 带宽成本低的节点优先                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Anycast BGP (选路层面):                                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  - 多个PoP广播相同IP段                                         │
│  - BGP协议自动计算最短AS Path                                  │
│  - 网络层自动选择最近PoP                                       │
│  - 结合 GeoDNS 实现双层路由: DNS层 + 网络层                    │
└────────────────────────────────────────────────────────────────┘
```

### 3. 缓存清除 (Purge / Invalidation)

```
┌────────────────────────────────────────────────────────────────┐
│                  缓存清除机制                                    │
│                                                                │
│  挑战: 200个边缘节点, 全球消息送达 < 5秒                         │
│                                                                │
│  清除流程:                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  ┌──────────────┐                                         │  │
│  │  │ 管理控制台    │  用户提交清除请求                        │  │
│  │  │ Purge URL    │                                         │  │
│  │  └──────┬───────┘                                         │  │
│  │         │                                                 │  │
│  │         ▼                                                 │  │
│  │  ┌──────────────┐                                         │  │
│  │  │ API Server   │  创建Purge Task, 投递到消息队列           │  │
│  │  └──────┬───────┘                                         │  │
│  │         │                                                 │  │
│  │         ▼                                                 │  │
│  │  ┌──────────────────────────────────────────┐            │  │
│  │  │        消息广播 (Purge Bus)               │            │  │
│  │  │                                          │            │  │
│  │  │  方案1: 星形推送 (Central → All Nodes)    │            │  │
│  │  │    - 中心向所有节点推送消息               │            │  │
│  │  │    - 简单但中心压力大                     │            │  │
│  │  │                                          │            │  │
│  │  │  方案2: Pub/Sub (Kafka/Redis)            │            │  │
│  │  │    - 所有节点订阅清除Topic                │            │  │
│  │  │    - 消息投递后节点自行消费               │            │  │
│  │  │    - 可扩展但需要各区域部署Broker         │            │  │
│  │  │                                          │            │  │
│  │  │  方案3: 树状分发 (Tree-based) - 推荐     │            │  │
│  │  │    ┌──────────────────────────┐         │            │  │
│  │  │    │      Master              │         │            │  │
│  │  │    │   ┌──────┴──────┐        │         │            │  │
│  │  │    │   US-West    EU-Ctrl     │         │            │  │
│  │  │    │  ┌──┴──┐   ┌──┴──┐       │         │            │  │
│  │  │    │  LAX SJC  LHR AMS       │         │            │  │
│  │  │    │   到各PoP的Edge节点      │         │            │  │
│  │  │    └──────────────────────────┘         │            │  │
│  │  │    - 层层转发, 降低中心压力              │            │  │
│  │  └──────────────────────────────────────────┘            │  │
│  │                                                          │  │
│  │  Purge执行方式:                                           │  │
│  │  1. Soft Purge (推荐): 标记失效, 请求时回源更新           │  │
│  │     - 不删除文件, 只修改元数据                            │  │
│  │     - 速度快, IO开销小                                    │  │
│  │  2. Hard Purge: 物理删除缓存文件和内存对象                 │  │
│  │     - 彻底但IO开销大                                      │  │
│  │  3. Purge by Tag: 按标签批量失效                          │  │
│  │     - 如 "v2", "product-images"                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 4. 请求合并 (Request Coalescing)

```
┌────────────────────────────────────────────────────────────────┐
│               请求合并 (Request Coalescing)                      │
│                                                                │
│  问题: 热门内容缓存过期瞬间 → 1000个请求同时回源                 │
│  → 源站被打爆 (Thundering Herd / 惊群效应)                       │
│                                                                │
│  解决方案: 请求合并 (Collapsed Forwarding)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │                                                     │  │  │
│  │  │  请求1 ──►                                      │  │  │
│  │  │  请求2 ──►  Cache Miss ──► 看是否已有进行中的│  │  │
│  │  │  请求3 ──►                 回源请求                    │  │  │
│  │  │  ...                                                   │  │  │
│  │  │  请求1000──►                                           │  │  │
│  │  │                                                     │  │  │
│  │  │  有 ──► 等待该请求完成 ──► 共享结果 ──► 返回给所有等待者│  │  │
│  │  │  无 ──► 发起唯一回源请求 ──► 缓存结果 ──► 返回        │  │  │
│  │  │                                                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  实现 (Nginx/Varnish/Apache Traffic Server):               │  │
│  │  - 为每个正在回源的URL维护一个等待队列                      │  │
│  │  - 使用 CondVar / Channel 等待                             │  │
│  │  - 第一个请求实际回源, 后续请求park等待                     │  │
│  │  - 回源完成 → unpark所有等待者 → 返回同一份数据            │  │
│  │                                                          │  │
│  │  伪代码:                                                  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ lock(pending_mutex)                                 │ │  │
│  │  │ if cache_key in pending_requests:                    │ │  │
│  │  │     waiter = register_waiter(cache_key)              │ │  │
│  │  │     unlock(pending_mutex)                            │ │  │
│  │  │     data = wait_for_result(waiter)  // 阻塞等待       │ │  │
│  │  │     return data                                      │ │  │
│  │  │                                                     │ │  │
│  │  │ pending_requests.add(cache_key)                      │ │  │
│  │  │ unlock(pending_mutex)                                │ │  │
│  │  │                                                     │ │  │
│  │  │ data = fetch_origin(url)                             │ │  │
│  │  │ cache_set(cache_key, data)                           │ │  │
│  │  │ notify_all_waiters(cache_key, data)                  │ │  │
│  │  │ pending_requests.remove(cache_key)                   │ │  │
│  │  │ return data                                          │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5. Origin Shield (父缓存层)

```
┌────────────────────────────────────────────────────────────────┐
│                Origin Shield (父缓存层)                         │
│                                                                │
│  问题: 200个边缘节点, 每个cache miss都回源 → 源站扛不住         │
│                                                                │
│  解决: 增加一层父缓存 (Shield/Mid-tier)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  没有Shield:                                              │  │
│  │                                                          │  │
│  │  Edge1 (LAX) ──miss──►                          │  │
│  │  Edge2 (SJC) ──miss──►    Origin               │  │
│  │  Edge3 (IAD) ──miss──►    (200次回源/秒)         │  │
│  │  Edge4 (LHR) ──miss──►                          │  │
│  │  ...                                                    │  │
│  │                                                          │  │
│  │  有Shield:                                                │  │
│  │                                                          │  │
│  │  Edge1 (LAX) ──miss──►  Shield US-East (仅1次miss回源)  │  │
│  │  Edge2 (SJC) ──miss──►     │                              │  │
│  │  Edge3 (IAD) ──miss──►     │   cache hit → 返回          │  │
│  │                           │                              │  │
│  │                     Shield miss → Origin (仅1次回源)     │  │
│  │                                                          │  │
│  │  效果: 200次回源 → 1次回源 (减少 99.5%)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Shield 拓扑 (每个大区1-2个):                                    │
│  - 北美: Shield-US-East, Shield-US-West                       │
│  - 欧洲: Shield-EU (Frankfurt)                                │
│  - 亚太: Shield-APAC (Singapore / Tokyo)                      │
│                                                                │
│  Shield 节点存储: 大容量SSD, 专门缓存中频内容                    │
└────────────────────────────────────────────────────────────────┘
```

### 6. 安全防护 (DDoS / WAF / Bot)

```
┌────────────────────────────────────────────────────────────────┐
│                    安全防护体系                                  │
│                                                                │
│  1. DDoS 防护 (L3/L4):                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  - Anycast: 攻击流量分散到全球所有PoP                            │
│  - SYN Proxy: 拦截SYN Flood, 完成握手后才转发                   │
│  - 流量清洗: 识别攻击模式, drop恶意包                            │
│  - 限速: 每源IP 每域名 限制 RPS                                 │
│                                                                │
│  2. DDoS 防护 (L7):                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  - JS Challenge (Cloudflare): 检测浏览器环境                    │
│  - CAPTCHA: 人机验证                                          │
│  - Rate Limiting: Token Bucket / Leaky Bucket                 │
│  - 特征匹配: 识别异常 User-Agent / 请求模式                     │
│                                                                │
│  3. WAF (Web Application Firewall):                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - SQL注入检测: 正则 + 语义分析                            │  │
│  │  - XSS检测: 输出编码, CSP策略                              │  │
│  │  - OWASP Top 10 规则                                     │  │
│  │  - 自定义规则 (ModSecurity 兼容)                           │  │
│  │  - 处理速度: Nginx + LuaJIT (OpenResty) 或 WAF模块       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  4. Bot 管理:                                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  - Good Bots (爬虫): 允许, 但限速                               │
│  - Bad Bots (撞库/刷票): 机器学习模型识别 + 拦截                │
│  - Fingerprinting: 浏览器指纹识别                              │
└────────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### 边缘节点高可用

```
┌──────────────────────────────────────────────────────────────┐
│              边缘节点 (PoP) 内部架构                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                     PoP (e.g., LAX)                      │  │
│  │                                                          │  │
│  │                  ┌──────────────┐                         │  │
│  │                  │  BGP Router  │ × 2 (主备)              │  │
│  │                  │  Anycast IP  │                         │  │
│  │                  └──────┬───────┘                         │  │
│  │                         │                                 │  │
│  │                  ┌──────▼───────┐                         │  │
│  │                  │  L4 LB       │ × 2 (主备)              │  │
│  │                  │  (ECMP分发)  │                         │  │
│  │                  └──────┬───────┘                         │  │
│  │                         │                                 │  │
│  │     ┌───────────────────┼───────────────────┐             │  │
│  │     │                   │                   │             │  │
│  │  ┌──▼──┐            ┌──▼──┐            ┌──▼──┐          │  │
│  │  │Edge │            │Edge │            │Edge │          │  │
│  │  │Svr 1│            │Svr 2│            │Svr N│          │  │
│  │  │     │            │     │            │     │          │  │
│  │  │ ┌──┐│            │ ┌──┐│            │ ┌──┐│          │  │
│  │  │ │NVMe│            │ │NVMe│           │ │NVMe│          │  │
│  │  │ └──┘│            │ └──┘│            │ └──┘│          │  │
│  │  └─────┘            └─────┘            └─────┘          │  │
│  │                                                          │  │
│  │  每台Edge Server运行:                                     │  │
│  │  - Nginx/ATS (HTTP反向代理)                               │  │
│  │  - Varnish/ATS (缓存引擎)                                 │  │
│  │  - Health Check Agent                                    │  │
│  │  - Stats Collector                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  PoP 高可用:                                                   │
│  - 单PoP内多台服务器 (4-16台)                                  │
│  - 同一PoP内多服务器健康检查 + L4 LB自动踢掉故障节点            │
│  - PoP故障 → GeoDNS 将该PoP从解析列表移除                     │
│  - 用户自动 fallback 到次近PoP                                 │
└──────────────────────────────────────────────────────────────┘
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 边缘代理 | Nginx/OpenResty | 高性能, 生态丰富(Lua脚本) |
| 缓存引擎 | ATS(Apache Traffic Server)或Varnish | 磁盘缓存, 分段LRU |
| 缓存存储 | RAM(L1) + NVMe SSD(L2) | 热冷分层 |
| 全球路由 | GeoDNS + Anycast BGP | 双层路由, 就近接入 |
| 缓存清除 | 树状消息分发 + Soft Purge | 低延迟, 全球5秒生效 |
| 请求合并 | Collapsed Forwarding | 防止惊群效应 |
| 父缓存层 | Origin Shield (区域性) | 大幅减少回源 |
| 安全防护 | SYN Proxy + WAF + RateLimit | 多层DDoS防护 |
| 日志分析 | Kafka + ClickHouse + Grafana | 实时分析 + 长期存储 |

核心设计要点:
1. **分层缓存是核心**: 边缘(L1) → Shield(L2) → Origin, 每层减少回源量级
2. **GeoDNS + Anycast 实现全球就近接入**: DNS和BGP两层智能路由
3. **Request Coalescing 是必备**: 节点级别的请求合并防止惊群回源
4. **Purge 是难点**: 200+节点全球同步, 需要树状分发 + 快速消息投递
5. **Origin Shield 大幅降本**: 90%边缘miss可在Shield命中, 回源只10%
6. **安全集成**: CDN既是加速方案也是安全方案, WAF+DDoS防护一体
