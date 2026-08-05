# 设计打车/网约车服务 (Design Ride-Sharing Service)

## 题目

设计一个网约车服务，类似 Uber / 滴滴出行。支持乘客发起叫车、司机接单、实时位置追踪、行程计费、评价等核心流程。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 乘客叫车 | 乘客输入目的地，发起叫车请求 |
| 司机匹配 | 系统匹配附近可用司机 |
| 司机接单 | 司机接受/拒绝行程 |
| 实时位置 | 实时追踪司机和乘客位置 |
| 行程导航 | 路径规划 + 预计到达时间 |
| 计费 | 按距离/时间/动态定价计算费用 |
| 支付 | 行程结束后自动扣费 |
| 评价 | 乘客/司机互评 |
| 历史行程 | 查看历史行程记录 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 延迟 | 司机匹配 P99 < 5s, 位置更新 < 2s |
| 可用性 | 99.99% |
| 实时性 | 位置更新频率: 每 3-5 秒 |
| 精度 | GPS 定位精度 5-20m |
| 并发 | 支持百万级同时在线司机+乘客 |
| 安全 | 数据加密 + 隐私保护 + 行程录音 |
| 一致性 | 司机状态强一致，行程状态最终一致 |

### 容量估算

```
假设 (一个城市):
  - DAU: 500万
  - 日订单: 200万
  - 在线司机: 50万
  - 同时在线乘客: 100万

QPS 估算:
  叫车: 200万 / 86400 = 23 QPS (平均)
  峰值(早/晚高峰): 200万 / (4 × 3600) × 2 = 278 QPS (高峰2小时占比40%)
  实际峰值 QPS: 278 × 3 = 834 QPS

位置上报 (最重):
  在线司机: 50万 × 1次/4s = 12.5万 QPS
  行程中司机: 10万(20%在线) × 1次/2s = 5万 QPS
  总位置上报: 17.5万 QPS

存储:
  行程记录: 200万 × 2KB = 4GB/天 ≈ 1.5TB/年
  位置轨迹: 每行程100个点 × 200字节 = 200万×20KB = 40GB/天 (保留7天)
  司机位置: 50万 × 200B = 100MB (Redis内存)

带宽:
  位置上报: 17.5万 QPS × 200B = 35 MB/s = 280 Mbps
```

---

## API设计

### 乘客端 API

```
=== 发起叫车 ===
POST /api/v1/rides/request
{
  "start_lat": 39.9242,
  "start_lng": 116.5118,
  "end_lat": 39.9542,
  "end_lng": 116.4918,
  "product_type": "PREMIUM",    // EXPRESS/PREMIUM/CARPOOL
  "payment_method": "WALLET",
  "passenger_count": 1
}

Response:
{
  "ride_id": "RIDE_20250101_00001",
  "status": "SEARCHING",
  "search_timeout": 60,          // 寻找超时秒数
  "nearby_drivers": 15,          // 附近可用司机数
  "eta_min": 180,                // 预计最快到达秒数
  "eta_max": 420,
  "price_estimate": {            // 预估价格
    "base_fare": 1000,           // 起步价(分)
    "distance_fare": 2500,
    "time_fare": 800,
    "surge_multiplier": 1.5,     // 动态加价倍数
    "total_estimate": 6450
  }
}

=== 查询叫车状态 ===
GET /api/v1/rides/{ride_id}/status

Response:
{
  "ride_id": "RIDE_20250101_00001",
  "status": "MATCHED",            // SEARCHING/MATCHED/ARRIVED/STARTED/COMPLETED/CANCELLED
  "driver": {
    "driver_id": "D_001",
    "name": "张师傅",
    "rating": 4.8,
    "car_plate": "京A12345",
    "car_model": "丰田凯美瑞",
    "car_color": "白色",
    "photo_url": "https://..."
  },
  "driver_location": {
    "lat": 39.9250,
    "lng": 116.5120
  },
  "eta_seconds": 180
}

=== 取消叫车 ===
POST /api/v1/rides/{ride_id}/cancel
{
  "reason": "等待时间过长"
}
```

### 司机端 API

```
=== 位置上报 ===
POST /api/v1/drivers/location
{
  "driver_id": "D_001",
  "lat": 39.9250,
  "lng": 116.5120,
  "bearing": 90,             // 方向角度
  "speed": 12.5,              // km/h
  "timestamp": 1704067200000,
  "accuracy": 8.5             // GPS精度(m)
}

=== 状态更新 ===
PUT /api/v1/drivers/status
{
  "driver_id": "D_001",
  "status": "ONLINE"            // OFFLINE/ONLINE/BUSY/TRIP
}

=== 接受/拒绝叫车 ===
POST /api/v1/rides/{ride_id}/accept
POST /api/v1/rides/{ride_id}/decline

=== 行程开始/结束 ===
POST /api/v1/rides/{ride_id}/start-trip
{
  "start_lat": 39.9242,
  "start_lng": 116.5118
}

POST /api/v1/rides/{ride_id}/complete-trip
{
  "end_lat": 39.9542,
  "end_lng": 116.4918,
  "toll_fee": 1500              // 过路费(分)
}

Response:
{
  "ride_id": "RIDE_20250101_00001",
  "distance_km": 8.5,
  "duration_minutes": 22,
  "fare_breakdown": {
    "base_fare": 1000,
    "distance_fare": 2550,       // 8.5km × 3元/km
    "time_fare": 880,            // 22min × 0.4元/min
    "surge_fee": 2215,           // (基础费) × 0.5
    "toll_fee": 1500,
    "total": 8145
  },
  "status": "COMPLETED"
}
```

### 地图/导航 API (内部)

```
=== 路径规划 ===
GET /api/v1/maps/route
params: start_lat, start_lng, end_lat, end_lng
Response:
{
  "distance_m": 8500,
  "duration_s": 1320,            // 预计时间
  "polyline": "encoded_polyline_string",
  "steps": [...]
}

=== ETA 预估 ===
GET /api/v1/maps/eta
params: from_lat, from_lng, to_lat, to_lng
Response: { "eta_seconds": 180, "distance_m": 1500 }
```

---

## 数据模型

### 核心数据库表

```sql
-- ============ 司机表 ============
CREATE TABLE driver (
    driver_id       BIGINT PRIMARY KEY,
    phone           VARCHAR(16) UNIQUE NOT NULL,
    name            VARCHAR(64),
    avatar_url      VARCHAR(512),
    rating          DECIMAL(3,2) DEFAULT 5.00,
    ride_count      INT DEFAULT 0,
    status          VARCHAR(16) DEFAULT 'OFFLINE',  -- OFFLINE/ONLINE/BUSY/TRIP
    lat             DOUBLE,                     -- 最新位置(存在Redis)
    lng             DOUBLE,
    bearing         INT,
    speed           DOUBLE,
    last_location_at TIMESTAMP,
    city_id         INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE driver_vehicle (
    vehicle_id      BIGINT PRIMARY KEY,
    driver_id       BIGINT,
    plate_number    VARCHAR(16) NOT NULL,
    car_brand       VARCHAR(64),
    car_model       VARCHAR(64),
    car_color       VARCHAR(16),
    car_year        INT,
    vehicle_type    VARCHAR(32) NOT NULL,       -- EXPRESS/PREMIUM/SUV
    status          TINYINT DEFAULT 1,           -- 1:正常 0:审核中 -1:禁用
    INDEX idx_driver (driver_id)
);

-- ============ 乘客表 ============
CREATE TABLE passenger (
    passenger_id    BIGINT PRIMARY KEY,
    phone           VARCHAR(16) UNIQUE NOT NULL,
    name            VARCHAR(64),
    rating          DECIMAL(3,2) DEFAULT 5.00,
    payment_methods JSON,                        -- [WALLET, CARD, ...]
    home_lat        DOUBLE,
    home_lng        DOUBLE,
    work_lat        DOUBLE,
    work_lng        DOUBLE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ 行程表 ============
CREATE TABLE ride (
    ride_id         VARCHAR(32) PRIMARY KEY,    -- RIDE_20250101_00001
    passenger_id    BIGINT NOT NULL,
    driver_id       BIGINT,
    status          VARCHAR(32) NOT NULL,       -- SEARCHING/MATCHED/ARRIVED/ON_TRIP/COMPLETED/CANCELLED
    product_type    VARCHAR(16) NOT NULL,        -- EXPRESS/PREMIUM/CARPOOL
    request_lat     DOUBLE NOT NULL,
    request_lng     DOUBLE NOT NULL,
    pickup_lat      DOUBLE,
    pickup_lng      DOUBLE,
    dest_lat        DOUBLE NOT NULL,
    dest_lng        DOUBLE NOT NULL,
    pickup_address  VARCHAR(256),
    dest_address    VARCHAR(256),
    matched_at      TIMESTAMP,
    arrived_at      TIMESTAMP,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    cancelled_at    TIMESTAMP,
    cancel_reason   VARCHAR(128),
    cancelled_by    VARCHAR(16),                -- PASSENGER/DRIVER/SYSTEM
    distance_km     DOUBLE,                     -- 实际里程
    duration_min    INT,                        -- 实际时间(分钟)
    fare            INT,                        -- 实收金额(分)
    fare_detail     JSON,                       -- 费用明细
    payment_status  VARCHAR(16),                -- UNPAID/PAID/REFUNDED
    passenger_rating DECIMAL(3,2),
    driver_rating   DECIMAL(3,2),
    INDEX idx_passenger (passenger_id, created_at),
    INDEX idx_driver (driver_id, created_at),
    INDEX idx_status (status)
) PARTITION BY RANGE (TO_DAYS(created_at));

-- ============ 行程轨迹表 (时序数据) ============
CREATE TABLE ride_track (
    track_id        BIGINT PRIMARY KEY AUTO_INCREMENT,
    ride_id         VARCHAR(32) NOT NULL,
    lat             DOUBLE NOT NULL,
    lng             DOUBLE NOT NULL,
    bearing         INT,
    speed           DOUBLE,
    accuracy        DOUBLE,
    event_type      VARCHAR(16),                -- POS/DEST_REACHED/START_TOLL
    recorded_at     TIMESTAMP NOT NULL,
    INDEX idx_ride (ride_id, recorded_at)
) PARTITION BY RANGE (TO_DAYS(recorded_at));
```

### Redis 数据结构

```
=== 司机位置 (GeoHash + 元数据) ===

# 司机实时位置 (按城市)
GEOADD  drivers:beijing:location  <lng> <lat> <driver_id>

# 按车辆类型分片
GEOADD  drivers:beijing:express     <lng> <lat> <driver_id>
GEOADD  drivers:beijing:premium     <lng> <lat> <driver_id>

# 司机详情
HASH    driver:{driver_id}
  name, phone, rating, ride_count,
  status, lat, lng, bearing, speed,
  vehicle_plate, vehicle_model, vehicle_color,
  last_location_at, city_id

# 可用司机集合 (活跃 + 非行程中 + 非派单中)
SET     drivers:beijing:available

# 正在叫车匹配中的行程
STRING  driver:match:{driver_id} -> ride_id
  TTL: 60s

=== 行程状态 ===
HASH    ride:{ride_id}
  status, passenger_id, driver_id,
  request_lat, request_lng, dest_lat, dest_lng,
  matched_at, arrived_at, started_at,
  current_lat, current_lng (实时位置),
  distance_km, fare_estimate

=== 动态定价 (Surge Pricing) ===
# 区域热度 (每500m网格)
STRING  surge:beijing:grid_{geohash_5}
  value: 1.0 ~ 3.0 (加价倍数)
  TTL: 5分钟

# 供需比
ZSET    surge:beijing:demand:{geohash_5}
  value: request_count (过去1分钟的请求数)
ZSET    surge:beijing:supply:{geohash_5}
  value: available_drivers

=== 匹配队列 (如果无司机立即匹配) ===
ZSET    ride:queue:beijing:express
  member: ride_id | score: timestamp (按等待时间排序)
```

---

## 高层次架构

### 系统架构图

```
+---------------------------------------------------------------------+
|                         API Gateway (Kong)                           |
+----------+----------+----------+----------+----------+--------------+
           |          |          |          |          |
     +-----v----+ +---v------+ +v--------+ +v--------+ +v----------+
     |Passenger | | Driver   | | Ride    | | Payment | | Map/Nav   |
     | Service  | | Service  | | Service | | Service | | Service   |
     +----+-----+ +----+-----+ +----+----+ +----+----+ +----+------+
          |            |            |           |           |
          +------+-----+------+-----+-----+-----+-----+-----+
                 |           |           |           |
     +-----------v-----------v-----------v-----------v-----------+
     |                    数据层                                   |
     |  +----------+ +----------+ +----------+ +---------------+  |
     |  | Redis    | | MySQL    | | Kafka    | | Object Store  |  |
     |  | Cluster  | | Shards   | | Cluster  | | (S3/OSS)      |  |
     |  +----------+ +----------+ +----------+ +---------------+  |
     +-------------------------------------------------------------+
                          |           |
     +--------------------v-----------v--------------------------+
     |                 实时数据管道                                 |
     |  +--------------------------------------------------------+ |
     |  | WebSocket/Apollo (实时推送: 匹配/位置/状态)              | |
     |  +--------------------------------------------------------+ |
     +-------------------------------------------------------------+
```

### 叫车匹配流程

```
乘客App            乘客服务           匹配引擎         司机位置索引      司机服务          司机App
   |                  |                  |                  |               |               |
   | ① 请求叫车        |                  |                  |               |               |
   |----------------->|                  |                  |               |               |
   |                  | ② 创建行程        |                  |               |               |
   |                  | ride.status=     |                  |               |               |
   |                  | SEARCHING        |                  |               |               |
   |                  |                  |                  |               |               |
   |                  | ③ 请求匹配        |                  |               |               |
   |                  |----------------->|                  |               |               |
   |                  |                  |                  |               |               |
   |                  |                  | ④ 搜索附近司机    |               |               |
   |                  |                  | GEORADIUS        |               |               |
   |                  |                  | drivers:beijing  |               |               |
   |                  |                  | radius=3000m     |               |               |
   |                  |                  |----------------->|               |               |
   |                  |                  | <-- candidates   |               |               |
   |                  |                  |                  |               |               |
   |                  |                  | ⑤ 筛选过滤        |               |               |
   |                  |                  | - 状态: AVAILABLE |               |               |
   |                  |                  | - 不在行程中      |               |               |
   |                  |                  | - 未被派单        |               |               |
   |                  |                  | - 司机评分过滤    |               |               |
   |                  |                  | - 计算ETA        |               |               |
   |                  |                  | - TopK排序        |               |               |
   |                  |                  |                  |               |               |
   |                  |                  | ⑥ 按距离分批派单  |               |               |
   |                  |                  | 第1批: 前3名      |               |               |
   |                  |                  | (每批等待10-15s)  |               |               |
   |                  |                  |                  |               |               |
   |                  |                  | ⑦ 发送叫车请求    |               |               |
   |                  |                  |-------------------------------------------->|
   |                  |                  |                  |               | ⑧ 显示叫车卡|
   |                  |                  |                  |               |   (10-15s)  |
   |                  |                  |                  |               |   司机响应   |
   |                  |                  |                  |               |   接收/拒绝  |
   |                  |                  |                  |               |               |
   |                  |                  | ⑨ 司机接受        |               |               |
   |                  |                  |<----------------------------------------------|
   |                  |                  |                  |               |               |
   |                  |                  | ⑩ 更新状态        |               |               |
   |                  |                  | driver=BUSY      |               |               |
   |                  |                  | ride=MATCHED     |               |               |
   |                  |                  | 锁定10s(防同抢)   |               |               |
   |                  |                  |                  |               |               |
   |                  | ⑾ 通知匹配成功    |                  |               |               |
   |<-----------------|                  |                  |               |               |
   |                  |                  |                  |               |               |
   | ⑿ 显示司机信息    |                  |                  |               | ⒀ 导航到乘客  |
   |<--实时位置更新--->|                  |                  |               |<--实时位置--->|
```

### 位置更新流程

```
司机App              WebSocket              Redis            行程消费者
  |                     |                    |                  |
  | ① 位置上报(每4秒)   |                    |                  |
  | GEO 数据 + 状态     |                    |                  |
  |-------------------->|                    |                  |
  |                     | ② GEOADD           |                  |
  |                     | drivers:bj         |                  |
  |                     |------------------->|                  |
  |                     |                    |                  |
  |                     | ③ HMSET driver:{id}|                  |
  |                     | status/lat/lng...  |                  |
  |                     |------------------->|                  |
  |                     |                    |                  |
  |                     | ④ 如果在行程中      |                  |
  |                     | PUSH Kafka         |                  |
  |                     | ride-track topic   |                  |
  |                     |------------------------------------->|
  |                     |                    |      ⑤ 持久化轨迹|
  |                     |                    |      MySQL写入   |
  |                     |                    |                  |
  | ⑥ 如果匹配中        |                    |                  |
  |                     | PUSH WebSocket     |                  |
  |                     | 给乘客: 司机位置    |                  |
  |<--------------------|                    |                  |
```

---

## 核心深入

### 1. 司机匹配算法

```
=== 搜索与筛选流程 ===

function findNearbyDrivers(lat, lng, productType, city):
    // Step 1: GeoHash 粗筛
    geoHash = encode(lat, lng, 5)  // ±2.4km精度
    grids = [geoHash] + getNeighbors(geoHash) // 9宫格
    candidateIds = []

    // Step 2: Redis Geo 精确搜索
    driversKey = "drivers:{city}:{productType}"
    for grid in grids:
        // ZSet range by GeoHash score
        minHash = geohash.get(grid, 0) // 网格左下
        maxHash = geohash.get(grid, 4095) // 网格右上
        candidates = redis.zrangebyscore(driversKey, minHash, maxHash)
        candidateIds.extend(candidates)

    // Step 3: 并行获取司机详情 + 过滤
    drivers = parallelGet(candidateIds, id ->
        redis.hgetall("driver:" + id)
    )

    filtered = drivers.filter(driver ->
        driver.status == "AVAILABLE" and
        driver.rating >= 4.2 and
        !redis.exists("driver:match:" + id) and // 未在派单中
        计算直线距离 < 5000m
    )

    // Step 4: 计算 ETA (最重的计算)
    etas = parallelGet(filtered, driver ->
        mapService.getETA(driver.lat, driver.lng, lat, lng)
    )

    // Step 5: 综合排序
    for (driver, eta) in filtered zip etas:
        driver.score = (
            w1 * (1 / eta.seconds) +           // ETA 权重 50%
            w2 * (driver.rating / 5.0) +       // 评分权重 20%
            w3 * (1 / (1 + driver.ride_count)) + // 新司机倾斜 10%
            w4 * 当前区域匹配  +                  // 区域偏好 20%
        )

    sorted = sortByScore(filtered)
    return sorted[:50] // 取前50名候选

=== 分批派单策略 ===

def dispatchRide(candidates, rideId, batchSize=3, batchTimeout=15):
    ride = db.get(rideId)
    startTime = now()

    for i in range(0, len(candidates), batchSize):
        if ride.status != "SEARCHING":
            break  // 已被取消或已匹配

        batch = candidates[i : i + batchSize]

        // Step 1: 标记司机(防止同时被多个行程锁定)
        locked = []
        for driver in batch:
            if redis.setnx("driver:match:" + driver.id, rideId, 15):
                locked.append(driver)

        if not locked:
            continue

        // Step 2: 通过 WebSocket 推送给司机
        for driver in locked:
            websocket.push(driver.id, {
                type: "NEW_RIDE_REQUEST",
                ride_id: rideId,
                pickup_address: ride.pickupAddress,
                dest_address: ride.destAddress,
                pickup_lat: ride.pickupLat,
                pickup_lng: ride.pickupLng,
                fare_estimate: ride.fareEstimate,
                distance_to_passenger: 1500,
                timeout: batchTimeout
            })

        // Step 3: 等待司机响应
        result = waitForResponse(locked, batchTimeout * 1000)

        if result.acceptedDriver:
            assignDriver(result.acceptedDriver, ride)
            return

        // Step 4: 释放未被接受的司机的锁
        for driver in locked:
            if driver != result.acceptedDriver:
                redis.del("driver:match:" + driver.id)

        // Step 5: 等待超时后, 派发给下一批

    // 所有候选司机都拒绝 -> 扩大搜索半径
    if expandedSearch(ride, radius=5000):
        retry()

    // 仍无司机 -> 叫车失败
    ride.status = "NO_DRIVER"
    notifyPassenger("附近暂无可用司机")
```

### 2. 司机状态机

```
              +-----------------+
              |     OFFLINE     |
              |   (司机离线)     |
              +--------+--------+
                       |
                driver_online (APP上线)
                       |
                       v
              +-----------------+
        +---->|     ONLINE      |
        |     |  (可接单状态)    |
        |     +--------+--------+
        |              |
        |   ride_accepted (接受行程)
        |              |
        |              v
        |     +-----------------+
        |     |     BUSY        |
        |     |  (已接单,前往接驾)|
        |     +--------+--------+
        |              |
        |    passenger_picked_up (乘客上车)
        |              |
        |              v
        |     +-----------------+
        |     |    ON_TRIP      |
        |     |  (行程进行中)    |
        |     +--------+--------+
        |              |
        |    trip_completed (行程结束)
        |              |
        |              v
        |     +-----------------+
        +-----|     ONLINE      |
              |  (回到在线状态)  |
              +-----------------+

状态转换与并发控制:
  - ONLINE -> BUSY: 必须原子 CAS (Compare and Set)
    redis: if driver:status == "ONLINE":
             driver:status = "BUSY"
           else: 司机已被其他行程锁定

  - 使用 Redis CAS Lua:
    local status = redis.call('HGET', 'driver:' .. driverId, 'status')
    if status == 'ONLINE' then
        redis.call('HSET', 'driver:' .. driverId, 'status', 'BUSY')
        redis.call('SREM', 'drivers:available:' .. cityId, driverId)
        return 1
    else
        return 0
    end
```

### 3. 实时位置推送

```
=== 位置推送方案对比 ===

+------------------+---------------+----------------+-----------------+
| 方案             | 延迟          | 服务器压力       | 适用场景         |
+------------------+---------------+----------------+-----------------+
| 轮询 (HTTP Poll) | 高 (3-5s)     | 高 (频繁连接)    | 不推荐           |
| 长轮询           | 中 (1-3s)     | 中              | 简单场景         |
| WebSocket        | 低 (< 100ms)  | 中 (长连接)      | 实时推送(推荐)   |
| SSE              | 低            | 低              | 单向推送         |
| MQTT (IoT)       | 极低          | 极高扩展         | 超大规模         |
+------------------+---------------+----------------+-----------------+

=== WebSocket 推送架构 ===

+--------------------------------------------------------+
|              WebSocket 网关服务 (无状态)                  |
|  +----------------+  +----------------+                |
|  |   Gateway 0    |  |   Gateway 1    |  ...           |
|  | (管理10万连接)  |  | (管理10万连接)  |                |
|  +--------+-------+  +--------+-------+                |
|           |                    |                        |
|           +----------+---------+                        |
|                      |                                  |
+--------------------------------------------------------+
                       |
             +---------v---------+
             |  Pub/Sub (Redis)   |
             |                   |
             | driver:{id}:pos   |
             | ride:{id}:status  |
             +--------+----------+
                       |
       +---------------+----------------+
       |               |                |
+------v-----+  +------v------+  +-----v------+
| Position   |  | Ride        |  | Notification|
| Service    |  | Service     |  | Service     |
+------------+  +-------------+  +-------------+

位置推送流程:
  1. 司机位置 -> Position Service -> Redis Geo + Redis Pub/Sub
  2. Redis Pub/Sub -> WebSocket Gateway -> 推送给相应乘客
  3. 乘客收到实时司机位置 -> 地图UI更新

Topic设计:
  ride:{ride_id}:driver_location  -> 司机位置
  ride:{ride_id}:status           -> 行程状态变更
  driver:{driver_id}:request      -> 叫车请求下发
```

### 4. 动态定价 (Surge/Dynamic Pricing)

```
=== 供需驱动定价算法 ===

function calculateSurgeMultiplier(lat, lng, productType):
    gridGeoHash = encode(lat, lng, 5)  // ±2.4km网格

    // 当前网格供需比
    demandKey = "surge:demand:" + gridGeoHash
    supplyKey = "surge:supply:" + gridGeoHash

    demand = redis.zcount(demandKey, now()-60s, now())  // 过去1分钟需求
    supply = redis.zcount(supplyKey, now()-60s, now())   // 过去1分钟供给

    ratio = demand / max(supply, 1)

    // 多级加价
    if ratio <= 1.0:   return 1.0    // 供需平衡
    if ratio <= 1.2:   return 1.2
    if ratio <= 1.5:   return 1.5
    if ratio <= 2.0:   return 1.8
    if ratio <= 3.0:   return 2.5
    return 3.0                         // 极端稀缺, 上限3倍

    // 平滑处理: 指数移动平均, 防止剧烈波动
    currentMultiplier = calculateSurgeMultiplier(lat, lng, productType)
    previousMultiplier = redis.get("surge:multiplier:" + gridGeoHash) or 1.0
    smoothed = 0.7 * previousMultiplier + 0.3 * currentMultiplier
    redis.set("surge:multiplier:" + gridGeoHash, smoothed, 300) // 5min TTL
    return smoothed

需求计数:
  // 每次叫车请求
  redis.zadd("surge:demand:" + gridGeoHash, {rideId: now()})
  redis.expire("surge:demand:" + gridGeoHash, 120)  // 2min后清理

供给计数:
  // 司机位置更新时
  redis.zadd("surge:supply:" + gridGeoHash, {driverId: now()})
  redis.expire("surge:supply:" + gridGeoHash, 120)
```

### 5. ETA 估算系统

```
=== ETA 估算方案 ===

方案A: 直线距离估算 (最简单, 不推荐)
  eta = distance_km * 60 / avg_speed_kmh
  误差: 30-50% (不考虑路况和道路结构)

方案B: 地图服务 API (推荐)
  使用高德/百度/Google 地图 API
  输入: from_lat, from_lng, to_lat, to_lng
  返回: 距离 + 预计时间(考虑实时路况)

方案C: 自建 ETA 模型 (超大规模)
  1. 离线构建道路图 (Graph)
  2. 使用 Dijkstra / A* 算法
  3. 每条路的权重 = 长度 / (当前速度 × 时间因子)
  4. 结合机器学习预测路况

=== 如何减少地图 API 调用 ===

1. 缓存热门路线:
   Redis: eta:grid_{geo5}_to_grid_{geo5} -> {distance, duration, time}
   两个 GeoHash 格子之间的 ETA 缓存
   相同格子内所有请求共享结果

2. 司机搜索时并行计算 ETA:
   CompletableFuture.allOf(etas).get(timeout, SECONDS)

3. 直方距离预估替代:
   如果 > 3000m 直线距离, 先不调 API
   直方距离 × 1.5 近似 (在城市中道路绕行系数 ≈ 1.3-1.5)
```

### 6. 计费系统

```
=== 计费公式 ===

Fare = base_fare                        // 起步价
     + max(0, distance_km - base_km) × price_per_km    // 里程费
     + duration_min × price_per_min                    // 时长费
     + surge_multiplier × (base_fare + distance_fare + time_fare)
     + toll_fee                                       // 过路费
     + other_fee                                    // 其他费用

计费示例 (EXPRESS):
  base_fare: 1000(分) / base_km: 3(km)
  price_per_km: 300(分/公里) = 3元/km
  price_per_min: 40(分/分钟) = 0.4元/min

  实际: 8.5km, 22min, surge=1.5

  base = 1000
  distance = max(0, 8.5-3) × 300 = 1650
  time = 22 × 40 = 880
  surge = (1000 + 1650 + 880) × 0.5 = 1765

  total = 1000 + 1650 + 880 + 1765 = 5295 (52.95元)

实现方式:
  - 行程中实时计算预估费用展示给用户
  - 行程结束时最终计费
  - 计费结果写入 ride_record + 发送到支付服务
```

---

## 扩展性与高可用

### 1. 位置数据管理

```
=== 司机位置存储分层 ===

Layer 1: 内存 (极热数据)
  - 当前匹配中的司机位置
  - 毫秒级更新

Layer 2: Redis (热数据)
  - 最近3分钟内的所有司机位置
  - 用于匹配和实时展示
  - GEOADD + GEOHASH

Layer 3: Cassandra/HBase (温数据)
  - 最近24小时的轨迹
  - 用于客服查询、纠纷处理

Layer 4: 对象存储 S3 (冷数据)
  - 历史轨迹归档
  - Spark 离线分析 (热力图、供需预测)

=== 位置数据处理优化 ===

// 轨迹压缩 (减少存储和传输)
function compressTrack(trackPoints):
    // Douglas-Peucker 算法
    if len(trackPoints) <= 2: return trackPoints

    maxDist = 0, maxIdx = 0
    line = (trackPoints[0], trackPoints[-1])
    for i = 1 to len-2:
        dist = perpendicularDist(trackPoints[i], line)
        if dist > maxDist:
            maxDist = dist, maxIdx = i

    if maxDist > EPSILON:  // 保留关键拐点
        left = compressTrack(trackPoints[0:maxIdx+1])
        right = compressTrack(trackPoints[maxIdx:])
        return left[:-1] + right
    else:
        return [trackPoints[0], trackPoints[-1]]
```

### 2. 大流量/高峰处理

```
=== 早晚高峰应对 ===

1. 水平扩展 WebSocket 网关
   - 按 driver_id 哈希分配连接
   - 峰值时扩容网关实例
   - 新实例重新分配连接

2. 匹配服务限流
   - 超过匹配超时的请求直接返回 "暂无司机"
   - 启用动态搜索半径 (高峰缩小到1km -> 扩大匹配速度)

3. 位置上报降级
   - 正常: 4s 上报
   - 高速: 2s 上报(行程中)
   - 拥堵(高负载): 自适应到 6-10s
   - 空闲(静止): 30s 上报

4. 乘客端降级
   - 降低地图刷新频率
   - 停止非必要的预加载
   - 显示简化地图 (无3D/卫星图)
```

### 3. 异地多活

```
=== 跨城市部署 ===

Region: 华北 (北京数据中心)
+---------------------------+
| 北京/天津/河北服务        |
| Redis: drivers:beijing   |
| MySQL: users partition0   |
+---------------------------+

Region: 华东 (上海数据中心)
+---------------------------+
| 上海/江苏/浙江服务        |
| Redis: drivers:shanghai  |
| MySQL: users partition1   |
+---------------------------+

司机注册时绑定到固定 Region
乘客叫车时根据 GPS 定位 -> GSLB 路由到对应 Region

跨城行程:
  - 如果乘客目的地跨城(北京->天津)
  - 行程在发起城市处理
  - 司机到达目的地后切换 Region
```

---

## 总结

设计网约车服务需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **匹配算法** | Geo 空间搜索 + 多维度排序(ETA/评分/距离) + 分批派单 + 超时扩大 |
| **实时通讯** | WebSocket 长连接 + Redis Pub/Sub + 位置推送 + 智能降频 |
| **司机状态** | 状态机(ONLINE/BUSY/TRIP) + Redis CAS 原子切换 + 防并发抢单 |
| **位置存储** | 分层(内存/Redis/Cassandra/S3) + 轨迹压缩 + GeoHash 索引 |
| **动态定价** | 供需比驱动 + 平滑处理 + 网格粒度 + 封顶保护 |
| **ETA** | 地图服务 API + 路线缓存 + 并行计算 + 直方距离退化 |
| **高可用** | 按城市分片 + 服务降级 + WebSocket 重连 + 状态对账机制 |

关键面试问答：
1. **如何匹配最近司机？** — GeoHash 空间搜索 -> 获取候选 -> 并行计算ETA -> 综合排序 -> 分批派单
2. **如何防止一个行程被多个司机抢？** — 分批派单(每批3-5个司机) + Redis CAS 锁定 + 司机响应超时释放
3. **司机位置怎么存储和更新？** — Redis Geo 实时(匹配用) + Redis Hash (详情) + Kafka 异步持久化
4. **动态定价怎么实现？** — 网格供需比 -> 多级加价倍数 -> 平滑处理 -> 封顶保护
5. **高峰期怎么保证可用性？** — 自适应位置上报频率 + 搜索半径动态调整 + 降低非核心功能 + 多级缓存
6. **精确计费如何保证？** — 行程开始/结束时记录里程表 + GPS 轨迹校验 + 地图服务距离对比 + 争议人工介入
