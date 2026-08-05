# 设计股票/证券交易系统 (Design Stock Exchange / Trading System)

## 题目

设计一个简化的股票交易系统，支持股票买卖委托、撮合交易、市场行情推送、账户管理等核心功能。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 下单 | 用户提交限价/市价买单或卖单 |
| 撤单 | 用户取消未成交的委托单 |
| 撮合交易 | 买卖委托按价格-时间优先原则自动撮合 |
| 行情查询 | 查询股票实时行情(最新价/涨跌幅/成交量) |
| 账户管理 | 查看持仓/资金/订单历史 |
| 行情K线 | 日K/周K/月K/分钟K线数据 |
| 深度行情 | 买卖盘口(五档/十档行情) |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 延迟 | 订单撮合 < 1ms, 行情推送 < 100ms |
| 吞吐量 | 支持 100万+ 笔/秒 委托单 |
| 可用性 | 99.999% (交易时间不可宕机) |
| 一致性 | 委托单强一致，账户资金强一致 |
| 顺序 | FIFO (价格→时间优先) |
| 可靠性 | 零丢失 — 每笔订单必须持久化 |

### 容量估算

```
假设:
  - 日活跃交易用户: 1000万
  - 日均成交: 5000万笔
  - 日均委托: 2亿笔 (含撤单)
  - 股票代码数: 5000 (A股市场)

委托 QPS:
  平均: 2亿 / (4 × 3600) = 13889 QPS (交易时间4小时)
  峰值: 13889 × 10 = 138,890 QPS (开盘/收盘峰值)

撮合 QPS:
  成交笔数: 5000万 / (4 × 3600) = 3472 QPS
  撮合次数: 成交量 × 5 = 17360 QPS (一笔大单拆成多笔成交)

行情推送 QPS:
  5000只股票 × 每秒至少1次快照 = 5000次/秒
  要推送到1000万在线用户
  实际: ~5000 × 1000万 = 极大数据量
  -> 需要分层推送 (按需 + 批量)

存储:
  委托单: 2亿 × 200B = 40GB/天
  成交记录: 5000万 × 150B = 7.5GB/天
  行情快照: 5000 × 1KB × 14400/day(每秒) = 72GB/天
  保留: 委托1年, 成交永久, 行情K线永久
```

---

## API设计

### 交易 API (低延迟协议)

```
=== 委托下单 (FIX/Protobuf over TCP) ===

// Protobuf 定义
message OrderRequest {
    uint64 order_id = 1;          // 客户端生成唯一ID
    uint64 user_id = 2;
    string symbol = 3;            // 股票代码 "000001.SZ"
    OrderSide side = 4;           // BUY / SELL
    OrderType type = 5;           // LIMIT / MARKET
    int64 price = 6;              // 限价(分), 市价单=0
    int64 quantity = 7;           // 股数
    uint64 timestamp = 8;         // 客户端时间戳
}

message OrderResponse {
    uint64 order_id = 1;
    OrderStatus status = 2;       // ACCEPTED / REJECTED
    string reject_reason = 3;
}

=== 撤单 ===
message CancelRequest {
    uint64 order_id = 1;
    uint64 user_id = 2;
    string symbol = 3;
}

message CancelResponse {
    uint64 order_id = 1;
    CancelStatus status = 2;      // CANCELLED / REJECTED (已成交/不存在)
}

=== 查询 (REST API) ===
GET /api/v1/orders?user_id={uid}&symbol={sym}&status=ACTIVE
GET /api/v1/orders/{order_id}

Response:
{
  "order_id": "ORD_20250101_000001",
  "user_id": 12345,
  "symbol": "000001.SZ",
  "side": "BUY",
  "type": "LIMIT",
  "price": 1500,          // 15.00 元
  "quantity": 1000,       // 10手(每手100股)
  "filled_quantity": 600,
  "avg_filled_price": 1498,
  "status": "PARTIALLY_FILLED",
  "created_at": "2025-01-01T09:30:00.123Z"
}
```

### 行情 API

```
=== 实时行情快照 (WebSocket) ====
{
  "type": "SNAPSHOT",
  "symbol": "000001.SZ",
  "price": 15.02,          // 最新价
  "change": 0.35,          // 涨跌额
  "change_pct": 2.38,      // 涨跌幅%
  "open": 14.80,
  "high": 15.10,
  "low": 14.75,
  "pre_close": 14.67,
  "volume": 45678900,      // 成交量(股)
  "amount": 685432100,     // 成交额(分)
  "timestamp": 1704067200,
  "bid": [                 // 买盘(买一 ~ 买五)
    [15.01, 5000],         // [价格, 手数]
    [15.00, 12000],
    [14.99, 8000],
    [14.98, 15000],
    [14.97, 20000]
  ],
  "ask": [                 // 卖盘(卖一 ~ 卖五)
    [15.02, 3000],
    [15.03, 10000],
    [15.04, 6000],
    [15.05, 8000],
    [15.06, 25000]
  ]
}

=== 行情K线 ===
GET /api/v1/market/kline?symbol=000001.SZ&period=1d&count=365

Response:
{
  "symbol": "000001.SZ",
  "period": "1d",
  "data": [
    [1704067200, 14.80, 15.10, 14.75, 15.02, 45678900],
    // [时间戳, 开盘, 最高, 最低, 收盘, 成交量]
    ...
  ]
}
```

---

## 数据模型

### 核心数据结构

```sql
-- ============ 账户表 ============
CREATE TABLE user_account (
    user_id         BIGINT PRIMARY KEY,
    balance         BIGINT NOT NULL DEFAULT 0,     -- 可用资金(分)
    frozen_balance  BIGINT NOT NULL DEFAULT 0,     -- 冻结资金
    currency        VARCHAR(3) DEFAULT 'CNY',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE user_position (
    position_id     BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id         BIGINT NOT NULL,
    symbol          VARCHAR(16) NOT NULL,
    total_shares    INT NOT NULL DEFAULT 0,        -- 总持仓
    available_shares INT NOT NULL DEFAULT 0,       -- 可用
    frozen_shares   INT NOT NULL DEFAULT 0,        -- 冻结(已挂卖单)
    cost_price      BIGINT,                        -- 成本价(分)
    updated_at      TIMESTAMP,

    UNIQUE KEY uk_user_symbol (user_id, symbol),
    INDEX idx_user (user_id)
);

-- ============ 委托表 ============
CREATE TABLE order_record (
    order_id        VARCHAR(32) PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    symbol          VARCHAR(16) NOT NULL,
    side            VARCHAR(4) NOT NULL,           -- BUY/SELL
    type            VARCHAR(8) NOT NULL,           -- LIMIT/MARKET
    price           BIGINT NOT NULL,
    quantity        INT NOT NULL,                  -- 委托数量(股)
    filled_quantity INT NOT NULL DEFAULT 0,
    avg_fill_price  BIGINT,
    status          VARCHAR(16) NOT NULL,          -- ACTIVE/FILLED/PARTIAL/CANCELLED/REJECTED
    created_at      TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    cancelled_at    TIMESTAMP(3),

    INDEX idx_user (user_id, status, created_at),
    INDEX idx_symbol (symbol, status, price)
);

-- ============ 成交表 ============
CREATE TABLE trade_record (
    trade_id        VARCHAR(32) PRIMARY KEY,
    symbol          VARCHAR(16) NOT NULL,
    buy_order_id    VARCHAR(32) NOT NULL,
    sell_order_id   VARCHAR(32) NOT NULL,
    buy_user_id     BIGINT NOT NULL,
    sell_user_id    BIGINT NOT NULL,
    price           BIGINT NOT NULL,               -- 成交价(分)
    quantity        INT NOT NULL,                  -- 成交量(股)
    amount          BIGINT NOT NULL,               -- 成交额(分)
    trade_time      TIMESTAMP(3) NOT NULL,

    INDEX idx_symbol_time (symbol, trade_time),
    INDEX idx_buy_user (buy_user_id, trade_time),
    INDEX idx_sell_user (sell_user_id, trade_time)
);

-- ============ 行情K线表 ============
CREATE TABLE kline_1d (
    symbol          VARCHAR(16) NOT NULL,
    trade_date      DATE NOT NULL,
    open            BIGINT NOT NULL,
    high            BIGINT NOT NULL,
    low             BIGINT NOT NULL,
    close           BIGINT NOT NULL,
    volume          BIGINT NOT NULL,
    amount          BIGINT NOT NULL,

    PRIMARY KEY (symbol, trade_date)
);
```

### 内存数据结构 (撮合引擎)

```
=== 订单簿 (Order Book) ===

每个 symbol 维护一个订单簿:

class OrderBook {
    String symbol;
    TreeMap<Long, PriceLevel> bidBook;  // 买盘: price desc (从高到低)
    TreeMap<Long, PriceLevel> askBook;  // 卖盘: price asc (从低到高)

    // 每笔成交记录历史 (提供行情快照)
    Deque<Trade> recentTrades;          // 最近1000笔成交
    long lastTradePrice;                // 最新成交价
    long openPrice;                     // 开盘价
    long highPrice;                     // 今日最高
    long lowPrice;                      // 今日最低
    long totalVolume;                   // 今日总成交量
}

class PriceLevel {
    long price;                         // 价格(分)
    long totalQuantity;                 // 该价格档位的总数量
    Queue<Order> orderQueue;            // FIFO队列 (时间优先)
}

class Order {
    String orderId;
    long userId;
    Side side;
    long price;
    long quantity;                      // 剩余未成交数量
    long filledQuantity;
    long timestamp;
    OrderStatus status;
}

订单簿示例:
_____________________________
BID (买盘)          ASK (卖盘)
                        15.05 × 8000
                        15.04 × 6000
                        15.03 × 10000
                        15.02 × 3000
15.01 × 5000
15.00 × 12000
14.99 × 8000
14.98 × 15000
_____________________________

对于限价买单 @ 15.02 × 2000 股:
  -> 匹配到 Ask 15.02 × 3000
  -> 成交 2000 股 @ 15.02
  -> Ask 15.02 剩余 1000 股

对于市价买单 × 5000 股:
  -> Ask 15.02 × 1000 -> 成交
  -> Ask 15.03 × 4000 -> 成交(剩余 6000)
  -> 总成交 5000 股
```

---

## 高层次架构

### 系统架构图

```
+----------------------------------------------------------------------------+
|                           Gateway Layer                                     |
|  +---------+ +---------+ +---------+ +---------+                            |
|  |GW FIX   | |GW REST  | |GW WS    | |GW Admin |                            |
|  |(交易网关)| |(查询网关)| |(行情网关)| |(后台管理)|                            |
|  +----+----+ +----+----+ +----+----+ +---------+                            |
|       |           |           |                                              |
+----------------------------------------------------------------------------+
        |           |           |
+-------v-----------v-----------v--------------------------------------------+
|                          Order Router                                        |
|  (按 symbol 哈希路由到对应的撮合引擎分区)                                      |
+----+-----+-----+-----+-----+-----+-----------------------------------------+
     |     |     |     |     |     |
+----v-+ +-v---+ +v---+ +v---+ +v---+                                         |
|Match | |Match| |Match| |Match| |Match|  ...  (内存撮合引擎集群)               |
|Engine| |Eng  | |Eng  | |Eng  | |Eng  |                                       |
| S0   | | S1  | | S2  | | S3  | | S4  |                                       |
+-+--+-+ +-++-++ +--+--+ +--+--+ +--+--+                                       |
  |  |     |  |     |      |      |                                            |
  |  +-----+--+-----+------+------+                                            |
  |        |                                                                   |
  |  +-----v------+        +-----------------+                                 |
  |  |  Journal    |        |  Market Data    |                                |
  |  | (持久化日志) |        |  (行情生成)      |                                |
  |  +-----+------+        +--------+--------+                                 |
  |        |                        |                                          |
  +--------v------------------------v-----------------------------------------+
     |                                   |
+----v--------+              +-----------v-------+
|  Order DB   |              |  Market Data Bus  |
|  (MySQL)    |              |  (Kafka/Redis)    |
+-------------+              +----------+--------+
                                        |
                          +-------------+------------+
                          |             |             |
                    +-----v-----+ +----v------+ +----v------+
                    | Quote Pusher| |Kline Calc | |Chart Data |
                    | (行情推送)   | |(K线计算)  | |(图表聚合) |
                    +------+------+ +------+----+ +-----------+
                           |               |
                    +------v-------+
                    |   WebSocket   |
                    |   (推送给客户端)|
                    +--------------+
```

### 撮合流程

```
用户A(买入)         Gateway          Order Router       Match Engine
    |                   |                  |                  |
    | ① Buy 15.02×1000 |                  |                  |
    |----------------->|                  |                  |
    |                   | ② 校验(账户/风控) |                  |
    |                   |                  |                  |
    |                   | ③ 路由            |                  |
    |                   | hash(symbol)->S0 |                  |
    |                   |----------------->|                  |
    |                   |                  | ④ 送达撮合引擎    |
    |                   |                  |----------------->|
    |                   |                  |                  |
    |                   |                  |                  | ⑤ 内存撮合
    |                   |                  |                  | 查找对手盘
    |                   |                  |                  | Ask:15.02×3000
    |                   |                  |                  | -> 成交1000股@15.02
    |                   |                  |                  |
    |                   |                  |                  | ⑥ 更新订单簿
    |                   |                  |                  | Ask 15.02 -> 2000
    |                   |                  |                  |
    |                   |                  |                  | ⑦ 写入 Journal
    |                   |                  |                  | (顺序WAL日志)
    |                   |                  |                  |
    |                   |                  |                  | ⑧ 生成行情快照
    |                   |                  |                  | lastPrice=15.02
    |                   |                  |                  |
    |                   |                  | ⑨ 成交回报        |
    |                   |                  |<-----------------|
    |                   | ⑩ 成交回报        |                  |
    |                   |<-----------------|                  |
    | <-- Trade Conf --|                  |                  |
```

---

## 核心深入

### 1. 撮合引擎 (Matching Engine)

```
=== 撮合算法 (价格-时间优先) ===

function matchOrder(ob: OrderBook, order: Order):
    matches = []

    if order.side == BUY:
        // 限价: 匹配 askPrice <= order.price
        // 市价: 匹配所有 ask
        while ob.askBook is not empty and order.quantity > 0:
            bestAsk = ob.askBook.firstEntry()  // 最低价
            if order.type == LIMIT and bestAsk.price > order.price:
                break  // 无对手盘

            priceLevel = bestAsk.value
            while priceLevel.orderQueue is not empty and order.quantity > 0:
                counterOrder = priceLevel.orderQueue.peek()

                tradeQty = min(order.quantity, counterOrder.quantity)
                tradePrice = bestAsk.price

                // 创建成交记录
                trade = new Trade(
                    order, counterOrder, tradePrice, tradeQty
                )
                matches.add(trade)

                // 更新数量
                order.filledQuantity += tradeQty
                order.quantity -= tradeQty
                counterOrder.filledQuantity += tradeQty
                counterOrder.quantity -= tradeQty

                // 更新对方订单状态
                if counterOrder.quantity == 0:
                    counterOrder.status = FILLED
                    priceLevel.orderQueue.poll()

            if priceLevel.orderQueue is empty:
                ob.askBook.remove(bestAsk.price)

    else: // SELL (对称逻辑)
        while ob.bidBook is not empty and order.quantity > 0:
            bestBid = ob.bidBook.firstEntry()  // 最高价
            if order.type == LIMIT and bestBid.price < order.price:
                break
            // ... 类似BUY撮合

    // 如果还有剩余且是限价单 -> 挂单
    if order.quantity > 0 and order.type == LIMIT:
        addToOrderBook(ob, order)
        order.status = ACTIVE
    elif order.quantity == 0:
        order.status = FILLED
    // 市价单剩余 -> 取消

    // 更新行情
    ob.lastTradePrice = lastTrade.price
    ob.updateHighLow(lastTrade.price)
    ob.totalVolume += totalMatchVolume
    ob.recentTrades.addAll(matches)

    return matches

=== 撮合引擎性能优化 ===

1. 基于 Disruptor / Single-Thread 模型
   // 同一个 symbol 的所有操作在单线程中顺序处理
   // 避免锁竞争, 利用 CPU 缓存友好
   // 每个 symbol 绑定一个线程/CPU核

2. 无锁环形队列 (Ring Buffer)
   // 订单先写入 Ring Buffer
   // 撮合线程从 Ring Buffer 消费

3. 内存预分配 (对象池)
   // 避免 GC 停顿
   // Order/Trade 对象复用

4. 基于 Chronicle Queue / 自建 Journal
   // 顺序写入 WAL, 极高性能
```

### 2. Journal 与容错

```
=== WAL (Write-Ahead Log) ===

撮合引擎处理每笔订单时:
  1. 顺序写入 WAL Journal
  2. 执行内存撮合 (修改 Order Book)
  3. 返回撮合结果

WAL 格式:
  [SEQ_NO | TIMESTAMP | EVENT_TYPE | PAYLOAD]

EVENT_TYPE:
  - ORDER_SUBMIT: {order_id, user_id, symbol, side, price, qty}
  - ORDER_CANCEL: {order_id}
  - TRADE: {trade_id, buy_order, sell_order, price, qty, user_ids}

Journal 文件:
  journal/000001.symbol.journal
  journal/000001.symbol.snapshot  (定期快照)

=== 故障恢复 ===
宕机后重启:
  1. 读取最新快照 (如每5分钟快照一次)
  2. 从快照后的 Journal offset 开始重放事件
  3. 重建内存订单簿状态
  4. 恢复到宕机前状态

=== 快照 (Snapshot) ===
每 5 分钟或每 100万次操作:
  将当前 Order Book 完整序列化:
    - bidBook (所有价格档位 + 所有订单)
    - askBook
    - Symbol 统计 (open, high, low, volume)
    - Journal offset
  
  恢复时: snapshot + journalFrom(offset)
```

### 3. 账户冻结/解冻

```
=== 买卖资金/持仓冻结 ===

买入预冻结资金:
  ① 用户提交买单
  ② 计算冻结金额:
     freezeAmount = order.price × order.quantity (限价)
     freezeAmount = highestAskPrice × order.quantity (市价买)
  ③ 原子扣减:
     UPDATE user_account
     SET balance = balance - freezeAmount,
         frozen_balance = frozen_balance + freezeAmount
     WHERE user_id = ? AND balance >= freezeAmount
  ④ 如果 affected_rows = 0 -> 余额不足 -> 拒绝

  成交解冻:
    实际成交金额 = Σ trades(price × qty)
    多冻结 = freezeAmount - 实际成交金额
    UPDATE user_account
    SET frozen_balance = frozen_balance - freezeAmount,
        balance = balance + 多冻结

卖出预冻结持仓:
  ① 用户提交卖单
  ② 冻结持仓:
     UPDATE user_position
     SET available_shares = available_shares - qty,
         frozen_shares = frozen_shares + qty
     WHERE user_id = ? AND symbol = ? AND available_shares >= qty

  成交解冻:
    实际卖出 = Σ trades(qty)
    未成交 = qty - 实际卖出
    UPDATE user_position
    SET total_shares = total_shares - 实际卖出,
        frozen_shares = frozen_shares - qty,
        available_shares = available_shares + 未成交

=== 结算 (Settlement) ===
  买方: 支付成交金额给对方
    买方余额 -= 成交金额
    买方持仓 += 成交量

  卖方: 收钱减仓
    卖方余额 += 成交金额
    卖方总持仓 -= 成交量
```

### 4. 行情生成与推送

```
=== 行情快照生成流程 ===

Match Engine 每成交一笔 -> 生成 Tick 数据:
  Tick { symbol, price, quantity, trade_time }

Tick Consumer (行情生成器):
  1. 聚合最近1秒的 Tick
  2. 生成 SNAPSHOT:
     latestPrice = last tick price
     open/high/low = 当天统计
     volume = 当天累计
     bid/ask = 订单簿前五档

  3. 写入 Kafka: topic=market.snapshot.{symbol}

行情推送:
  WebSocket Push Service 从 Kafka 消费:
    对订阅该 symbol 的客户端推送快照

=== 行情优化方案 ===

序列化优化:
  使用 Protobuf / SBE (Simple Binary Encoding)
  每个 tick < 50 字节

推送合并:
  聚合 50ms 内的所有行情变化
  批量推送 (减少网络包数量)

推送分层:
  热门股票: 实时推送 (每 tick)
  普通股票: 合并推送 (每 500ms)
  冷门股票: 按需拉取 (REST API)
```

### 5. 风控系统

```
=== 实时风控 ===

交易前检查 (Pre-Trade Risk Check):
  1. 资金检查: balance >= requiredAmount
  2. 持仓检查: available >= sellQuantity
  3. 涨跌停板: price must be in [limit_down, limit_up]
  4. 最小价格变动单位: price % tick_size == 0
  5. 最小下单量: quantity >= 100 and quantity % 100 == 0
  6. 最大下单量: quantity <= maxOrderSize
  7. 频率限制: 同一用户每秒最多 N 笔

风控服务 (独立部署):
  +------------------+
  | Risk Service     |
  | (风控规则引擎)    |
  |                  |
  | 输入: Order/Cancel|
  | 输出: ACCEPT/     |
  |       REJECT +    |
  |       reason      |
  +------------------+

  撮合引擎处理订单前先过风控
  风控服务用 Redis 缓存 + 实时状态

=== 异常检测 ===
  1. 价格异常波动: 5分钟内涨跌 > 10% -> 触发熔断
  2. 某账户异常交易: 短时间内大量挂单/撤单
  3. 某 symbol 成交量突增:  > 20日平均的 5 倍
```

---

## 扩展性与高可用

### 1. 撮合引擎水平扩展

```
=== 按 Symbol 哈希分片 ===

symbol -> shardId = hash(symbol) % N

Engine 0: SH600000 ~ SH600xxx, SZ000001 ~ SZ000xxx
Engine 1: SH600xxx ~ SH600yyy, SZ000xxx ~ SZ000yyy
...

特点:
  - 每个 symbol 的所有操作集中在单个引擎
  - 不存在跨 symbol 的竞态条件
  - 引擎间完全独立, 故障隔离

热 symbol (如: 贵州茅台 600519.SH):
  - 单个引擎负载可能过高
  - 解决方案: 将热门股单独放在一个引擎
  - 或: 热门股内部使用多线程并行 (更复杂)

=== N+1 冗余 ===

每组 symbol 使用 2 个引擎 (主备):
  Engine 0A (Active) + Engine 0B (Standby)

主备同步:
  1. Engine 0A 处理所有请求
  2. 每笔操作的 Journal 同步发送给 0B
  3. 0B 实时复制 0A 状态
  4. 0A 宕机 -> 0B 快速接管 (接管时间 < 100ms)
  5. 0B 从 Journal 中恢复最后几笔操作
```

### 2. 数据持久化策略

```
=== 分层存储 ===

L0: Journal (最热) 
  顺序写入本地 SSD
  低延迟 (< 10us 写入)

L1: Order DB (热)
  异步批量写入 MySQL
  通过 Kafka 消费 Journal -> 写入 MySQL

L2: 归档 (冷)
  3个月前的交易记录 -> Parquet/Hive
  用于报表分析、合规审查

=== 零丢失保证 ===

1. Gateway -> Order Router:
   请求带有唯一 orderId, Gateway 收到 ACK 前重试

2. Order Router -> Match Engine:
   Journal 写入成功后才返回 ACK

3. Match Engine -> Journal:
   fsync() 确保落盘
   可配置: 每笔 fsync (最安全) / 每 1ms 批量 fsync (平衡)

4. Journal -> MySQL:
   使用 Kafka 保证 at-least-once
   通过 order_id 做幂等去重
```

### 3. 行情分发优化

```
=== 行情分级发送 ===

Level 1: 基础行情 (实时)
  - 最新价 / 涨跌幅 / 成交量
  - 实时推送

Level 2: 五档行情 (近实时)
  - 买卖5档盘口
  - 每100ms推送

Level 3: 深度行情 (按需)
  - 全量订单簿
  - 按需订阅

=== 行情二进制协议 ===
// 极力减少每条行情消息大小
struct QuoteSnapshot {
    char[8]   symbol;        // 8 bytes
    int32     price;         // 4 bytes (price * 100)
    int16     change;        // 2 bytes (change * 100)
    int64     volume;        // 8 bytes
    int32     timestamp;     // 4 bytes (unix seconds)
    // 总计: 26 bytes per update
}
// 5000 symbols × 每秒2次 × 26 bytes = 260 KB/s 带宽(Push Service)
// 但推送给 1000万 用户: 260 KB/s * 1000万 = 2.6 TB/s 不可能!
// => 需要推送合并 + 热门推送分级

方案: 
  - 前端用 WebSocket 时只订阅用户关注的股票
  - 每个用户平均关注 10-50 只股票
  - 10M × 10 symbols × 26B × 2/s = 5.2 GB/s 可行
```

### 4. 监控与灾备

```
=== 监控指标 ===

撮合引擎:
  - 撮合延迟 P50/P99 (目标: P50 < 100us, P99 < 1ms)
  - 委托吞吐量 (笔/秒)
  - 撮合成交量 (笔/秒)
  - 订单簿内存大小 (MB)
  - Journal 写入速率 / 延迟
  - GC 暂停时间 (目标: < 10ms)
  - 引擎 CPU 使用率 / 可用内存

交易:
  - 下单 QPS / 成功率 / 拒绝率
  - 撤单 QPS
  - 成交 QPS
  - 平均成交价与报价偏差
  - 账户余额异常

行情:
  - 行情延迟 (Tick -> 推送时间差)
  - 行情消息速率
  - WebSocket 连接数
  - 推送丢失率

告警:
  - 撮合延迟 P99 > 5ms (连续1s)
  - 委托成功率 < 99%
  - Journal写入失败
  - 行情延迟 > 500ms
  - 引擎 CPU > 80%
  - 订单簿内存 > 阈值

=== 灾备 ===

同城灾备 (RPO < 1s):
  Engine A (主) + Engine B (备,同机房)
  通过 Journal 实时同步
  
异地灾备 (RPO < 5s):
  跨机房 Kafka 消息同步
  Journal 异步复制到远端
  紧急时切换 DNS / VIP
```

---

## 总结

设计股票交易系统需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **撮合** | 价格-时间优先 + 内存订单簿 + 双向 TreeMap |
| **性能** | 单 Symbol 单线程 + RingBuffer + 对象池 + 无锁设计 |
| **可靠性** | WAL Journal + Snapshot + 主备同步 + 零丢失架构 |
| **账户** | 预冻资金/持仓 + 成交解冻 + 原子 SQL 扣减 |
| **行情** | Tick聚合 + Protobuf序列化 + 分级推送 + 订阅模式 |
| **水平扩展** | 按 Symbol 哈希分片 + 热门股独立引擎 |
| **风控** | 前置检查(资金/限价/频率) + 实时熔断 + 异常检测 |

关键面试问答：
1. **撮合引擎怎么实现？** — 内存 Order Book (bid/ask TreeMap) + 价格-时间优先 + 单Symbol单线程
2. **如何保证不丢单？** — WAL Journal先行写入 -> 撮合 -> 返回ACK; 主备同步Journal
3. **撮合引擎怎么快速恢复？** — Snapshot(每5分钟) + Journal回放 -> 重建内存状态
4. **买卖资金怎么管理？** — 下单预冻结(可用->冻结) + 成交解冻(多退少补) + DB原子操作
5. **行情推送怎么高效分发？** — 订阅模式(用户只看自己关注的股票) + 二进制压缩 + 批量推送
6. **撮合引擎是怎么水平扩展的？** — 按 Symbol 哈希分片到不同引擎，单引擎只负责部分股票
