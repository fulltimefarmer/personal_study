# 38. 设计民宿/市场平台 (Marketplace like Airbnb)

## 题目

设计一个类似 Airbnb 的在线民宿预订平台，支持房东发布房源、租客搜索和预订、在线支付、评价系统等核心功能。

---

## 需求澄清

### 功能性需求

- 房东发布和管理房源（标题、描述、照片、价格、地理位置、设施）
- 租客按位置、日期、价格、房型等条件搜索房源
- 房源详情页（照片画廊、评价、位置地图）
- 预订系统（选择日期、计算价格、下单）
- 支付系统（预付/到付、平台抽成）
- 评价系统（双向评价：房东评租客、租客评房源）
- 消息系统（房东与租客沟通）
- 收藏/心愿单
- 房东日历管理（价格、可预订状态）
- 搜索推荐和排序算法

### 非功能性需求

| 指标 | 要求 |
|------|------|
| 可用性 | 99.99% |
| 搜索延迟 | P99 < 500ms |
| 预订一致性 | 强一致性（防止超卖） |
| 支付安全 | PCI-DSS 合规 |
| 扩展性 | 全球多区域部署 |
| QPS | 峰值: 搜索10万QPS, 预订1000QPS |

### 容量估算

假设 DAU 500万：
- 房源总量：100万活跃房源
- 每天预订：10万笔
- 每条预订平均价值：$200
- GMV：10万 × $200 × 365 ≈ $73亿/年
- 每房源平均20张照片
- 照片存储：100万 × 20 × 2MB(压缩后) ≈ 40TB

---

## 数据模型

### 核心实体

```sql
-- 用户表
CREATE TABLE users (
    id              UUID PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    avatar_url      TEXT,
    is_host         BOOLEAN DEFAULT FALSE,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 房源表
CREATE TABLE listings (
    id              UUID PRIMARY KEY,
    host_id         UUID NOT NULL REFERENCES users(id),
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    property_type   VARCHAR(50),       -- apartment, house, villa, etc
    room_type       VARCHAR(50),       -- entire_place, private_room, shared_room
    accommodates    INTEGER,           -- 最多入住人数
    bedrooms        INTEGER,
    beds            INTEGER,
    bathrooms       INTEGER,
    base_price      DECIMAL(10,2) NOT NULL,  -- 基础价格/晚
    cleaning_fee    DECIMAL(10,2),
    currency        VARCHAR(3) DEFAULT 'CNY',
    address_line    TEXT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(100) NOT NULL,
    latitude        DECIMAL(10,7),
    longitude       DECIMAL(10,7),
    amenities       JSONB,             -- ["wifi", "kitchen", "pool", ...]
    house_rules     TEXT,
    max_guests      INTEGER DEFAULT 1,
    min_nights      INTEGER DEFAULT 1,
    max_nights      INTEGER DEFAULT 365,
    status          VARCHAR(20) DEFAULT 'draft',  -- draft/published/unlisted/banned
    instant_book    BOOLEAN DEFAULT FALSE,
    review_score    DECIMAL(3,2),       -- 平均评分
    review_count    INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 地理空间索引 (PostGIS)
CREATE INDEX idx_listings_location ON listings 
    USING GIST (ST_MakePoint(longitude, latitude));
CREATE INDEX idx_listings_city ON listings(city, status);
CREATE INDEX idx_listings_price ON listings(base_price);

-- 房源照片
CREATE TABLE listing_photos (
    id              UUID PRIMARY KEY,
    listing_id      UUID NOT NULL REFERENCES listings(id),
    url             TEXT NOT NULL,
    caption         VARCHAR(500),
    sort_order      INTEGER DEFAULT 0,
    is_primary      BOOLEAN DEFAULT FALSE,
    width           INTEGER,
    height          INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 房源日历（价格和可用性）
CREATE TABLE listing_calendar (
    listing_id      UUID NOT NULL REFERENCES listings(id),
    date            DATE NOT NULL,
    price           DECIMAL(10,2),          -- 可覆盖base_price
    is_available    BOOLEAN DEFAULT TRUE,
    min_nights      INTEGER,
    notes           VARCHAR(500),
    PRIMARY KEY (listing_id, date)
);

-- 预订表
CREATE TABLE bookings (
    id              UUID PRIMARY KEY,
    listing_id      UUID NOT NULL REFERENCES listings(id),
    guest_id        UUID NOT NULL REFERENCES users(id),
    host_id         UUID NOT NULL REFERENCES users(id),
    check_in        DATE NOT NULL,
    check_out       DATE NOT NULL,
    guests_count    INTEGER NOT NULL,
    status          VARCHAR(20) NOT NULL,  -- pending/confirmed/cancelled/completed
    subtotal        DECIMAL(10,2),         -- 房费小计
    cleaning_fee    DECIMAL(10,2),
    service_fee     DECIMAL(10,2),         -- 平台服务费
    total_amount    DECIMAL(10,2),
    currency        VARCHAR(3),
    payment_status  VARCHAR(20),           -- unpaid/paid/refunded
    payment_id      UUID,
    cancelled_by    VARCHAR(10),            -- guest or host
    cancelled_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bookings_listing_dates ON bookings(listing_id, check_in, check_out);
CREATE INDEX idx_bookings_guest ON bookings(guest_id, created_at DESC);
CREATE UNIQUE INDEX idx_bookings_no_overlap 
    ON bookings(listing_id, check_in, check_out, status)
    WHERE status != 'cancelled';
```

---

## 高层次架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            CDN (静态资源 + 图片)                           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Load Balancer + API Gateway                     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Search Service  │   │  Booking Service │   │  Payment Service │
│  (Elasticsearch) │   │  (核心业务)       │   │  (Stripe/Adyen)  │
│                  │   │                  │   │                  │
│  - 全文搜索      │   │  - 可用性检查     │   │  - 支付处理      │
│  - 地理位置过滤  │   │  - 价格计算      │   │  - 退款          │
│  - 价格排序      │   │  - 预订创建      │   │  - 分账(平台+房东)│
│  - 评价聚合      │   │  - 状态管理      │   │  - Payout        │
└──────────────────┘   └────────┬─────────┘   └──────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Review Service  │   │ Message Service  │   │  User Service    │
│                  │   │  (Chat)          │   │                  │
│  - 评价CRUD      │   │                  │   │  - 注册/登录     │
│  - 评分计算      │   │  - 即时通讯      │   │  - 认证/鉴权     │
│  - 虚假评价检测  │   │  - 消息持久化    │   │  - 用户画像      │
└──────────────────┘   └──────────────────┘   └──────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                          Infrastructure                                   │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐           │
│  │PostgreSQL│  │  Redis   │  │Elasticsearch│ │   S3/CDN    │           │
│  │(主业务库) │  │(缓存/Session)│(搜索)     │  │  (图片存储)  │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. 搜索系统设计

```
搜索数据流:

MySQL/PostgreSQL (房源数据) ──CDC (Debezium)──► Kafka ──► Indexer ──► Elasticsearch

搜索架构:
┌──────────────────────────────────────────────────────────────────────┐
│                         Search Request                                │
│                           │                                          │
│                           ▼                                          │
│               ┌───────────────────────┐                              │
│               │     Geo Filtering     │ ← 先做地理过滤(大幅缩小范围)  │
│               │   latitude, longitude │                              │
│               │   radius: 10km        │                              │
│               └───────────┬───────────┘                              │
│                           ▼                                          │
│               ┌───────────────────────┐                              │
│               │   Availability Filter │ ← 日期可用性(join calendar)   │
│               │   check_in, check_out │                              │
│               └───────────┬───────────┘                              │
│                           ▼                                          │
│               ┌───────────────────────┐                              │
│               │   其他过滤条件         │ ← price, guests, amenities   │
│               └───────────┬───────────┘                              │
│                           ▼                                          │
│               ┌───────────────────────┐                              │
│               │     排序 & 打分       │ ← ML Ranking Model           │
│               │                      │                              │
│               │  打分因子:            │                              │
│               │  - Relevance(文本匹配)│                              │
│               │  - Location(距离)    │                              │
│               │  - Price(价格优势)   │                              │
│               │  - Rating(评价)     │                              │
│               │  - Bookings(热门度) │                              │
│               │  - Host Quality     │                              │
│               │  - 个性化CTR预估    │                              │
│               └───────────┬───────────┘                              │
│                           ▼                                          │
│                       Search Results                                │
└──────────────────────────────────────────────────────────────────────┘
```

**Elasticsearch 查询示例：**

```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "geo_distance": {
            "distance": "10km",
            "location": { "lat": 39.9, "lon": 116.4 }
          }
        },
        { "range": { "base_price": { "gte": 100, "lte": 1000 } } },
        { "term": { "accommodates": 2 } },
        { "terms": { "amenities": ["wifi", "kitchen"] } },
        { "term": { "status": "published" } }
      ],
      "must": {
        "multi_match": {
          "query": "cozy apartment near subway",
          "fields": ["title^3", "description", "city^2", "address_line"]
        }
      },
      "must_not": {
        "ids": { "values": ["id1","id2",...] }  // 已预订的ID
      }
    }
  },
  "sort": [
    { "_score": "desc" },
    { "review_score": "desc" },
    { "review_count": "desc" }
  ]
}
```

### 2. 预订系统与并发控制

这是市场平台最核心也最容易出问题的部分——防止超卖。

```
预订流程 (Pessimistic Lock 方案):

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Client Request: "预订 listing_123, 2024-03-01 ~ 2024-03-05"         │
│                          │                                           │
│                          ▼                                           │
│          ┌───────────────────────────────┐                           │
│          │ 1. 开始事务 (SERIALIZABLE)     │                           │
│          └───────────────┬───────────────┘                           │
│                          ▼                                           │
│          ┌───────────────────────────────┐                           │
│          │ 2. 悲观锁日历行:              │                           │
│          │    SELECT * FROM listing_calendar                          │
│          │    WHERE listing_id = '123'                                │
│          │      AND date BETWEEN '2024-03-01' AND '2024-03-04'       │
│          │    FOR UPDATE;                    ← 行级锁                 │
│          └───────────────┬───────────────┘                           │
│                          ▼                                           │
│          ┌───────────────────────────────┐                           │
│          │ 3. 检查所有日期是否可用:       │                           │
│          │    is_available == TRUE?       │                           │
│          │    ↓ Yes              ↓ No    │                           │
│          │    继续              返回错误  │                           │
│          └───────────────┬───────────────┘                           │
│                          ▼                                           │
│          ┌───────────────────────────────┐                           │
│          │ 4. 更新日历状态:               │                           │
│          │    UPDATE listing_calendar     │                           │
│          │    SET is_available = FALSE    │                           │
│          │    WHERE listing_id = '123'    │                           │
│          │      AND date BETWEEN ...     │                           │
│          └───────────────┬───────────────┘                           │
│                          ▼                                           │
│          ┌───────────────────────────────┐                           │
│          │ 5. 创建预订记录                │                           │
│          │ 6. 创建支付订单                │                           │
│          │ 7. 发送确认通知                │                           │
│          │ 8. COMMIT                     │                           │
│          └───────────────────────────────┘                           │
│                                                                      │
│  超时处理: BEGIN → 如果在300s内未完成 → ROLLBACK + 释放日历           │
│  一般不会超时, 锁只在极短时间(毫秒级)内持有                           │
└──────────────────────────────────────────────────────────────────────┘
```

**Redis 优化方案（热点房源高并发预订）：**

```python
def check_and_reserve_listing_redis(listing_id, check_in, check_out):
    """
    使用 Redis 位图 + 事务 快速检查可用性
    适用场景: 热门房源的高并发预订检查
    """
    dates = date_range(check_in, check_out)
    pipeline = redis.pipeline()
    
    # 1. 检查所有日期是否可用 (O(N) 但 N 通常 < 30)
    for date in dates:
        key = f"listing:available:{listing_id}:{date.year}-{date.month}"
        offset = date.day - 1
        pipeline.getbit(key, offset)
    
    results = pipeline.execute()
    
    if not all(results):  # 有日期不可用
        return False, "Some dates are unavailable"
    
    # 2. 标记不可用 (使用WATCH + MULTI防止竞态)
    redis.watch(*[f"listing:available:{listing_id}:{d.year}-{d.month}" 
                  for d in dates])
    
    pipeline = redis.pipeline(transaction=True)
    for date in dates:
        key = f"listing:available:{listing_id}:{date.year}-{date.month}"
        pipeline.setbit(key, date.day - 1, 0)
    
    try:
        pipeline.execute()
        # 成功标记 → 写入DB (异步)
        async_db_reservation(listing_id, check_in, check_out)
        return True, "Reserved"
    except WatchError:
        return False, "Concurrent booking detected"
```

### 3. 价格计算引擎

```python
class PriceCalculator:
    """
    复杂预订价格计算
    
    价格组成:
    - 基础房费 = sum(每日价格)  ← 从 listing_calendar 获取
    - 清洁费 = 一次性固定费用
    - 平台服务费 = (基础房费 + 清洁费) × rate%
    - 税费(可选) = 按地区计算
    - 长期住宿折扣 = 满7晚享9折, 满30晚享8折
    """
    
    def calculate(self, listing_id, check_in, check_out, guests):
        # 1. 获取每日价格
        daily_prices = self.get_daily_prices(listing_id, check_in, check_out)
        
        # 2. 计算基础房费
        nights = (check_out - check_in).days
        subtotal = sum(daily_prices)
        
        # 3. 计算清洁费
        cleaning_fee = self.listing.cleaning_fee or 0
        
        # 4. 计算长期住宿折扣
        discount = self.calculate_long_stay_discount(nights, subtotal)
        
        # 5. 计算平台服务费
        service_fee = (subtotal - discount + cleaning_fee) * self.SERVICE_FEE_RATE
        
        # 6. 计算额外客人费用
        extra_guest_fee = self.calculate_extra_guest_fee(guests)
        
        total = subtotal - discount + cleaning_fee + service_fee + extra_guest_fee
        
        return {
            'subtotal': subtotal,
            'discount': discount,
            'cleaning_fee': cleaning_fee,
            'service_fee': service_fee,
            'extra_guest_fee': extra_guest_fee,
            'total': total,
            'currency': self.listing.currency,
            'nights': nights,
            'price_per_night': subtotal / nights
        }
    
    def calculate_long_stay_discount(self, nights, subtotal):
        if nights >= 28:
            return subtotal * 0.20  # 月租8折
        elif nights >= 7:
            return subtotal * 0.10  # 周租9折
        return 0
```

### 4. 支付与分账系统

```
支付分账流程:

     ┌────────┐
     │ Guest  │ 支付 $200 (总费用)
     └───┬────┘
         │
         ▼
┌─────────────────┐
│ Payment Gateway │ (Stripe / Adyen)
│                 │
│  收单: $200     │
└────────┬────────┘
         │
    ┌────┴─────────────────────────────┐
    │         Payment Split             │
    │                                   │
    │  ┌─────────┐     ┌──────────┐    │
    │  │ 平台账户  │     │ 房东账户  │    │
    │  │         │     │          │    │
    │  │ 服务费   │     │ 房费(80%)│    │
    │  │ $30     │     │ +清洁费  │    │
    │  │ (15%)   │     │ $170     │    │
    │  └─────────┘     └────┬─────┘    │
    └───────────────────────┼───────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Payout Service│
                    │ (定期结算)     │
                    │               │
                    │ 入住后24h     │
                    │ → 自动打款    │
                    │ → 银行账户    │
                    └───────────────┘

支付状态机:
  PENDING → PROCESSING → PAID → SETTLED
     │          │          │
     └──────────┴──────────┴──► FAILED/REFUNDED
```

### 5. 评价系统

```sql
CREATE TABLE reviews (
    id              UUID PRIMARY KEY,
    booking_id      UUID NOT NULL REFERENCES bookings(id) UNIQUE,
    listing_id      UUID NOT NULL,
    reviewer_id     UUID NOT NULL,         -- 评价者
    reviewee_id     UUID NOT NULL,          -- 被评价者(房东或租客)
    review_type     VARCHAR(10) NOT NULL,   -- guest_to_host, host_to_guest
    rating          INTEGER CHECK (rating BETWEEN 1 AND 5),
    content         TEXT,
    aspects         JSONB,                  -- {"cleanliness": 5, "location": 4, ...}
    response        TEXT,                   -- 被评价者的回复
    responded_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**评价策略：**
- 双盲评价：双方提交评价后14天或另一方提交后同时公开（防止报复性评价）
- 只有完成入住的预订才能评价
- 评价加权：近期评价权重更高

### 6. 搜索结果缓存

```
缓存策略:

┌──────────────────────────────────────────────────────────────────────┐
│                       搜索缓存层次                                     │
│                                                                      │
│  L1: CDN (房源详情页静态部分)                                         │
│      TTL: 1小时                                                      │
│                                                                      │
│  L2: Redis (搜索结果缓存)                                             │
│      Key: search:{city}:{checkin}:{checkout}:{guests}:{price_range}  │
│              :hash(filters):{page}                                   │
│      Value: [listing_id, ...]  ← id列表, 不从缓存读完整对象          │
│      TTL: 5分钟 (短期, 因为库存变化)                                  │
│      Invalidation: 有新预订 → 删除相关城市/日期的缓存key              │
│                                                                      │
│  L3: Redis (房源详情缓存)                                             │
│      Key: listing:{id}:detail                                        │
│      TTL: 1小时 + Write-Through (更新时同步写缓存)                    │
│                                                                      │
│  L4: Elasticsearch (实时搜索)                                         │
│      Read-your-own-writes: refresh=1s                               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 扩展性与高可用

### 1. 数据库分片

```
分片策略 (Sharding):

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  分片键: listing_id 的哈希 (最常用查询维度)                           │
│                                                                      │
│  分片方案:                                                            │
│    Shard 0: listing_id hash % 4 == 0                                 │
│    Shard 1: listing_id hash % 4 == 1                                 │
│    Shard 2: listing_id hash % 4 == 2                                 │
│    Shard 3: listing_id hash % 4 == 3                                 │
│                                                                      │
│  关联表分片:                                                          │
│    bookings, listing_photos, listing_calendar → 按 listing_id 分片   │
│    reviews → 按 listing_id 分片 (方便按房源查评价)                    │
│    users → 不分片(或按 user_id 分片)                                 │
│    messages → 按 (sender_id, receiver_id) 分片                       │
│                                                                      │
│  跨分片查询:                                                          │
│    按用户查预订: 使用全局二级索引 (反向索引: user_id → listing_ids)    │
│                 或使用 Elasticsearch 做联合查询                       │
│                 或使用 CQRS: 预订数据双写到 user_bookings 视图         │
└──────────────────────────────────────────────────────────────────────┘
```

### 2. CQRS 读写分离

```
CQRS 分离:

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Write Side (Command):                                               │
│    房源发布、预订创建、评价提交                                        │
│    → PostgreSQL (ACID保证) → CDC → Kafka                             │
│                                                                      │
│  Read Side (Query):                                                   │
│    搜索、房源详情查看、评价列表                                        │
│    → Elasticsearch + Redis (优化读取)                                 │
│                                                                      │
│  数据同步:                                                            │
│    PostgreSQL ──CDC(Debezium)──► Kafka ──Consumer──► Elasticsearch   │
│                                                                │     │
│                                                     Redis Cache │     │
│                                                                      │
│  一致性: 最终一致性 (< 2s 延迟)                                       │
│  关键路径(预订可用性检查): 回源到PG, 不走ES                           │
└──────────────────────────────────────────────────────────────────────┘
```

### 3. 预订超时处理

```python
class BookingTimeoutHandler:
    """
    处理未支付预订的超时自动取消
    
    场景: 用户在预订页面, 房源被临时锁定,
          但用户15分钟内未完成支付 → 自动释放
    """
    
    TIMEOUT_MINUTES = 15
    
    def hold_inventory(self, listing_id, check_in, check_out):
        booking_id = generate_id()
        
        # 1. 在Redis设置临时锁 + TTL
        hold_key = f"hold:{listing_id}:{check_in}:{check_out}"
        success = redis.set(hold_key, booking_id, 
                           nx=True, ex=self.TIMEOUT_MINUTES * 60)
        
        if not success:
            return None  # 已被其他人持有
        
        # 2. 监听Key过期事件 (Redis Keyspace Notifications)
        # 当hold_key过期→自动触发释放逻辑
        # 或者用延迟队列 (SQS Delay Queue / Redis Keyspace)
        
        # 方案A: SQS Delay Queue
        sqs.send_message(
            QueueUrl='booking-timeout-queue',
            MessageBody=json.dumps({'booking_id': booking_id}),
            DelaySeconds=self.TIMEOUT_MINUTES * 60
        )
        
        # 消费者收到消息时:
        #   1. 检查此预订是否已完成支付
        #   2. 如果未支付 → UPDATE listing_calendar SET is_available = TRUE
        #   3. 如果已支付 → 忽略
        
        return booking_id
    
    def release_hold(self, booking_id, listing_id, check_in, check_out):
        """支付成功后主动释放hold"""
        hold_key = f"hold:{listing_id}:{check_in}:{check_out}"
        redis.delete(hold_key)
```

### 4. 消息系统

```
房东-租客消息:

┌──────────────────────────────────────────────────────────────────────┐
│ 消息限制: 只有确认预订后双方才能发消息(防止骚扰)                       │
│ 预定时可发消息: Message with Booking Request (特定模板)               │
│                                                                      │
│ 敏感信息屏蔽:                                                         │
│  - 预订前: 电话号码、Email等联系信息自动过滤                          │
│  - 预订后: 可交换联系方式                                             │
│                                                                      │
│ 架构:                                                                 │
│  WebSocket (实时) + Kafka (持久化) + PostgreSQL (历史)                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 搜索 | Elasticsearch + Geo索引 + ML排序 |
| 预订 | 悲观锁 + Redis位图 + 超时释放 |
| 支付 | 托管支付 + 分账 + 定期结算 |
| 评价 | 双盲策略 + 近期加权 |
| 分片 | listing_id哈希分片 + CQRS |
| 缓存 | CDN + Redis + 搜索结果缓存 |
| 一致性 | 预订强一致(PG) + 搜索最终一致(ES) |

**CAP 取舍：** 市场平台是混合一致性系统。预订交易路径选择 **CP**（一致性优先）——使用悲观锁/数据库锁防止超卖，牺牲部分可用性以确保预订绝不冲突。搜索和浏览路径选择 **AP**（可用性优先）——使用 Elasticsearch 最终一致性，可以忍受短暂的数据延迟。

**核心业务挑战：**
1. **防止超卖：** 悲观锁 + 超时释放 + Redis快速检查
2. **搜索精准度：** ES全文搜索 + 地理位置 + ML排序模型
3. **信任体系：** 双向评价 + 身份验证 + 支付托管 + 平台保障
4. **价格策略：** 动态定价(季节性/需求) + 灵活计费组成
