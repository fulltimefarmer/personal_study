# 01. 设计短链接系统 (Design URL Shortener)

## 题目

设计一个类似 TinyURL 的短链接系统，用户输入长链接，系统返回短链接；用户访问短链接时，系统将其重定向到原始长链接。

---

## 需求澄清

### 功能性需求

1. **短链接生成**：用户提交一个长 URL，系统生成一个唯一的短 URL
2. **重定向**：用户访问短 URL 时，系统进行 301（永久）或 302（临时）重定向到原始长 URL
3. **自定义短链接（可选）**：用户可自定义短链接后缀
4. **过期机制（可选）**：短链接可设置过期时间，过期后自动失效
5. **统计分析（可选）**：记录点击次数、来源、地域等信息
6. **API 访问**：提供 REST API 供第三方集成

### 非功能性需求

1. **高可用性**：系统必须 99.99% 可用，重定向是核心功能不能中断
2. **低延迟**：重定向延迟应 < 50ms（P99）
3. **高吞吐量**：读操作远大于写操作，读写比约 100:1 甚至 1000:1
4. **URL 不可预测**：短链接不宜被猜测，防止恶意遍历
5. **永久存储**：链接一旦创建，理论上应永久保留（除非设置过期）

### 容量估算

**假设条件：**
- 日活跃用户: 1 亿（100M）
- 每日新增短链接: 假设每用户平均创建 0.5 条短链接
  - 每日写入: 100M × 0.5 = 50M 条/天
- 读操作: 每日新增链接的 100 倍
  - 每日读取: 50M × 100 = 5B 次/天  
- QPS 估算:
  - 写入 QPS: 50M / 86400 ≈ **580 QPS**（峰值 ×2 ≈ 1160 QPS）
  - 读取 QPS: 5B / 86400 ≈ **57,870 QPS**（峰值 ×2 ≈ 115K QPS）
- 存储估算（5 年）:
  - 总链接数: 50M × 365 × 5 = 91.25B 条
  - 每条记录约 500 bytes（原URL 200B + 短码 7B + 元数据）
  - 总存储: 91.25B × 500B ≈ **45.6 TB**
- 带宽估算:
  - 写入带宽: 580 × 500B ≈ 290 KB/s
  - 读取带宽: 57,870 × 500B ≈ 29 MB/s（含响应头）
- 缓存估算:
  - 遵循 80-20 法则，20% 的短链接产生 80% 的流量
  - 每日热点容量: 50M × 365 × 5 × 0.2 = 18.25B × 500B ≈ 9.1 TB（全量缓存不现实）
  - 实际缓存策略: 缓存最近访问和热点，设 256GB Redis 集群

---

## API 设计

### REST API

```
1. 创建短链接
POST /api/v1/shorten
Content-Type: application/json
Authorization: Bearer <api_key>

Request:
{
  "long_url": "https://www.example.com/very/long/path?param=value",
  "custom_alias": "myalias",          // 可选，自定义后缀
  "expire_at": "2025-12-31T23:59:59Z" // 可选，过期时间
}

Response: 201 Created
{
  "short_url": "https://short.ly/abc123",
  "long_url": "https://www.example.com/very/long/path?param=value",
  "expire_at": "2025-12-31T23:59:59Z",
  "created_at": "2025-01-01T00:00:00Z"
}

Error Response: 409 Conflict (自定义别名已被占用)
Error Response: 429 Too Many Requests (限流)
```

```
2. 重定向短链接
GET /api/v1/{short_code}

Response: 301 Moved Permanently
Location: https://www.example.com/very/long/path?param=value

或

Response: 302 Found (Temporary Redirect)
Location: https://www.example.com/very/long/path?param=value

--- 如果是 301: 浏览器会缓存重定向，后续请求不再访问短链接服务器
--- 如果是 302: 浏览器每次都会访问短链接服务器（方便做统计分析）
```

```
3. 查询统计信息
GET /api/v1/stats/{short_code}
Authorization: Bearer <api_key>

Response: 200 OK
{
  "short_code": "abc123",
  "long_url": "https://www.example.com/...",
  "total_clicks": 10234,
  "daily_clicks": {...},
  "referrers": {...},
  "last_accessed": "2025-01-15T10:30:00Z"
}
```

```
4. 删除短链接
DELETE /api/v1/{short_code}
Authorization: Bearer <api_key>

Response: 204 No Content
```

```
5. 更新短链接
PUT /api/v1/{short_code}
Authorization: Bearer <api_key>

Request:
{
  "long_url": "https://www.new-example.com/new-path",
  "expire_at": "2025-12-31T23:59:59Z"
}

Response: 200 OK
```

### 301 vs 302 重定向的选择

| 特性 | 301 永久重定向 | 302 临时重定向 |
|------|-------------|-------------|
| 浏览器缓存 | 会缓存 | 不缓存 |
| 服务器负载 | 低（只处理一次） | 高（每次请求都到服务器） |
| 统计分析 | 不准确 | 准确（可统计每次点击） |
| SEO 影响 | PageRank 转移到短链接域名 | PageRank 保留在原域名 |
| 推荐场景 | 纯重定向、无统计需求 | 需要点击统计、动态更新 |

**推荐策略**：默认使用 302 重定向以确保获得准确的点击统计，同时通过 CDN 缓存减轻服务器压力。

---

## 数据模型

### 核心表结构 (SQL)

```sql
-- 短链接映射表（核心）
CREATE TABLE url_mappings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    short_code VARCHAR(10) NOT NULL UNIQUE,
    long_url TEXT NOT NULL,
    long_url_hash CHAR(64) NOT NULL,     -- SHA-256 hash，用于去重
    user_id BIGINT,
    expire_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_short_code (short_code),
    INDEX idx_long_url_hash (long_url_hash),
    INDEX idx_user_id (user_id),
    INDEX idx_expire_at (expire_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 点击统计表（时序，建议使用时序数据库或列存储）
CREATE TABLE click_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    short_code VARCHAR(10) NOT NULL,
    click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referrer VARCHAR(2048),
    user_agent VARCHAR(512),
    ip_address VARBINARY(16),
    country CHAR(2),
    INDEX idx_short_code_click_time (short_code, click_time),
    INDEX idx_click_time (click_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- 注：此表增长极快，需要分片或使用时序DB（ClickHouse/InfluxDB）
```

### 缓存数据结构 (Redis)

```
# 短链接映射缓存
Key:   url:{short_code}
Type:  String
Value: original_long_url
TTL:   根据热点自适应设置（LRU淘汰）

# 长链接去重缓存（Bloom Filter 或 Hash 缓存）
Key:   hash:{sha256_of_long_url}
Type:  String
Value: short_code  # 如果已存在，返回已生成的短码

# 点击计数（Redis HyperLogLog 或 Bitmap）
Key:   clicks:daily:{short_code}:{date}
Type:  HyperLogLog
Value: unique_visitor_count

# 限流计数器
Key:   ratelimit:user:{user_id}:{window}
Type:  String
Value: request_count
TTL:   window_size_seconds
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────┐
                              │                 CDN / LB                  │
                              │          (CloudFlare / Nginx)             │
                              └─────┬──────────────────────────┬─────────┘
                                    │                          │
                          ┌─────────▼─────────┐      ┌────────▼──────────┐
                          │   短链接生成服务    │      │   重定向服务       │
                          │   (Write Path)    │      │   (Read Path)     │
                          │                   │      │                   │
                          │  - 接收长URL       │      │  - 接收短码        │
                          │  - 短码生成        │      │  - 缓存查找        │
                          │  - 冲突检测        │      │  - 数据库回源       │
                          │  - 持久化存储      │      │  - 301/302 重定向  │
                          └────────┬──────────┘      └────────┬──────────┘
                                   │                          │
                          ┌────────▼──────────────────────────▼──────────┐
                          │                Redis 缓存集群                  │
                          │           (主从 + Sentinel/Cluster)            │
                          │  ┌─────────────┐  ┌──────────────────────┐   │
                          │  │ url:{code}  │  │ hash:{sha256}:{code} │   │
                          │  └─────────────┘  └──────────────────────┘   │
                          └──────────────────────┬───────────────────────┘
                                                 │
                          ┌──────────────────────▼───────────────────────┐
                          │              MySQL / PostgreSQL 集群           │
                          │         (主从复制 / 分库分表 / Vitess)          │
                          │  ┌─────────────┐  ┌──────────────────────┐   │
                          │  │url_mappings │  │   click_events (TSDB) │   │
                          │  └─────────────┘  └──────────────────────┘   │
                          └──────────────────────────────────────────────┘
                                                 │
                          ┌──────────────────────▼───────────────────────┐
                          │              消息队列 (Kafka / Pulsar)         │
                          │          click_events_topic (异步处理)          │
                          └──────────────────────┬───────────────────────┘
                                                 │
                          ┌──────────────────────▼───────────────────────┐
                          │                流/批处理 (Flink / Spark)         │
                          │         - 点击聚合统计                           │
                          │         - 热点分析                              │
                          │         - 数据清理 (过期链接)                     │
                          └──────────────────────────────────────────────┘
```

### 数据流

**写路径 (短链接生成)：**
```
User → LB → 短链接生成服务
                │
                ├── 1. 验证长URL格式、长度
                ├── 2. SHA-256 哈希长URL → 查询去重缓存/DB
                ├── 3. 如果长URL已存在 → 返回已有短码
                ├── 4. 如果不存在：
                │      ├── 生成唯一ID (Snowflake / 自增ID)
                │      ├── Base62 编码 → 短码 (7位)
                │      ├── 写入 MySQL (url_mappings 表)
                │      ├── 写入 Redis 缓存
                │      └── 返回短链接给用户
                └── 5. 返回响应
```

**读路径 (重定向)：**
```
User → CDN → LB → 重定向服务
                   │
                   ├── 1. 提取短码 (short_code)
                   ├── 2. 查询 Redis 缓存: url:{short_code}
                   ├── 3. 缓存命中 → 301/302 重定向 → User
                   ├── 4. 缓存未命中 (Cache Miss):
                   │      ├── 查询 MySQL: SELECT long_url WHERE short_code = ?
                   │      ├── 若找到 → 回填 Redis，返回 301/302
                   │      └── 若未找到 → 返回 404
                   ├── 5. 异步发送点击事件 → Kafka
                   └── 6. 流处理聚合统计
```

---

## 核心深入

### 短码生成算法对比

#### 方案一：Hash 函数法 (MD5/SHA-256 + Base62)

```
算法流程：
1. 对长URL做 MD5/SHA-256 哈希 → 得到 128/256 bit 哈希值
2. 取前 7 个字节 (42 bit) → Base62 编码 → 7 位短码
3. 进行冲突检测：在 DB 中检查短码是否已存在
4. 如果有冲突：在长URL后追加随机串，重新哈希

特点：
- 优点：无需全局计数器，分布式友好
- 缺点：哈希冲突，可能需要多次尝试
- 冲突概率：7位Base62 → 62^7 ≈ 3.5万亿 种组合
  - 当生成 10亿 个短链接时，冲突概率约 1 - e^(-n²/2m) ≈ 14%（较高）
  - 8位短码：62^8 ≈ 218万亿，冲突概率大幅降低
```

```python
import hashlib

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def base62_encode(num: int) -> str:
    if num == 0:
        return BASE62_ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, 62)
        chars.append(BASE62_ALPHABET[rem])
    return ''.join(reversed(chars))

def hash_shorten(long_url: str, length: int = 7) -> str:
    hash_hex = hashlib.md5(long_url.encode()).hexdigest()
    # 取前 42 bits (7字符 Base62)
    hash_int = int(hash_hex[:11], 16)
    short_code = base62_encode(hash_int).zfill(length)[:length]
    return short_code
```

#### 方案二：自增ID + Base62 编码（推荐）

```
算法流程：
1. 使用分布式ID生成器 (Snowflake/Twitter Snowflake) 生成唯一 64-bit ID
2. 将 ID 进行 Base62 编码 → 得到固定长度的短码
3. 无需冲突检测（ID本身就是唯一的）

特点：
- 优点：无冲突，高效
- 缺点：需要分布式ID生成器
- Snowflake ID: 41bit时间戳 + 10bit机器ID + 12bit序列号
  - 1000 ID/秒/节点，可用 ~69年
```

```python
# Snowflake ID 实现（简化版）
import time

class Snowflake:
    def __init__(self, datacenter_id: int, worker_id: int):
        self.datacenter_id = datacenter_id  # 5 bits
        self.worker_id = worker_id          # 5 bits
        self.sequence = 0                   # 12 bits
        self.last_timestamp = -1
        self.epoch = 1704067200000  # 2024-01-01

    def _timestamp(self) -> int:
        return int(time.time() * 1000) - self.epoch

    def next_id(self) -> int:
        timestamp = self._timestamp()
        if timestamp < self.last_timestamp:
            raise Exception("Clock moved backwards!")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits
            if self.sequence == 0:
                # 序列号用完，等待下一毫秒
                while timestamp <= self.last_timestamp:
                    timestamp = self._timestamp()
        else:
            self.sequence = 0

        self.last_timestamp = timestamp
        return (timestamp << 22) | (self.datacenter_id << 17) | \
               (self.worker_id << 12) | self.sequence

def id_to_short_code(unique_id: int) -> str:
    return base62_encode(unique_id)
```

#### 方案三：预生成短码池 (Pre-generated Pool)

```
算法流程：
1. 批量预生成短码存入 Redis Set/Queue
2. 写入请求时从池中弹出短码（原子操作）
3. 定期补充短码池

特点：
- 优点：极低延迟，无需实时计算
- 缺点：需要维护短码池水位线，额外复杂性
- 适用场景：极高并发写入
```

```python
# Redis Lua 脚本：原子弹出短码
LUA_POP_CODE = """
local code = redis.call('SPOP', KEYS[1])
if not code then
    return nil
end
return code
"""

# 补充短码池的脚本
LUA_REFILL = """
local codes = {}
for i = 1, tonumber(ARGV[1]) do
    table.insert(codes, ARGV[2] .. i)
end
-- ARGV[2] is prefix batch identifier
redis.call('SADD', KEYS[1], unpack(codes))
return #codes
"""
```

**算法对比总结：**

| 方案 | 性能 | 冲突 | 可预测性 | 复杂度 | 推荐 |
|------|------|------|---------|--------|------|
| Hash函数 | 中 | 有冲突 | 不可预测 | 低 | 小规模 |
| Snowflake+Base62 | 高 | 无 | 可预测(时间相关) | 中 | **推荐** |
| 预生成池 | 极高 | 无 | 不可预测 | 高 | 极高并发 |
| UUID截断 | 低 | 有冲突 | 不可预测 | 低 | 不推荐 |

---

### 数据库分片策略

根据 45.6TB 的存储需求，单机无法支撑，需要分片。

**分片键选择：short_code**

```sql
-- 分片策略：一致性哈希 (Consistent Hashing)
-- 对 short_code 取哈希，映射到 1024 个虚拟节点

-- 分片计算方法
shard_id = CRC32(short_code) % num_shards

-- 或者使用 Range 分片
-- Shard 0: a00000 ~ gzzzzz
-- Shard 1: h00000 ~ nzzzzz
-- Shard 2: o00000 ~ uzzzzz
-- Shard 3: v00000 ~ zzzzzz
```

**一致性哈希的优势：**
- 扩容时只需迁移 1/N 的数据
- 节点故障时影响范围最小化
- 适合读多写少的场景

### 缓存策略设计

```python
# 多级缓存架构

class URLCacheService:
    """
    L1: CDN (边缘节点缓存热门短链接)
    L2: 本地缓存 (Caffeine/Guava Cache, 进程内)
    L3: Redis 集群 (分布式缓存)
    L4: MySQL (持久化存储)
    """

    def get_long_url(self, short_code: str) -> Optional[str]:
        # L2: 本地缓存 (热点短链接的终极缓存)
        local_url = self.local_cache.get(short_code)
        if local_url:
            self._record_cache_hit("L2", short_code)
            return local_url

        # L3: Redis 分布式缓存
        redis_url = self.redis_client.get(f"url:{short_code}")
        if redis_url:
            # 回填本地缓存
            self.local_cache.put(short_code, redis_url)
            self._record_cache_hit("L3", short_code)
            return redis_url

        # L4: MySQL 回源
        db_url = self.db.query(
            "SELECT long_url FROM url_mappings WHERE short_code = ? AND "
            "(expire_at IS NULL OR expire_at > NOW())",
            short_code
        )
        if db_url:
            # 回填所有缓存层
            self.redis_client.setex(f"url:{short_code}", ttl=86400, value=db_url)
            self.local_cache.put(short_code, db_url)
            return db_url

        return None
```

**缓存预热与淘汰策略：**
- 使用 **LRU (Least Recently Used)** + **LFU (Least Frequently Used)** 混合策略
- Redis 的 `allkeys-lru` 策略自动淘汰冷数据
- 通过离线分析识别热点短链接，主动预热到 CDN

---

### 扩展性与高可用

#### 水平扩展

```
                     ┌──────────────────────┐
                     │     Global LB         │
                     │   (DNS Round Robin)   │
                     └──────┬───────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
     ┌────────▼───┐ ┌──────▼────┐ ┌──────▼────┐
     │  Region-A  │ │ Region-B  │ │ Region-C  │
     │  (US-East) │ │ (EU-West) │ │ (APAC)    │
     │            │ │           │ │           │
     │ App x N    │ │ App x N   │ │ App x N   │
     │ Redis x 3  │ │ Redis x 3 │ │ Redis x 3 │
     │ DB Master  │ │ DB ReadR  │ │ DB ReadR  │
     └────────────┘ └───────────┘ └───────────┘
```

#### 数据库高可用

```
┌──────────────────────────────────────────────────┐
│                 MySQL 拓扑架构                     │
│                                                  │
│  ┌──────────┐   Binlog    ┌──────────┐          │
│  │  Master  │────────────▶│  Slave-1 │ (同步)    │
│  │ (Write)  │             │ (Read)   │          │
│  └────┬─────┘             └──────────┘          │
│       │                                          │
│       │ Async                                     │
│       ▼                                          │
│  ┌──────────┐                                    │
│  │  Slave-2 │ (异步，跨DC容灾)                      │
│  │ (DR)     │                                    │
│  └──────────┘                                    │
└──────────────────────────────────────────────────┘
```

#### 故障处理

```
场景1: Redis 缓存故障
  ├── 断路器 (Circuit Breaker) 自动熔断
  ├── 流量直连 MySQL（压力增加，但服务可用）
  └── Redis 恢复后逐步恢复流量

场景2: MySQL 主库故障
  ├── Orchestrator 自动故障转移
  ├── 从库提升为主库 (< 30s)
  ├── 应用层连接池自动切换到新主库
  └── 恢复后进行数据一致性校验

场景3: 数据中心故障
  ├── DNS 故障转移到备用 DC
  ├── 跨 DC 数据异步同步
  ├── RPO < 1s, RTO < 5min
  └── 事后数据核对与补偿
```

#### 监控与告警

```
关键指标：
├── 服务指标
│   ├── 重定向延迟 (P50, P95, P99) - 阈值: P99 > 100ms 告警
│   ├── 短链接生成延迟 - 阈值: P99 > 200ms 告警
│   ├── 错误率 (4xx, 5xx) - 阈值: > 1% 告警
│   └── QPS (读写分离监控)
│
├── 基础设施指标
│   ├── Redis 命中率 - 阈值: < 90% 告警
│   ├── Redis 内存使用率 - 阈值: > 80% 告警
│   ├── MySQL 连接数 - 阈值: > 80% 限流
│   ├── MySQL 主从延迟 - 阈值: > 5s 告警
│   └── Kafka 消费延迟 - 阈值: > 10min 告警
│
├── 业务指标
│   ├── 每日创建数 vs 预测
│   ├── 短码碰撞率
│   ├── 热门短链接 Top-K
│   └── 异常流量检测 (DDoS/爬虫)
│
└── 告警渠道: PagerDuty + Slack + 邮件分级
```

---

#### CAP定理分析

```
短链接系统的 CAP 选择: AP (可用性 + 分区容错) 偏向

P (Partition Tolerance) - 必然选择
  分布式系统无法避免网络分区，必须支持分区容错

A (Availability) vs C (Consistency) 权衡:
  读操作（重定向）:
    - 优先保证可用性 (A)
    - 允许短暂的不一致（刚创建的短链接缓存未同步）
    - 通过 Read-Repair 机制最终一致

  写操作（创建短链接）:
    - 需要强一致性保证短码唯一性
    - 使用数据库 UNIQUE 约束 + 重试机制
  
  最终方案: BASE (Basically Available, Soft state, Eventually consistent)
    - 写操作: 强一致（DB唯一约束保障）
    - 读操作: 最终一致（缓存与DB在TTL内达到一致）
```

---

## 总结

短链接系统看似简单，但扩展到十亿级别时面临着深层次的架构挑战：

1. **读写分离是关键**：读操作是写操作的 100~1000 倍，读路径必须高度优化（多级缓存 + CDN）
2. **短码生成算法**：Snowflake + Base62 是生产环境的最佳实践，兼顾性能与唯一性
3. **缓存策略决定成败**：CDN → 本地缓存 → Redis → MySQL 四级缓存体系是低延迟的保障
4. **301 vs 302 的选择**：取决于统计分析需求，推荐使用 302 配合 CDN 缓存
5. **数据分片**：一致性哈希分片是处理 TB 级数据的标准方案
6. **CAP优先AP**：重定向优先保证可用性，容忍短暂的数据不一致
7. **监控至关重要**：缓存命中率、P99延迟、主从延迟是需要重点关注的指标
8. **安全考虑**：短码不可预测性、恶意链接检测、访问频率限制都是必备功能

**面试中需要强调的核心权衡：**
- Hash 算法 vs 自增ID 编码：唯一性冲突 vs 分布式ID依赖
- 301 vs 302 重定向：性能 vs 统计分析
- 数据分片：Range分片 vs Hash分片 (扩展性与热点问题)
- 缓存一致性：Cache-Aside vs Write-Through
