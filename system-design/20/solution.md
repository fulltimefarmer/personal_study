# 设计停车场系统 (Design Parking Lot System)

## 题目

设计一个智能停车场管理系统，支持多楼层多车位管理、车辆进出、计费、预定、找车位等核心功能。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 车位管理 | 管理多楼层、多类型车位的状态(可用/占用/预留) |
| 车辆进场 | 车牌识别/取票进场，分配车位 |
| 车辆出场 | 查询停车时长，计算费用，支付离场 |
| 车位预定 | 用户提前预定车位，预留车位 |
| 找车导航 | 帮车主找到所停车辆位置 |
| 计费系统 | 按时段/车型/会员等级差异化收费 |
| 月卡/会员 | 长期停车卡管理 |
| 车场监控 | 实时监控车场车位占用率 |
| 管理员后台 | 车场配置/节假日调价/异常处理 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 延迟 | 进场/出场识别 < 2s, 支付 P99 < 500ms |
| 可用性 | 99.9% (进出场链路 99.99%) |
| 并发 | 支持高峰时段多车道同时进出 |
| 一致性 | 车位状态强一致(同车位不能分配给两辆车) |
| 实时性 | 车位状态变化后 < 1s 更新 |

### 容量估算

```
假设 (大城市连锁停车场):
  - 停车场数量: 1000个
  - 每场平均: 500个车位
  - 总车位: 50万
  - 每场日均车流量: 2000车次
  - 日总车流量: 200万车次

进场/出场 QPS:
  平均: 200万 × 2 / (12 × 3600) = 92.6 QPS (营业时间12h)
  高峰: 92.6 × 5 = 463 QPS (早晚高峰)

停车记录:
  日增量: 200万条 × 1KB = 2GB/天
  年增量: 2GB × 365 = 730GB/年

车位状态:
  50万车位 × 100B = 50MB (Redis 内存轻松容纳)

支付:
  日交易: 200万 × 80% = 160万笔
  高峰: 160万 × 5 / (12 × 3600) = 185 QPS

会员:
  月卡用户: 20% × 50万 = 10万人
```

---

## API设计

### 车辆进场 API

```
=== 车辆进场 (车牌识别) ===
POST /api/v1/entry
{
  "gate_id": "GATE_N001",          // 入口编号
  "plate_number": "京A12345",
  "plate_image_url": "https://cdn.xxx/plate_001.jpg",
  "vehicle_type": "CAR",           // CAR/Truck/ELECTRIC/MOTORCYCLE
  "entry_time": "2025-01-01T09:00:00Z"
}

Response:
{
  "ticket_id": "TKT_20250101_000001",
  "plate_number": "京A12345",
  "assigned_floor": 2,             // 分配楼层
  "assigned_spot": "B-023",        // 分配车位(显示引导)
  "entry_time": "2025-01-01T09:00:00Z",
  "status": "ENTERED"
}

=== 车辆进场 (取票, 无车牌识别) ===
POST /api/v1/entry/ticket
{
  "gate_id": "GATE_S003",
  "vehicle_type": "CAR"
}

Response:
{
  "ticket_id": "TKT_20250101_000002",
  "ticket_qr": "https://xxx/qr/TKT_20250101_000002.png",
  "entry_time": "...",
  "status": "ENTERED"
}

=== 车辆出场 ===
POST /api/v1/exit
{
  "gate_id": "GATE_X001",          // 出口编号
  "plate_number": "京A12345",      // 1. 车牌识别方式
  "exit_time": "2025-01-01T12:30:00Z"
}
// 或
{
  "gate_id": "GATE_X001",
  "ticket_id": "TKT_20250101_000002",  // 2. 取票方式
  "exit_time": "2025-01-01T12:30:00Z"
}

Response:
{
  "ticket_id": "TKT_20250101_000001",
  "plate_number": "京A12345",
  "entry_time": "...",
  "exit_time": "...",
  "duration_minutes": 210,
  "fare_detail": {
    "base_fare": 1500,              // 15元(分) - 前2小时
    "extra_fare": 900,              // 9元 - 超出1.5小时
    "total_fare": 2400,             // 24元
    "discount": 0
  },
  "payment_url": "https://pay.xxx.com/bill/TKT_20250101_000001",
  "payment_qr": "https://qr.xxx/pay/TKT_20250101_000001"
}

=== 支付确认 ===
POST /api/v1/payments/confirm
{
  "ticket_id": "TKT_20250101_000001",
  "payment_method": "WECHAT_PAY",
  "transaction_id": "WXP_20250101_123456",
  "amount": 2400
}

Response:
{
  "ticket_id": "TKT_20250101_000001",
  "status": "PAID",
  "exit_allowed": true,
  "exit_deadline": "2025-01-01T12:45:00Z"  // 支付后15分钟离场
}
```

### 车位预定

```
=== 搜索可用车场 ===
GET /api/v1/parking-lots/search
params:
  - lat, lng: double     // 用户位置
  - radius: int          // 搜索半径(米)
  - entry_time: string   // 预计到达时间

Response:
{
  "lots": [
    {
      "lot_id": "PL_001",
      "name": "国贸停车场",
      "address": "朝阳区建国路88号",
      "lat": 39.9087, "lng": 116.4605,
      "total_spots": 500,
      "available_spots": 120,
      "available_electric_spots": 5,
      "hourly_rate": 800,
      "daily_max": 8000,
      "distance_m": 350
    }
  ]
}

=== 预定车位 ===
POST /api/v1/reservations
{
  "lot_id": "PL_001",
  "plate_number": "京A12345",
  "start_time": "2025-01-01T14:00:00Z",
  "end_time": "2025-01-01T16:00:00Z",
  "vehicle_type": "CAR"
}

Response:
{
  "reservation_id": "RES_20250101_001",
  "lot_id": "PL_001",
  "spot_id": "B-045",
  "start_time": "...",
  "end_time": "...",
  "reservation_deadline": "2025-01-01T14:15:00Z",  // 15分钟内到达
  "fee": 1600,                     // 预扣费用
  "status": "RESERVED"
}

=== 月卡/会员 ===
POST /api/v1/memberships
{
  "plate_number": "京A12345",
  "lot_id": "PL_001",
  "period": "MONTHLY",           // MONTHLY / QUARTERLY / YEARLY
  "start_date": "2025-01-01"
}
```

---

## 数据模型

### 数据库表

```sql
-- ============ 车场 ============
CREATE TABLE parking_lot (
    lot_id          VARCHAR(16) PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    address         VARCHAR(256),
    lat             DOUBLE,
    lng             DOUBLE,
    total_spots     INT NOT NULL,
    total_floors    INT DEFAULT 1,
    phone           VARCHAR(32),
    opening_time    TIME DEFAULT '00:00:00',
    closing_time    TIME DEFAULT '23:59:59',
    hourly_rate     INT,                        -- 每小时费用(分)
    daily_max       INT,                        -- 每日封顶(分)
    extra_hour_rate INT,                        -- 超出基础时段的每小时费用
    free_duration   INT DEFAULT 0,              -- 免费时长(分钟)
    base_duration   INT DEFAULT 120,            -- 基础收费时段(分钟)
    status          TINYINT DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============ 车位 ============
CREATE TABLE parking_spot (
    spot_id         VARCHAR(32) PRIMARY KEY,    -- PL_001-F1-A-023
    lot_id          VARCHAR(16) NOT NULL,
    floor           INT NOT NULL,
    zone            VARCHAR(8),                 -- A/B/C区
    spot_number     VARCHAR(16) NOT NULL,       -- 车位号
    spot_type       VARCHAR(16) DEFAULT 'STANDARD', -- STANDARD/LARGE/ELECTRIC/DISABLED
    status          VARCHAR(16) DEFAULT 'AVAILABLE', -- AVAILABLE/OCCUPIED/RESERVED/MAINTENANCE
    current_ticket  VARCHAR(32),                -- 当前占用车辆ticket_id
    occupied_at     TIMESTAMP,
    updated_at      TIMESTAMP,

    UNIQUE KEY uk_lot_spot (lot_id, floor, spot_number),
    INDEX idx_lot_status (lot_id, status),
    INDEX idx_lot_type_status (lot_id, spot_type, status)
);

-- ============ 停车记录 ============
CREATE TABLE parking_record (
    ticket_id       VARCHAR(32) PRIMARY KEY,    -- TKT_20250101_000001
    lot_id          VARCHAR(16) NOT NULL,
    spot_id         VARCHAR(32),
    plate_number    VARCHAR(16),
    vehicle_type    VARCHAR(16),
    entry_time      TIMESTAMP NOT NULL,
    entry_gate_id   VARCHAR(16),
    exit_time       TIMESTAMP,
    exit_gate_id    VARCHAR(16),
    duration_minutes INT,
    fare            INT,
    payment_status  VARCHAR(16) DEFAULT 'UNPAID', -- UNPAID/PAYING/PAID/FREE
    payment_method  VARCHAR(16),
    payment_time    TIMESTAMP,
    status          VARCHAR(16) DEFAULT 'PARKING', -- PARKING/EXITED/VIOLATION
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_plate_status (plate_number, status),
    INDEX idx_lot_time (lot_id, entry_time),
    INDEX idx_status (status)
);

-- ============ 预定记录 ============
CREATE TABLE reservation (
    reservation_id  VARCHAR(32) PRIMARY KEY,
    lot_id          VARCHAR(16) NOT NULL,
    spot_id         VARCHAR(32),
    ticket_id       VARCHAR(32),                -- 到场后关联
    plate_number    VARCHAR(16),
    vehicle_type    VARCHAR(16),
    start_time      TIMESTAMP NOT NULL,
    end_time        TIMESTAMP NOT NULL,
    reserved_fee    INT,
    status          VARCHAR(16) DEFAULT 'RESERVED', -- RESERVED/ACTIVE/COMPLETED/CANCELLED/EXPIRED
    deadline        TIMESTAMP NOT NULL,         -- 到达截止时间
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ 月卡/会员 ============
CREATE TABLE membership (
    membership_id   BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id         BIGINT,
    lot_id          VARCHAR(16) NOT NULL,
    plate_number    VARCHAR(16) NOT NULL,
    type            VARCHAR(16) NOT NULL,       -- MONTHLY/QUARTERLY/YEARLY
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    fee             INT,
    payment_status  VARCHAR(16),
    status          TINYINT DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ 进出闸口 ============
CREATE TABLE parking_gate (
    gate_id         VARCHAR(16) PRIMARY KEY,    -- GATE_N001
    lot_id          VARCHAR(16) NOT NULL,
    gate_type       VARCHAR(8) NOT NULL,        -- ENTRY/EXIT/BOTH
    floor           INT,
    description     VARCHAR(64),
    camera_device_id VARCHAR(64),               -- 车牌识别设备ID
    status          TINYINT DEFAULT 1
);
```

### Redis 数据结构

```
=== 车场实时状态 ===

# 车场可用车位数
HASH    lot:{lot_id}:stats
  total_spots: 500
  available_standard: 120
  available_large: 15
  available_electric: 5
  available_disabled: 3
  occupied: 357
  reserved: 10

# 可用车位集合 (按类型)
SET     lot:{lot_id}:available:standard
  members: [spot_id_1, spot_id_2, ...]
SET     lot:{lot_id}:available:electric
  members: [spot_id_5, spot_id_8, ...]

# 被占用车位
HASH    lot:{lot_id}:occupied
  spot_id_1: ticket_id
  spot_id_2: ticket_id

# 车位分配 (入场时 SPOP)
SPOP lot:{lot_id}:available:{type}
  -> 返回一个车位ID, 该车位从集合中移除
  -> 如果返回 nil, 说明无该类型车位

# 车辆当前状态
HASH    plate:{plate_number}
  current_ticket: TKT_abc
  current_lot: PL_001
  current_spot: B-023
  entry_time: 2025-01-01T09:00:00Z

# 停车费用缓存
HASH    ticket:{ticket_id}
  plate_number, lot_id, spot_id,
  entry_time, vehicle_type,
  fare, duration, payment_status

# 月卡用户集合
SET     lot:{lot_id}:membership
  members: [plate_1, plate_2, ...]
  TTL: 每天凌晨刷新一次

# 预定车位
HASH    reservation:{reservation_id}
  lot_id, spot_id, plate_number,
  start_time, end_time, deadline, status
```

---

## 高层次架构

### 系统架构图

```
+-------------------------------------------------------------------------+
|                           IoT/Edge Layer                                  |
|  +------------------+  +------------------+  +------------------+        |
|  | 进场闸口         |  | 车牌识别摄像头    |  | 车位传感器       |        |
|  | (抬杆/降杆)      |  | (OCR 识别)       |  | (超声波/地磁)    |        |
|  +--------+---------+  +--------+---------+  +--------+---------+        |
+-------------------------------------------------------------------------+
           |                       |                     |
+----------v-----------------------v---------------------v----------------+
|                          IoT Gateway                                      |
|  (协议适配 / 数据清洗 / 设备管理 / 固件升级)                               |
+--------------------------------+----------------------------------------+
                                 |
+--------------------------------v----------------------------------------+
|                         API Gateway                                       |
|  +--------------+  +---------------+  +-----------------+                |
|  | Parking API  |  | Payment API   |  | User API        |                |
|  | (进出场/车位)|  | (支付/退款)    |  | (预定/月卡/查询)|                |
|  +------+-------+  +-------+-------+  +--------+--------+                |
+-------------------------------------------------------------------------+
                                 |
+----------+---------+---------+--------+---------+---------+
|          |         |         |        |         |         |
+------v---+ +-------v-+ +-----v---+ +--v------+ +-v-------+ +v--------+
|Parking  | |Spot    | |Pricing  | |Payment  | |User    | |Notif    |
|Service  | |Service | |Service  | |Service  | |Service | |Service  |
|(进出场) | |(车位管理)| |(计费)   | |(支付)    | |(用户)   | |(通知)   |
+----+----+ +---+----+ +----+----+ +----+----+ +----+----+ +----+-----+
     |          |          |           |           |           |
     +----+-----+-----+----+-----+-----+-----+-----+-----+-----+
          |           |          |           |           |
+---------v-----------v----------v-----------v-----------v---------------+
|                           数据层                                          |
|  +----------+  +----------+  +----------+  +-------------------------+  |
|  | Redis    |  | MySQL    |  | MQ       |  | Object Store (S3)       |  |
|  | (实时状态)|  | (主数据)  |  | (异步事件)|  | (抓拍图片/监控录像)     |  |
|  +----------+  +----------+  +----------+  +-------------------------+  |
+-------------------------------------------------------------------------+

+-----------------------------------------------------------------------+
|                        管理后台 (Web)                                   |
|  车场管理 | 计费配置 | 车位监控大屏 | 异常处理 | 数据报表                    |
+-----------------------------------------------------------------------+
```

### 进场流程

```
闸口/摄像头         IoT Gateway       Parking Service    Spot Service     Redis
    |                    |                   |                 |            |
    | ① 车辆驶入          |                   |                 |            |
    | 摄像头拍照         |                   |                 |            |
    | OCR识别车牌        |                   |                 |            |
    |------------------->|                   |                 |            |
    |  {plate: 京A12345, |                   |                 |            |
    |   gate: N001,      |                   |                 |            |
    |   timestamp: ...}  |                   |                 |            |
    |                    | ② POST /entry     |                 |            |
    |                    |----------------->|                 |            |
    |                    |                   | ③ 检查是否月卡   |            |
    |                    |                   | SISMEMBER       |            |
    |                    |                   | lot:PL:membership|            |
    |                    |                   |---------------->|            |
    |                    |                   | <-- Yes/No      |            |
    |                    |                   |                 |            |
    |                    |                   | ④ 检查是否重复进场|            |
    |                    |                   | HGET plate:京A  |            |
    |                    |                   |---------------->|            |
    |                    |                   | <-- null(未进场) |            |
    |                    |                   |                 |            |
    |                    |                   | ⑤ 分配车位       |            |
    |                    |                   | SPOP lot:PL:    |            |
    |                    |                   |   available:    |            |
    |                    |                   |   standard      |            |
    |                    |------------------>|                 |            |
    |                    |                   | <-- B-023 or nil|            |
    |                    |                   |                 |            |
    |                    | (若无车位)         |                 |            |
    |                    | return "车位已满"  |                 |            |
    |                    |                   |                 |            |
    |                    |                   | ⑥ 标记车位占用   |            |
    |                    |                   | HSET lot:PL:    |            |
    |                    |                   |   occupied       |            |
    |                    |                   | DEL lot:PL:     |            |
    |                    |                   |   stats(update)  |            |
    |                    |                   |---------------->|            |
    |                    |                   |                 |            |
    |                    |                   | ⑦ 创建停车记录   |            |
    |                    |                   | INSERT record   |            |
    |                    |                   | (MySQL)         |            |
    |                    |                   |                 |            |
    |                    |                   | ⑧ 更新车辆状态   |            |
    |                    |                   | HSET plate:京A  |            |
    |                    |                   |   current_ticket|            |
    |                    |                   |---------------->|            |
    |                    |                   |                 |            |
    |                    | <-- ticket_id ----|                 |            |
    | <-- 抬杆指令+      |                   |                 |            |
    |     车位引导       |                   |                 |            |
    |                    |                   |                 |            |
    | ⑨ 抬杆 + 显示      |                   |                 |            |
    |   "B-023"         |                   |                 |            |
```

### 出场流程

```
闸口/摄像头         IoT Gateway       Parking Service    Pricing Service  Payment Service
    |                    |                   |                 |                |
    | ① 车辆驶出          |                   |                 |                |
    | OCR识别车牌        |                   |                 |                |
    |------------------->|                   |                 |                |
    |  {plate: 京A12345, |                   |                 |                |
    |   exit_time: ...}  |                   |                 |                |
    |                    | ② POST /exit      |                 |                |
    |                    |----------------->|                 |                |
    |                    |                   | ③ 查询停车记录   |                |
    |                    |                   | HGET plate:京A  |                |
    |                    |                   |   curr_ticket   |                |
    |                    |                   |                 |                |
    |                    |                   | ④ 获取停车详情   |                |
    |                    |                   | HGETALL ticket: |                |
    |                    |                   |   {ticket_id}   |                |
    |                    |                   |                 |                |
    |                    |                   | ⑤ 计算费用       |                |
    |                    |                   | duration =      |                |
    |                    |                   | exit - entry    |                |
    |                    |                   |---------------->|                |
    |                    |                   |                 | 计费规则引擎    |
    |                    |                   |                 | base + extra   |
    |                    |                   | <-- fare_detail |                |
    |                    |                   |                 |                |
    |                    |                   | ⑥ 月卡/免费检查  |                |
    |                    |                   | (若是月卡且有效)  |                |
    |                    |                   | fare = 0        |                |
    |                    |                   |                 |                |
    |                    |                   | ⑦ 生成账单       |                |
    |                    |                   | UPDATE record   |                |
    |                    |                   | SET fare, exit  |                |
    |                    |                   |                 |                |
    |                    |                   | ⑧ 支付引导       |                |
    |                    | <-- fare+pay_url |                 |                |
    | <-- 显示费用+      |                   |                 |                |
    |    支付二维码      |                   |                 |                |
    |                    |                   |                 |                |
    | 用户扫码支付...     |                   |                 |                |
    |                    |                   |                 |                |
    |                    |                   | ⑨ 支付确认       |                |
    |                    |                   |------------------------------->|
    |                    |                   |                 | <-- PAID      |
    |                    |                   |                 |                |
    |                    |                   | ⑩ 释放车位       |                |
    |                    |                   | SADD lot:PL:    |                |
    |                    |                   | available       |                |
    |                    |                   | HDEL lot:PL:    |                |
    |                    |                   | occupied         |                |
    |                    |                   |                 |                |
    |                    |                   | ⑾ 清理车辆状态   |                |
    |                    |                   | DEL plate:京A   |                |
    |                    |                   |                 |                |
    | <-- 抬杆放行指令    |                   |                 |                |
    | ⑿ 抬杆             |                   |                 |                |
```

---

## 核心深入

### 1. 车位分配策略

```
=== 分配算法 ===

方案A: 随机分配
  spot = SPOP lot:{lotId}:available:{type}
  优点: 简单, Redis 原子操作
  缺点: 不考虑最优路径

方案B: 最近可用 (最优)
  按距离入口排序, 分配最近的车位
  使用 Redis Sorted Set:
    # 预先计算每个车位到各入口的距离
    ZADD lot:PL:available:entry_N001
      {distance} {spot_id}

    # 进场时取最近
    spot = ZPOPMIN lot:PL:available:entry_N001
  优点: 用户体验好
  缺点: 需要预计算距离

方案C: 分层分配 (平衡)
  def assignSpot(lotId, vehicleType, entryFloor):
      # 从当前楼层开始优先分配
      for floor in [entryFloor, entryFloor+1, ...]:
          spot = SPOP lot:{lotId}:available:{vehicleType}:floor{floor}
          if spot: return spot
      # 当前楼层以上无, 向下找
      for floor in range(entryFloor-1, 0, -1):
          spot = SPOP lot:{lotId}:available:{vehicleType}:floor{floor}
          if spot: return spot
      return nil  # 无车位

  优点: 均衡楼层负载, 避免一层全满
  缺点: Redis Key 数量较多

  Redis 结构:
    SET lot:PL:available:standard:floor1 -> [B1-001, B1-002, ...]
    SET lot:PL:available:standard:floor2 -> [B2-001, B2-002, ...]

=== 车位释放 ===
  SADD lot:{lotId}:available:{type} {spotId}
  # 同时清理 reserved / maintenance 标记
```

### 2. 计费引擎

```
=== 计费规则配置 ===

每家车场独立计费规则:

class PricingRule {
    int freeDuration;          // 免费时长(分钟), 如: 15
    int baseDuration;          // 基础收费时段(分钟), 如: 120
    int baseFare;              // 基础时段费用(分), 如: 1500 (15元)
    int extraInterval;         // 超出后计费间隔(分钟), 如: 30
    int extraFarePerInterval;  // 每间隔费用(分), 如: 300 (3元)
    int dailyMax;              // 每日最高(分), 如: 8000 (80元)
    int overnightFare;         // 过夜费(分), 如: 3000 (30元)
    Map<String, int> discountByType;  // 电动车折扣
}

=== 计费算法 ===

function calculateFare(entryTime, exitTime, vehicleType, rule, isMember):
    durationMinutes = (exitTime - entryTime).totalMinutes

    if isMember and membershipValid:
        return 0  # 月卡用户免费

    if durationMinutes <= rule.freeDuration:
        return 0  # 免费时段内

    // 电动车折扣
    discount = vehicleType == "ELECTRIC" ? 0.5 : 1.0

    fare = 0
    remaining = durationMinutes

    // 基础时段
    if remaining > 0:
        fare += rule.baseFare
        remaining -= rule.baseDuration

    // 超出时段 (按间隔计费, 不足一个间隔按一个算)
    if remaining > 0:
        intervals = ceil(remaining / rule.extraInterval)
        fare += intervals * rule.extraFarePerInterval

    // 日封顶
    days = floor(durationMinutes / (24 * 60))
    singleDayFare = min(farePerDay, rule.dailyMax)
    totalFare = singleDayFare * (days + 1)

    // 月计费 (例如, 部分车场按日封顶, 部分按月)
    // ...

    return totalFare * discount

=== 计费配置热更新 ===
  Redis: pricing:rule:{lotId} -> JSON
  每1分钟从 MySQL 刷新
  支持节假日特殊定价(单独 rule, 按日期范围生效)
```

### 3. 月卡/会员管理

```
=== 月卡进场逻辑 ===

进场时检查是否为月卡用户:
  1. SISMEMBER lot:{lotId}:membership {plateNumber}
     -> 是: 直接放行, 不分配固定车位(随机分配)
     -> 否: 进入普通分配流程

月卡有效性:
  - 月卡有效期: [startDate, endDate]
  - 每日刷新 Redis 中的会员集合:
    定时任务 (每日 00:00):
      members = SELECT plate_number FROM membership
                WHERE lot_id = ? AND start_date <= TODAY
                  AND end_date >= TODAY AND status = 1
      Redis: SADD lot:{lotId}:membership members
      Redis: EXPIRE lot:{lotId}:membership 86400

月卡续费:
  提前15天通知续费 -> 支付 -> 延长 endDate
  未续费 -> 到期后移除会员列表 -> 自动转为临时用户
```

### 4. 异常场景处理

```
=== 常见异常与处理 ===

1. 无牌/污渍车牌
   方案A: 发给用户取票码/二维码纸票
   方案B: 人工介入 - 管理员确认放行
   方案C: 预留一个 "MANUAL" 输入框在闸口

2. 车牌识别错误
   问题: 识别成错误车牌 -> 进来时记录正确, 出去时识别错
   处理: 人工复核, 通过 entry_time 和 exit_time 匹配历史记录

3. 出场时找不到记录
   情况1: 识别错误
   情况2: 数据丢失
   处理:
     - 模糊匹配: 出场时间前后 N 分钟正在停放的车辆
     - 人工输入车牌号
     - 最后手段: 人工查监控

4. 支付后不离开(超15分钟)
   发现: HGETALL ticket:{ticketId} payment_status=PAID
          exit_time 超 15分钟
   处理: 重新进入计费(按超过的时长追加费用)
   系统: 定时扫描 + 标记超时

5. 车位被占(传感器显示占用但系统中无记录)
   处理: 管理员标记 spot 为 MAINTENANCE
         在系统中有新车辆注册之前不分配

6. 系统断电/Redis 数据丢失
   通过 MySQL 中的 parking_record 重建
   Redis 车位状态:
     occupied = SELECT spot_id, ticket_id FROM parking_record
                WHERE lot_id = ? AND status = 'PARKING'
     available = total - occupied
     SADD lot:PL:available:standard spare_spots
```

### 5. 物联网对接

```
=== 硬件设备类型 ===

1. 车牌识别摄像头:
   协议: RTSP (视频流) + HTTP/ONVIF (控制)
   数据: 车牌号码, 置信度, 图片 URL, 抓拍时间
   集成: IoT Gateway 统一接入

2. 超声波车位传感器 (每车位):
   检测: 车位是否有车
   上传频率: 0.5s (状态变化时)
   数据: spot_id, occupied (0/1), timestamp

3. LED 引导屏:
   显示: 各层剩余车位数
   更新频率: 3秒刷新
   协议: RS485/TCP

4. 闸机控制器:
   指令: 抬杆/降杆/禁行
   接口: HTTP/REST 或 Modbus

=== IoT Gateway ===
  功能:
    - 设备注册与发现
    - 协议适配 (MQTT/Modbus/HTTP)
    - 数据清洗 (去重/异常值过滤)
    - 固件管理/OTA升级
    - 心跳检测/离线告警
```

### 6. 监控大屏与报表

```
=== 实时监控大屏 ===

数据来源: WebSocket 推送实时数据

展示内容:
  ┌──────────────────────────────────────────────────┐
  │  XX停车场实时监控                       2025-01-01 │
  ├──────────────────┬───────────────────────────────┤
  │  车位总览         │  今日统计                     │
  │  [████████░░░░]   │  进: 1247  出: 1102           │
  │    80% 已占用     │  当前在库: 145                │
  │  共:500 空:100    │  收入: ¥12,450               │
  ├──────────────────┼───────────────────────────────┤
  │  F1 [██████░░] 60%│  F2 [████████░░] 80%          │
  │  F3 [████░░░░] 40%│  F4 [██░░░░░░░░] 20%         │
  └──────────────────┴───────────────────────────────┘

=== 数据报表 ===
  日/周/月报表:
    - 车流量 (入场/出场)
    - 收入 (分时段)
    - 车位占用率 (分时段)
    - 平均停车时长
    - 会员 vs 临时用户比例
  
  技术: 离线 Spark 任务, 每天凌晨跑
  存储: MySQL 统计表
  展示: Grafana / 自建BI
```

---

## 扩展性与高可用

### 1. 离线与弱网处理

```
=== 问题 ===
  停车场网络可能不稳定
  尤其是地下停车场

=== 解决方案 ===

1. 设备端本地缓存
   闸口控制器本地缓存:
     - 最近的月卡列表 (同步频率: 1分钟)
     - 离线模式: 月卡匹配本地, 临时车辆记录本地方案
     - 恢复连接后上传离线记录

2. 数据同步
   本地 DB (SQLite) + 云端 MySQL
   断网时存在本地 -> 网络恢复时同步

3. 自动重试
   闸口每次进出先尝试云端
   超时 3s 后降级到本地处理
   本地记录标记 "pending_sync"

4. 支付降级
   网络不通时:
    - 显示固定金额 (如按次收费)
    - 现金支付
    - 离场后补缴 (记录欠费)
```

### 2. 数据库扩展

```
=== 分库分表 ===

按停车记录分片:
  按 ticket_id 哈希分 16 库
  或: 按 lot_id 分库 (每个大型车场独立库)
  
中小车场合并:
  按 city_id 分组, 多个小车场合用一个库

历史数据归档:
  保留最近 6个月的详细停车记录
  6个月前的记录 -> 归档到 Hive/Spark 分析
  保留 2 年以上 (法律法规要求)
```

### 3. 高可用架构

```
=== 数据高可用 ===

MySQL: 主从复制 (MHA)
  Master (写) -> Slave (读) -> 监控/统计

Redis: Sentinel / Cluster
  车位状态和实时数据
  RDB 快照(每5分钟) + AOF(everysec)

=== 服务高可用 ===

Parking Service: 
  无状态, 部署 3+ 节点
  进场/出场使用 Redis 保证状态一致

IoT Gateway:
  部署在每个停车场 (或城市边缘节点)
  网络断开时本地处理

=== 灾难恢复 ===

场景: 某车场服务全部宕机
  闸口本地模式 (SQLite 离线记录)
  恢复后上传 + 对账

场景: Redis 全部数据丢失
  从 MySQL parking_record 重建实时状态
  30秒恢复
```

### 4. 监控与告警

```
关键指标:
  - 进场/出场 QPS / 成功率
  - 支付 QPS / 支付转化率
  - 车场车位占用率 (每5分钟)
  - Redis 车位状态与实际传感器数据偏差
  - 闸口设备在线率
  - 车牌识别准确率
  - API P99 延迟

告警规则:
  - 进场成功率 < 95% (连续5分钟)
  - 支付转化率 < 80%
  - 某车场 Redis 不可用
  - 闸口设备离线 > 2分钟
  - 车位占用率 > 95% (即将满位)
  - 车牌识别准确率 < 90%
```

---

## 总结

设计停车场系统需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **车位管理** | Redis SET 可用车位池 + SPOP 原子分配 + 分层分配策略 |
| **进出场** | 车牌识别(OCR) + 月卡会员优先 + Redis 状态校验 |
| **计费** | 规则引擎(免费时长/基础时段/超时/日封顶/月卡) + 节假日特殊定价 |
| **支付** | 扫码支付 + 月卡自动扣款 + 支付后15分钟离场宽限 |
| **离线** | IoT Gateway 本地处理 + SQLite 本地缓存 + 恢复后同步 |
| **实时监控** | Redis 实时车位状态 + WebSocket 大屏推送 + 传感器数据融合 |
| **异常** | 车牌识别错误(人工复核) + 支付后超时(追加费用) + 车位占用异常(人工标记) |

关键面试问答：
1. **怎么分配车位？** — SPOP 从可用车位池原子弹出一个车位，按楼层分层分配(当前楼层优先)
2. **如何保证不把同一车位分配给两辆车？** — Redis SET SPOP 原子操作，一旦弹出就从集合移除
3. **计费规则怎么设计？** — 规则引擎(免费时长 + 基础时段 + 超时间隔计费 + 日封顶 + 月卡豁免)
4. **月卡会员怎么处理？** — Redis SET 缓存月卡列表(每日刷新)，进场时先查会员集合，会员直接放行不计费
5. **车牌识别错误怎么办？** — 入口给纸票备用；出口模糊匹配(时间/车位) + 人工复核
6. **系统断网怎么处理？** — 闸口本地缓存(月卡列表) + 本地SQLite离线记录 + 恢复后同步
