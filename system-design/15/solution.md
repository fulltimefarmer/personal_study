# 设计电商系统 (Design E-commerce System)

## 题目

设计一个大型电商系统，类似 Amazon / 淘宝。涵盖商品浏览、搜索、购物车、下单、支付、库存管理等核心流程，支持高并发和水平扩展。

---

## 需求澄清

### 功能性需求

| 模块 | 功能描述 |
|------|----------|
| 用户系统 | 注册/登录/个人信息/收货地址管理 |
| 商品管理 | 商品 CRUD/分类/属性/SKU 管理 |
| 商品搜索 | 关键词搜索/分类浏览/筛选/排序 |
| 商品详情 | 商品详情页(图片/描述/价格/库存/评价) |
| 购物车 | 添加/删除/修改数量/选中结算 |
| 下单 | 创建订单/库存扣减/支持优惠券/满减 |
| 支付 | 对接支付网关(支付宝/微信支付)/支付回调 |
| 库存管理 | 库存扣减/回补/预占/安全库存预警 |
| 订单管理 | 订单状态流转/查询/取消/退款 |
| 物流 | 发货/物流单号/轨迹追踪 |
| 评价系统 | 商品评价/评分/晒图 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 可用性 | 99.99% (核心链路: 下单/支付) |
| 响应时间 | 页面加载 P99 < 2s, API P99 < 200ms |
| 并发能力 | 秒杀场景支撑百万 QPS |
| 一致性 | 库存扣减强一致，订单最终一致 |
| 安全性 | HTTPS + 数据加密 + 防刷/防作弊 |
| 可扩展性 | 微服务化, 独立服务可独立扩展 |

### 容量估算

```
假设 (对标中型电商):
  - DAU: 5000万
  - 商品 SKU: 1亿
  - 日订单量: 200万
  - 大促峰值: 日常的 10-50 倍

商品存储 (MySQL):
  每个商品: ~10KB (基础信息+SKU+图片URL+属性)
  总存储: 1亿 × 10KB = 1TB
  索引: ~30% = 300GB
  总: ~1.3TB

订单存储 (MySQL):
  日订单 200万, 每条 ~2KB
  日增量: 200万 × 2KB = 4GB
  年增量: 4GB × 365 ≈ 1.5TB
  归档策略: 3个月热数据, 1年温数据, 归档到 Hive

图片存储 (对象存储):
  平均每商品 5 张图, 每张 ~200KB
  总存储: 1亿 × 5 × 200KB = 100TB

QPS 估算:
  商品详情页: 5000万 × 3次 / 86400 = 1736 QPS (平均)
  搜索: 5000万 × 2次 / 86400 = 1157 QPS (平均)
  下单: 200万 / 86400 = 23 QPS (平均)
  大促峰值: 日常 × 50
    详情页: 1736 × 50 = 86,800 QPS
    搜索: 1157 × 50 = 57,850 QPS
    下单: 23 × 50 = 1,150 QPS

购物车 QPS:
  5000万 × 5次(加购/查看/修改) / 86400 = 2894 QPS (平均)
  峰值: 2894 × 50 = 144,700 QPS
```

---

## API设计

### 商品服务

```
=== 商品搜索 ===
GET /api/v1/products/search
params:
  - q: string              // 关键词
  - category_id: int       // 分类
  - brand_id: int          // 品牌
  - price_min/price_max    // 价格范围
  - sort: string           // price_asc/price_desc/sales/rating/newest
  - page: int, size: int   // 分页

Response:
{
  "total": 12345,
  "products": [
    {
      "product_id": "P001",
      "title": "iPhone 15 Pro Max 256GB",
      "category": "手机通讯/智能手机",
      "brand": "Apple",
      "min_price": 999900,          // 分(最小SKU价格)
      "max_price": 1299900,
      "main_image": "https://cdn.xxx/p001.jpg",
      "sales": 52341,
      "rating": 4.8,
      "tags": ["5G", "钛金属", "A17 Pro"]
    }
  ],
  "filters": {
    "brands": [...],
    "price_ranges": [...],
    "attributes": [...]
  }
}

=== 商品详情 ===
GET /api/v1/products/{product_id}

Response:
{
  "product_id": "P001",
  "spu": {                          // SPU 信息
    "title": "iPhone 15 Pro Max",
    "description": "...",
    "brand": "Apple",
    "category_tree": [1, 10, 25],
    "images": ["url1", "url2", ...],
    "attributes": {
      "屏幕尺寸": "6.7英寸",
      "处理器": "A17 Pro",
      ...
    },
    "rating": 4.8,
    "review_count": 23456
  },
  "skus": [                         // SKU 列表
    {
      "sku_id": "S001",
      "spec": {"颜色": "原色钛金属", "存储": "256GB"},
      "price": 999900,
      "original_price": 1099900,
      "stock": 230,
      "status": "on_sale"
    },
    {
      "sku_id": "S002",
      "spec": {"颜色": "蓝色钛金属", "存储": "512GB"},
      "price": 1199900,
      "original_price": 1299900,
      "stock": 0,                  // 无库存
      "status": "on_sale"
    }
  ]
}

=== 商品分类列表 ===
GET /api/v1/categories           // 所有一级分类
GET /api/v1/categories/{id}/children  // 子分类
```

### 购物车服务

```
=== 购物车操作 ===
GET /api/v1/cart                      // 获取购物车

POST /api/v1/cart/items
{
  "sku_id": "S001",
  "quantity": 2
}

PUT /api/v1/cart/items/{item_id}
{
  "quantity": 3
}

DELETE /api/v1/cart/items/{item_id}

PUT /api/v1/cart/items/batch-select   // 批量选中/取消
{
  "item_ids": ["item_1", "item_3"],
  "selected": true
}

DELETE /api/v1/cart/clear             // 清空购物车

Response:
{
  "items": [
    {
      "item_id": "cart_item_001",
      "sku_id": "S001",
      "spu_id": "P001",
      "title": "iPhone 15 Pro Max 256GB 原色钛金属",
      "image": "https://cdn.xxx/p001.jpg",
      "price": 999900,
      "quantity": 2,
      "selected": true,
      "stock": 230,
      "promotion": { "type": "直降", "discount": 10000 }
    }
  ],
  "total_count": 5,
  "selected_total": 1999800           // 选中商品金额(分)
}
```

### 订单服务

```
=== 创建订单 ===
POST /api/v1/orders
{
  "address_id": "ADDR_001",
  "items": [
    {"sku_id": "S001", "quantity": 2, "cart_item_id": "cart_item_001"},
    {"sku_id": "S003", "quantity": 1}
  ],
  "coupon_code": "COUPON_XMAS2025",   // 可选
  "remark": "请发顺丰"
}

Response:
{
  "order_id": "ORD_20250101_000001",
  "total_amount": 2499700,            // 总金额(分)
  "discount_amount": 50000,           // 优惠金额
  "actual_amount": 2449700,           // 实付
  "status": "PENDING_PAYMENT",
  "expire_time": "2025-01-01T12:30:00Z"  // 支付超时时间
}

=== 订单列表/详情 ===
GET /api/v1/orders?status=PENDING_PAYMENT&page=1
GET /api/v1/orders/{order_id}

=== 订单状态流转 ===
PUT /api/v1/orders/{order_id}/cancel  // 取消订单
PUT /api/v1/orders/{order_id}/confirm-receipt  // 确认收货
```

### 支付服务

```
=== 发起支付 ===
POST /api/v1/payments
{
  "order_id": "ORD_20250101_000001",
  "pay_method": "ALIPAY",           // ALIPAY / WECHAT_PAY
  "return_url": "https://xxx.com/result"
}

Response:
{
  "payment_id": "PAY_001",
  "pay_url": "https://alipay.com/...",  // H5支付页
  "qr_code": "https://...",            // 扫码支付二维码
  "status": "WAITING"
}

=== 支付回调 (第三方 -> 我方) ===
POST /api/v1/payments/callback/alipay
{
  "trade_no": "2025010122001412345",
  "out_trade_no": "ORD_20250101_000001",
  "total_amount": 24497.00,
  "status": "SUCCESS",
  "sign": "..."                       // 验签字段
}
```

---

## 数据模型

### 核心数据库表

```sql
-- ============ 商品域 ============

-- SPU 表 (Standard Product Unit)
CREATE TABLE spu (
    spu_id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    title           VARCHAR(256) NOT NULL,
    subtitle        VARCHAR(512),
    category_id     INT NOT NULL,
    brand_id        INT,
    description     TEXT,                    -- 图文详情 (HTML)
    main_image      VARCHAR(512),
    status          TINYINT DEFAULT 1,       -- 1:上架 0:下架
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category_id, status),
    INDEX idx_brand (brand_id),
    FULLTEXT INDEX idx_title (title)
);

-- SKU 表 (Stock Keeping Unit)
CREATE TABLE sku (
    sku_id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    spu_id          BIGINT NOT NULL,
    spec            JSON NOT NULL,           -- {"颜色":"原色","存储":"256GB"}
    price           INT NOT NULL,            -- 售价(分)
    original_price  INT,                     -- 原价(分)
    cost_price      INT,                     -- 成本价(分)
    stock           INT NOT NULL DEFAULT 0,  -- 库存
    locked_stock    INT NOT NULL DEFAULT 0,  -- 锁定库存(下单未支付)
    sold_count      INT DEFAULT 0,           -- 销量
    image           VARCHAR(512),
    status          TINYINT DEFAULT 1,
    INDEX idx_spu (spu_id),
    INDEX idx_status (status)
);

-- 分类表 (邻接表 + 路径枚举混合)
CREATE TABLE category (
    category_id     INT PRIMARY KEY,
    name            VARCHAR(64) NOT NULL,
    parent_id       INT NOT NULL DEFAULT 0,
    level           TINYINT NOT NULL,        -- 1/2/3级
    path            VARCHAR(128) NOT NULL,   -- "1/10/25" 路径枚举
    sort_order      INT DEFAULT 0,
    INDEX idx_parent (parent_id),
    INDEX idx_path (path)
);

-- ============ 订单域 ============

-- 订单主表
CREATE TABLE orders (
    order_id        VARCHAR(32) PRIMARY KEY, -- ORD_20250101_000001
    user_id         BIGINT NOT NULL,
    status          VARCHAR(32) NOT NULL,     -- PENDING_PAYMENT/PAID/SHIPPED/DELIVERED/CANCELLED
    total_amount    INT NOT NULL,            -- 总金额(分)
    discount_amount INT DEFAULT 0,
    freight_amount  INT DEFAULT 0,
    actual_amount   INT NOT NULL,            -- 实付(分)
    pay_method      VARCHAR(16),
    pay_time        TIMESTAMP NULL,
    address_snapshot JSON NOT NULL,          -- 收货地址快照
    expire_time     TIMESTAMP NOT NULL,       -- 支付超时时间
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_status (user_id, status),
    INDEX idx_created (created_at),
    INDEX idx_expire (expire_time, status)
);

-- 订单明细表
CREATE TABLE order_item (
    order_item_id   BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id        VARCHAR(32) NOT NULL,
    sku_id          BIGINT NOT NULL,
    spu_id          BIGINT NOT NULL,
    title           VARCHAR(256) NOT NULL,   -- 商品标题快照
    spec            JSON NOT NULL,
    price           INT NOT NULL,            -- 下单时价格快照
    quantity        INT NOT NULL,
    total_price     INT NOT NULL,
    image           VARCHAR(512),
    INDEX idx_order (order_id)
);

-- 订单日志表 (状态流转记录)
CREATE TABLE order_log (
    log_id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id        VARCHAR(32) NOT NULL,
    from_status     VARCHAR(32),
    to_status       VARCHAR(32) NOT NULL,
    operator        VARCHAR(64),            -- user/system
    remark          VARCHAR(512),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order (order_id)
);

-- ============ 购物车 ============

-- 购物车表 (持久化存储)
CREATE TABLE cart_item (
    item_id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id         BIGINT NOT NULL,
    sku_id          BIGINT NOT NULL,
    spu_id          BIGINT NOT NULL,
    quantity        INT NOT NULL DEFAULT 1,
    selected        TINYINT NOT NULL DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_sku (user_id, sku_id),
    INDEX idx_user (user_id)
);

-- ============ 库存扣减日志 ============
CREATE TABLE inventory_log (
    log_id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    sku_id          BIGINT NOT NULL,
    order_id        VARCHAR(32) NOT NULL,
    change_type     VARCHAR(16) NOT NULL,    -- LOCK/UNLOCK/DEDUCT/RESTORE
    change_amount   INT NOT NULL,
    before_stock    INT NOT NULL,
    after_stock     INT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sku (sku_id),
    INDEX idx_order (order_id)
);

-- ============ 用户域 (简化) ============
CREATE TABLE user (
    user_id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    nickname        VARCHAR(64),
    avatar          VARCHAR(512),
    phone           VARCHAR(16) UNIQUE,
    email           VARCHAR(128),
    password_hash   VARCHAR(256) NOT NULL,
    status          TINYINT DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_address (
    address_id      BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id         BIGINT NOT NULL,
    receiver_name   VARCHAR(64) NOT NULL,
    phone           VARCHAR(16) NOT NULL,
    province        VARCHAR(32),
    city            VARCHAR(32),
    district        VARCHAR(32),
    detail          VARCHAR(256),
    is_default      TINYINT DEFAULT 0,
    INDEX idx_user (user_id)
);

-- ============ 分库分表策略 ============
-- orders: 按 user_id 哈希分 16 库
-- 单库按时间再次分表: orders_202501, orders_202502, ...
-- order_item: 与 orders 同库同表策略
-- sku stock: 独立库存服务, 放在 Redis 中
```

### 缓存数据结构

```
=== Redis 缓存设计 ===

# 商品详情缓存
HASH  product:{spu_id}
  title, main_image, description, category_id, brand_id, ...
  TTL: 1小时

# SKU 库存缓存
HASH  stock:{sku_id}
  total: 230
  locked: 5
  available: 225
  TTL: 永不过期(数据通过库存服务维护)

# SKU 价格缓存
STRING  price:{sku_id}  ->  "999900"
  TTL: 5分钟

# 购物车缓存
HASH  cart:{user_id}
  {sku_id}: 2     -- sku_id -> quantity
HASH  cart:{user_id}:selected
  {sku_id}: 1     -- sku_id -> 是否选中
HASH  cart:{user_id}:meta
  item_ids: "sku_1,sku_2"
  TTL: 30天

# 用户会话/Token
STRING  token:{user_id}  ->  "access_token_value"
  TTL: 30天(可刷新)

# 分类树缓存
STRING  category:tree  -> JSON (全部分类树)
  TTL: 1小时

# 热榜/推荐
ZSET   hot:products  -> {product_id: score}
  TTL: 15分钟刷新

# 防重复下单
STRING  order:dedup:{user_id}:{request_id}  ->  1
  TTL: 5分钟
```

---

## 高层次架构

### 微服务架构图

```
                              +-------------------+
                              |   API Gateway     |
                              |  (Kong / APISIX)  |
                              +--------+----------+
                                       |
                +----------------------+----------------------+
                |                      |                       |
+---------------v-------+  +----------v---------+  +----------v---------+
|   用户服务             |  |   商品服务           |  |   搜索服务           |
|  (注册/登录/地址)      |  |  (SPU/SKU/分类)     |  |  (ES Search)        |
+-----------------------+  +--------------------+  +--------------------+
                |                      |                       |
+---------------v-------+  +----------v---------+  +----------v---------+
|   购物车服务           |  |   库存服务           |  |   订单服务           |
|  (Redis + MySQL)      |  |  (Redis 库存扣减)    |  |  (下单/状态机)       |
+-----------------------+  +--------------------+  +--------------------+
                |                      |                       |
+---------------v-------+  +----------v---------+  +----------v---------+
|   支付服务             |  |   物流服务           |  |   推荐/评价服务      |
|  (对接支付网关)        |  |  (发货/轨迹查询)     |  |  (协同过滤/评分)     |
+-----------------------+  +--------------------+  +--------------------+
                                       |
                         +-------------+-------------+
                         | 消息中间件 (Kafka/RMQ)     |
                         |                              |
                         |  订单创建 -> 库存扣减确认     |
                         |  支付成功 -> 发货通知        |
                         |  退款请求 -> 库存回补        |
                         +-----------------------------+
                                       |
                         +-------------+-------------+
                         | 数据平台 (离线)             |
                         | Hive/Spark/Flink           |
                         | 报表 / 数据看板 / 用户画像  |
                         +-----------------------------+
```

### 下单核心流程

```
用户                Gateway          订单服务          库存服务         支付服务       MQ
 |                    |                 |                 |               |           |
 |  ① POST /orders    |                 |                 |               |           |
 |------------------->|                 |                 |               |           |
 |                    |  ② 创建订单      |                 |               |           |
 |                    |---------------->|                 |               |           |
 |                    |                 | ③ 参数校验       |               |           |
 |                    |                 | (商品/地址/库存) |               |           |
 |                    |                 |                 |               |           |
 |                    |                 | ④ 预占库存       |               |           |
 |                    |                 |---------------->|               |           |
 |                    |                 |                 | 检查库存       |           |
 |                    |                 |                 | stock >= qty  |           |
 |                    |                 |                 | stock -= qty  |           |
 |                    |                 |                 | locked += qty |           |
 |                    |                 | <OK, remaining=N|               |           |
 |                    |                 |                 |               |           |
 |                    |                 | ⑤ 生成订单       |               |           |
 |                    |                 | INSERT orders   |               |           |
 |                    |                 | INSERT order_items              |           |
 |                    |                 | status=PENDING_PAYMENT          |           |
 |                    |                 | expire=30min                    |           |
 |                    |                 |                 |               |           |
 |                    |                 | ⑥ 发送订单创建事件              |           |
 |                    |                 |--------------------------------------------->|
 |                    |                 |                 |               | 延迟消息    |
 |                    |                 |                 |               | 30min超时   |
 |                    |                 |                 |               |            |
 |                    |<--- 返回订单-----|                 |               |           |
 | <-- 订单详情 ------|                 |                 |               |           |
 |                    |                 |                 |               |           |
 |  ⑦ POST /payments |                 |                 |               |           |
 |------------------->|                                 |               |           |
 |                    | ⑧ 发起支付------------------------>|               |           |
 |                    |                 |                 | ⑨ 调第三方支付 |           |
 |                    |                 |                 |---------------|           |
 |                    |                 |                 | <--支付页URL---|           |
 | <-- 支付URL -------|                 |                 |               |           |
 |                    |                 |                 |               |           |
 |  用户完成支付...    |                 |                 |               |           |
 |                    |                 |                 |               |           |
 |                    |                 |                 | ⑩ 支付回调      |           |
 |                    |                 |                 |<--------------|           |
 |                    |                 |                 |               |           |
 |                    |                 | ⑾ 支付成功事件   |               |           |
 |                    |                 |<----------------------------------|           |
 |                    |                 |                 |               |           |
 |                    |                 | ⑿ 更新订单状态   |               |           |
 |                    |                 | PENDING -> PAID |               |           |
 |                    |                 |                 |               |           |
 |                    |                 | ⒀ 实际扣库存     |               |           |
 |                    |                 |---------------->|               |           |
 |                    |                 |                 | locked -= qty |           |
 |                    |                 |                 | total -= qty  |           |
 |                    |                 |                 |               |           |
 |                    |                 | ⒁ 发送发货通知   |               |           |
 |                    |                 |--------------------------------------------->|
```

---

## 核心深入

### 1. 库存扣减方案

```
=== 方案A: 数据库行锁 (SELECT ... FOR UPDATE) ===
BEGIN;
SELECT stock FROM sku WHERE sku_id = 1 FOR UPDATE;
-- check stock >= quantity
UPDATE sku SET stock = stock - quantity WHERE sku_id = 1;
INSERT INTO order_item ...;
COMMIT;

优点: 强一致，实现简单
缺点: DB 压力大，行锁竞争严重，并发能力差
适用: QPS < 1000

=== 方案B: Redis 缓存库存 + 异步同步 DB (推荐) ===

下单流程:
  1. Redis Lua 脚本原子扣减:
     local stock = redis.call('HGET', KEYS[1], 'available')
     if tonumber(stock) >= tonumber(ARGV[1]) then
         redis.call('HINCRBY', KEYS[1], 'available', -ARGV[1])
         redis.call('HINCRBY', KEYS[1], 'locked', ARGV[1])
         return 1  -- 成功
     end
     return 0  -- 库存不足

  2. 成功 -> 写入订单到 DB
  3. 失败 -> 无需回滚 (Redis 未修改)

支付完成后:
  4. Redis Lua 脚本:
     redis.call('HINCRBY', KEYS[1], 'locked', -ARGV[1])
     redis.call('HINCRBY', KEYS[1], 'total', -ARGV[1])

支付超时/取消:
  5. 回补库存:
     redis.call('HINCRBY', KEYS[1], 'locked', -ARGV[1])
     redis.call('HINCRBY', KEYS[1], 'available', ARGV[1])

Redis 库存结构:
HASH stock:S001
  total: 10000          -- 总库存
  available: 9500       -- 可售库存 (total - locked)
  locked: 500           -- 锁定库存 (下单未支付)

=== Redis 库存与 DB 最终一致性 ===
定时 Job (每分钟):
  for each sku in modified_sku_set:
      db_stock = SELECT stock FROM sku WHERE sku_id = ?
      redis_stock = HGETALL stock:{sku_id}
      if db_stock != redis_stock.total:
          -- 以 DB 为准, 或报警人工介入
          alert("库存不一致: sku={sku_id}")

=== 方案C: 库存分桶 (秒杀专用) ===
将库存分成 N 个桶:
Redis:
  stock:S001:bucket:0 -> 500
  stock:S001:bucket:1 -> 500
  ...

用户请求随机路由到某个桶:
  bucket = hash(user_id) % N
  DECR stock:S001:bucket:{bucket}

优点: 分散热点，避免单 Key 竞争
缺点: 库存扣减不够精确
```

### 2. 订单状态机

```
订单状态流转:

                   +-----------+
                   | 待付款     |
                   | PENDING    |
                   | PAYMENT    |
                   +-----+-----+
            user_pay      |         expire/cancel
        +-----------------+--------------+
        |                                |
        v                                v
+-------+--------+            +----------+---------+
|    已支付       |            |     已取消          |
|    PAID        |            |    CANCELLED        |
+-------+--------+            +--------------------+
        |                                ^
        | merchant_ship                  | refund
        v                                |
+-------+--------+            +----------+---------+
|    已发货       |            |     退款处理中      |
|    SHIPPED     |----------> |    REFUNDING        |
+-------+--------+  refund    +----------+---------+
        |                                |
        | confirm_receipt                | complete
        v                                v
+-------+--------+            +----------+---------+
|    已完成       |            |     已退款          |
|    DELIVERED   |            |    REFUNDED         |
+----------------+            +--------------------+

状态机实现 (Saga 模式):
  OrderSaga {
      createOrder() -> PENDING_PAYMENT
      pay() -> PAID
      ship() -> SHIPPED
      confirm() -> DELIVERED

      补偿操作:
      cancel() -> CANCELLED (回补库存)
      refund() -> REFUNDING -> REFUNDED
  }
```

### 3. 支付超时取消 (延迟队列)

```
=== 方案A: RocketMQ 延迟消息 (推荐) ===
下单时发送延迟消息:
  msg.setDelayTimeLevel(16)  // 30min 延迟
  mq.send(msg, {orderId: xxx})

消费者:
  msg = mq.receive("order_pay_timeout")
  orderId = msg.orderId

  order = db.get(orderId)
  if order.status == "PENDING_PAYMENT":
      关闭订单:
        order.status = "CANCELLED"
        回补库存: Redis HINCRBY stock:{sku_id} available {qty}
                     Redis HINCRBY stock:{sku_id} locked -{qty}

=== 方案B: Redis 过期回调 ===
SET order:timeout:{order_id} 1 EX 1800  -- 30min过期
通过 Redis Keyspace Notification 监听过期事件
config: notify-keyspace-events Ex

缺点: Redis 过期回调不可靠，可能丢失

=== 方案C: 定时扫描 (兜底) ===
每分钟扫描:
SELECT order_id FROM orders
WHERE status = 'PENDING_PAYMENT'
  AND expire_time < NOW()
LIMIT 1000

批量关闭订单 + 回补库存
```

### 4. 商品搜索架构

```
+---------------------------------------------------------+
|                    ES 搜索集群                            |
|                                                         |
|  +-------------------+  +-------------------+            |
|  |   Primary Shard 0  |  |   Primary Shard 1  |   ...    |
|  |   (商品0-5000万)   |  |   (商品5000万-1亿) |         |
|  +---------+---------+  +---------+---------+            |
|            |                       |                     |
|  +---------v---------+  +---------v---------+            |
|  |   Replica 0       |  |   Replica 1       |            |
|  +-------------------+  +-------------------+            |
+---------------------------------------------------------+
         ^                       ^
         |                       |
+--------+-------+     +---------+--------+
|  Search Service |     |  Search Service  |
|  (查询构建)      |     |  (结果处理)      |
+--------+-------+     +---------+--------+
         |                       |
         +-------+-------+-------+
                 |       |
         +-------v-------v-------+
         |   数据同步 (Canal)      |
         |   MySQL Binlog -> ES   |
         +-----------------------+

=== 搜索 query 构建 ===
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": { "query": "手机", "boost": 3 } } },
        { "match": { "description": "手机" } }
      ],
      "filter": [
        { "term": { "status": 1 } },
        { "term": { "category_id": 25 } },
        { "range": { "price": { "gte": 500000, "lte": 1000000 } } },
        { "range": { "stock": { "gt": 0 } } }  -- 有库存
      ]
    }
  },
  "sort": [
    { "sales": "desc" },     -- 按销量
    { "_score": "desc" }     -- 按相关度
  ],
  "aggs": {
    "brands": { "terms": { "field": "brand_id" } },
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 200000 }, { "from": 200000, "to": 500000 },
          { "from": 500000, "to": 1000000 }, { "from": 1000000 }
        ]
      }
    }
  }
}
```

### 5. 大促/秒杀架构

```
=== 秒杀关键设计 ===

1. 前端限流
   - 按钮置灰 + 倒计时 + 防重复点击
   - 客户端答题/验证码

2. 网关层
   - Nginx 限流: limit_req_zone $binary_remote_addr rate=5r/s
   - 防刷: IP 黑名单 + 设备指纹

3. 服务层
   - 秒杀令牌 (令牌桶):
     提前生成 N 个秒杀令牌, 放入 Redis List
     RPOP seckill:tokens  -> 抢到令牌才进入下单
   - 限流降级: Sentinel / Hystrix

4. 数据层
   - Redis 库存扣减 (Lua 原子)
   - 库存预热: 大促前将库存加载到 Redis
   - 下单异步化: 先返回"排队中", MQ 异步处理订单

=== 秒杀架构图 ===
+-----------+     +------------+     +--------------+
|  Nginx    | --> | API Gateway| --> | 秒杀Token服务 |
| (限流/WAF)|     | (鉴权+限流) |     | (Redis List) |
+-----------+     +------------+     +------+-------+
                                            |
                                      (持有Token)
                                            |
+-----------+     +------------+     +------v-------+
|  用户端    | <-- | 秒杀服务    | --> | Redis 库存   |
| (排队等待) |     | (下单处理)  |     | (Lua 扣减)   |
+-----------+     +------+-----+     +------+-------+
                         |                   |
                         v                   v
                  +-------------+     +------------+
                  | Kafka (削峰) | --> | 订单消费者  |
                  +-------------+     +-----+------+
                                            |
                                            v
                                     +------------+
                                     | MySQL 订单  |
                                     | (异步写入)  |
                                     +------------+
```

### 6. 防重复下单

```
=== 幂等性保证 ===

1. 前端防重:
   - 下单按钮点击后 disabled + loading
   - 防抖: 300ms 内只触发一次

2. 服务端防重 (Token机制):
   进入下单页时:
     token = UUID.random()
     Redis: SET order:token:{user_id} {token} EX 300

   提交订单时:
     带上 token
     if not Redis: DEL order:token:{user_id} == 1:
         return "请勿重复提交"
     // token 删除成功 -> 首次提交, 继续下单

3. 数据库唯一约束:
   UNIQUE KEY uk_order_dedup (user_id, spu_id, sku_id, created_date)
   -- 同一用户同一天同商品不能重复创建订单
   -- INSERT 失败 -> 返回重复下单

4. 支付回调幂等:
   根据 out_trade_no (订单号) 做幂等:
   if order.status in ("PAID", "SHIPPED", "DELIVERED"):
       return "SUCCESS"  -- 已处理, 直接返回成功

=== 下单请求去重 ===
// requestId 由客户端生成, 全局唯一
String requestKey = "order:dedup:" + requestId;
if (redis.setnx(requestKey, "1", 300)) {
    // 首次请求, 执行下单
    try {
        createOrder(...);
    } catch (Exception e) {
        redis.del(requestKey);  // 失败删除, 允许重试
        throw e;
    }
} else {
    // 重复请求, 返回已有结果
    String cachedResult = redis.get("order:result:" + requestId);
    return JSON.parse(cachedResult);
}
```

---

## 扩展性与高可用

### 1. 数据库分库分表

```
=== 分库分表策略 ===

orders 表:
  - 分库键: user_id % 16  (16个库)
  - 分表键: 按月分表 (orders_202501, orders_202502, ...)

  优势:
    - 按用户查询订单: 路由到单个库
    - 按订单号查询: 通过订单号反解 user_id
     (order_id 中包含 user_id 信息)
    - 按月分表: 历史数据归档方便

order_item 表:
  - 与 orders 同库同分表策略
  - 通过 order_id 关联

spu / sku 表:
  - 按 spu_id 哈希分库 (读多写少, 无需频繁扩缩容)
  - 或: 按 category_id 分库 (同一分类在一个库, 方便管理)

=== 分布式ID ===
order_id 生成: Snowflake + 业务含义
结构: 日期(8位) + 机器位(2位) + 序号(8位) + 用户ID末4位
例如: 20250101-01-00000001-1234

好处:
  - 从 order_id 可反解日期和用户, 方便路由
  - 趋势递增, 对 MySQL B+Tree 友好
```

### 2. 读写分离与多级缓存

```
=== 读写分离 ===
+----------+         +----------+
|  Master  | ------> |  Slave   |
|  (写)    |  主从复制 |  (读)    |
+----------+         +----------+
     ^                     ^
     |                     |
 写操作路由             读操作路由

商品详情: 99% 读, 优先走 Slave + Redis 缓存
库存扣减: 必须走 Redis (Lua原子) + Master DB

=== 多级缓存穿透保护 ===
请求 -> 本地缓存(Caffeine,1min) -> Redis(5min) -> DB(带布隆过滤器)
                     |                    |              |
                   miss                 miss           miss
                     v                    v              v
           - 热点商品永远缓存             - 重建缓存      - 查DB
           - TTL短(1min),减少不一致      - 互斥锁防击穿  - 更新Redis
```

### 3. 服务降级与熔断

```
=== 降级策略 ===

大促期间降级预案:
  1. 非核心服务关闭:
     - 评价/收藏/足迹 -> 降级(不可用)
     - 推荐算法 -> 降级到热门推荐
     - 用户画像 -> 降级到通用模板

  2. 读降级:
     - 商品详情: 返回Redis缓存数据(即使是旧数据)
     - 搜索: 降级到热门搜索词推荐
     - 购物车: 读缓存, 不调用库存服务

  3. 写降级:
     - 库存: 只有库存充足的SKU可下单
     - 评价: 异步写入MQ, 延迟展示
     - 日志: 采样(只记录1%请求)

=== 熔断配置 ===
@SentinelResource(value = "createOrder",
    fallback = "createOrderFallback",
    blockHandler = "createOrderBlockHandler")

createOrderFallback:
  // 依赖服务异常时的降级处理
  return R.error("系统繁忙, 请稍后再试")

// 熔断规则: 1s内错误率 > 50% -> 熔断10s
CircuitBreakerRule rule = new CircuitBreakerRule()
    .setGrade(RuleConstant.GRADE_EXCEPTION_RATIO)
    .setCount(0.5)
    .setTimeWindow(10)
    .setMinRequestAmount(20)
    .setStatIntervalMs(1000);
```

### 4. 监控与告警

```
=== 关键指标 ===

业务指标:
  - 下单成功 QPS / 下单成功率
  - 支付转化率 (Paid / Created)
  - 客单价
  - 退款率
  - 库存售罄 SKU 数量
  - 订单各状态数量分布

技术指标:
  - 各服务 QPS / P99延迟 / 错误率
  - Redis 命中率 / 内存使用
  - ES 搜索延迟 / 索引延迟
  - DB 连接池使用率 / 慢查询 / 主从延迟
  - MQ 消息积压 / 消费延迟
  - JVM GC 暂停时间

告警规则:
  - 下单成功率 < 95%
  - 支付转化率 < 正常值的80%
  - 库存扣减失败率 > 1%
  - Redis 库存与 DB 偏差 > 阈值
  - 数据库主从延迟 > 5s
  - MQ 积压 > 10万条
  - 任何服务 P99 > 500ms (非大促期间)

=== 全链路追踪 ===
TraceId 贯穿:
  Nginx -> Gateway -> Service A -> Service B -> Redis/DB/MQ
  使用 SkyWalking / Jaeger / Zipkin
  Log 中打印 TraceId, 方便问题排查
```

---

## 总结

设计电商系统需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **架构** | 微服务拆分(用户/商品/订单/库存/支付) + 领域驱动设计 |
| **库存** | Redis Lua 原子扣减 + DB 异步同步 + 定时对账 |
| **订单** | 有限状态机 + Saga 模式 + 延迟队列(超时取消) |
| **搜索** | ES 全文搜索 + 分类过滤器 + 聚合 + Canal 实时同步 |
| **缓存** | 多级(本地+Redis) + 穿透/击穿/雪崩保护 |
| **高并发** | 秒杀令牌 + 库存分桶 + MQ 削峰 + 异步下单 |
| **一致性** | 下单幂等(Token/唯一约束) + 支付对账 + 库存对账 |
| **大促** | 降级(非核心关闭) + 熔断 + 限流 + 压测准备 |

关键面试问答：
1. **如何保证库存不超卖？** — Redis Lua 原子 `check-and-deduct` + DB 行锁 `SELECT FOR UPDATE` 兜底
2. **下单 -> 支付流程怎么设计？** — 下单预占库存(RDB+Redis) -> 生成订单(PENDING) -> 支付回调 -> 确认扣库存 -> 触发发货
3. **未支付订单怎么处理？** — 延迟消息(RocketMQ 30min) -> 检查状态 -> 关闭订单 + 回补库存
4. **大促秒杀怎么设计？** — 前端限流 + 令牌桶 + Redis 库存分桶 + MQ 异步削峰 + 降级预案 + 全链路压测
5. **分库分表怎么设计？** — 按 user_id 分库(用户维度查询) + 按月分表(归档) + order_id 包含路由信息
6. **如何保证数据一致性？** — 核心流程强一致(Redis Lua + DB事务) + 非核心最终一致(MQ + 补偿) + 定时对账
