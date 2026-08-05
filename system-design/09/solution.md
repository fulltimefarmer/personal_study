# 09. 设计通知系统 (Design Notification System)

## 题目

设计一个类似微信、Slack 或 App Push Notification 的通知系统。支持多种通知渠道（Push、短信、邮件、站内信），具备高可用、低延迟和高吞吐能力。系统需要支持优先级调度、模板化、用户偏好设置和防打扰策略。

---

## 需求澄清

### 功能性需求

1. **多渠道发送**：Push Notification (APNs/FCM)、短信、邮件、站内信、WebSocket 实时通知
2. **通知模板**：支持通知内容模板化（如 "您有新的评论" / "订单已发货"）
3. **触发机制**：由业务系统事件触发通知发送（订单状态变更、消息到达、活动提醒等）
4. **优先级调度**：根据通知类型和紧急程度分配优先级（高/中/低）
5. **用户偏好设置**：用户可配置接收哪些类型通知、在什么时间段接收（免打扰）
6. **通知历史**：用户可查看历史通知记录
7. **送达追踪**：记录通知是否成功发送、用户是否点击/阅读
8. **批量发送**：支持向大量用户群发通知（营销/活动推送）
9. **频率控制**：防止对同一用户在短时间内发送过多通知（通知轰炸）
10. **多语言支持**：根据用户语言偏好发送不同语言版本的通知

### 非功能性需求

1. **高可用**：99.99% 可用，核心通知不能丢失
2. **低延迟**：用户触发通知 → 接收 < 5s（实时通知 < 1s）
3. **高吞吐**：支持万级 QPS 写入，百万级 QPS 发送
4. **可靠性**：至少一次投递（At-Least-Once），不丢通知
5. **扩展性**：轻松支持新增通知渠道
6. **合规性**：遵守 GDPR/CCPA 等隐私法规，用户可选择不接收营销通知

### 容量估算

**假设条件：**
- DAU: 5 亿
- 每日通知总量: 50 亿（每用户平均 10 条）
- 各渠道占比:
  - Push: 50%（25 亿）
  - 站内信: 35%（17.5 亿）
  - 邮件: 10%（5 亿）
  - 短信: 5%（2.5 亿）
- 事务性通知: 70%（实时性要求高）
- 营销通知: 30%（可延迟发送）

**QPS 估算：**
- 通知创建 QPS: 50 亿 / 86400 ≈ **57,870 QPS**（峰值 ×3 ≈ **173K QPS**）
- 通知发送 QPS (渠道):
  - Push: 25亿 / 86400 ≈ 29K QPS
  - 站内信 (写入DB): 同创建 QPS
  - 邮件 (SMTP): 5亿 / 86400 ≈ 5,787 QPS
  - 短信: 2.5亿 / 86400 ≈ 2,894 QPS

**存储估算：**
- 站内信存储（30天保留）:
  - 每条站内信约 1KB
  - 17.5亿 × 30 × 1KB ≈ **5.25 TB**
- 历史记录（90天）: 
  - 50亿 × 90 × 500B ≈ **22.5 TB**
- 用户偏好设置: 5亿 × 1KB ≈ 500 GB
- 总存储: ~30 TB

---

## API 设计

### 通知发送 API (供业务系统调用)

```
1. 发送通知
POST /api/v1/notifications
Authorization: Bearer <service_token>
X-Service-ID: order-service

Request:
{
  "template_id": "order_shipped",        // 模板 ID
  "recipients": [                         // 接收者
    {
      "user_id": "user_12345",
      "channels": ["push", "in_app", "email"],  // 请求的渠道
      "contact": {
        "email": "user@example.com",
        "phone": "+8613800138000",
        "device_tokens": [
          "ios_token_xxx",
          "android_token_yyy"
        ]
      }
    }
  ],
  "template_vars": {                      // 模板变量
    "order_id": "ORD-2025-0001",
    "tracking_number": "SF1234567890",
    "estimated_delivery": "2025-01-15"
  },
  "priority": "high",                     // high | normal | low
  "category": "transactional",            // transactional | marketing
  "send_at": null,                        // 定时发送 (null = 立即)
  "ttl_seconds": 86400,                   // 通知有效期
  "idempotency_key": "ord-0001-shipped"   // 幂等键
}

Response: 202 Accepted
{
  "notification_id": "notif_abc123",
  "status": "accepted",
  "tracking": {
    "total_recipients": 1,
    "breakdown": {
      "push": {"queued": 1, "failed": 0},
      "in_app": {"queued": 1, "failed": 0},
      "email": {"queued": 1, "failed": 0}
    }
  }
}

2. 查询通知状态
GET /api/v1/notifications/notif_abc123

Response: 200 OK
{
  "notification_id": "notif_abc123",
  "status": "completed",
  "breakdown": {
    "push": {"sent": 1, "delivered": 1, "failed": 0},
    "in_app": {"sent": 1},
    "email": {"sent": 1, "delivered": 1, "opened": 0}
  },
  "completed_at": 1704070800000
}

3. 批量查询通知状态
POST /api/v1/notifications/batch-status
{
  "notification_ids": ["notif_abc", "notif_def"]
}

4. 取消定时通知
DELETE /api/v1/notifications/notif_abc123
```

### 用户侧 API (查询/管理通知)

```
1. 获取站内信列表
GET /api/v1/users/{user_id}/in-app-notifications?status=unread&page_size=20&cursor=xxx

Response:
{
  "notifications": [
    {
      "id": "inapp_001",
      "type": "order_update",
      "title": "订单已发货",
      "body": "您的订单 ORD-0001 已发货，快递单号：SF1234567890",
      "is_read": false,
      "action_url": "app://orders/ORD-0001",
      "image_url": "https://cdn.example.com/notif_icon.png",
      "created_at": 1704070800000
    }
  ],
  "unread_count": 5,
  "next_cursor": "1704070800000_inapp_001"
}

2. 标记已读
POST /api/v1/users/{user_id}/in-app-notifications/read
{
  "notification_ids": ["inapp_001", "inapp_002"],
  "mark_all": false
}

3. 获取/更新通知偏好设置
GET /api/v1/users/{user_id}/notification-preferences

Response:
{
  "channels": {
    "push": true,
    "email": true,
    "sms": false,
    "in_app": true
  },
  "categories": {
    "transactional": {
      "push": true, "email": true, "sms": true, "in_app": true
    },
    "marketing": {
      "push": false, "email": false, "sms": false, "in_app": true
    },
    "social": {
      "push": true, "email": false, "sms": false, "in_app": true
    }
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "timezone": "Asia/Shanghai"
  },
  "rate_limit": {
    "marketing": {"max_per_day": 3},
    "social": {"max_per_hour": 10}
  }
}

PUT /api/v1/users/{user_id}/notification-preferences
{...} // 更新偏好设置
```

---

## 数据模型

### 通知记录表

```sql
-- 通知主表 (存放发送历史和站内信)
CREATE TABLE notifications (
    id VARCHAR(32) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    template_id VARCHAR(64),
    category VARCHAR(32) NOT NULL,       -- transactional | marketing | social
    priority ENUM('high','normal','low') DEFAULT 'normal',
    title VARCHAR(255),
    body TEXT NOT NULL,
    action_url VARCHAR(2048),
    image_url VARCHAR(2048),
    is_read BOOLEAN DEFAULT FALSE,
    read_at BIGINT,
    created_at BIGINT NOT NULL,
    ttl_seconds INT DEFAULT 86400,       -- 有效期
    expires_at BIGINT,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_user_unread (user_id, is_read, created_at DESC),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB
PARTITION BY RANGE (created_at) (...);
-- 分片键: user_id

-- 渠道发送状态表
CREATE TABLE notification_deliveries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notification_id VARCHAR(32) NOT NULL,
    channel VARCHAR(16) NOT NULL,        -- push | email | sms | in_app
    recipient VARCHAR(255),              -- device_token | email | phone
    status ENUM('pending','sent','delivered','failed','bounced','clicked','opened'),
    provider_message_id VARCHAR(128),    -- 第三方返回的 ID
    error_code VARCHAR(64),
    error_message TEXT,
    sent_at BIGINT,
    delivered_at BIGINT,
    created_at BIGINT NOT NULL,
    INDEX idx_notif_channel (notification_id, channel),
    INDEX idx_status (status, created_at)
);
```

### 模板存储

```sql
CREATE TABLE notification_templates (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    category VARCHAR(32),
    channels JSON,                        -- ["push", "email", "sms", "in_app"]
    push_template JSON,
    email_template JSON,
    sms_template JSON,
    in_app_template JSON,
    variables JSON,                       -- ["order_id", "tracking_number", ...]
    default_priority VARCHAR(16) DEFAULT 'normal',
    default_ttl_seconds INT DEFAULT 86400,
    is_active BOOLEAN DEFAULT TRUE,
    created_at BIGINT NOT NULL,
    updated_at BIGINT
);

-- 模板示例 (email_template)
{
  "subject": "订单 #{order_id} 已发货",
  "body_html": "<h1>订单更新</h1><p>您的订单 <strong>#{order_id}</strong> 已发货</p><p>快递单号: #{tracking_number}</p><p>预计送达: #{estimated_delivery}</p>",
  "body_text": "您的订单 #{order_id} 已发货。快递单号: #{tracking_number}。预计送达: #{estimated_delivery}。"
}
```

### 用户偏好

```
用户偏好存储于 Redis + 定期同步到 MySQL:

Redis Key:   user:prefs:{user_id}
Type:        Hash
Fields:
  channels_push:      1
  channels_email:    1
  channels_sms:      0
  transactional_push: 1
  marketing_email:    0
  quiet_enabled:      1
  quiet_start:        2200         # 22:00
  quiet_end:          800          # 08:00
  quiet_timezone:     Asia/Shanghai
  lang:               zh-CN

优势:
  - 发送时频繁读取 → Redis 极速读取
  - MySQL 异步持久化 → 容灾恢复
  - 偏好变更时先写 Redis + 异步写 MySQL

设备 Token 存储:
Key:   user:devices:{user_id}
Type:  Hash
Fields:
  ios_prod_token:    abc123...
  android_fcm_token: def456...
  huawei_token:      ghi789...
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────┐
                              │        业务系统 (Event Producers)          │
                              │  订单系统  评论系统  消息系统  营销系统     │
                              └─────────────────────┬────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────┐
                              │          Notification API Gateway         │
                              │  ┌──────────────────────────────────────┐ │
                              │  │  - 参数校验 + 鉴权                    │ │
                              │  │  - 幂等检测 (idempotency_key)         │ │
                              │  │  - 限流 (Rate Limiting)               │ │
                              │  │  - 请求标准化 → Notification Event     │ │
                              │  └──────────────────────────────────────┘ │
                              └─────────────────────┬────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────┐
                              │          Kafka / Pulsar (消息队列)         │
                              │                                          │
                              │  ┌────────────────────────────────────┐  │
                              │  │ Topic: notification.events         │  │
                              │  │ 32 分区, 持久化, 复制因子 3          │  │
                              │  │                                    │  │
                              │  │ 消息格式:                           │  │
                              │  │ {                                   │  │
                              │  │   "event_id": "...",               │  │
                              │  │   "template_id": "order_shipped",  │  │
                              │  │   "recipients": [...],             │  │
                              │  │   "priority": "high",              │  │
                              │  │   "template_vars": {...}           │  │
                              │  │ }                                   │  │
                              │  └────────────────────────────────────┘  │
                              └─────────────────────┬────────────────────┘
                                                    │
          ┌─────────────────────────────────────────┼──────────────────────────┐
          │                                         │                          │
┌─────────▼──────────┐                  ┌───────────▼─────────┐    ┌───────────▼──────────┐
│  通知处理引擎        │                  │   用户偏好服务        │    │   Frequency Control   │
│  (Worker Pool)     │                  │                     │    │   (频率控制)           │
│                   │                  │  - 读取用户偏好        │    │                       │
│  ┌───────────────┐│                  │  - 渠道开关            │    │  - 每用户每类别        │
│  │ 模板渲染        ││                  │  - 免打扰时段          │    │    频率限制            │
│  │ (Template     ││                  │  - 语言偏好            │    │  - 全局发送            │
│  │  Engine)      ││                  │  - 设备 Token          │    │    速率控制            │
│  └───────┬───────┘│                  │                     │    │                       │
│          │        │                  │  Redis + MySQL        │    │  Redis Counter +      │
│  ┌───────▼───────┐│                  └───────────┬─────────┘    │  Token Bucket          │
│  │ 渠道路由        ││                             │              └───────────┬──────────┘
│  │ (Channel      ││                             │                          │
│  │  Router)      ││                             │                          │
│  └───────┬───────┘│                             │                          │
│          │        │                             │                          │
│  ┌───────▼───────┐│                             │                          │
│  │ 优先级调度      ││                             │                          │
│  │ (Priority     ││                             │                          │
│  │  Queue)       ││                             │                          │
│  └───────────────┘│                             │                          │
└─────────┬─────────┘                             │                          │
          │                                       │                          │
          ▼                                       ▼                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              渠道发送 Worker                                       │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐│
│  │ Push Worker     │  │ Email Worker    │  │ SMS Worker      │  │ In-App Worker ││
│  │                 │  │                 │  │                 │  │               ││
│  │ APNs HTTP/2    │  │ 第三方SMTP/AWS  │  │ 第三方SMS Provider│  │ 写入 DB       ││
│  │ FCM HTTP v1    │  │ SES / SendGrid  │  │ Twilio / 阿里云  │  │ + WebSocket   ││
│  │ 华为推送        │  │                 │  │                 │  │ 推送          ││
│  │ 小米推送        │  │ - 模板渲染      │  │ - 内容截断       │  │               ││
│  │ OPPO推送       │  │ - Link Tracking│  │ - 黑名单检查     │  │ - 批量写入     ││
│  │ VIVO推送       │  │ - Unsubscribe  │  │ - 发送状态回调   │  │ - 实时通知     ││
│  │               │  │ - Bounce处理   │  │                 │  │               ││
│  │ - 设备Token    │  │                 │  │                 │  │               ││
│  │   有效性检测    │  │                 │  │                 │  │               ││
│  │ - 厂商通道降级  │  │                 │  │                 │  │               ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘│
└───────────┼────────────────────┼────────────────────┼───────────────────┼────────┘
            │                    │                    │                   │
            ▼                    ▼                    ▼                   ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                          状态回调 & 追踪                                      │
   │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐   │
   │  │ Delivery Status  │   │ Click/Open       │   │ 故障队列 (DLQ)        │   │
   │  │ Queue            │   │ Tracking Queue   │   │ - 重试失败的消息       │   │
   │  │ - 更新DB状态      │   │ - 记录用户行为     │   │ - 人工介入             │   │
   │  └──────────────────┘   └──────────────────┘   └──────────────────────┘   │
   └───────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 通知优先级调度

```
优先级队列设计:

┌─────────────────────────────────────────────────────┐
│               Priority Queue Architecture            │
│                                                     │
│  入向:                                               │
│  ┌──────────────────────────────┐                   │
│  │ notification.events (Kafka)  │                   │
│  └──────────────┬───────────────┘                   │
│                 │                                   │
│                 ▼                                   │
│  ┌──────────────────────────────┐                   │
│  │ Priority Classifier           │                   │
│  │ - 用户VIP等级                  │                   │
│  │ - 通知类别                     │                   │
│  │ - 业务指定优先级                │                   │
│  └──────────────┬────────────────┘                   │
│                 │                                   │
│     ┌───────────┼───────────┐                       │
│     ▼           ▼           ▼                       │
│  ┌──────┐  ┌──────┐  ┌──────┐                       │
│  │ P1:  │  │ P2:  │  │ P3:  │                       │
│  │ 紧急  │  │ 普通  │  │ 低优 │                       │
│  │ Redis│  │ Redis│  │ Redis│                       │
│  │ List │  │ List │  │ List │                       │
│  └──┬───┘  └──┬───┘  └──┬───┘                       │
│     │         │         │                           │
│     ▼         ▼         ▼                           │
│  ┌──────────────────────────────┐                   │
│  │ Weighted Round-Robin Dispatcher│                  │
│  │ 权重: P1=70%, P2=25%, P3=5%  │                   │
│  │ P3 在低负载时逐步消费          │                   │
│  └──────────────────────────────────────────────────────────────────────────┘
```

```python
class PriorityDispatcher:
    def __init__(self):
        self.queues = {
            'high':   {'key': 'notif:queue:high',   'weight': 0.70},
            'normal': {'key': 'notif:queue:normal', 'weight': 0.25},
            'low':    {'key': 'notif:queue:low',    'weight': 0.05},
        }
        self.current_weight = {'high': 0, 'normal': 0, 'low': 0}

    def dispatch_batch(self, batch_size=100):
        """加权轮询分发"""
        for priority in ['high', 'normal', 'low']:
            self.current_weight[priority] += self.queues[priority]['weight']

            if self.current_weight[priority] >= 1:
                self.current_weight[priority] -= 1
                notifications = redis.lpop(
                    self.queues[priority]['key'], batch_size
                )
                if notifications:
                    return priority, notifications

        # 如果高优先级队列为空，降级消费
        for priority in ['high', 'normal', 'low']:
            notifications = redis.lpop(self.queues[priority]['key'], batch_size)
            if notifications:
                return priority, notifications
        return None, []
```

### 用户偏好过滤与免打扰

```python
class UserPreferenceFilter:
    def should_send(self, user_id: int, category: str, channel: str, 
                    priority: str) -> tuple[bool, str]:
        """
        判断是否应该向该用户发送通知
        Returns: (should_send, reason)
        """
        # 1. 获取用户偏好 (Redis)
        prefs = redis.hgetall(f"user:prefs:{user_id}")
        if not prefs:
            # 无偏好设置 → 使用默认策略
            return True, "default_allow"

        # 2. 检查渠道开关
        if prefs.get(f"channels_{channel}", "1") == "0":
            return False, f"channel_{channel}_disabled"

        # 3. 检查类别渠道开关
        if prefs.get(f"{category}_{channel}", "1") == "0":
            return False, f"category_{category}_channel_disabled"

        # 4. 免打扰时段检查
        if prefs.get("quiet_enabled") == "1" and priority != "high":
            quiet_start = int(prefs["quiet_start"])     # e.g. 2200
            quiet_end = int(prefs["quiet_end"])         # e.g. 800
            tz = prefs.get("quiet_timezone", "UTC")
            local_time = self._get_time_in_tz(tz)

            if quiet_start < quiet_end:
                # 正常区间: 如 08:00 ~ 22:00 是活跃时段
                in_quiet = not (quiet_start <= local_time <= quiet_end)
            else:
                # 跨天区间: 如 22:00 ~ 08:00 是免打扰
                in_quiet = local_time >= quiet_start or local_time <= quiet_end

            if in_quiet:
                return False, "quiet_hours"

        # 5. 频率限制检查
        if not FrequencyController.check(user_id, category, channel):
            return False, "rate_limited"

        return True, "allowed"
```

### 多渠道重试与降级策略

```python
class MultiChannelDeliveryStrategy:
    """
    多渠道发送策略:
    1. 按用户偏好顺序选择主渠道
    2. 主渠道失败后自动降级到备用渠道
    3. 紧急通知可同时发送多渠（确保到达）
    """

    CHANNEL_PRIORITY = ['push', 'in_app', 'email', 'sms']

    def deliver(self, notification):
        user = notification.recipient
        target_channels = self._resolve_channels(notification, user)

        results = {}
        for channel in target_channels:
            try:
                result = self._deliver_channel(notification, channel, user)
                results[channel] = result

                if channel == notification.primary_channel and not result.success:
                    # 主渠道失败，尝试降级
                    fallback = self._get_fallback_channel(channel)
                    if fallback and fallback not in target_channels:
                        fallback_result = self._deliver_channel(
                            notification, fallback, user
                        )
                        results[fallback] = fallback_result
            except ChannelException as e:
                results[channel] = DeliveryResult(success=False, error=str(e))

        return results

    def _deliver_channel(self, notification, channel, user):
        if channel == 'push':
            return self.push_provider.send(
                tokens=user.device_tokens,
                title=notification.title,
                body=notification.body,
                data={'notification_id': notification.id, 'type': notification.type}
            )
        elif channel == 'email':
            return self.email_provider.send(
                to=user.email,
                subject=notification.email_subject,
                html_body=notification.email_html
            )
        elif channel == 'sms':
            return self.sms_provider.send(
                to=user.phone,
                content=notification.sms_content[:140]
            )
        elif channel == 'in_app':
            return self.in_app_service.store(
                user_id=user.id,
                notification=notification
            )
```

### 厂商推送通道管理

```
移动端推送(FCM/APNs) + 国内厂商通道:

Android 推送生态:
┌─────────────────────────────────────────────────────┐
│  后台运行                       前台运行               │
│  ┌─────────────┐              ┌─────────────┐       │
│  │ FCM (Google) │              │ 长连接 保持   │       │
│  │ 海外设备支持  │              │ (WebSocket) │       │
│  └──────┬──────┘              └─────────────┘       │
│         │                    │                       │
│  国内厂商通道（自动降级）:                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │ 华为HMS   │ │ 小米MiPush│ │ OPPO/VIVO Push       │  │
│  │ Push Kit │ │          │ │                      │  │
│  └──────────┘ └──────────┘ └──────────────────────┘  │
│                                                      │
│  策略: FCM 主通道 + 厂商通道自动降级                     │
│  - 海外: FCM 直连                                     │
│  - 国内: 检测厂商 → 选择对应厂商Push SDK                 │
│  - 厂商通道不可用 → 应用内长连接保活                      │
└─────────────────────────────────────────────────────┘

iOS 推送:
  统一通过 APNs (Apple Push Notification service)
  HTTP/2 endpoint: api.push.apple.com
  支持 notification 和 background 两种类型
```

---

## 扩展性与高可用

### 保证通知不丢失

```
多层级可靠性保障:

Layer 1: API Gateway
  - 幂等性: idempotency_key 防止重复提交
  - 请求校验: 格式、字段完整性

Layer 2: Kafka 消息队列
  - 持久化: 消息写入磁盘 (replication factor = 3)
  - 确认机制: acks=all (所有 ISR 确认)
  - 分区: 按 (user_id % N) 分区, 保证同一用户的消息有序
  - 最小 ISR: min.insync.replicas = 2 (容忍 1 台故障)

Layer 3: Worker 处理
  - At-Least-Once 消费: 处理完成后提交 offset
  - 重试: 失败最多重试 3 次 (指数退避: 1s, 5s, 25s)
  - DLQ (Dead Letter Queue): 3 次重试失败 → 进入 DLQ
  - 人工处理 DLQ 消息 (Dashboard + 告警)

Layer 4: 渠道发送
  - 第三方 API 超时与重试
  - 设备 Token 失效检测 → 异步清理
  - 邮件 Bounce 处理 → 标记无效邮箱
  - 短信黑名单检查
```

### 大促/峰值流量处理

```
营销大促期间的峰值流量处理:

1. 消息队列缓冲:
   - 非实时营销通知可以缓存在 Kafka 中排队
   - 控制实际发送速率 (全局令牌桶)

2. 营销限速:
   - 营销通知全局速率限制 (e.g., 10K/s)
   - 事务性通知不受限 (优先通过)

3. 冷数据预热:
   - 大促前预先加载用户 Device Token 到 Redis 热数据中
   - 减少大促期间 DB 回源

4. 动态扩容:
   - Worker Pool 基于 Kafka Lag 自动扩缩容 (K8s HPA)
   - 渠道发送 Worker 独立扩容

5. 分批次发送:
   - 千万级用户营销推送 → 按 user_id hash 分批
   - 每批间隔 5-30 分钟
   - 监控发送量、投诉率、退订率

6. 降级策略:
   - 短信/邮件资源有限 → 优先保证事务性通知
   - 营销通知可全部降为站内信
```

### 监控与告警

```
通知系统核心监控:

业务指标 (按渠道、类别分组):
  - 通知发送量 (total / per channel / per category)
  - 发送成功率、失败率
  - 送达率 (Delivered / Sent)
  - 点击率 (CTR = Clicked / Delivered)
  - 退订率 (邮件 Unsubscribe)
  - 投诉率 (邮件 Spam report)
  - Bounce Rate (硬弹/软弹)

性能指标:
  - 端到端延迟 (API收到 → 用户收到) P50/P95/P99
  - Kafka 消费 Lag (阈值: > 5min 告警)
  - Worker 处理延迟 P95
  - 各渠道 Provider API 延迟 P95

基础设施指标:
  - Notification DB 写入 QPS、读取 QPS
  - 站内信未读数总览
  - Redis 用户偏好缓存命中率
  - DLQ 队列深度 (阈值: > 100 条 告警)

费用指标:
  - 每日短信发送量 (费用)
  - 每日邮件发送量 (费用)
  - Push 通知量 (通常免费)
  - 厂商Push通道调用量
```

---

## 总结

通知系统的设计核心挑战和权衡：

1. **多渠道抽象**：Push/邮件/短信/站内信需要统一的抽象层，新增渠道时最小化改动
2. **可靠性 > 实时性**：至少一次投递 (At-Least-Once) + 幂等消费是核心可靠性保障
3. **优先级调度**：加权轮询将优先级差异化，紧急通知跳过免打扰等限制
4. **用户偏好 & 免打扰**：每用户细粒度的渠道/类别/时段控制是用户体验关键
5. **厂商推送生态**：Android 的 FCM + 国内厂商通道的多通道降级是真实的工程挑战
6. **频率控制**：防止通知轰炸，每用户每类别每渠道的细粒度限制
7. **模板系统**：内容与逻辑解耦，业务方只需传入变量即可
8. **大促削峰**：Kafka 缓冲 + 全局限速 + 分批次发送 + 营销降级的多重保障
9. **状态追踪**：发送 → 送达 → 阅读的全链路追踪帮助分析通知效果
10. **合规性**：GDPR/CCPA 要求用户可自由选择接收哪些通知

**面试核心权衡讨论：**
- 实时性 vs 可靠性：Kafka 异步处理 vs 同步直接发送
- 优先级：紧急通知是否可以突破免打扰/频率限制
- 集中式 vs 去中心化：由业务方直接调用渠道 vs 经过通知中心
- 推送通道：自建长连接 vs 厂商Push vs 混合策略
- 通知合并：多条同类通知合并为一条 (提示有 N 条新消息) vs 逐条发送
- 内容渲染：模板渲染在服务端 vs 客户端本地拼接
