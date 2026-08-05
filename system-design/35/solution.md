# 35. 设计视频会议系统 (Video Conferencing like Zoom)

## 题目

设计一个类似 Zoom/Google Meet 的视频会议系统，支持多人实时音视频通信、屏幕共享、聊天、录制等功能。

---

## 需求澄清

### 功能性需求 (Functional Requirements)

- 支持多人视频会议（2～1000人）
- 音视频通信支持（双向/单向）
- 屏幕共享（单个/多个参与者）
- 会议录制与回放
- 文字聊天（会议中消息）
- 虚拟背景和背景模糊
- 等候室（Waiting Room, 主持人批准后进入）
- 举手、表情回应
- 会议角色管理（主持人/参与者）
- 跨平台支持（Web、iOS、Android、Desktop）

### 非功能性需求 (Non-functional Requirements)

| 指标 | 要求 |
|------|------|
| 延迟 | 端到端 < 200ms（实时通信） |
| 带宽 | 自适应码率（100kbps～4Mbps） |
| 可用性 | 99.99% |
| 丢包恢复 | 30%网络丢包下仍可通信 |
| 回声消除 | 自动回声消除、降噪 |
| 扩展性 | 支持百万场并发会议 |
| 安全性 | E2EE（端到端加密）/传输加密 |

### 容量估算

假设：
- DAU: 500万
- 峰值并发会议: 10万场
- 平均每会议人数: 5人
- 最大会议人数: 1000人（Webinar模式）
- 音视频码率: 平均 1Mbps/人（视频）
- SFU模式下服务端转发带宽：
  - 上行: 每用户 1Mbps
  - 下行: 每用户接收 (N-1) 路 ≈ 需要SFU做选择性转发
  - 总带宽需求 ≈ 并发言频用户数 × 1Mbps × 2(上下行)

---

## 高层次架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Client Applications                               │
│    Web (WebRTC)    iOS App     Android App    Desktop App               │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     Signaling Server Cluster (信令服务)                    │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │Signaling Node│  │Signaling Node│  │Signaling Node│  (WebSocket)      │
│  │ - 加入/离开   │  │ - SDP Exchange│  │ - ICE候选    │                   │
│  │ - 房间管理   │  │ - 角色控制    │  │ - 状态同步   │                   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │
│         │                 │                  │                            │
└─────────┼─────────────────┼──────────────────┼────────────────────────────┘
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       Media Server Cluster (媒体服务)                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SFU (Selective Forwarding Unit)                │   │
│  │                                                                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │SFU Node │  │SFU Node │  │SFU Node │  │SFU Node │            │   │
│  │  │ Room A  │  │ Room B  │  │ Room C  │  │ Room D  │            │   │
│  │  │         │  │         │  │         │  │         │            │   │
│  │  │P1→P2,P3│  │         │  │         │  │         │            │   │
│  │  │P2→P1,P3│  │         │  │         │  │         │            │   │
│  │  │P3→P1,P2│  │         │  │         │  │         │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │   │
│  │                                                                  │   │
│  │  SFU职责: 接收→选择性转发（不解码/不转码，只转发RTP包）           │   │
│  │  Simulcast: 每个发布者发送多路不同码率，SFU根据接收方带宽选择     │   │
│  │  SVC: 可伸缩视频编码，SFU根据网络状况选择转发层数                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    MCU (Multipoint Control Unit)                  │   │
│  │  用于: 录制、PSTN接入、传统视频会议设备互通                         │   │
│  │  功能: 解码→混流/合成→编码输出                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           Storage & Services                              │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐           │
│  │PostgreSQL│  │  Redis   │  │  Kafka   │  │ S3/Blob      │           │
│  │ 用户/会议  │  │ 在线状态  │  │ 聊天消息  │  │ 录制文件      │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

### SFU vs MCU vs P2P 架构对比

```
P2P (Mesh) 架构:
  每个参与者直接与所有其他人建立连接
  ┌───┐         ┌───┐
  │ P1│◄───────►│ P2│
  └─┬─┘         └─┬─┘
    │    ┌───┐    │
    └───►│ P3│◄───┘
         └───┘
  上行: 每人发送 2 路 (N-1)
  下行: 每人接收 2 路 (N-1)
  总带宽: 每人 (N-1) × 1Mbps 上下行

SFU (Selective Forwarding Unit) 架构:
  ┌───┐         ┌───────────────────┐         ┌───┐
  │ P1│──RTP───►│                   │──RTP───►│ P2│
  └───┘         │       SFU         │         └───┘
  ┌───┐         │  (只转发不解码)    │         ┌───┐
  │ P3│──RTP───►│                   │──RTP───►│ P4│
  └───┘         └───────────────────┘         └───┘
  上行: 每人发送 1 路到SFU
  下行: SFU选择性转发 (只转发言频讲话者、钉选者)
  总带宽: 上行 1Mbps, 下行 ≤ 5Mbps（选择转发）

MCU (Multipoint Control Unit) 架构:
  ┌───┐         ┌───────────────────┐         ┌───┐
  │ P1│──RTP───►│       MCU         │──1路───►│ P2│
  └───┘         │  解码→混流→编码    │         └───┘
                └───────────────────┘
  上行: 每人发送 1 路到MCU
  下行: MCU合成1路发给每人
  总带宽: 最小, 但MCU CPU消耗巨大
```

| 指标 | P2P (Mesh) | SFU | MCU |
|------|------------|-----|-----|
| 服务器CPU | 无 | 低(只转发) | 极高(编解码) |
| 客户端带宽 | 高(N×1Mbps) | 中(可控制) | 低(1路) |
| 延迟 | 最低 | 低(+10-20ms) | 中(+50-100ms) |
| 适用人数 | < 5人 | 5～1000人 | 任意(但成本高) |
| 录制 | 客户端各自录制 | 需额外处理 | 天然支持 |

**推荐: SFU 为主 + MCU 为辅**
- 日常会议(3-20人): SFU选择性转发
- 大型Webinar(100+): SFU + 听众只接收不发送
- 录制: MCU 混流录制器作为"虚拟参与者"接入
- PSTN接入: MCU转换

---

## 核心深入

### 1. WebRTC 技术栈

```
WebRTC 协议栈:

┌─────────────────────────────────────────────┐
│              Application API                 │
│  getUserMedia | RTCPeerConnection | RTCData │
├─────────────────────────────────────────────┤
│           WebRTC C++ API (PeerConnection)    │
├────────────────┬──────────────┬─────────────┤
│  Audio Engine  │ Video Engine │ Transport   │
│  - Opus 编码    │ - VP8/VP9    │ - SRTP      │
│  - 回声消除(AEC) │ - H.264/AV1  │ - ICE       │
│  - 降噪(ANS)    │ - 抖动缓冲   │ - STUN/TURN │
│  - 自动增益(AGC)│ - FEC/NACK   │ - DTLS      │
└────────────────┴──────────────┴─────────────┘

Simulcast (多码率同时发送):
  发布者: 同时发送 3 路不同码率
    - 高清: 1920x1080 @ 2.5Mbps
    - 标清: 640x360  @ 500kbps
    - 低清: 320x180  @ 150kbps

  SFU: 根据每个接收者网络状况选择转发哪一层
    - P2 (好网络): 转发高清层
    - P3 (一般网络): 转发标清层
    - P4 (差网络): 转发低清层

SVC (Scalable Video Coding):
  单流多层编码, 每层依赖前一层
    - Base Layer (基础层, 可独立解码)
    - Enhancement Layer 1 (增强层1)
    - Enhancement Layer 2 (增强层2)
  SFU: 根据带宽去掉某些增强层即可降码率
```

### 2. 会议信令流程

```
信令交互流程 (Join Conference):

Client                    Signaling Server           SFU/MCU
  │                             │                       │
  │ 1. Create Offer (SDP)       │                       │
  │─────────────────────────────>                       │
  │                             │                       │
  │ 2. Verify Token/Permission  │                       │
  │                    ┌────────┴────────┐              │
  │                    │ Room Manager    │              │
  │                    │ - 检查会议是否存在│              │
  │                    │ - 检查用户权限    │              │
  │                    │ - 分配SFU节点    │              │
  │                    └────────┬────────┘              │
  │                             │                       │
  │ 3. 返回SDP Answer + SFU地址 │                       │
  │<────────────────────────────│                       │
  │                             │                       │
  │ 4. ICE Candidate 收集       │                       │
  │    (STUN/TURN 服务器)        │                       │
  │                             │                       │
  │ 5. DTLS 握手 + SRTP 建立    │                       │
  │───────────────────────────────────────────────────>│
  │                             │                       │
  │ 6. RTP 媒体流开始传输        │                       │
  │<══════════════════════════════════════════════════=>│
  │                             │                       │
  │ 7. 通知其他参与者            │                       │
  │   "User X joined"           │                       │
  │          ┌──────────────────┤                       │
  │          ▼                  ▼                       │
  │      P2 Offer→Answer交换   P3 Offer→Answer交换      │
  │      P2 RTP→SFU            P3 RTP→SFU              │
```

### 3. 网络适应策略

```python
class NetworkAdaptation:
    """
    GCC (Google Congestion Control) 拥塞控制
    基于延迟和丢包的混合拥塞控制
    """
    
    def estimate_bandwidth(self, rtcp_feedback):
        """
        带宽估计算法:
        1. Delay-based: 基于单向延迟梯度(overuse/normal/underuse)
        2. Loss-based: 基于丢包率
        3. 取两者最保守估计
        
        自适应策略:
        - 当前带宽足够: 提升码率(AIMD)
        - 当前带宽不足: 降级 (视频分辨率/帧率/码率)
        """
        # Delay-based estimate
        delta_delay = self.compute_delay_gradient(rtcp_feedback)
        if delta_delay > OVERUSE_THRESHOLD:
            overuse_detected = True
            target_rate *= 0.85  # 快速降速
        elif delta_delay < UNDERUSE_THRESHOLD:
            target_rate *= 1.05  # 慢速升速
        
        # Loss-based: 丢包率 > 2% → 严重拥塞
        loss_rate = rtcp_feedback.fraction_lost / 256.0
        if loss_rate > 0.10:
            return target_rate * 0.5
        elif loss_rate > 0.02:
            return target_rate * (1 - 0.5 * loss_rate)
        
        return target_rate
    
    def choose_simulcast_layer(self, estimated_bw, layers):
        """根据估带宽选择转发层"""
        for i, layer in enumerate(layers):
            if estimated_bw >= layer.bitrate:
                return i
        return len(layers) - 1  # 最底层

# 丢包恢复策略:
# 1. FEC (Forward Error Correction): 发送冗余编码数据
# 2. NACK (Negative ACK): 请求重传丢失的包
# 3. PLC (Packet Loss Concealment): 在接收端通过插值隐藏丢包
# 组合策略: 关键帧→NACK重传, 非关键帧→FEC+PLC
```

### 4. SFU 服务器设计

```cpp
// SFU核心转发逻辑
class SFUEngine {
    struct Participant {
        string id;
        vector<MediaStream> published_streams;  // 发布的流
        vector<Subscription> subscriptions;     // 订阅的流
        NetworkQuality quality;                 // 网络质量
        
        // Simulcast rid: "f" (full), "h" (half), "q" (quarter)
        string active_rid;
    };
    
    void onRTPPacket(const string& room_id, 
                     const string& sender_id,
                     const RTPPacket& packet) {
        auto& room = rooms_[room_id];
        auto& sender = room.participants[sender_id];
        
        // 选择转发目标
        for (auto& [pid, receiver] : room.participants) {
            if (pid == sender_id) continue;
            
            // 检查该接收者是否订阅了此流
            auto& sub = findSubscription(receiver, packet.ssrc);
            if (!sub.active) continue;
            
            // 根据接收者网络质量选择转发层
            auto& layer = selectLayer(packet, receiver.quality);
            
            // 转发（只转发不解码）
            forwardBuffer(layer.data, receiver.transport);
        }
    }
    
    void selectLayer(const RTPPacket& packet, NetworkQuality quality) {
        // Simulcast: 根据接收方带宽选择rid
        // SVC: 根据带宽选择空间/时间/质量层
        // Dominant Speaker: 当前发言者→最高优先级转发
    }
};

// 选择性转发策略:
// Prioritization:
//   1. 活跃发言者 (Dominant Speaker): 高清, 优先转发
//   2. 钉选用户 (Pinned): 高清
//   3. 最近发言者: 标清
//   4. 静默参与者: 低清 / 暂停视频转发
//   5. 屏幕共享: 最高优先级 (需要清晰度)
```

### 5. 聊天系统设计

```
会议内聊天:

┌──────────┐    ┌──────────┐    ┌──────────┐
│ Client A │    │  Client B │    │ Client C │
└────┬─────┘    └─────┬─────┘    └────┬─────┘
     │                │               │
     │  sendMessage   │               │
     │──────►         │               │
     │         ┌──────▼───────────────▼──────┐
     │         │   Chat Service (无状态)      │
     │         │   1. 验证用户在会议中         │
     │         │   2. 写入Kafka              │
     │         │   3. 广播给会议内所有人       │
     │         └──────────────────────────────┘
     │                │               │
     │   newMessage   │   newMessage  │
     │◄───────────────┼───────────────┤
     │                ▼               ▼
     │           Client B        Client C

消息存储:
  - Kafka: 实时消息传递
  - PostgreSQL/Redis: 最近N条消息缓存
  - 历史消息归档到S3 (通过Kafka消费写入)
```

### 6. 会议录制

```
录制方案:

方案1: 服务器端录制 (推荐)
  ┌───────────────────────────────────────┐
  │           Recorder Service            │
  │                                       │
  │  作为特殊参与者接入会议:               │
  │  1. 接收所有参与者的音频流              │
  │  2. 接收所有参与者的视频流              │
  │  3. 接收屏幕共享流                     │
  │  4. 接收聊天消息流                     │
  │                                       │
  │  录制模式:                             │
  │  a) 复合录制: 混流为单一布局文件        │
  │  b) 独立录制: 每路流单独录制            │
  │                                       │
  │  输出: MP4/WebM + 元数据JSON           │
  │  存储: S3 → CDN分发                    │
  └───────────────────────────────────────┘

方案2: 客户端录制 (备选)
  - 本地录制, 无需服务端资源
  - 质量取决于客户端网络
  - 大型会议不适用

录制后处理流水线:
  Raw Recording → Transcoding (多分辨率) → 
  语音转文字(STT) → 时间线标记 → 
  存储分发 → CDN播放
```

---

## 扩展性与高可用

### 1. SFU 扩容策略

```
SFU 扩容方案:

智能分配:
  1. 分配算法: 新会议→选择负载最低的SFU节点
  2. 紧急扩容: SFU节点达到容量80%→自动启动新节点
  3. 预热池: 保持5%空闲节点应对突发

Cascading SFU (级联, 超大型会议):
                     ┌──────────┐
                     │ SFU Root │ (汇总节点)
                     └────┬─────┘
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │SFU    │ │SFU    │ │SFU    │
         │Leaf 1 │ │Leaf 2 │ │Leaf 3 │
         │100人  │ │100人  │ │100人  │
         └────────┘ └────────┘ └────────┘
  
  每个Leaf SFU处理100人, 跨SFU只转发活跃发言者的流
  总共: 300人 × 上行(本地) + N活跃 × 跨SFU转发
```

### 2. 地理分布 (Geo-distributed SFU)

```
多区域部署:

         ┌─────────────┐         ┌─────────────┐
         │  Region A   │         │  Region B   │
         │  (北京)     │◄───────►│  (新加坡)   │
         │             │ 专线/    │             │
         │  SFU Cluster│ Internet │  SFU Cluster│
         └─────────────┘         └─────────────┘
                ▲                       ▲
                │                       │
          ┌─────┴─────┐          ┌─────┴─────┐
          │ P1 │  P2  │          │ P3 │  P4  │
          │ 北京│ 上海│          │ 新加坡│东京│
          └─────────┘          └─────────┘

  区域选择: 新会议选择大多数参与者最近的SFU区域
  跨区域: 每个区域一个SFU, 区域间只转发活跃发言者
```

### 3. 故障恢复

| 故障 | 处理 |
|------|------|
| SFU节点崩溃 | 信令服务检测到, 自动迁移会议到备份SFU |
| 信令服务崩溃 | 客户端自动重连到其他信令节点 |
| 网络波动 | 自适应码率 + FEC + NACK |
| TURN中继故障 | 多TURN服务器, ICE自动选择备选路径 |

### 4. 安全设计

```
安全层次:

┌──────────────────────────────────┐
│  传输层: DTLS-SRTP (加密媒体流)   │
│  信令层: WSS (加密信令)           │
│  应用层: JWT Token + Meeting ID  │
│         + Meeting Password       │
├──────────────────────────────────┤
│  端到端加密 (E2EE):              │
│   方案: Insertable Streams API   │
│   密钥协商: ECDH + 客户端加解密   │
│   SFU/MCU 无法访问明文媒体内容     │
├──────────────────────────────────┤
│  防会议轰炸 (Zoombombing):      │
│  - Waiting Room 审核             │
│  - 会议密码                      │
│  - 仅认证用户可加入               │
└──────────────────────────────────┘
```

---

## 数据模型

```sql
-- 用户表
CREATE TABLE users (
    id          UUID PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 会议表
CREATE TABLE meetings (
    id              UUID PRIMARY KEY,
    host_id         UUID NOT NULL REFERENCES users(id),
    topic           VARCHAR(500),
    status          VARCHAR(20) DEFAULT 'scheduled',  -- scheduled/active/ended
    password        VARCHAR(100),
    settings        JSONB,          -- waiting_room, mute_on_join, etc
    scheduled_start TIMESTAMP,
    scheduled_end   TIMESTAMP,
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 会议参与者表
CREATE TABLE meeting_participants (
    meeting_id      UUID NOT NULL REFERENCES meetings(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    role            VARCHAR(20) DEFAULT 'participant', -- host/participant/viewer
    joined_at       TIMESTAMP,
    left_at         TIMESTAMP,
    sfu_node        VARCHAR(100),     -- 被分配到的SFU节点
    PRIMARY KEY (meeting_id, user_id)
);

-- 会议录制表
CREATE TABLE recordings (
    id              UUID PRIMARY KEY,
    meeting_id      UUID NOT NULL REFERENCES meetings(id),
    format          VARCHAR(20),      -- mp4, webm
    storage_url     TEXT NOT NULL,    -- S3 URL
    duration_sec    INTEGER,
    resolution      VARCHAR(20),
    file_size_bytes BIGINT,
    status          VARCHAR(20),      -- processing/ready/failed
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 会议聊天表
CREATE TABLE meeting_messages (
    id              UUID PRIMARY KEY,
    meeting_id      UUID NOT NULL,
    user_id         UUID NOT NULL,
    content         TEXT NOT NULL,
    message_type    VARCHAR(20) DEFAULT 'chat', -- chat/system/emoji
    sent_at         TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_meeting ON meeting_messages(meeting_id, sent_at);
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 媒体架构 | 主要SFU + 录制用MCU |
| 信令服务 | WebSocket + HTTP API 混合 |
| 网络适应 | GCC拥塞控制 + Simulcast/SVC + FEC/NACK |
| 音视频编码 | Opus(音频) + H.264/VP9(AV1)(视频) |
| 扩展性 | 级联SFU + 多区域部署 |
| 录制 | 服务端复合/独立录制 → S3 → CDN |
| 安全 | DTLS-SRTP + E2EE可选 + Meeting密码 |

**关键选型理由：**
- **SFU > MCU:** 服务器CPU成本降低10x+，延迟更低
- **Simulcast > 单码率:** 每个接收者自适应网络，不需要转码
- **WebRTC > 私有协议:** 浏览器原生支持，无需插件
- **级联SFU > 单SFU:** 支持超大规模会议(1000+)
