# 题目：Design a URL Shortener (TinyURL)

## 需求澄清（Requirement Clarification）

### 功能需求
1. 给定一个长 URL，系统生成一个唯一短链接。
2. 用户访问短链接时，系统将其重定向到原始长 URL。
3. 短链接支持自定义别名（可选，如 `short.url/myalias`）。
4. 短链接可设置过期时间（默认不过期）。
5. 用户可选短链接生命周期，到期后自动失效。
6. 提供访问统计：点击次数、来源、设备信息（可选）。
7. 提供 API 供第三方集成。

### 非功能需求
- **高可用**：服务需 99.99% 可用，重定向响应必须低延迟。
- **低延迟**：重定向操作 < 50ms（P99）。
- **持久性**：短链接一经创建不可丢失。
- **扩展性**：支持每天十亿级的短链接创建。
- **一致性**：同一长链接生成同一短链接（去重）或每次生成新短链接（需明确策略）。

### 容量估算
- **写入**：假设每日生成 100M 短链接 = 100M / (24 × 3600) ≈ 1160 QPS（写入峰值 ×3 ≈ 3500 QPS）。
- **读取**：假设读写比 100:1，读取 QPS ≈ 3500 × 100 = 350K QPS。
- **存储**：每条记录约 1KB（URL + 元数据 + 索引），100M/天 × 365 天 × 5 年 ≈ 182.5B 条 ≈ 182.5TB。考虑副本 ×3 ≈ 547TB。
- **带宽**：350K QPS × 500B/响应 ≈ 175MB/s 出站。

---

## 系统接口（API Design）

### 1. 创建短链接
```
POST /api/v1/urls
Content-Type: application/json

Request:
{
  "long_url": "https://www.example.com/very/long/url/...",
  "custom_alias": "myalias",         // 可选
  "expire_at": "2026-12-31T23:59:59Z" // 可选
}

Response 201:
{
  "short_url": "https://short.url/abc123",
  "long_url": "https://www.example.com/very/long/url/...",
  "expire_at": null,
  "created_at": "2026-07-30T10:00:00Z"
}
```

### 2. 重定向
```
GET /api/v1/urls/{short_key}

Response 302 Found:
Location: https://www.example.com/very/long/url/...

// 短链接不存在时
Response 404:
{
  "error": "Short URL not found"
}

// 短链接已过期时
Response 410 Gone:
{
  "error": "Short URL has expired"
}
```

### 3. 获取统计信息
```
GET /api/v1/urls/{short_key}/stats

Response 200:
{
  "short_key": "abc123",
  "total_clicks": 102345,
  "created_at": "...",
  "last_accessed": "..."
}
```

### 4. 删除短链接
```
DELETE /api/v1/urls/{short_key}
Authorization: Bearer <token>

Response 204 No Content
```

---

## 数据模型（Data Model）

### 主表：short_urls

| 字段 | 类型 | 描述 |
|------|------|------|
| id | BIGINT (PK) | 自增主键（用于 Base62 编码） |
| short_key | VARCHAR(10) (UNIQUE) | 短链接标识 |
| long_url | TEXT | 原始长 URL |
| long_url_hash | VARCHAR(64) (INDEX) | 长 URL 哈希（用于去重查询） |
| user_id | BIGINT | 创建者 ID（可选） |
| expire_at | TIMESTAMP NULL | 过期时间 |
| created_at | TIMESTAMP | 创建时间 |
| status | TINYINT | 0=正常, 1=已删除, 2=已过期 |

### 统计表：click_stats（可选，分表存储）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | BIGINT (PK) | 主键 |
| short_key | VARCHAR(10) | 关联短链接 |
| timestamp | TIMESTAMP | 点击时间 |
| ip | VARCHAR(45) | 访问者 IP |
| user_agent | VARCHAR(512) | User Agent |
| referer | VARCHAR(2048) | 来源页面 |

### 索引策略
- `short_key` 哈希索引（等值查询，重定向核心路径）。
- `long_url_hash` 索引（创建时去重检查）。
- `expire_at` 索引（定期清理过期数据）。
- `(user_id, created_at)` 联合索引（用户查询自己的短链接）。

### SQL vs NoSQL 选择

**推荐：SQL（MySQL/PostgreSQL）+ Redis 缓存**

理由：
- 短链接数据为结构化数据，关联性强（用户、统计），天然适合关系模型。
- 重定向查询路径短、等值查询为主，SQL 哈希索引足够高效。
- 创建时需要去重检查，事务能保证一致性。
- 若需超大规模水平扩展，可参考 NoSQL 的分片思路对 MySQL 分库分表（按 short_key 哈希分片）。

---

## 架构设计（High-Level Design）

### 架构图（ASCII）

```
                    ┌─────────────┐
                    │   CDN/DNS   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Load Balancer│
                    └──┬───────┬──┘
                       │       │
              ┌────────▼─┐  ┌──▼──────────┐
              │  API Server│  │ Redirect    │
              │  (Create)  │  │ Server      │
              └──┬─────┬──┘  └──┬──────┬───┘
                 │     │        │      │
         ┌───────▼─┐ ┌─▼────┐   │      │
         │  MySQL   │ │Redis │◄──┘      │
         │(Sharded) │ │Cache │          │
         └──────────┘ └──────┘   ┌──────▼─────┐
                                 │  Kafka      │
                                 │ (Click Log) │
                                 └──────┬──────┘
                                        │
                                 ┌──────▼──────┐
                                 │  Click Stats│
                                 │  Processor  │
                                 └──────┬──────┘
                                        │
                                 ┌──────▼──────┐
                                 │  OLAP DB    │
                                 │ (ClickHouse)│
                                 └─────────────┘
```

### 组件职责

| 组件 | 职责 |
|------|------|
| **Load Balancer** | 将流量分发到 API 和 Redirect 服务实例 |
| **API Server** | 处理短链接的创建、删除、更新操作；调用 ID 生成服务；写入主库 |
| **Redirect Server** | 处理重定向请求；先查 Redis 缓存，未命中则查 MySQL |
| **Redis Cluster** | 缓存热点短链接（short_key → long_url），TTL 策略降低内存占用 |
| **MySQL（分片）** | 持久存储所有短链接数据，按 short_key 一致性哈希分片 |
| **Kafka** | 异步收集点击事件，解耦重定向与统计 |
| **Click Stats Processor** | 消费 Kafka 消息，聚合统计写入 ClickHouse |
| **ClickHouse（OLAP）** | 存储聚合统计，支持高效分析查询 |

---

## 深入探讨（Deep Dive）

### 1. 短链接生成算法对比

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **MD5/SHA256 截断** | 对 long_url 计算哈希，取前 7 位 | 无需全局 ID 服务，分布式友好 | 碰撞风险；同一 URL 每次生成可能不同 |
| **UUID 截取** | 生成 UUID，取前 7 位 | 碰撞概率低 | 长度较长，可读性差 |
| **自增 ID + Base62** | 维护全局自增 ID，用 Base62 编码 | 无碰撞；可解码反推 ID；长度可控 | 需要全局 ID 生成器（单点/分布式 ID） |
| **随机字符串生成** | 随机生成 N 位字母数字 | 实现简单 | 需检查重复，随数据量增长性能下降 |

**推荐方案：自增 ID + Base62 编码**

- Base62 字符集：`[0-9, a-z, A-Z]`，共 62 个字符。
- 7 位 Base62 可表示 62^7 ≈ 3.5 万亿个不同短链接，足够使用。
- 分布式 ID 生成可使用 **Snowflake 算法**，跨机房无冲突，高位带时间戳信息。
- 编码流程：Snowflake ID（64bit）→ 十进制整数 → 循环除以 62 取余 → 映射字符 → 不足 7 位左侧补 `0`。
- 去重策略：对 long_url 计算 SHA256，存入 `long_url_hash` 字段建唯一索引；创建前先查询，命中则返回已有短链接，减少冗余存储。

### 2. 缓存策略

- **写穿（Write-Through）**：创建短链接时同时写入 Redis，保证首次访问也能命中缓存。
- **LRU 淘汰 + TTL**：内存有限，采用 Redis 的 `allkeys-lru` 淘汰策略 + 每个 key 设置 7 天 TTL。热门链接持续被访问会刷新 TTL（lazy expiration + touch 机制）。
- **布隆过滤器**：在缓存前加一层布隆过滤器，快速过滤不存在的短链接请求（防止缓存穿透攻击）。
- **缓存预热**：新创建短链接写入缓存；服务启动或扩容时从 DB 回导热门数据。

### 3. 分库分表策略

- **分片键**：选择 `short_key` 的哈希值（如 CRC32 取模 64）。
- **分片数量**：预设 64 个逻辑分片，每个分片对应一个 MySQL 实例或一个数据库。
- **路由逻辑**：`shard_index = hash(short_key) % 64`，应用层通过中间件（如 ShardingSphere）或 SDK 路由。
- **扩容方案**：一致性哈希 + 虚拟节点，或在预设分片充足时逐步迁移。
- **跨分片查询**：按 `long_url_hash` 去重时需广播查询所有分片——优化为维护一个独立的去重辅助索引表（分片数可少一些，如 4 分片）；或使用 Redis 集中式去重。

---

## 扩展与高可用

### 水平扩展
- **API / Redirect Server**：无状态服务，通过负载均衡器水平扩展，K8s HPA 自动伸缩。
- **MySQL**：分片后每个分片可独立扩展读写分离（一主多从），读流量打到从库。
- **Redis**：Redis Cluster 模式自动分片，增加节点即可扩容。

### 故障转移
- **MySQL**：主库故障时自动将从库提升为主库（MHA/Orchestrator）。
- **Redis**：Sentinel 监控主节点，自动故障转移。Cluster 模式下每个分片一主多从。
- **应用层**：数据库连接池配置重试 + 熔断（Hystrix/Sentinel），下游不可用时快速失败。
- **多机房部署**：两地三中心，主库跨机房同步，Redis 异步复制。

### 数据备份与恢复
- **MySQL**：全量备份（每日）+ Binlog 增量备份（实时），可回滚到任意时间点。
- **Redis**：RDB 快照（每小时）+ AOF 持久化（每秒刷盘），防止断电丢失。
- **灾难恢复演练**：定期从备份恢复至预发布环境，验证数据完整性。

---

## 总结

### 关键设计决策回顾
1. **短链接生成**：采用分布式 ID（Snowflake）+ Base62 编码，兼顾性能与唯一性。
2. **去重策略**：SHA256 哈希 + 数据库唯一索引，先查后写。
3. **缓存架构**：Redis 集群 + 布隆过滤器 + 写穿策略，保证重定向 P99 < 10ms。
4. **存储分片**：按 short_key 哈希分片 MySQL，一致性哈希支持弹性扩容。
5. **统计解耦**：点击事件通过 Kafka 异步写入 ClickHouse，不影响重定向主链路。

### 可能的改进方向
- 引入边缘节点（CDN Edge）直接返回 302 重定向，进一步降低延迟。
- 支持自定义短链接时的冲突检测与预留机制。
- 滥用检测：基于 IP + 频率的限流，防止恶意生成大量短链接。
- 支持更细粒度的权限管理（私有链接、团队共享）。
- 使用 Service Mesh 统一治理流量、熔断和可观测性。
