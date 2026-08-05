# 43. 设计弹幕/实时评论系统 (Design Live Comment/Danmaku System like Bilibili)

## 题目

设计一个弹幕（Danmaku/弹幕）系统，类似 Bilibili 的实时评论系统。用户在观看视频时发送弹幕，弹幕实时飘过视频画面，同时其他用户可以看到。系统需支持高并发写入、实时分发、历史回放、内容审核等。

## 需求澄清

### 功能性需求

1. **发送弹幕 (Send Danmaku)**: 用户在视频播放时发送弹幕评论
2. **实时展示 (Real-time Display)**: 弹幕实时飘过所有观看者的视频画面
3. **历史弹幕加载 (History Danmaku)**: 视频回放/跳转时加载该时间点的历史弹幕
4. **弹幕配置 (Danmaku Config)**: 用户可设置弹幕密度、透明度、显示区域、速度
5. **弹幕样式 (Danmaku Style)**: 支持颜色、字号、位置（顶部/底部/滚动）、特效弹幕
6. **高级弹幕 (Advanced Danmaku)**: 支持特殊效果（如弹幕停留在指定位置）
7. **弹幕举报 (Report Danmaku)**: 用户举报不当弹幕
8. **弹幕点赞 (Like Danmaku)**: 用户对弹幕互动

### 非功能性需求

1. **低延迟 (Low Latency)**: 发送到显示 < 500ms（最好 < 200ms）
2. **高并发写入**: 热门直播可达 10K+ 弹幕/秒（单个房间）
3. **高并发分发**: 百万级观众同时接收弹幕
4. **消息可靠**: 不丢弹幕，不乱序
5. **审核实时**: 敏感内容 < 1秒 审核拦截
6. **可扩展性**: 支持百万级并发房间

### 容量估算

```
假设平台有 1 亿月活用户，峰值 500 万同时在线

单个人气直播间（如B站跨年晚会）:
  同时观看 = 100 万人
  弹幕发送量 = 5,000 条/秒 (用户中 0.5% 发送)
  弹幕分发量 = 100万 * 5,000 = 50 亿条/秒 (理论广播量)

实际分发优化后:
  - 弹幕鉴黄/审核后约 80% 通过 = 4,000 条/秒
  - 长连接推送，每个连接 4,000 条/秒
  - 需要强大的推送网关支撑

存储估算:
  平均弹幕大小 = 200 字节
  日均弹幕量 = 假设 5 亿条
  日增存储 = 5亿 * 200B ≈ 100GB/天
  保留 1 年 ≈ 36.5TB

带宽估算:
  弹幕下行带宽 = 4000条/秒 * 200B ≈ 800KB/s (服务器出站)
  100万观众 = 800KB/s * 100万 ≈ 800GB/s (极端情况)
  实际通过 CDN/边缘节点分发，中心带宽 < 10GB/s
```

## API设计

### HTTP API（弹幕发送）

```
POST   /api/v1/videos/{video_id}/danmakus
  发送弹幕
  Body: {
    "content": "前方高能!!!",
    "time_offset": 120.5,   // 视频时间轴位置(秒)
    "color": "#FFFFFF",
    "font_size": 25,
    "mode": "scroll",       // scroll/top/bottom
    "request_id": "uuid"    // 幂等键
  }

GET    /api/v1/videos/{video_id}/danmakus
  获取历史弹幕
  Query: ?start_time=120&end_time=130&limit=100

POST   /api/v1/danmakus/{danmaku_id}/report
  举报弹幕

POST   /api/v1/danmakus/{danmaku_id}/like
  点赞弹幕

GET    /api/v1/videos/{video_id}/danmaku_config
  获取弹幕配置(密度等级、关键词屏蔽列表)
```

### WebSocket 协议（实时推送）

```
Client -> Server:
  {
    "type": "subscribe",
    "room_id": "video_12345",
    "time_offset": 0,
    "filters": {
      "density": 3,          // 1-5 密度等级
      "blocked_keywords": ["剧透", "结局"],
      "blocked_users": ["user_789"]
    }
  }

  {
    "type": "send_danmaku",
    "data": {
      "content": "前方高能!!!",
      "time_offset": 120.5,
      "color": "#FFFFFF",
      "mode": "scroll",
      "request_id": "uuid"
    }
  }

Server -> Client:
  {
    "type": "danmaku",
    "id": "dm_abc123",
    "user": {"id": "user_456", "name": "用户A", "level": 5},
    "content": "前方高能!!!",
    "time_offset": 120.5,
    "color": "#FFFFFF",
    "mode": "scroll",
    "timestamp": 1690000000000
  }

  {
    "type": "danmaku_blocked",
    "request_id": "uuid",
    "reason": "SENSITIVE_CONTENT"
  }

  {
    "type": "system_message",
    "content": "系统升级中，弹幕功能暂时受限"
  }
```

## 数据模型

### MySQL 持久化存储

```sql
-- 弹幕主表 - 按 video_id 分库分表
CREATE TABLE danmakus (
    danmaku_id VARCHAR(32) PRIMARY KEY,
    video_id VARCHAR(32) NOT NULL,
    user_id VARCHAR(32) NOT NULL,
    content VARCHAR(500) NOT NULL,
    time_offset DECIMAL(10,3) NOT NULL COMMENT '视频内时间偏移(秒), 如120.500',
    mode ENUM('scroll','top','bottom','special') DEFAULT 'scroll',
    color VARCHAR(7) DEFAULT '#FFFFFF',
    font_size TINYINT DEFAULT 25,
    status ENUM('pending','approved','rejected','deleted') DEFAULT 'pending',
    like_count INT DEFAULT 0,
    report_count INT DEFAULT 0,
    ip_address VARCHAR(45),
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    INDEX idx_video_time (video_id, time_offset, created_at),
    INDEX idx_video_created (video_id, created_at),
    INDEX idx_user_id (user_id, created_at)
) ENGINE=InnoDB;

-- 弹幕举报表
CREATE TABLE danmaku_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    danmaku_id VARCHAR(32) NOT NULL,
    reporter_id VARCHAR(32) NOT NULL,
    reason VARCHAR(255),
    status ENUM('pending','reviewed','dismissed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_danmaku_reporter (danmaku_id, reporter_id)
) ENGINE=InnoDB;

-- 视频弹幕配置表
CREATE TABLE video_danmaku_config (
    video_id VARCHAR(32) PRIMARY KEY,
    max_density TINYINT DEFAULT 5,
    enable_guest TINYINT DEFAULT 0,     -- 是否允许游客发弹幕
    enable_keyword_filter TINYINT DEFAULT 1,
    custom_blocked_keywords TEXT,        -- 视频主自定义屏蔽词(JSON)
    danmaku_speed FLOAT DEFAULT 1.0,     -- 弹幕速度倍率
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
```

### Redis 数据结构

```
# 实时弹幕缓存 - Sorted Set
# Key: video:danmakus:realtime:{video_id}
# Score: time_offset (精确到毫秒: 120500)
# Member: danmaku JSON
ZADD video:danmakus:realtime:video_12345 120500 '{"id":"dm_1","content":"...",...}'
EXPIRE video:danmakus:realtime:video_12345 7200  # 2小时后过期

# 弹幕计数器 - 用于防刷
# Key: user:danmaku:rate:{user_id}:{video_id}
INCR user:danmaku:rate:user_456:video_12345
EXPIRE user:danmaku:rate:user_456:video_12345 60

# 在线用户房间映射 - Set
# Key: room:viewers:{video_id}
SADD room:viewers:video_12345 user_456
# 通过心跳维持

# 弹幕审核队列 - List (可选,用于异步审核)
LPUSH danmaku:review:queue '{"danmaku_id":"dm_1","content":"..."}'
```

### 时序数据库（可选，用于弹幕密度分析）

```
InfluxDB / TDengine:
  measurement: danmaku_metrics
  tags: video_id, mode, status
  fields: count
  timestamp: time(1s bucket)
```

## 高层次架构

```
                          ┌──────────────────────────┐
                          │      CDN / 视频流         │
                          └──────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────┐
│                        Client (App/Web)                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Video Player + Danmaku Engine                           │ │
│  │  - HTTP (历史弹幕) + WebSocket (实时弹幕)                 │ │
│  │  - 本地弹幕缓存 + 时序排布 + Canvas 渲染                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────┬──────────────────────────┬───────────────────┘
                │ HTTP POST                │ WebSocket
                │ (发送弹幕)                │ (接收弹幕)
                │                          │
    ┌───────────▼───────────┐    ┌────────▼──────────┐
    │   API / HTTP Gateway  │    │  WebSocket Gateway │
    │   (鉴权/限流/去重)     │    │  (长连接管理)      │
    └───────────┬───────────┘    └────────┬──────────┘
                │                         │
                │                         │
    ┌───────────▼──────────────────────────▼───────────┐
    │                Danmaku Service                    │
    │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
    │  │ 发送模块  │ │ 审核模块  │ │  分发模块         │  │
    │  │(Validate)│ │(Moderate)│ │  (Dispatch)      │  │
    │  └────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
    └───────┼────────────┼───────────────┼─────────────┘
            │            │               │
     ┌──────┼────────────┼───────────────┼──────┐
     │      │            │               │      │
     ▼      ▼            ▼               ▼      ▼
┌─────────┐ ┌──────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│  MySQL  │ │Redis │ │ Kafka  │ │  Content │ │  WebSocket│
│(持久化) │ │(缓存)│ │(消息)  │ │  Filter  │ │  Push     │
│         │ │      │ │        │ │  (审核)  │ │  Gateway  │
└─────────┘ └──────┘ └────────┘ └──────────┘ └──────────┘
```

### 数据流

```
发送弹幕流程:

1. Client -> HTTP POST /api/v1/videos/{video_id}/danmakus
2. API Gateway 鉴权 + 限流 (频率控制: 每用户每房间每10秒1条)
3. Danmaku Service 校验:
   - 内容长度 (<= 500 字符)
   - time_offset 有效性 (0 ~ 视频总时长)
   - 敏感词预过滤
4. 写入 MySQL (持久化)
5. 写入 Redis Sorted Set (实时缓存)
6. 通过 Kafka 发送到审核模块 (异步)
7. 审核通过后 -> Kafka -> WebSocket Gateway 广播

接收弹幕流程:

1. Client -> WebSocket 连接建立
2. Client 发送 subscribe 消息到 WebSocket Gateway
3. Gateway 将此连接注册到房间 (room:{video_id})
4. 新弹幕到达后，Gateway 广播给房间内所有订阅者
5. 用户跳转时，Gateway 从 Redis Sorted Set 按 time_offset 范围查询
6. 返回范围内的弹幕列表
```

## 核心深入

### 实时分发方案对比

#### 方案A: 轮询 (Polling)

```
Client 每隔 N 秒 GET /api/v1/videos/{id}/danmakus?since=timestamp
```

**缺点**: 延迟高（等于轮询间隔），服务器压力大，带宽浪费
**适用**: 仅适合对实时性要求不高的场景

#### 方案B: WebSocket 长连接推送 ⭐ 推荐

```
Client 与 Gateway 建立持久 WebSocket 连接
Gateway 维护房间 -> 连接映射
新弹幕 -> Broadcast 到房间内所有连接
```

**优点**: 实时性高(< 100ms)，双向通信，节省带宽
**缺点**: 需要维护大量长连接

#### 方案C: SSE (Server-Sent Events)

```
EventSource 单向推送，比 WebSocket 简单
适合只需服务端推送单向下行的场景
```

**选型**: WebSocket 最优，因为弹幕需要双向通信（用户要发送弹幕）

### WebSocket Gateway 设计

```
Gateway 架构:

                    ┌─────────────────────────┐
                    │     Load Balancer       │
                    │  (IP Hash / Least Conn) │
                    └───────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
    │ Gateway 1 │         │ Gateway 2 │         │ Gateway N │
    │ ┌───────┐ │         │ ┌───────┐ │         │ ┌───────┐ │
    │ │Room   │ │  Pub/Sub│ │Room   │ │         │ │Room   │ │
    │ │Manager│◄├─────────┼►│Manager│◄├─────────┼►│Manager│ │
    │ └───────┘ │  Redis  │ └───────┘ │         │ └───────┘ │
    │ 100K Conn │         │ 100K Conn │         │ 100K Conn │
    └───────────┘         └───────────┘         └───────────┘
```

```python
class DanmakuGateway:
    """弹幕长连接网关 - 单节点实现"""

    def __init__(self):
        self.rooms = {}                    # room_id -> set<websocket>
        self.user_connections = {}         # user_id -> websocket
        self.redis_pubsub = None
        self.buffer = DanmakuBuffer()      # 弹幕缓冲合并

    async def handle_connection(self, websocket):
        """处理 WebSocket 连接"""
        try:
            async for message in websocket:
                msg = json.loads(message)
                if msg['type'] == 'subscribe':
                    await self.subscribe(websocket, msg)
                elif msg['type'] == 'send_danmaku':
                    await self.send_danmaku(msg, websocket)
        finally:
            await self.unsubscribe(websocket)

    async def subscribe(self, websocket, msg):
        """订阅房间"""
        room_id = msg['room_id']
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

        # 发送当前时间点之前的弹幕(如最近10秒)
        recent_danmakus = await self.get_recent_danmakus(
            room_id, msg.get('time_offset', 0), window=10
        )
        for dm in recent_danmakus:
            await websocket.send(json.dumps({'type': 'danmaku', **dm}))

    async def send_danmaku(self, msg, websocket):
        """接收用户弹幕并处理"""
        # 1. 频率限制
        user_id = msg['user_id']
        if not await self.rate_check(user_id, msg['room_id']):
            await websocket.send(json.dumps({
                'type': 'error',
                'message': '发送太频繁，请稍后再试'
            }))
            return

        # 2. 敏感词过滤
        filtered = await self.content_filter(msg['content'])
        if filtered.blocked:
            await websocket.send(json.dumps({
                'type': 'danmaku_blocked',
                'reason': filtered.reason
            }))
            return

        # 3. 写入 Kafka（持久化 + 异步分发）
        await kafka_producer.send('danmaku_topic', value={
            'danmaku_id': generate_id(),
            'room_id': msg['room_id'],
            'user_id': user_id,
            'content': filtered.content,
            'time_offset': msg['time_offset'],
            'mode': msg.get('mode', 'scroll'),
            'color': msg.get('color', '#FFFFFF'),
            'timestamp': int(time.time() * 1000)
        })

    async def broadcast_to_room(self, room_id, danmaku):
        """向房间内所有连接广播弹幕"""
        if room_id in self.rooms:
            message = json.dumps({'type': 'danmaku', **danmaku})
            tasks = []
            for ws in list(self.rooms[room_id]):
                try:
                    tasks.append(ws.send(message))
                except Exception:
                    self.rooms[room_id].discard(ws)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_recent_danmakus(self, room_id, time_offset, window=10):
        """获取历史弹幕"""
        start = max(0, time_offset - window)
        end = time_offset
        key = f"video:danmakus:realtime:{room_id}"

        danmakus = await redis.zrangebyscore(
            key, start, end, start=0, num=200
        )
        return [json.loads(dm) for dm in danmakus]
```

### 弹幕缓冲与合并

弹幕不需要逐条立即下发，可以微批量合并发送以减少 TCP 包数量：

```python
class DanmakuBuffer:
    """弹幕缓冲合并发送"""

    def __init__(self, flush_interval=0.1, max_batch=50):
        self.buffer = {}           # room_id -> [danmakus]
        self.flush_interval = flush_interval
        self.max_batch = max_batch
        asyncio.create_task(self._periodic_flush())

    def add(self, room_id, danmaku):
        if room_id not in self.buffer:
            self.buffer[room_id] = []
        self.buffer[room_id].append(danmaku)

        if len(self.buffer[room_id]) >= self.max_batch:
            self._flush_room(room_id)

    async def _periodic_flush(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            for room_id in list(self.buffer.keys()):
                self._flush_room(room_id)

    def _flush_room(self, room_id):
        if room_id not in self.buffer or not self.buffer[room_id]:
            return
        batch = self.buffer[room_id]
        self.buffer[room_id] = []

        # 合并为一条消息下发
        batch_msg = json.dumps({
            'type': 'danmaku_batch',
            'count': len(batch),
            'items': batch
        })
        asyncio.create_task(gateway.broadcast_to_room(room_id, batch_msg))
```

### 敏感词过滤 (Content Moderation)

```python
class ContentFilter:
    """三层过滤机制"""

    def __init__(self):
        # Layer 1: AC自动机 - 精确词匹配
        self.ac_automaton = AhoCorasick()
        self.ac_automaton.build(keywords_list)

        # Layer 2: 正则表达式 - 模式匹配（手机号、身份证等）
        self.patterns = [
            (re.compile(r'1[3-9]\d{9}'), 'PHONE_NUMBER'),
            (re.compile(r'\d{17}[\dXx]'), 'ID_CARD'),
        ]

        # Layer 3: ML 模型 - 语义理解（可选，用于高级审核）
        self.ml_model = load_sentiment_model()

    def filter(self, text: str) -> FilterResult:
        # Layer 1: AC自动机 (极快, O(n))
        matches = self.ac_automaton.search(text)
        if matches:
            # 有敏感词 -> 替换为 ***
            for match in matches:
                text = text.replace(match.word, '*' * len(match.word))
            return FilterResult(
                cleaned_text=text,
                matched_keywords=[m.word for m in matches]
            )

        # Layer 2: 正则检查
        for pattern, reason in self.patterns:
            if pattern.search(text):
                return FilterResult(
                    blocked=True,
                    reason=f"检测到{reason}"
                )

        # Layer 3: ML 模型（异步，非阻塞）
        # 弹幕先放行，ML 结果异步回调处理
        asyncio.create_task(self.async_ml_check(text, danmaku_id))

        return FilterResult(cleaned_text=text)

    async def async_ml_check(self, text, danmaku_id):
        score = await self.ml_model.predict(text)
        if score > 0.8:
            await self.mark_for_review(danmaku_id, score)
        elif score > 0.95:
            await self.delete_danmaku(danmaku_id, "ML_MODEL_BLOCK")
            await self.notify_room_revoke(danmaku_id)
```

### 弹幕去重（客户端渲染层面）

弹幕可能因网络重传导致重复，需要在客户端去重：

```javascript
// 客户端去重
class DanmakuDeduplicator {
    constructor() {
        this.seen = new Set();           // danmaku_id 集合
        this.maxSize = 10000;            // 最多缓存1万条
        this.evictionQueue = [];
    }

    isDuplicate(danmakuId) {
        if (this.seen.has(danmakuId)) {
            return true;
        }
        this.seen.add(danmakuId);
        this.evictionQueue.push(danmakuId);

        if (this.evictionQueue.length > this.maxSize) {
            const oldest = this.evictionQueue.shift();
            this.seen.delete(oldest);
        }
        return false;
    }
}
```

### 弹幕密度控制

```
用户设备/网络能力不同，在客户端根据配置做降级:

密度等级 1 (极低): 同时显示 < 10 条弹幕
密度等级 2 (低):   同时显示 < 30 条
密度等级 3 (中):   同时显示 < 50 条 (默认)
密度等级 4 (高):   同时显示 < 100 条
密度等级 5 (极高): 无限制

服务端也可以根据密度等级做过滤:
- 高密度时随机丢弃(drop rate)一部分弹幕再下发
- 或者下发时带上优先级：付费弹幕 > 高级用户 > 普通用户 > 游客
```

### 历史弹幕查询优化

```sql
-- 问题: 高并发下的 time_offset 范围查询
SELECT * FROM danmakus
WHERE video_id = 'v123'
  AND time_offset BETWEEN 120.0 AND 130.0
ORDER BY time_offset ASC, created_at ASC
LIMIT 500;

-- 优化方案:
-- 1. 联合索引 (video_id, time_offset, created_at)
-- 2. 热门视频使用 Redis Sorted Set 缓存热点时间段
-- 3. 冷视频直接查 DB，不占 Redis 内存

def get_danmakus(video_id, start_time, end_time):
    cache_key = f"video:danmakus:realtime:{video_id}"
    is_hot = redis.exists(cache_key)

    if is_hot:
        # 从 Redis 读取 (前 2 小时的弹幕)
        danmakus = redis.zrangebyscore(cache_key, start_time, end_time)
        return parse_danmakus(danmakus)
    else:
        # 从 MySQL 读取
        return db.query(
            "SELECT * FROM danmakus WHERE video_id=? AND "
            "time_offset BETWEEN ? AND ? ORDER BY time_offset LIMIT 500",
            video_id, start_time, end_time
        )
```

## 扩展性与高可用

### 水平扩展策略

| 组件 | 扩展策略 |
|------|---------|
| WebSocket Gateway | 按 room_id 一致性哈希，同一房间尽量同一节点；新节点加入时平滑迁移 |
| Danmaku Service | 无状态，K8s HPA 自动扩缩 |
| Redis | Cluster 模式，按 {video_id} 的 hash tag 分片 |
| MySQL | 按 video_id 分库分表（1024 分片） |
| Kafka | 按 video_id 分区，保证同一房间的消息有序 |

### 热点房间处理

```
热门直播(百万观看) vs 普通视频(几百观看):

方案1: 独立资源池
  - 识别热门房间 (在线人数 > 阈值)
  - 将其流量路由到专用集群(更多资源)
  - 避免热门房间影响普通房间

方案2: 弹幕聚合下发
  - 普通房间: 单条弹幕立即下发
  - 热门房间: 每 100ms 聚合一次批量下发
  - 减少网络包数量和系统调用

方案3: 边缘计算
  - CDN 边缘节点也跑 WebSocket Gateway
  - 弹幕就近广播给用户
  - 减少中心机房压力
```

### 灾难恢复

```
场景: WebSocket Gateway 宕机
  影响: 连接到此 Gateway 的用户断开
  恢复:
    1. 客户端自动重连 (exponential backoff: 1s, 2s, 4s, 8s...)
    2. 负载均衡器自动摘除故障节点
    3. 新 Gateway 实例接管

场景: Kafka 积压
  影响: 弹幕分发延迟
  恢复:
    1. 增加 Consumer 数量
    2. 降低非关键审核步骤
    3. 限流弹幕发送
```

## 总结

弹幕系统的核心设计要点：

1. **实时分发架构**: WebSocket 长连接 + Redis Pub/Sub 跨 Gateway 广播，P99 延迟控制在 200ms 内
2. **三层审核体系**: AC 自动机精确匹配 + 正则模式匹配 + ML 语义理解，逐层递进，前台快速放行
3. **弹幕缓冲合并**: 热门房间每 100ms 批量下发，减少网络包数量，支持百万级并发
4. **双存储模式**: Redis Sorted Set（实时热点）+ MySQL（持久化全量），兼顾性能与可靠性
5. **客户端去重**: danmaku_id 集合去重，防止网络重传导致弹幕重复显示
6. **密度控制**: 服务端按优先级过滤 + 客户端按设备能力动态控制显示数量
7. **热点隔离**: 热门房间独立资源池 + 边缘节点分发
8. **消息有序性**: Kafka 同 video_id 分区保证弹幕时序

面试中面试官可能追问：弹幕的时序一致性如何保证？Kafka 分区内有序但跨分区如何排序？弹幕推送失败如何重试？WebSocket 连接数上限如何突破（C10M 问题）？
