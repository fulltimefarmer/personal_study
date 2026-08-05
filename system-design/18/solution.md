# 设计酒店/住宿预订系统 (Design Hotel/Booking System)

## 题目

设计一个酒店预订系统，类似 Booking.com / 携程酒店。支持酒店搜索、房间浏览、日期查询、订单预订、支付等核心流程。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 酒店搜索 | 按城市/区域搜索酒店，日期区间筛选有剩余房源的酒店 |
| 酒店详情 | 酒店信息(名称/地址/星级/设施/图片/评分) |
| 房间管理 | 查看房型列表(房型/价格/面积/床型/库存) |
| 价格查询 | 根据入住/离店日期查询动态价格和库存 |
| 预订下单 | 选择房型 -> 填写入住人信息 -> 提交订单 |
| 支付 | 支持多种支付方式(信用卡/支付宝/微信) |
| 订单管理 | 查看/取消/修改订单 |
| 评价 | 离店后对酒店进行评分和评价 |
| 管理后台 | 酒店方管理房型和房价/库存 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 可用性 | 99.99% (预订链路) |
| 延迟 | 搜索 P99 < 500ms, 预订 P99 < 1s |
| 一致性 | 房间库存强一致，同一日期房间不超售 |
| 并发 | 支持节假日预订高峰 (10倍日常) |
| 扩展性 | 支持全球数百万酒店 |
| 国际化 | 多语言、多币种、多时区 |

### 容量估算

```
假设:
  - 酒店数: 200万 (全球)
  - 每家酒店平均 20 间房, 5 个房型
  - DAU: 5000万
  - 日搜索: 5000万 × 3次 = 1.5亿次
  - 日预订: 5000万 × 2% = 100万单

搜索 QPS:
  平均: 1.5亿 / 86400 = 1736 QPS
  峰值: 1736 × 5 = 8680 QPS

预订 QPS:
  平均: 100万 / 86400 = 11.6 QPS
  峰值: 11.6 × 10 = 116 QPS (预订不是瓶颈)

存储:
  酒店信息: 200万 × 5KB = 10GB (基础数据)
  房间信息: 200万 × 5房型 × 1KB = 10GB
  库存数据: 200万 × 5房型 × 365天 = 36.5亿条
    每条 50B: 36.5亿 × 50B = 182.5GB (库存数据)
  订单数据: 100万/天 × 2KB = 2GB/天 ≈ 730GB/年

缓存:
  酒店详情: 200万 × 3KB = 6GB (可全部缓存)
  城市首页酒店: 热点城市 Top 2000 × 100城市 = 20万条
```

---

## API设计

### 搜索/浏览 API

```
=== 城市/区域酒店搜索 ===
GET /api/v1/hotels/search
params:
  - city_id: int             // 城市ID
  - check_in: string         // 入住日期 "2025-03-15"
  - check_out: string        // 离店日期 "2025-03-17"
  - guests: int              // 入住人数(默认2)
  - rooms: int               // 房间数(默认1)
  - price_min/price_max: int // 价格范围(分)
  - stars: string            // 星级 "4,5"
  - facilities: string       // 设施 "wifi,pool,gym"
  - sort: string             // price_asc/price_desc/rating/distance
  - page: int, size: int     // 分页

Response:
{
  "total": 2345,
  "city": { "city_id": 1, "name": "北京" },
  "check_in": "2025-03-15",
  "check_out": "2025-03-17",
  "hotels": [
    {
      "hotel_id": "H001",
      "name": "北京国贸大酒店",
      "stars": 5,
      "rating": 4.7,
      "review_count": 2345,
      "address": "朝阳区建国门外大街1号",
      "lat": 39.9087,
      "lng": 116.4605,
      "distance_to_city_center_km": 0.8,
      "main_image": "https://cdn.xxx/h001.jpg",
      "min_price": 128000,          // 入住期间最低房型总价(分)
      "facilities": ["wifi", "pool", "gym", "spa"],
      "available_room_types": 3,    // 可选房型数
      "breakfast_included": true,
      "cancellation": "free"
    }
  ],
  "filters": {
    "stars": [...],
    "price_ranges": [...],
    "facilities": [...],
    "districts": [...]
  }
}

=== 酒店详情 ===
GET /api/v1/hotels/{hotel_id}?check_in=2025-03-15&check_out=2025-03-17

Response:
{
  "hotel_id": "H001",
  "name": "北京国贸大酒店",
  "description": "...",
  "stars": 5,
  "rating": 4.7,
  "review_count": 2345,
  "address": "...",
  "lat": 39.9087,
  "lng": 116.4605,
  "images": ["url1", "url2", ...],
  "facilities": [...],
  "policies": {
    "check_in_time": "14:00",
    "check_out_time": "12:00",
    "cancellation": "入住前24小时免费取消"
  },
  "room_types": [
    {
      "room_type_id": "RT001",
      "name": "豪华大床房",
      "description": "...",
      "bed_type": "大床(1.8m)",
      "area_sqm": 35,
      "floor": "15-30层",
      "max_guests": 2,
      "images": ["url3", "url4"],
      "facilities": ["wifi", "空调", "电视", "浴缸"],
      "inventory": {
        "2025-03-15": { "available": 5, "price": 64000 },
        "2025-03-16": { "available": 3, "price": 64000 }
      },
      "total_price": 128000,      // 两晚总价
      "breakfast_included": true,
      "cancellation_policy": "free"
    }
  ],
  "reviews": {
    "summary": {"clean": 4.8, "location": 4.6, "service": 4.7},
    "top_reviews": [...]
  }
}
```

### 预订 API

```
=== 创建预订 ===
POST /api/v1/bookings
{
  "hotel_id": "H001",
  "room_type_id": "RT001",
  "check_in": "2025-03-15",
  "check_out": "2025-03-17",
  "rooms": 1,
  "guests": [
    {
      "first_name": "Jun",
      "last_name": "Zhou",
      "email": "junzhou@example.com",
      "phone": "+86-13800001234"
    }
  ],
  "special_requests": "高楼层，无烟房",
  "promo_code": "SPRING2025"    // 可选
}

Response:
{
  "booking_id": "BKG_20250101_000001",
  "status": "CONFIRMED",       // PENDING/CONFIRMED/CANCELLED/COMPLETED
  "total_amount": 128000,       // 原价
  "discount": 12800,            // 优惠
  "paid_amount": 115200,        // 实付
  "currency": "CNY",
  "check_in": "2025-03-15",
  "check_out": "2025-03-17",
  "cancel_deadline": "2025-03-14T14:00:00Z",  // 免费取消截止
  "payment_deadline": "2025-01-01T11:00:00Z"  // 支付截止(如果是待支付)
}

=== 查询预订 ===
GET /api/v1/bookings/{booking_id}
GET /api/v1/bookings?status=UPCOMING&page=1

=== 取消预订 ===
POST /api/v1/bookings/{booking_id}/cancel
{
  "reason": "行程变更"
}

=== 支付 ===
POST /api/v1/bookings/{booking_id}/pay
{
  "method": "CREDIT_CARD",
  "card_token": "tok_visa_1234"
}
```

---

## 数据模型

### 核心数据库表

```sql
-- ============ 酒店 ============
CREATE TABLE hotel (
    hotel_id        BIGINT PRIMARY KEY,
    name            VARCHAR(256) NOT NULL,
    name_en         VARCHAR(256),              -- 英文名
    city_id         INT NOT NULL,
    address         VARCHAR(512),
    address_en      VARCHAR(512),
    lat             DOUBLE NOT NULL,
    lng             DOUBLE NOT NULL,
    stars           TINYINT,                    -- 1-5
    rating          DECIMAL(3,2) DEFAULT 0,
    review_count    INT DEFAULT 0,
    description     TEXT,
    main_image      VARCHAR(512),
    phone           VARCHAR(32),
    email           VARCHAR(128),
    check_in_time   TIME DEFAULT '14:00:00',
    check_out_time  TIME DEFAULT '12:00:00',
    status          TINYINT DEFAULT 1,          -- 1:在线 0:下线
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_city (city_id, status, stars),
    INDEX idx_rating (rating, status),
    INDEX idx_location (lat, lng)
);

CREATE TABLE hotel_facility (
    hotel_id        BIGINT,
    facility_id     INT,
    PRIMARY KEY (hotel_id, facility_id)
);

CREATE TABLE hotel_image (
    image_id        BIGINT PRIMARY KEY AUTO_INCREMENT,
    hotel_id        BIGINT NOT NULL,
    url             VARCHAR(512) NOT NULL,
    sort_order      INT DEFAULT 0,
    category        VARCHAR(32),                -- EXTERIOR/LOBBY/ROOM/RESTAURANT
    INDEX idx_hotel (hotel_id, sort_order)
);

-- ============ 房型 ============
CREATE TABLE room_type (
    room_type_id    BIGINT PRIMARY KEY,
    hotel_id        BIGINT NOT NULL,
    name            VARCHAR(128) NOT NULL,
    name_en         VARCHAR(128),
    description     TEXT,
    bed_type        VARCHAR(32),                -- SINGLE/DOUBLE/KING/TWIN
    area_sqm        INT,
    max_guests      TINYINT DEFAULT 2,
    floor_info      VARCHAR(64),
    breakfast_included TINYINT DEFAULT 0,
    free_cancellation  TINYINT DEFAULT 1,
    cancel_hours_before INT DEFAULT 24,         -- 免费取消提前小时数
    total_rooms     INT NOT NULL,               -- 该房型的房间总数
    status          TINYINT DEFAULT 1,
    INDEX idx_hotel (hotel_id, status)
);

-- ============ 房价与库存 (核心表) ============
CREATE TABLE room_inventory (
    inventory_id    BIGINT PRIMARY KEY AUTO_INCREMENT,
    room_type_id    BIGINT NOT NULL,
    date            DATE NOT NULL,
    total_rooms     INT NOT NULL,               -- 当天该房型可用总数
    booked_rooms    INT NOT NULL DEFAULT 0,     -- 已预订数量
    price           INT NOT NULL,               -- 当天价格(分)
    currency        VARCHAR(3) DEFAULT 'CNY',
    status          TINYINT DEFAULT 1,          -- 1:可售 0:不可售(关房)
    version         INT DEFAULT 0,              -- 乐观锁版本号
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_room_date (room_type_id, date),
    INDEX idx_date (date)
);

-- ============ 预订 ============
CREATE TABLE booking (
    booking_id      VARCHAR(32) PRIMARY KEY,    -- BKG_20250101_000001
    user_id         BIGINT NOT NULL,
    hotel_id        BIGINT NOT NULL,
    room_type_id    BIGINT NOT NULL,
    check_in        DATE NOT NULL,
    check_out       DATE NOT NULL,
    rooms           INT NOT NULL DEFAULT 1,
    guest_info      JSON NOT NULL,              -- 入住人信息
    status          VARCHAR(16) NOT NULL,       -- PENDING/CONFIRMED/CANCELLED/CHECKED_IN/COMPLETED
    total_amount    INT NOT NULL,
    discount_amount INT DEFAULT 0,
    paid_amount     INT NOT NULL,
    currency        VARCHAR(3) DEFAULT 'CNY',
    payment_status  VARCHAR(16) DEFAULT 'UNPAID', -- UNPAID/PAID/REFUNDED
    payment_method  VARCHAR(16),
    special_requests TEXT,
    cancel_deadline TIMESTAMP,
    cancelled_at    TIMESTAMP,
    cancel_reason   VARCHAR(256),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user (user_id, created_at),
    INDEX idx_hotel (hotel_id, check_in),
    INDEX idx_status (status),
    INDEX idx_payment_deadline (payment_deadline, payment_status)
);

CREATE TABLE booking_room (
    booking_room_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    booking_id      VARCHAR(32) NOT NULL,
    room_type_id    BIGINT NOT NULL,
    date            DATE NOT NULL,
    price           INT NOT NULL,
    INDEX idx_booking (booking_id),
    INDEX idx_room_date (room_type_id, date)
);

-- ============ 城市表 ============
CREATE TABLE city (
    city_id         INT PRIMARY KEY,
    name            VARCHAR(64) NOT NULL,
    name_en         VARCHAR(64),
    country         VARCHAR(64),
    country_code    VARCHAR(2),
    timezone        VARCHAR(32),
    lat             DOUBLE,
    lng             DOUBLE,
    status          TINYINT DEFAULT 1
);
```

### Redis 缓存结构

```
=== 搜索缓存 ===
# 城市搜索结果页缓存 (仅缓存第一页)
STRING  search:{city_id}:{check_in}:{check_out}:{guests}:default
  value: JSON(top 200 hotels)
  TTL: 5分钟

# 如果带筛选条件, 缓存条件组合
STRING  search:{city_id}:{check_in}:{check_out}:{guests}:{filter_hash}
  TTL: 10分钟

=== 酒店详情缓存 ===
# 酒店基础信息
HASH    hotel:{hotel_id}
  name, stars, rating, address, lat, lng, description, images_json, ...

# 房型信息
HASH    hotel:{hotel_id}:room_types
  {room_type_id}_name, {room_type_id}_json, ...

# 房价&库存 (实时数据, 短TTL)
HASH    inventory:{room_type_id}:{date}
  total, booked, price  (当天有效, TTL=24h)

=== 库存 CAS 操作 ===
# 原子扣减库存
Lua Script:
  local key = KEYS[1]  -- inventory:{roomTypeId}:{date}
  local qty = tonumber(ARGV[1])
  local total = redis.call('HGET', key, 'total')
  local booked = redis.call('HGET', key, 'booked')

  if tonumber(total) - tonumber(booked) >= qty then
      redis.call('HINCRBY', key, 'booked', qty)
      return 1  -- 成功
  end
  return 0  -- 库存不足

=== 预订信息缓存 ===
HASH    booking:{booking_id}
  status, hotel_id, check_in, check_out, total_amount, ...

=== 热门酒店排行 ===
ZSET    hot:hotels:{city_id}
  {hotel_id}: {click_score}
  ZREVRANGE 获取 TOP N
  TTL: 15分钟刷新

=== 汇率缓存 ===
STRING  fx:USD:CNY -> "7.25"
  TTL: 1小时
```

---

## 高层次架构

### 系统架构图

```
+-----------------------------------------------------------------------+
|                          CDN (全局加速)                                |
|                  (酒店图片 / 静态资源 / 搜索预渲染)                      |
+-----------------------------------+-----------------------------------+
                                    |
+-----------------------------------v-----------------------------------+
|                         Load Balancer                                  |
+--+--------+--------+--------+--------+--------+--------+-------------+
   |        |        |        |        |        |        |
+--v----+ +-v-----+ +v------+ +v------+ +v------+ +v------+ +v--------+
| Search| |Hotel  | |Room   | |Booking| |Payment| |User   | |Review   |
| Service| |Detail | |Price  | |Service| |Service| |Service| |Service  |
+--+----+ +-+-----+ +--+----+ +---+---+ +---+---+ +---+---+ +---+-----+
   |        |          |          |         |         |         |
   +---+----+----------+----------+---------+---------+---------+
       |               |          |         |         |
+------v---------------v----------v---------v---------v----------------+
|                           数据层                                       |
|  +----------+ +----------+ +-----------+ +----------+ +-----------+   |
|  | Redis    | | MySQL    | | ES Search | | Kafka    | | S3/OSS    |   |
|  | (库存+   | | (主数据)  | | (搜索索引) | | (异步)   | | (图片存储) |   |
|  |  缓存)   | |           | |           | |          | |           |   |
|  +----------+ +----------+ +-----------+ +----------+ +-----------+   |
+-----------------------------------------------------------------------+

+--------------------------+     +------------------------------------+
|   库存管理后台             |     |   离线数据 (Hive/Spark)            |
|  (酒店方调价/关房)        |     |   - 价格预测/推荐算法              |
+--------------------------+     |   - 热门酒店分析                  |
                                 |   - 用户画像/个性化推荐            |
                                 +------------------------------------+
```

### 预订核心流程

```
用户App/Web         Booking Service       Inventory Service       Payment Service       MQ
     |                    |                      |                      |                |
     | ① POST /bookings   |                      |                      |                |
     |------------------->|                      |                      |                |
     |                    | ② 参数校验+价格计算     |                      |                |
     |                    |  (入住/离店/人数)      |                      |                |
     |                    |  (价格查询+优惠计算)    |                      |                |
     |                    |                      |                      |                |
     |                    | ③ 预占库存(原子操作)    |                      |                |
     |                    |--------------------->|                      |                |
     |                    |                      | 遍历 date in         |                |
     |                    |                      | [check_in, check_out) |                |
     |                    |                      |                      |                |
     |                    |                      | 检查每日库存 >= rooms |                |
     |                    |                      | 若某天不足 -> ROLLBACK|                |
     |                    |                      | (之前天数释放)        |                |
     |                    |                      |                      |                |
     |                    |                      | UPDATE inventory     |                |
     |                    |                      | SET booked += rooms  |                |
     |                    |                      | WHERE version = ?    |                |
     |                    |                      | (乐观锁防并发)        |                |
     |                    |                      |                      |                |
     |                    | <-- 库存预占成功 -----|                      |                |
     |                    |                      |                      |                |
     |                    | ④ 创建订单记录         |                      |                |
     |                    | INSERT booking       |                      |                |
     |                    | INSERT booking_room  |                      |                |
     |                    | status = CONFIRMED   |                      |                |
     |                    |                      |                      |                |
     |                    | ⑤ 发送预订成功事件     |                      |                |
     |                    |-------------------------------------------------------------->
     |                    |                      |                      |  发送确认邮件    |
     |                    |                      |                      |  短信通知等     |
     |                    |                      |                      |                |
     |                    | ⑥ 15min未支付检查      |                      |                |
     |                    | (延迟消息,如果需即时支付)|                      |                |
     |                    |-------------------------------------------------------------->
     |                    |                      |                      |                |
     | <-- 预订确认 --------|                      |                      |                |
     | (booking_id,       |                      |                      |                |
     |  金额, 取消截止日)   |                      |                      |                |
```

---

## 核心深入

### 1. 库存管理 (核心)

```
=== 库存模型 ===

酒店库存是 "多日连续库存" 问题

库存表: room_inventory(room_type_id, date, total, booked, price)

# 查询某个房型在日期区间的库存
SELECT date, total_rooms, booked_rooms, price
FROM room_inventory
WHERE room_type_id = 'RT001'
  AND date >= '2025-03-15'
  AND date < '2025-03-17'  -- 不包含离店日
  AND status = 1
ORDER BY date;

=== 库存扣减 (ACID 事务 + 乐观锁) ===

BEGIN;
-- 锁定日期区间内的所有库存行
SELECT date, total_rooms, booked_rooms, version
FROM room_inventory
WHERE room_type_id = 'RT001'
  AND date >= '2025-03-15'
  AND date < '2025-03-17'
FOR UPDATE;  -- 行锁, 按主键排序避免死锁

-- 逐日检查
for each row:
    if row.total - row.booked < request.rooms:
        ROLLBACK;
        return "库存不足";

-- 逐日扣减
for each row:
    UPDATE room_inventory
    SET booked_rooms = booked_rooms + request.rooms,
        version = version + 1
    WHERE inventory_id = row.id
      AND version = row.version;  -- 乐观锁校验
    if affected_rows == 0:
        ROLLBACK;
        return "库存变更,请重试";

INSERT INTO booking (...) VALUES (...);
INSERT INTO booking_room (...) VALUES (...);
COMMIT;

=== 跨房型兜底扣减 ===
如果用户选择"A房型", 但该日期A房型不足:
  1. 检查同酒店B房型是否有库存
  2. 提供 "升级房型" 选项
  3. 用户确认后在B房型上扣减库存

=== Redis 缓存库存 ===
// 库存热点用 Redis 防 MySQL 行锁热点
Lua 脚本:
  local dates = cjson.decode(ARGV[1])  -- {"2025-03-15","2025-03-16"}
  local qty = tonumber(ARGV[2])

  for i, date in ipairs(dates) do
      local key = "inventory:" .. KEYS[1] .. ":" .. date
      local booked = tonumber(redis.call('HGET', key, 'booked') or 0)
      local total = tonumber(redis.call('HGET', key, 'total') or 0)

      if total - booked < qty then
          -- 回滚之前的扣减
          for j = 1, i-1 do
              local rollbackKey = "inventory:" .. KEYS[1] .. ":" .. dates[j]
              redis.call('HINCRBY', rollbackKey, 'booked', -qty)
          end
          return 0
      end

      redis.call('HINCRBY', key, 'booked', qty)
  end
  return 1

// Redis 成功后异步写 MySQL DB + 发送 MQ 确认
```

### 2. 房价管理

```
=== 房价策略 ===

1. 基础价格: 酒店方设定
   room_inventory.price = base_price (按日期不同)

2. 动态调价 (Revenue Management):
   根据以下因素调整:
     - 入住率: 70%以下 -> 降价吸引; 90%以上 -> 提价
     - 提前预订天数: 越早订 -> 越便宜 (早期优惠)
     - 工作日/周末/节假日: 周末加价
     - 竞争酒店价格: 低于竞品
     - 特殊事件: 演唱会/展会 -> 大幅提价

   价格公式:
   finalPrice = basePrice
              × occupancyMultiplier (0.8~2.0)
              × advanceMultiplier (0.7~1.5)
              × dayOfWeekMultiplier (0.9~1.5)
              × seasonMultiplier (0.8~3.0)

3. 价格缓存:
   Redis: price:{roomTypeId}:{date} -> {finalPrice}
   每天凌晨由离线任务计算当天价格
   实时调整时延迟 < 1分钟
```

### 3. 搜索优化

```
=== 搜索流程分层 ===

Layer 1: 城市范围确定
  获取所有目标城市的酒店ID列表
  Redis: city:{cityId}:hotels -> SET of hotel_ids

Layer 2: 库存过滤 (最重)
  过滤出所有日期内都有库存的房型
  Redis Pipeline:
    for hotel in relevant_hotels:
        for roomType in hotel.roomTypes:
            for date in [checkIn, checkOut):
                GET inventory:{roomTypeId}:{date}

Layer 3: 排序
  按价格/评分/距离/热度排序

Layer 4: 补充分页
  OFFSET/LIMIT

=== Elasticsearch 搜索优化 ===

ES Mappings:
{
  "hotel": {
    "properties": {
      "hotel_id": {"type": "long"},
      "name": {"type": "text", "analyzer": "standard"},
      "city_id": {"type": "integer"},
      "stars": {"type": "integer"},
      "rating": {"type": "float"},
      "coordinates": {"type": "geo_point"},
      "facilities": {"type": "keyword"},
      "min_price": {"type": "integer"},
      "check_in": {"type": "date"},
      "check_out": {"type": "date"}
    }
  }
}

问题: ES 本身不支持复杂的库存逻辑
方案: ES 做文本检索 + 初步过滤, 再用 MySQL/Redis 做精确库存过滤

=== 预计算 + 缓存 ===

每天凌晨预计算:
  - 每个城市 未来60天 每天的价格最低的 TOP 200 酒店
  - 缓存到 Redis sorted set
  - 搜索时直接返回, 再补充分页

Redis:
  search:beijing:2025-03-15:2025-03-17:2guest:default -> [H001, H023, ...]

当用户有筛选条件时 (stars=5, facilities=pool):
  从缓存结果中内存过滤 (TOP 200 已经足够丰富)
  如果结果不足1页 -> 再回源搜索
```

### 4. 支付与退款

```
=== 支付模式 ===

模式A: 即时支付 (Pay Now)
  预订时立即支付 -> status=PAID
  如果 15min 内未支付 -> status=CANCELLED + 释放库存

模式B: 到店支付 (Pay Later/Pay at Hotel)
  预订时不支付 -> status=CONFIRMED
  需要信用卡担保(预授权)
  到店时支付或离店时支付

模式C: 混合
  部分预付 + 到店付余款

=== 取消与退款 ===

取消流程:
  1. 用户请求取消
  2. 检查取消政策:
     cancelDeadline = checkInDate - cancelHoursBefore
     if now() < cancelDeadline:
         免费取消 -> 全额退款
     else:
         部分退款(如第一晚房费)
  3. 更新 booking status=CANCELLED
  4. 释放库存:
     for date in [checkIn, checkOut):
         UPDATE room_inventory
         SET booked_rooms = booked_rooms - rooms
         WHERE room_type_id = ? AND date = ?
  5. 退款:
     if paid_amount > 0:
         调用支付网关退款
         booking.payment_status = REFUNDED
  6. 发送取消确认

=== 退款幂等 ===
  同一 booking_id 不能重复退款
  查询 booking 状态:
    if status == CANCELLED or payment_status == REFUNDED:
        return refundResult  -- 幂等返回
```

### 5. 并发控制与超售防止

```
=== 库存的并发问题 ===

场景: 100 用户同时预订最后一间房

方案A: 悲观锁 (DB 行锁) - 简单直接
  SELECT ... FOR UPDATE 锁定库存行
  + 绝对不超售
  - 并发能力差, 容易死锁

方案B: 乐观锁 (version 字段) - 推荐
  UPDATE inventory SET booked = booked + 1, version = version + 1
  WHERE room_type_id = ? AND date = ? AND version = oldVersion
  如果 affected_rows = 0 -> 重试

方案C: Redis 原子扣减 - 高性能
  Lua 脚本原子 check-and-deduct
  + 单机 10万+ QPS
  - 需要最终一致性保证

方案D: 库存池 (连接池模式) - 秒杀场景
  预分配 N 个库存名额到 MQ
  用户从池中领取一个名额 -> 成功后扣减 DB

推荐: Redis (热点) + DB 乐观锁 (最终)
  Redis 前置扣减 ( 10万+ QPS)
  DB 异步同步 (1000 QPS)
  定时对账 (每小时)
```

---

## 扩展性与高可用

### 1. 多语言多币种

```
=== 多语言支持 ===

酒店信息本地化表:
CREATE TABLE hotel_i18n (
    hotel_id    BIGINT,
    locale      VARCHAR(5),     -- zh-CN/en-US/ja-JP
    name        VARCHAR(256),
    address     VARCHAR(512),
    description TEXT,
    PRIMARY KEY (hotel_id, locale)
);

API 响应根据 Accept-Language header 选择语言

=== 多币种 ===

价格基准货币: 酒店所在国家货币 (如 CNH/CNY)
展示货币: 用户偏好 (可在 Profile 中设置)

汇率获取:
  Redis: fx:{base}:{target} -> rate
  从外部 API (如 Fixer/ExchangeRates API) 每小时更新
  预订时锁定价 (booking 中存储当时汇率)
```

### 2. 数据库分片

```
=== 分片策略 ===

按 city_id 分库 (16库):
  dbIndex = city_id % 16
  
  同一个城市的所有酒店/房型/库存在一个库中
  搜索时只需查一个库

订单独自分库 (按 user_id):
  dbIndex = user_id % 16
  
  用户查订单 -> 一个库
  酒店查订单 -> 查多个库(低频, 可接受)

=== 历史数据归档 ===
  booking: 6个月前的订到 -> 迁移到归档库(Hive)
  booking_room: 同上
  inventory: 过去日期的库存 -> 归档
```

### 3. 图片存储

```
=== 酒店图片管理 ===

用户上传流程:
  1. 客户端上传原图到 CDN/S3
  2. 图片处理服务:
     - 生成多尺寸缩略图 (200x200, 400x300, 800x600, 1920x1080)
     - 压缩优化 (WebP 格式, quality=80)
     - 水印(可选)
  3. 存储到 S3, URL 写入 MySQL
  4. CDN 预热

图片 URL 格式:
  https://img.example.com/hotels/{hotel_id}/{size}/{hash}.webp
  size: thumb/small/medium/large

路由规则:
  - 列表页: thumb(200x200)
  - 详情页缩略: small(400x300)
  - 详情页主图: large(1920x1080)
  - 全屏查看: 原图
```

### 4. 监控与告警

```
=== 关键指标 ===

搜索:
  - 搜索 QPS / P99 延迟
  - 搜索返回空结果率
  - 搜索 -> 详情页转化率
  - 缓存命中率

库存:
  - 库存扣减 QPS
  - 库存不足返回率
  - 库存扣减成功率
  - 超售事件 (应为0)

预订:
  - 预订 QPS / 预订成功率
  - 预订转化率 (搜索->详情->预订)
  - 取消率
  - 平均房价 (ADR)
  - 入住率 (Occupancy Rate)

支付:
  - 支付成功率
  - 退款 QPS/成功率
  - 支付渠道可用性

系统:
  - 各服务 GC 暂停时间 / CPU/内存
  - MySQL 慢查询 / 主从延迟
  - Redis 内存 / 命中率
  - Kafka Lag

告警:
  - 预订成功率 < 90% (可能库存问题)
  - 超售检测 (booked > total)
  - 库存不一致 (Redis vs MySQL)
  - 搜索 P99 > 1s (连续5分钟)
  - 支付成功率 < 95%
```

---

## 总结

设计酒店预订系统需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **库存模型** | room_inventory (room_type_id, date, total, booked) + 日期区间行锁 |
| **并发控制** | Redis Lua 原子扣减(热点) + MySQL 行锁(兜底) + 乐观锁版本号 |
| **搜索** | ES 全文检索 + Redis 预计算热点搜索 + 内存过滤筛选条件 |
| **定价** | 固定基础价 + 动态调价(供需/提前/节假日) + 离线计算+实时调整 |
| **支付** | 即时支付/到店支付/混合 + 支付超时取消 + 退款幂等 |
| **取消** | 免费取消截止 + 阶梯退款 + 库存释放 + 确定性状态机 |
| **去重/防超售** | Redis CAS + DB 行锁 + 定时每日对账 |

关键面试问答：
1. **如何保证一间房不被两个人同时预订？** — DB 行锁 SELECT FOR UPDATE + 乐观锁(version) + Redis Lua 前置原子扣减
2. **酒店库存模型怎么设计？** — room_inventory(room_type_id, date, total, booked)，多日连续库存 = 逐日检查+扣减
3. **搜索怎么实现？** — ES 做全文检索和基础过滤，再用 Redis/MySQL 做精确库存过滤，最后结果排序分页
4. **价格动态调整怎么做？** — 每晚离线计算未来60天的调价系数(入住率/提前预订/周末/节假日/竞品)，实时微调
5. **取消预订怎么处理？** — 检查取消政策 -> 计算退款金额 -> 释放库存 -> 退款 -> 通知用户
6. **支付超时未支付怎么处理？** — 支付截止时间 + 定时扫描超时订单 + 自动取消 + 释放库存 + 通知用户
