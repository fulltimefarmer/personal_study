# 02. 设计聊天/即时通讯系统 (Design Chat/Messaging System)

## 题目

设计一个类似 WhatsApp / WeChat 的即时通讯系统，支持一对一聊天、群组聊天、消息发送与接收、在线状态管理等功能。

---

## 需求澄清

### 功能性需求

1. **一对一聊天**：两个用户之间发送和接收文本消息
2. **群组聊天**：多个用户在群组内收发消息（最多支持数百人）
3. **消息状态**：已发送、已送达、已读（单勾/双勾/双蓝勾）
4. **在线/离线状态**：用户可以看到联系人的在线/最后上线时间
5. **多媒体消息**：图片、视频、文件、语音消息（需缩略图预览）
6. **消息历史**：拉取历史消息记录（分页/无限滚动）
7. **消息通知**：Push Notification 推送
8. **消息同步**：多设备同步（手机、桌面、Web）

### 非功能性需求

1. **低延迟**：消息端到端延迟 < 200ms（P99 < 500ms）
2. **高可靠性**：消息不丢失，不重复（至少一次投递，客户端去重）
3. **高可用性**：99.95% 可用性
4. **顺序保证**：同一会话内消息严格有序
5. **扩展性**：支持 10 亿+ 用户、百万级并发连接
6. **安全性**：端到端加密（E2EE）、传输层加密（TLS）

### 容量估算

**假设条件：**
- 日活跃用户 (DAU): 5 亿
- 每用户日均消息数: 50 条
- 每用户平均连接会话: 2 个设备
- 群组消息占比: 20%，私聊占比: 80%

**QPS 估算：**
- 日均消息总量: 5 亿 × 50 = 250 亿条
- 消息发送 QPS: 250 亿 / 86400 ≈ **289,000 QPS**（峰值 ×2 ≈ 578K QPS）
- 消息接收 QPS: 群组消息需广播，接收 QPS ≈ 发送 QPS × 平均群成员数 × 群组比例
  - 假设平均群 50 人，群组比例 20%
  - 接收 QPS ≈ 289K × (1 + 50 × 0.2) = 289K × 11 ≈ **3.2M QPS**

**存储估算：**
- 每条消息平均大小: ~1KB（含元数据、索引）
- 每日存储: 250 亿 × 1KB = 25 TB / 天
- 保留 5 年历史: 25TB × 365 × 5 ≈ **45,625 TB = 45.6 PB**
- 实际存储（假设 3 副本 + 压缩比 2:1）: 45.6 PB × 3 / 2 ≈ **68.4 PB**

**连接数估算：**
- 并发连接: 5 亿 × 0.3 (同时在线率) × 2 (多设备) = 3 亿连接
- 每台服务器支持 100K 连接: 需要 3,000 台 WebSocket 服务器

---

## API 设计

### 消息协议 (WebSocket / QUIC)

聊天系统的核心是**长连接**协议，而不是 REST API。主流选择：

| 协议 | 特点 | 适用场景 |
|------|------|---------|
| WebSocket | 全双工通信、浏览器原生支持 | Web端、移动端降级 |
| MQTT | 轻量级、发布/订阅模型 | IoT、弱网环境 |
| gRPC Bidirectional Stream | 高性能、HTTP/2 | 内部服务通信 |
| 自定义TCP长连接 | 极致优化 | 移动端主要方案 |
| QUIC | 0-RTT、连接迁移 | 弱网优化（新兴趋势） |

**推荐方案**：移动端使用自定义TCP/QUIC长连接，Web端使用WebSocket，内部服务使用gRPC。

### WebSocket 消息格式

```json
// 客户端 → 服务端：发送消息
{
  "type": "message.send",
  "seq_id": 12345,
  "data": {
    "conversation_id": "c_abc123",
    "conversation_type": "private",   // private | group
    "message_type": "text",           // text | image | video | file | voice
    "content": {
      "text": "你好，世界！"
    },
    "client_msg_id": "uuid-xxx",     // 客户端生成的唯一消息ID（去重）
    "timestamp": 1704067200123
  }
}

// 服务端 → 客户端：消息回执
{
  "type": "message.ack",
  "seq_id": 12345,
  "status": "success",
  "server_msg_id": "msg_789",
  "server_timestamp": 1704067200456
}

// 服务端 → 接收方：推送新消息
{
  "type": "message.push",
  "data": {
    "server_msg_id": "msg_789",
    "conversation_id": "c_abc123",
    "from_user_id": "u_456",
    "message_type": "text",
    "content": {"text": "你好，世界！"},
    "timestamp": 1704067200456
  }
}

// 服务端 → 发送方：已读确认
{
  "type": "message.read_receipt",
  "data": {
    "conversation_id": "c_abc123",
    "read_up_to": "msg_789",
    "read_by": "u_456",
    "timestamp": 1704067201000
  }
}

// 客户端 → 服务端：心跳
{
  "type": "heartbeat",
  "client_timestamp": 1704067200000
}

// 服务端 → 客户端：心跳响应
{
  "type": "heartbeat.ack",
  "server_timestamp": 1704067200001
}
```

### REST API（离线消息拉取、历史记录）

```
1. 获取会话列表
GET /api/v1/conversations?page_size=50&page_token=xxx

Response:
{
  "conversations": [
    {
      "id": "c_abc123",
      "type": "private",
      "participants": [{"user_id": "u_456", "name": "张三"}],
      "last_message": {...},
      "unread_count": 3,
      "updated_at": 1704067200000
    }
  ],
  "next_page_token": "yyy"
}

2. 拉取历史消息
GET /api/v1/conversations/{conv_id}/messages?before=msg_789&limit=50

Response:
{
  "messages": [
    {
      "msg_id": "msg_789",
      "from_user_id": "u_456",
      "content": {"text": "你好"},
      "timestamp": 1704067200000,
      "status": "read"
    }
  ],
  "has_more": true
}

3. 上传媒体文件
POST /api/v1/media/upload
Content-Type: multipart/form-data

Response:
{
  "media_id": "media_xyz",
  "url": "https://cdn.chat.com/media/xyz.jpg",
  "thumbnail_url": "https://cdn.chat.com/media/xyz_thumb.jpg",
  "size": 102400,
  "mime_type": "image/jpeg"
}

4. 用户在线状态
GET /api/v1/users/status?user_ids=u_456,u_789

Response:
{
  "statuses": {
    "u_456": {"status": "online", "last_seen": null},
    "u_789": {"status": "offline", "last_seen": 1704060000000}
  }
}
```

---

## 数据模型

### 消息存储 (NoSQL - 宽列存储, 如 HBase / Cassandra)

```
Row Key: conversation_id + `::` + timestamp (逆序, 便于查最新消息)
         c_private:u_123_u_456::9999999999999-1704067200

Column Family: msg
  - content       : JSON/Protobuf 序列化的消息体
  - from          : 发送者 user_id
  - msg_type      : text | image | video | file
  - status        : sent | delivered | read
  - client_msg_id : 客户端消息 ID
  - reply_to      : 被回复消息的 msg_id (引用回复)
```

```sql
-- 或者使用分片的 MySQL/TiDB (更简单的方案)

CREATE TABLE messages (
    msg_id BIGINT NOT NULL,
    conversation_id VARCHAR(64) NOT NULL,
    from_user_id VARCHAR(32) NOT NULL,
    msg_type ENUM('text','image','video','file','voice') NOT NULL,
    content JSON NOT NULL,
    client_msg_id VARCHAR(64),
    reply_to_msg_id BIGINT,
    status ENUM('sent','delivered','read') DEFAULT 'sent',
    created_at BIGINT NOT NULL COMMENT 'Unix毫秒时间戳',
    PRIMARY KEY (conversation_id, created_at, msg_id),
    UNIQUE KEY uk_client_msg (client_msg_id, conversation_id),
    INDEX idx_from_user (from_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
PARTITION BY RANGE (created_at) (...) -- 按时间分区
-- 分片键: conversation_id
```

### 会话列表存储 (Redis Sorted Set + MySQL)

```sql
-- MySQL 会话表
CREATE TABLE conversations (
    id VARCHAR(64) PRIMARY KEY,
    type ENUM('private','group') NOT NULL,
    participants JSON NOT NULL,
    last_message JSON,
    last_message_time BIGINT NOT NULL,
    created_at BIGINT NOT NULL
);
```

```
Redis 数据结构: 用户的会话列表（按最后消息时间排序）

Key:   user:conv:{user_id}
Type:  Sorted Set
Members:
  - conversation_id_1 : last_message_timestamp_1
  - conversation_id_2 : last_message_timestamp_2
  ...

ZREVRANGE user:conv:u_123 0 49 WITHSCORES  # 获取最近50个会话
```

### 在线状态存储 (Redis Hash + Pub/Sub)

```
# 在线状态 (Redis Hash)
Key:   user:status:{user_id}
Fields:
  status:     online | offline | away
  last_seen:  1704067200000 (Unix毫秒)
  device_count: 2

TTL: 5分钟 (心跳过期)

# 用户活跃设备列表 (Redis Hash)
Key:   user:devices:{user_id}
Fields:
  device_1: {"token":"abc","platform":"ios","last_heartbeat":1704067200}
  device_2: {"token":"def","platform":"android","last_heartbeat":1704067200}
```

### 未读消息计数 (Redis)

```
# 每个用户在每个会话的未读数
Key:   unread:{user_id}:{conversation_id}
Type:  Integer
Value: 5 (未读计数)

INCR unread:u_789:c_abc123    # 新消息到达时 +1
SET  unread:u_789:c_abc123 0  # 用户打开会话时清零
```

---

## 高层次架构

```
                                    ┌────────────────────────────────────┐
                                    │         DNS / Global LB            │
                                    └───────────────────┬────────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        │                               │                               │
              ┌─────────▼──────────┐         ┌──────────▼─────────┐        ┌───────────▼──────────┐
              │  Connection Layer  │         │   Business Layer   │        │    Media Handling     │
              │  ┌──────────────┐  │         │  ┌──────────────┐  │        │   ┌──────────────┐    │
              │  │ WebSocket    │  │         │  │ Message      │  │        │   │ Upload       │    │
              │  │ Gateway x N  │  │         │  │ Router       │  │        │   │ Service      │    │
              │  ├──────────────┤  │         │  ├──────────────┤  │        │   ├──────────────┤    │
              │  │ Connection   │  │         │  │ Group        │  │        │   │ Transcoding  │    │
              │  │ Manager      │  │         │  │ Manager      │  │        │   │ Service      │    │
              │  ├──────────────┤  │         │  ├──────────────┤  │        │   ├──────────────┤    │
              │  │ Session      │  │         │  │ Status/      │  │        │   │ CDN          │    │
              │  │ Store        │  │         │  │ Presence Svc │  │        │   │ Integration  │    │
              │  └──────────────┘  │         │  └──────────────┘  │        │   └──────────────┘    │
              └────────┬──────────┘         └──────────┬─────────┘        └───────────┬──────────┘
                       │                               │                              │
              ┌────────▼───────────────────────────────▼──────────────────────────────▼───────────┐
              │                           Kafka / Pulsar Message Queue                             │
              │  ┌──────────────────┐  ┌────────────────────────┐  ┌─────────────────────────┐   │
              │  │ message.send     │  │ message.delivery_status  │  │ message.notification    │   │
              │  │ Topic (32分区)    │  │ Topic                   │  │ Topic                   │   │
              │  └──────────────────┘  └────────────────────────┘  └─────────────────────────┘   │
              └──────────────────────────────────┬───────────────────────────────────────────────┘
                                                 │
              ┌──────────────────────────────────▼───────────────────────────────────────────────┐
              │                               存储层                                              │
              │  ┌───────────────┐  ┌──────────────────┐  ┌───────────────┐  ┌────────────────┐ │
              │  │ HBase/        │  │ Redis Cluster    │  │ MySQL/        │  │ Object Store   │ │
              │  │ Cassandra     │  │ (会话/状态/缓存)  │  │ TiDB          │  │ (S3/OSS)       │ │
              │  │ (消息主体)     │  │                  │  │ (用户/群组)    │  │ (媒体文件)      │ │
              │  └───────────────┘  └──────────────────┘  └───────────────┘  └────────────────┘ │
              └─────────────────────────────────────────────────────────────────────────────────┘
                                                 │
              ┌──────────────────────────────────▼───────────────────────────────────────────────┐
              │                    离线处理 & 推送                                                │
              │  ┌──────────────────────┐  ┌────────────────────────────────────────────────┐   │
              │  │ Push Notification    │  │ Feed / Inbox Service (用户离线消息收件箱)          │   │
              │  │ (APNs / FCM)         │  │ 每个用户维护离线消息队列                            │   │
              │  └──────────────────────┘  └────────────────────────────────────────────────┘   │
              └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 消息发送全流程

```
┌─ 发送方: User A ───────────────────────────────────────────────────────────────┐
│                                                                                │
│  1. App 生成 client_msg_id (UUID v7 / Snowflake)                                │
│  2. 通过长连接发送消息到 Connection Gateway                                      │
│  3. Gateway 做基础校验 (token/限流)                                              │
│  4. 消息进入 Kafka message.send topic                                            │
│                                                                                │
├─ 消息路由服务 ─────────────────────────────────────────────────────────────────┤
│                                                                                │
│  5. Message Router 消费 Kafka 消息                                              │
│  6. 校验用户权限 (是否在该会话中)                                                  │
│  7. 生成 server_msg_id (全局递增ID)                                              │
│  8. 写入消息存储 (HBase/Cassandra)                                               │
│     - RowKey: conversation_id::(MAX_TIMESTAMP - created_at)                     │
│  9. 更新会话最后消息                                                             │
│  10. 返回 ACK 给发送方                                                          │
│                                                                                │
├─ 接收方: User B ───────────────────────────────────────────────────────────────┤
│                                                                                │
│  11. Message Router 查询接收方连接状态                                            │
│      ├── 在线: 通过 Connection Gateway 直接推送 (Push)                            │
│      │   ├── 更新未读计数 (Redis INCR)                                            │
│      │   └── 推送消息体到客户端                                                    │
│      └── 离线: 消息存入离线收件箱 + 发送 Push Notification                         │
│                                                                                │
│  12. 客户端收到消息后发送 delivery_ack                                           │
│  13. Message Router 更新消息状态为 "delivered"                                    │
│  14. 用户点击消息后发送 read_ack                                                 │
│  15. Message Router 更新消息状态为 "read"                                        │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 群组消息扇出策略

群组消息的扇出是聊天系统最大的性能挑战之一。

#### 方案对比

**方案一：简单写扩散 (Write-time Fanout)**

```
发送者 → 消息存储 → 写入每个群成员的收件箱
适用于: 小群 (< 100人)
```

```
优点: 读取简单，每个用户只需拉取自己的收件箱
缺点: 写入放大严重。500人群每天50条消息 = 25,000次写入
```

**方案二：读扩散 (Read-time Fanout)**

```
发送者 → 消息仅存储到群会话 → 用户读取时查询群消息
```

```
优点: 写入简单，无放大
缺点: 读取昂贵，需要实时索引查询；无法推送通知内容
```

**方案三：混合策略（推荐）**

```
策略:
  - 小群 (< 100人): 写扩散到所有成员的收件箱
  - 中群 (100-500人): 写扩散到在线用户的收件箱 + 离线用户读扩散
  - 大群 (> 500人): 纯读扩散 + 在线用户实时推送仅含消息ID
  - 超大群/频道 (> 10K人): 类似发布/订阅，用户拉取 + 分页
```

```python
def fanout_message(message, group_id):
    group = group_service.get_group(group_id)
    member_count = group.member_count
    online_members = presence_service.get_online_members(group_id)

    if member_count <= 100:
        # 写扩散：写入所有人收件箱
        for member in group.members:
            inbox_service.add_message(member.user_id, message)

    elif member_count <= 500:
        # 混合：写扩散给在线用户，离线用户仅发通知
        for member in online_members:
            inbox_service.add_message(member.user_id, message)
            push_to_connection(member.user_id, message)

        for member in group.members - online_members:
            push_notification(member.user_id, message_summary)

    else:
        # 读扩散：仅推送轻量级通知（消息ID），用户真正查看时拉取完整消息
        for member in online_members:
            connection_manager.push(member.user_id, {
                "type": "message.new",
                "conversation_id": group_id,
                "msg_id": message.msg_id  # 仅推送ID
            })
        # 大群离线用户不发Push，防止骚扰
```

**微信的群组架构参考：**

```
微信群: 第 40 人进群前是写扩散，之后是读扩散
原因：
  - 用户发一条消息，服务端需要写入 N 个收件箱
  - N > 40 时写入成本太高
  - 切换为读扩散后，读取时需要拉取最新消息
```

### 消息顺序保证

聊天系统中，**同一会话内的消息需要严格有序**。

```
方案1: 全局单调递增ID (在消息路由器生成 server_msg_id)
  - 单线程生成 ID，成为单点/性能瓶颈
  - 适用于小规模

方案2: 会话级别 Lamport Clock (逻辑时钟)
  - 每个会话维护计数器
  - 发送时携带会话时钟值
  - 接收端按时钟排序
  - 分布式友好，无单点
  
方案3: HLC (Hybrid Logical Clock)【推荐】
  - 结合物理时钟 + 逻辑时钟
  - hlc = max(local_hlc, received_hlc) + 1
  - 物理时间可大致排序，逻辑部分处理同时事件
```

```python
# HLC 实现示例
class HybridLogicalClock:
    def __init__(self):
        self.wall_clock = 0  # 物理时钟部分
        self.logical = 0     # 逻辑时钟部分

    def tick(self):
        now = int(time.time() * 1000)
        if now > self.wall_clock:
            self.wall_clock = now
            self.logical = 0
        else:
            wall_clock += 1  # 预防物理时钟回拨

    def update(self, received_hlc):
        now = int(time.time() * 1000)
        rcvd_wall = received_hlc >> 16
        rcvd_log = received_hlc & 0xFFFF

        self.wall_clock = max(now, self.wall_clock, rcvd_wall)
        if self.wall_clock == rcvd_wall:
            self.logical = max(self.logical, rcvd_log) + 1
        else:
            self.logical = 0

    def get(self):
        return (self.wall_clock << 16) | self.logical
```

### 在线状态系统设计

状态系统需要一个高效的**发布/订阅模型**。

```
架构:

User A 登录 → Connection Gateway → Status Service
                                        │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                    Redis Set      Redis Pub/Sub   Kafka Topic
                 online:u_A = 1    channel:status  presence.change
                          │             │             │
                          ▼             ▼             ▼
                    查询状态      实时推送状态变化   离线分析

心跳机制:
  - 客户端每 30s 发送心跳包
  - 服务端每 60s 未收到心跳 → 标记离线
  - Redis Key 设置 TTL 90s (3×心跳间隔)
  - 用户状态变更时推送好友列表中的在线用户

在线状态扩散:
  微信方案: 仅通知双向好友 (互为好友)
  每次状态变更扩散 O(好友数) 条推送
  
  优化:
  - 批处理: 300ms 窗口内汇聚多次状态变更
  - 好友列表缓存 + 分推
  - 对于超大好友列表 (>5000人) 不推送，仅被动查询
```

### 多端消息同步

多设备场景下消息需要在所有设备间同步：

```
┌────────────────────────────────────────────┐
│          多端同步方案                        │
│                                            │
│  1. 每条消息记录 msg_id 和 seq_in_conv      │
│     (会话内递增序号)                         │
│                                            │
│  2. 每个设备维护 checkpoint:                │
│     Key: device:checkpoint:{device_id}      │
│     Value: {conversation_id: last_seq}     │
│                                            │
│  3. 设备上线时:                              │
│     - 发送本地 checkpoint 到服务端           │
│     - 服务端计算差异 → 拉取新消息            │
│     - 客户端应用增量消息                     │
│                                            │
│  4. 已读状态同步:                            │
│     - 用户在任一设备标记已读                  │
│     - 服务端广播已读状态到所有在线设备         │
│     - 设备对比本地未读数，更新角标            │
└────────────────────────────────────────────┘
```

### 端到端加密 (E2EE)

```
Signal Protocol (双棘轮算法) 已被 WhatsApp/ Signal/Matrix 采用:

核心组件:
  1. X3DH (Extended Triple Diffie-Hellman): 初始密钥协商
  2. Double Ratchet (双棘轮): 每条消息使用不同密钥
     - DH Ratchet: 每一次往返更新根密钥
     - Symmetric Ratchet: 每条消息派生新消息密钥
  3. PreKeys: 预生成的密钥包存储在服务端

前向安全性 (Forward Secrecy):
  - 即使长期密钥泄露，历史消息也无法解密
  - 每次棘轮轮转都丢弃旧密钥材料

后向安全性 (Post-Compromise Security / Future Secrecy):
  - 密钥泄露后，通过新的 DH 协商可恢复安全

服务端仅作为中继:
  - 不持有解密密钥
  - 无法读取消息内容
  - 元数据 (谁和谁通信、何时) 仍可被观察到
```

---

## 扩展性与高可用

### 连接网关的水平扩展

```
┌──────────────────────────────────────────────────────┐
│                    连接网关集群                         │
│                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ GW-1    │  │ GW-2    │  │ GW-N    │             │
│  │ (100K   │  │ (100K   │  │ (100K   │  ...        │
│  │ conns)  │  │ conns)  │  │ conns)  │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
│       │            │            │                   │
│  ┌────▼────────────▼────────────▼────┐              │
│  │   Route Table (Redis / etcd)      │              │
│  │   user_id → {gateway_id, conn_id} │              │
│  └───────────────────────────────────┘              │
│                                                      │
│  消息寻址: Message Router 查询 Route Table →          │
│  找到用户连接的 Gateway → 通过内部 RPC 推送            │
└──────────────────────────────────────────────────────┘
```

### 热点会话处理

```
问题: 热门群组（明星群、事件群）消息爆炸
  1个 1000W 人群组，每秒 100 条消息
  写扩散不可行: 100 × 1,000W = 10亿次写入/秒

解决方案:
  1. 热门会话识别: 
     - 基于消息频率 (msg/s) 识别热点会话
     - 动态切换扇出策略

  2. 热点会话读扩散:
     - 消息统一写入一个消息流 (Kafka partition)
     - 在线用户订阅该流，本地消费
     - 离线用户进入会话时拉取

  3. 分页 + 游标:
     - 大群不推送完整消息列表
     - 用户打开群时从最新消息开始分页拉取
```

### 宕机恢复

```
场景: 连接网关宕机

1. 客户端检测到连接断开
2. 客户端启动重连逻辑 (指数退避: 1s → 2s → 4s → ... → 60s)
3. 重新连接到可用网关 (通过LB/DNS)
4. 新网关查 Route Table 更新路由信息
5. 客户端发送本地 checkpoint
6. 服务端计算增量 → 推送离线期间遗漏的消息
7. 恢复完成

场景: Kafka / 消息队列故障
1. 消息临时写入网关本地磁盘 (WAL - Write Ahead Log)
2. Kafka 恢复后批量重放
3. 去重机制 (client_msg_id) 防止重复消息

场景: 消息存储 (HBase) 故障
1. 写操作降级到备用集群或本地日志
2. 读操作返回缓存数据或友好错误
3. 故障恢复后数据补齐
```

### 监控与告警

```
核心监控指标:

连接层:
  - 活跃连接数 (按网关/区域)
  - 新建连接速率、连接断开率
  - 心跳超时率 (指标: >1% 告警)
  - 消息接收/发送吞吐量 (按网关)

消息层:
  - 端到端延迟 P50/P95/P99 (指标: P99 > 500ms 告警)
  - 消息发送成功率 (指标: <99.9% 告警)
  - 消息去重率 (检测重放攻击)
  - ACK 延迟 P99

队列层:
  - Kafka 消费延迟 (指标: >1s 告警)
  - 消息积压量
  - 分区消费速率

业务层:
  - 未读消息累计量 (按用户)
  - Push 送达率 / 点击率
  - 群组扇出系数
  - 媒体上传成功率
```

---

## 总结

设计聊天系统是分布式系统中挑战最大的场景之一，核心难点在于：

1. **低延迟 vs 高可靠**：如何在不可靠的网络上保证消息低延迟到达
2. **扇出策略**：写扩散 vs 读扩散的权衡，是群聊系统的灵魂决策
3. **顺序保证**：同一会话内消息有序是用户体验的底线需求
4. **在线状态**：千万级状态变更的实时广播是巨大挑战
5. **多端同步**：消息在所有设备间保持一致性的复杂状态管理
6. **端到端加密**：在加密前提下实现群组、多端支持
7. **存储策略**：消息数据选择 HBase/Cassandra 等宽列存储而非关系型数据库
8. **连接管理**：百万级长连接的维护是基础设施层面的核心挑战

**面试核心权衡点：**
- 私聊扇出 vs 群聊扇出（写扩散 vs 读扩散 vs 混合）
- TCP 长连接 vs WebSocket vs QUIC 协议选择
- 消息顺序算法（HLC vs Lamport Clock vs 全局序列号）
- 在线状态推送策略（全量推送 vs 被动查询 vs 混合）
- 存储选型（HBase vs Cassandra vs TiDB vs 分片MySQL）
- E2EE 安全性与功能的平衡（加密 vs 服务端搜索/推荐）
