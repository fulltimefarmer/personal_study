# 设计支付系统 (Design Payment System)

## 题目

设计一个高可靠、高一致的支付系统，类似 Stripe / PayPal / Alipay，支持账户管理、支付交易、退款、对账等功能。

## 需求澄清

### 功能性需求

1. **用户支付**: 用户发起支付(信用卡、借记卡、银行转账、数字钱包)
2. **商户收款**: 商户接入支付系统完成收款
3. **账户管理**: 用户/商户的虚拟账户(余额、冻结金额、流水)
4. **退款**: 全额/部分退款，原路返回
5. **对账 (Reconciliation)**: 与银行/支付网关逐笔对账
6. **清结算 (Settlement)**: T+1 结算给商户
7. **风控**: 交易风险评估，反欺诈，反洗钱(AML)
8. **账单**: 用户/商户交易记录查询和导出

### 非功能性需求

- **强一致性**: 资金相关操作必须强一致性，不能丢钱，不能多扣
- **高可用**: 99.999% (5个9)，每年宕机 < 5.26 分钟
- **低延迟**: 支付请求 < 2秒（实际用户感知时间含银行交互）
- **幂等性**: 所有API必须支持幂等，防止重复扣款
- **安全性**: PCI-DSS 合规，敏感数据加密
- **可审计**: 每个操作有完整的审计日志
- **数据持久性**: 账务数据 100% 不丢失

### 容量估算

```
假设:
- 用户量: 1亿
- 日均交易笔数: 1000万笔
- 峰值QPS: 1000万 / 86400 × 10(高峰系数) ≈ 1,157 QPS
- 每笔交易产生数据: ~5KB (支付请求、支付结果、账户变更、审计日志)

存储估算:
- 日均数据: 1000万 × 5KB ≈ 50 GB/天
- 保留7年(监管要求): 50GB × 365 × 7 ≈ 127 TB
- 考虑冗余备份(3副本) + 审计日志 → ~500 TB

账户表:
- 1亿用户 + 100万商户 ≈ 1.01亿账户
- 每账户 ~500 bytes → 1.01亿 × 500 ≈ 50 GB

支付网关交互:
- 与银行/卡组织交互的网络延迟: 200ms-2s (不可控)
- 异步通知(Webhook) QPS: ~2,000 (支付结果回调)
```

## API设计

### 核心支付 API

```protobuf
// 创建支付订单
// POST /api/v1/payments
message CreatePaymentRequest {
  string idempotency_key = 1;            // 幂等键，必填
  string merchant_id = 2;
  string order_id = 3;                   // 商户侧订单号
  Money amount = 4;
  string currency = 5;                   // "USD", "CNY"
  PaymentMethod payment_method = 6;
  PaymentChannel channel = 7;            // CREDIT_CARD, ALIPAY, WECHAT_PAY, BANK_TRANSFER
  string return_url = 8;                 // 支付完成跳转地址
  string notify_url = 9;                 // 异步通知回调地址
  int64 expire_time_ms = 10;             // 订单过期时间
  string description = 11;
  map<string, string> metadata = 12;     // 商户自定义扩展
}

message PaymentMethod {
  oneof method {
    CreditCard credit_card = 1;
    Wallet wallet = 2;
    BankAccount bank_account = 3;
  }
}

message CreditCard {
  string card_number = 1;                // 仅传输至PCI-DSS环境
  string expiry_month = 2;
  string expiry_year = 3;
  string cvv = 4;
  string card_holder_name = 5;
  string token = 6;                      // 已token化的卡信息
}

message Money {
  int64 amount = 1;                      // 最小货币单位(分)
  string currency = 2;                   // ISO 4217
}

message CreatePaymentResponse {
  string payment_id = 1;                 // 系统内部支付ID
  string status = 2;                     // "pending", "processing", "processing_3ds"
  string redirect_url = 3;               // 3DS 验证跳转 / 收银台URL
  int64 created_at_ms = 4;
}
```

### 支付确认/查询 API

```protobuf
// 查询支付状态
// GET /api/v1/payments/{payment_id}
message Payment {
  string payment_id = 1;
  string merchant_id = 2;
  string order_id = 3;
  Money amount = 4;
  string currency = 5;
  string status = 6;                     // pending, processing, authorized, captured,
                                         // succeeded, failed, cancelled, refunded,
                                         // partially_refunded, expired
  string channel = 7;
  string channel_transaction_id = 8;     // 支付渠道交易号
  string failure_reason = 9;
  int64 created_at_ms = 10;
  int64 updated_at_ms = 11;
  map<string, string> metadata = 12;
}

// 退款
// POST /api/v1/refunds
message CreateRefundRequest {
  string idempotency_key = 1;
  string payment_id = 2;
  Money amount = 3;
  string reason = 4;                     // "customer_request", "duplicate", "fraudulent"
  string notify_url = 5;
}

message Refund {
  string refund_id = 1;
  string payment_id = 2;
  Money amount = 3;
  string status = 4;                     // pending, processing, succeeded, failed
  string channel_refund_id = 5;
  int64 created_at_ms = 6;
}
```

### 支付通知 Webhook

```protobuf
// 支付结果异步通知 (服务端 → 商户)
// POST {notify_url}
message PaymentNotification {
  string event_id = 1;
  string event_type = 2;                 // "payment.succeeded", "payment.failed",
                                         // "refund.succeeded", "refund.failed"
  Payment data = 3;
  string signature = 4;                  // HMAC 签名, 商户可验证来源
  int64 created_at_ms = 5;
}
```

### 账户/结算 API

```protobuf
// 查询商户账户余额
// GET /api/v1/accounts/{merchant_id}
message Account {
  string account_id = 1;
  string merchant_id = 2;
  Money available_balance = 3;           // 可用余额 (可提现)
  Money pending_balance = 4;             // 待清算余额 (T+1)
  Money frozen_balance = 5;              // 冻结金额
  string currency = 6;
  string status = 7;                     // "active", "suspended", "closed"
}

// 查询交易流水
// GET /api/v1/accounts/{merchant_id}/transactions
message AccountTransaction {
  string transaction_id = 1;
  string payment_id = 2;
  string type = 3;                       // "charge", "refund", "settlement", "withdrawal", "fee"
  Money amount = 4;
  Money balance_before = 5;
  Money balance_after = 6;
  int64 created_at_ms = 7;
}
```

## 数据模型

### 核心表结构 (分库分表)

```sql
-- 支付订单表 (按 payment_id hash 分库分表)
CREATE TABLE payments (
    payment_id VARCHAR(64) PRIMARY KEY,
    idempotency_key VARCHAR(128) NOT NULL,
    merchant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64),
    order_id VARCHAR(128) NOT NULL,
    amount BIGINT NOT NULL,                    -- 最小单位(分)
    currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    channel VARCHAR(32) NOT NULL,
    channel_transaction_id VARCHAR(128),
    channel_response JSON,
    failure_reason VARCHAR(500),
    description TEXT,
    metadata JSON,
    notify_url VARCHAR(500),
    notify_status VARCHAR(32) DEFAULT 'pending',  -- pending, sent, failed, acknowledged
    notify_retry_count INT DEFAULT 0,
    version INT NOT NULL DEFAULT 1,            -- 乐观锁版本号
    created_at_ms BIGINT NOT NULL,
    updated_at_ms BIGINT NOT NULL,
    expired_at_ms BIGINT,
    INDEX idx_merchant_created (merchant_id, created_at_ms DESC),
    INDEX idx_order_id (merchant_id, order_id),
    UNIQUE KEY uk_idempotency (idempotency_key),
    INDEX idx_expired (status, expired_at_ms)
) ENGINE=InnoDB;

-- 退款表
CREATE TABLE refunds (
    refund_id VARCHAR(64) PRIMARY KEY,
    idempotency_key VARCHAR(128) NOT NULL,
    payment_id VARCHAR(64) NOT NULL,
    merchant_id VARCHAR(64) NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    channel_refund_id VARCHAR(128),
    reason VARCHAR(500),
    created_at_ms BIGINT NOT NULL,
    updated_at_ms BIGINT NOT NULL,
    PRIMARY KEY (refund_id),
    INDEX idx_payment_id (payment_id),
    UNIQUE KEY uk_idempotency (idempotency_key)
) ENGINE=InnoDB;

-- 账户表 (按 account_id hash 分库分表)
CREATE TABLE accounts (
    account_id VARCHAR(64) PRIMARY KEY,
    merchant_id VARCHAR(64) UNIQUE NOT NULL,
    available_balance BIGINT NOT NULL DEFAULT 0,
    pending_balance BIGINT NOT NULL DEFAULT 0,
    frozen_balance BIGINT NOT NULL DEFAULT 0,
    total_revenue BIGINT NOT NULL DEFAULT 0,   -- 历史总收入
    total_refunded BIGINT NOT NULL DEFAULT 0,  -- 历史总退款
    currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    version INT NOT NULL DEFAULT 1,           -- 乐观锁
    created_at_ms BIGINT NOT NULL,
    updated_at_ms BIGINT NOT NULL
) ENGINE=InnoDB;

-- 账户流水表 (只追加，不可修改)
CREATE TABLE account_ledger (
    ledger_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL,
    payment_id VARCHAR(64),
    transaction_type VARCHAR(32) NOT NULL,     -- charge, refund, settlement, withdrawal, fee
    direction VARCHAR(8) NOT NULL,             -- credit(入金), debit(出金)
    amount BIGINT NOT NULL,
    balance_before BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    description VARCHAR(500),
    created_at_ms BIGINT NOT NULL,
    INDEX idx_account_time (account_id, created_at_ms DESC),
    INDEX idx_payment_id (payment_id)
) ENGINE=InnoDB;

-- 审计日志表 (不可修改/删除)
CREATE TABLE audit_logs (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    operator VARCHAR(64),
    old_value JSON,
    new_value JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at_ms BIGINT NOT NULL,
    INDEX idx_entity_time (entity_type, entity_id, created_at_ms DESC)
) ENGINE=InnoDB;
```

## 高层次架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           支付系统整体架构                               │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                         接入层 (Gateway)                           │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │ │
│  │  │ API Gateway   │  │ 收银台/Web SDK│  │ 移动端 SDK     │         │ │
│  │  │ (认证/限流/    │  │ (PC端支付页)  │  │ (iOS/Android)  │         │ │
│  │  │  路由/SSL     │  │               │  │                │         │ │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘         │ │
│  └──────────┼──────────────────┼──────────────────┼──────────────────┘ │
│             │                  │                  │                     │
│             └──────────────────┼──────────────────┘                    │
│                                │                                        │
│  ┌─────────────────────────────┼────────────────────────────────────┐  │
│  │                        业务服务层                                  │  │
│  │                             │                                     │  │
│  │  ┌──────────────┐  ┌───────▼───────┐  ┌──────────────┐           │  │
│  │  │ 支付处理服务   │  │ 退款服务       │  │ 账户服务       │           │  │
│  │  │ Payment       │  │ Refund        │  │ Account       │           │  │
│  │  │ Service       │  │ Service       │  │ Service       │           │  │
│  │  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘           │  │
│  │         │                  │                  │                   │  │
│  │         └──────────────────┼──────────────────┘                   │  │
│  │                            │                                      │  │
│  └────────────────────────────┼──────────────────────────────────────┘  │
│                               │                                         │
│  ┌────────────────────────────┼──────────────────────────────────────┐ │
│  │                      支付渠道层 (Payment Gateway)                   │ │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │ │
│  │  │ 信用卡  │ │ 支付宝  │ │ 微信支付│ │ 银行转账│ │ PayPal │         │ │
│  │  │ V/MC/AE│ │Channel │ │Channel │ │Channel │ │Channel │         │ │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘         │ │
│  │                    │                                                    │ │
│  │          ┌─────────▼─────────┐                                      │ │
│  │          │ 支付渠道路由        │                                      │ │
│  │          │ (Channel Router)  │                                      │ │
│  │          │ 渠道选择/降级/重试│                                      │ │
│  │          └───────────────────┘                                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                               │                                         │
│  ┌────────────────────────────┼──────────────────────────────────────┐ │
│  │                      数据层 (多数据中心)                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │ │
│  │  │ MySQL Cluster│  │ Redis Cluster│  │ 消息队列      │            │ │
│  │  │ (交易数据)    │  │ (缓存/幂等键) │  │ (异步通知/    │            │ │
│  │  │ 主-主 + 异地 │  │              │  │  对账/结算)   │            │ │
│  │  │ 灾备        │  │              │  │              │            │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      支撑系统                                       │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │ │
│  │  │ 风控引擎    │ │ 对账系统    │ │ 结算系统    │ │ 监控告警    │     │ │
│  │  │ (规则+ML)  │ │ (T+1日报)  │ │ (T+1结算)  │ │ (实时大盘)  │     │ │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 支付主流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         支付主流程详解                                   │
│                                                                         │
│  用户                商户              支付系统              银行/渠道    │
│  │                  │                  │                    │          │
│  │  1. 下单          │                  │                    │          │
│  │─────────────────►│                  │                    │          │
│  │                  │                  │                    │          │
│  │                  │  2. 创建支付     │                    │          │
│  │                  │   (幂等键)      │                    │          │
│  │                  │────────────────►│                    │          │
│  │                  │                  │                    │          │
│  │                  │  3. 返回收银台   │                    │          │
│  │                  │◄────────────────│                    │          │
│  │                  │   URL/Token     │                    │          │
│  │  4. 跳转收银台    │                  │                    │          │
│  │◄─────────────────│                  │                    │          │
│  │                  │                  │                    │          │
│  │  5. 用户输入支付信息 (卡号/密码/指纹)                                 │
│  │─────────────────────────────────────►│                    │          │
│  │                  │                  │                    │          │
│  │                  │                  │  6. 风控检查        │          │
│  │                  │                  │─────────────────   │          │
│  │                  │                  │                    │          │
│  │                  │                  │  7. 提交支付请求    │          │
│  │                  │                  │───────────────────►│          │
│  │                  │                  │                    │          │
│  │                  │                  │  8. 支付结果回调    │          │
│  │                  │                  │◄───────────────────│          │
│  │                  │                  │                    │          │
│  │                  │                  │  9. 更新订单状态    │          │
│  │                  │                  │─────────────────   │          │
│  │                  │                  │  更新账户余额       │          │
│  │                  │                  │  记账户流水         │          │
│  │                  │                  │                    │          │
│  │                  │ 10. 异步通知结果  │                    │          │
│  │                  │◄────────────────│                    │          │
│  │                  │                  │                    │          │
│  │ 11. 显示支付结果  │                  │                    │          │
│  │◄─────────────────│                  │                    │          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心深入

### 1. 幂等性设计 (Idempotency)

```
┌────────────────────────────────────────────────────────────────┐
│                    幂等性保证机制                               │
│                                                                │
│  核心问题: 网络超时 → 客户端重试 → 不能产生重复扣款              │
│                                                                │
│  实现方案: Idempotency Key + 数据库唯一约束                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  1. 客户端生成 idempotency_key (UUID)                     │  │
│  │     header: Idempotency-Key: 550e8400-e29b-41d4-a716-... │  │
│  │                                                          │  │
│  │  2. 服务端处理:                                           │  │
│  │     ┌────────────────────────────────────────────────┐   │  │
│  │     │ def create_payment(idempotency_key, ...):        │   │  │
│  │     │     # 步骤1: 检查幂等键是否已存在                 │   │  │
│  │     │     existing = db.query(                         │   │  │
│  │     │         "SELECT * FROM payments                  │   │  │
│  │     │          WHERE idempotency_key = ?",              │   │  │
│  │     │         idempotency_key                          │   │  │
│  │     │     )                                            │   │  │
│  │     │     if existing:                                  │   │  │
│  │     │         return existing  # 幂等返回,不重复执行     │   │  │
│  │     │                                                  │   │  │
│  │     │     # 步骤2: 插入新记录 (利用唯一约束防并发)       │   │  │
│  │     │     try:                                          │   │  │
│  │     │         payment = db.insert_payment(              │   │  │
│  │     │             idempotency_key=...,                  │   │  │
│  │     │             payment_id=generate_id(),             │   │  │
│  │     │             ...                                   │   │  │
│  │     │         )                                         │   │  │
│  │     │         process_payment(payment)                  │   │  │
│  │     │         return payment                            │   │  │
│  │     │     except DuplicateKeyError:                     │   │  │
│  │     │         # 并发场景: 另一个请求先插入了              │   │  │
│  │     │         return db.query(                          │   │  │
│  │     │             "SELECT * FROM payments               │   │  │
│  │     │              WHERE idempotency_key = ?",           │   │  │
│  │     │             idempotency_key                       │   │  │
│  │     │         )                                         │   │  │
│  │     └────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  │  3. 幂等键过期策略:                                       │  │
│  │     - Redis: TTL = 24小时                                │  │
│  │     - MySQL: 定时清理 > 24h 的幂等键记录                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  多层幂等保证:                                                  │
│  1. 应用层: idempotency_key (业务幂等)                         │
│  2. 数据库层: UNIQUE约束 (存储幂等)                             │
│  3. 支付渠道层: 渠道transaction_id (渠道幂等)                   │
│  4. 消息层: 消费者offset + 业务ID防重消费                       │
└────────────────────────────────────────────────────────────────┘
```

### 2. 分布式事务与一致性保证

```
┌────────────────────────────────────────────────────────────────┐
│                   支付系统的一致性模型                           │
│                                                                │
│  CAP 分析: 支付系统必须选择 CP (一致性 + 分区容忍)               │
│  - 资金数据不能不一致 (不能丢钱/多钱)                            │
│  - 必须能在网络分区时做出正确决策                               │
│                                                                │
│  方案一: 两阶段提交 (2PC) - 不推荐用于高并发                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  问题: Coordinator单点, 同步阻塞, 性能差                        │
│                                                                │
│  方案二: TCC (Try-Confirm-Cancel) - 推荐                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  场景: 用户A向商户B支付100元                               │  │
│  │                                                          │  │
│  │  Try 阶段 (预留资源):                                     │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 1. 冻结用户A账户100元 (available -= 100, frozen += 100)│  │
│  │  │ 2. 创建待处理状态支付订单                              │  │
│  │  │ 3. 记录冻结流水                                        │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  Confirm 阶段 (提交):                                     │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 1. 扣除用户A冻结金额 (frozen -= 100)                  │  │
│  │  │ 2. 增加商户B待结算金额 (pending += 100)                │  │
│  │  │ 3. 更新支付订单为"已支付"                              │  │
│  │  │ 4. 记录支付流水                                        │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  Cancel 阶段 (回滚):                                      │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 1. 解冻用户A金额 (frozen -= 100, available += 100)    │  │
│  │  │ 2. 更新支付订单为"已取消"                              │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  方案三: Saga 模式 (长事务补偿)                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  适用于多服务多步骤的场景:                                 │  │
│  │                                                          │  │
│  │  正向流程:                                                │  │
│  │  Step1: 风控检查 → Step2: 渠道扣款 → Step3: 账户入账     │  │
│  │                                                          │  │
│  │  补偿流程 (任一Step失败):                                 │  │
│  │  Step3失败 → 补偿Step2(渠道退款) → 补偿Step1(风控解禁)    │  │
│  │  Step2失败 → 补偿Step1(风控解禁)                          │  │
│  │                                                          │  │
│  │  实现: 事件驱动 + 状态机                                  │  │
│  │  Pub/Sub (Kafka/RabbitMQ) + Compensation Handler         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  方案四: 本地事务 + 异步最终一致 (常用模式)                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. 在同一个本地数据库事务中:                              │  │
│  │     UPDATE accounts SET balance = balance - 100          │  │
│  │     INSERT INTO account_ledger (amount=100, type=debit)  │  │
│  │     UPDATE payments SET status = 'succeeded'             │  │
│  │     INSERT INTO outbox (payment_id, event_type)          │  │
│  │                                                          │  │
│  │  2. 异步 Worker 消费 Outbox 表, 发送通知给商户             │  │
│  │     (Debezium/CDC 或 定时轮询)                            │  │
│  │                                                          │  │
│  │  3. 通知失败 → 重试 → 最终一致                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 3. 对账系统 (Reconciliation)

```
┌────────────────────────────────────────────────────────────────┐
│                      对账系统设计                               │
│                                                                │
│  为什么需要对账?                                                │
│  - 支付渠道可能漏回调/重复回调/错误回调                          │
│  - 两边数据可能不一致导致资金差错                                │
│  - 监管要求每日对账                                            │
│                                                                │
│  对账流程:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  每日流程 (每天凌晨执行):                                  │  │
│  │                                                          │  │
│  │  Step 1: 获取对账文件                                     │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 从支付渠道下载前一日交易流水文件 (CSV/SFTP)           │ │  │
│  │  │ 同时导出我方系统的交易流水                             │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                          │                               │  │
│  │                          ▼                               │  │
│  │  Step 2: 数据比对                                        │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ ┌─────────────────┐   ┌─────────────────┐           │ │  │
│  │  │ │ 我方交易流水     │   │ 渠道交易流水     │           │ │  │
│  │  │ │ (Internal)      │   │ (External)      │           │ │  │
│  │  │ │ payment_id +    │   │ channel_tx_id + │           │ │  │
│  │  │ │ amount          │   │ amount          │           │ │  │
│  │  │ └────────┬────────┘   └────────┬────────┘           │ │  │
│  │  │          │                     │                     │ │  │
│  │  │          └──────────┬──────────┘                     │ │  │
│  │  │                     │                                │ │  │
│  │  │                     ▼                                │ │  │
│  │  │          ┌─────────────────────┐                    │ │  │
│  │  │          │    比对结果         │                    │ │  │
│  │  │          │                    │                    │ │  │
│  │  │          │  ✓ 匹配 (1对1)     │ → 正常，标记已对账 │ │  │
│  │  │          │  金额交易号均一致    │                    │ │  │
│  │  │          │                    │                    │ │  │
│  │  │          │  ⚠ 渠道有，我方无   │ → 长款 (长收/长付)│ │  │
│  │  │          │   (金额不一致)      │   需要人工处理     │ │  │
│  │  │          │                    │                    │ │  │
│  │  │          │  ⚠ 我方有，渠道无   │ → 短款 (少收/少付) │ │  │
│  │  │          │                    │   需要调查原因     │ │  │
│  │  │          └─────────────────────┘                    │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                          │                               │  │
│  │                          ▼                               │  │
│  │  Step 3: 差错处理                                        │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 长款: 我方差收入 → 人工确认 → 补记录 → 入账         │ │  │
│  │  │ 短款: 我方差支出 → 调查 → 联系渠道确认 → 补救/退款  │ │  │
│  │  │ 金额不符: 按渠道数据为准 → 标记差异 → 人工核实      │ │  │
│  │  │ 差异 > 阈值: 发出告警 → 冻结账户 → 人工介入         │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  对账优化:                                                     │
│  - 实时对账: 关键交易(大额)实时的对比                           │
│  - 分批对账: 按金额分批次，大金额优先对账                        │
│  - 自动冲正: 已明确的差错自动调整                               │
└────────────────────────────────────────────────────────────────┘
```

### 4. 支付渠道路由与降级

```
┌────────────────────────────────────────────────────────────────┐
│                    渠道路由策略                                 │
│                                                                │
│  路由因子:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. 费率: 渠道手续费率                                    │  │
│  │ 2. 成功率: 历史成功率 (最近1小时)                        │  │
│  │ 3. 延迟: 平均响应时间                                    │  │
│  │ 4. 限额: 单笔/日限额                                     │  │
│  │ 5. 渠道状态: 在线/降级/熔断                               │  │
│  │ 6. 业务规则: 信用卡/借记卡分开, 国际/国内分开            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  路由算法 (加权随机):                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  weight_i = 费率权重 × 成功率权重 × 速度权重              │  │
│  │                                                          │  │
│  │  示例:                                                    │  │
│  │  渠道A: 费率0.6%, 成功率99.9%, 延迟200ms → weight=0.95   │  │
│  │  渠道B: 费率0.5%, 成功率99.5%, 延迟300ms → weight=0.88   │  │
│  │  渠道C: 费率0.7%, 成功率99.9%, 延迟180ms → weight=0.91   │  │
│  │                                                          │  │
│  │  cumulative_weights = [0.95, 1.83, 2.74]                 │  │
│  │  random(0, 2.74) → 选择对应渠道                          │  │
│  │                                                          │  │
│  │  动态熔断:                                                │  │
│  │  渠道成功率 < 80% for 1min → weight = 0 (断路)           │  │
│  │  渠道超时率 > 30% for 1min → weight = 0.1 (降级)        │  │
│  │  恢复: 半开状态 5min → 探测请求 → 恢复全量                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  降级策略:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. 主渠道超时 → 自动重试1次 → 仍失败 → 切换备用渠道     │  │
│  │  2. 所有渠道不可用 → 支付订单状态 = pending_retry         │  │
│  │      → 后台任务定时重试 (exponential backoff)            │  │
│  │  3. 银行侧系统维护 → 预设维护时间 → 提前切换到备用渠道    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5. 风控体系 (Risk Management)

```
┌────────────────────────────────────────────────────────────────┐
│                        风控系统架构                             │
│                                                                │
│  实时风控决策:                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  支付请求 → 风控引擎 → pass/block/review                  │  │
│  │                                                          │  │
│  │  规则引擎 (轻量):                                         │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │ IF 单笔金额 > 10000 AND 用户信用分 < 60 → review   │  │  │
│  │  │ IF 同一卡 5分钟内 > 3笔交易 → block                │  │  │
│  │  │ IF 设备指纹在风控黑名单 → block                    │  │  │
│  │  │ IF IP地址在异常地区 → review                       │  │  │
│  │  │ IF 用户7天内首次异地交易 → 3DS验证                 │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ML模型 (准实时, 异步):                                   │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │ 特征:                                               │  │  │
│  │  │ - 用户交易频率/金额的近期变化                        │  │  │
│  │  │ - 设备/行为特征                                      │  │  │
│  │  │ - 交易时间模式                                       │  │  │
│  │  │ - 商家类型风险等级                                   │  │  │
│  │  │                                                     │  │  │
│  │  │ 模型: 异常检测 (Isolation Forest) + 分类 (XGBoost)  │  │  │
│  │  │ 输出: 风险分 0-100                                   │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  处理决策:                                                │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │ risk_score:                                          │  │  │
│  │  │   0-30   → pass (自动放行)                           │  │  │
│  │  │  30-60  → 3DS challenge (额外验证)                   │  │  │
│  │  │  60-90  → review (人工审核)                          │  │  │
│  │  │  90-100 → block (直接拒绝)                           │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  性能要求: 风控检查 < 50ms (否则影响支付体验)              │  │
│  │  高并发: 风控规则全量加载内存, 或使用 Redis 缓存特征       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 6. 结算系统 (Settlement)

```
┌──────────────────────────────────────────────────────────────┐
│                     结算系统                                  │
│                                                              │
│  结算流程 (T+1):                                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  每日子夜:                                              │  │
│  │                                                         │  │
│  │  1. 日切: 锁定前一日的交易数据                            │  │
│  │     UPDATE payment_settlement SET status='locked'       │  │
│  │     WHERE date = YESTERDAY                              │  │
│  │                                                         │  │
│  │  2. 汇总计算:                                            │  │
│  │     - 净交易额 = 成功支付总额 - 成功退款总额              │  │
│  │     - 手续费 = 净交易额 × 费率                           │  │
│  │     - 可结算金额 = 净交易额 - 手续费                     │  │
│  │                                                         │  │
│  │  3. 生成结算单:                                          │  │
│  │     INSERT INTO settlement_orders (merchant_id,         │  │
│  │       settlement_date, amount, fee, net_amount,         │  │
│  │       transaction_count, status)                        │  │
│  │                                                         │  │
│  │  4. 执行结算:                                            │  │
│  │     - 调用银行接口批量转账                                │  │
│  │     - 更新账户 pending_balance → available_balance       │  │
│  │     - 记录结算流水                                        │  │
│  │                                                         │  │
│  │  5. 通知商户: 推送结算单 + 结算明细                       │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  结算校验:                                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  每日校验总账平衡:                                        │  │
│  │                                                          │  │
│  │  Σ期初余额 + Σ收入 - Σ支出 - Σ结算 = Σ期末余额          │  │
│  │                                                          │  │
│  │  不平衡 → 触发告警 → 暂停结算 → 人工处理                  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### 数据分片策略

```
┌──────────────────────────────────────────────────────────────┐
│                    数据库分库分表                              │
│                                                              │
│  分片策略:                                                    │
│  - 按 payment_id / account_id hash 取模                      │
│  - MySQL Sharding: 使用 Vitess / ShardingSphere               │
│  - 分片数: 32 (可动态扩展)                                    │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  shard_key = hash(payment_id) % 32                     │  │
│  │                                                        │  │
│  │  痛点: 按 payment_id 分片后, 查询商户维度需要广播        │  │
│  │                                                        │  │
│  │  解决方案:                                               │  │
│  │  1. 商户维度查询 → ES/HBase 冗余索引                     │  │
│  │  2. 商户+时间维度实时查询 → Redis sorted set             │  │
│  │  3. 商户+日维度统计查询 → 汇总表 (payment_daily_stats)   │  │
│  │  4. CQRS: 写模型按 payment_id 分片, 读模型冗余到 ES     │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 跨数据中心容灾

```
┌──────────────────────────────────────────────────────────────┐
│                    多数据中心架构                              │
│                                                              │
│  ┌─────────────────┐              ┌─────────────────┐        │
│  │  DC-A (主)       │  异步复制    │  DC-B (备)       │        │
│  │  ───────────────│◄─────────────│  ───────────────│        │
│  │                  │              │                  │        │
│  │  MySQL Master    │  Binlog Sync │  MySQL Standby   │        │
│  │  Redis Master    │  AOF Sync    │  Redis Standby   │        │
│  │  App Server × N  │              │  App Server × N  │        │
│  └─────────────────┘              └─────────────────┘        │
│                                                              │
│  灾难切换:                                                    │
│  1. 监测: 心跳检测 DC-A 存活                                  │
│  2. 切换: DNS → CNAME → DC-B IP, TTL=60s                    │
│  3. 数据: DC-B MySQL 提升为 Master                            │
│  4. 防脑裂: 使用 ZooKeeper/Etcd 锁 + Fencing Token           │
│  5. 回切: DC-A 恢复 → 数据同步 → 切回                        │
│                                                              │
│  关键指标:                                                     │
│  - RPO (恢复点目标): < 1分钟 (Binlog异步复制延迟)             │
│  - RTO (恢复时间目标): < 5分钟 (DNS切换+MySQL提升)            │
└──────────────────────────────────────────────────────────────┘
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 一致性 | TCC + 本地事务 + Outbox | 资金强一致 + 异步通知最终一致 |
| 幂等性 | Idempotency Key + DB UNIQUE | 防重复扣款，并发安全 |
| 分库 | Vitess/ShardingSphere | MySQL 水平扩展 |
| 对账 | 每日批量对账 + 实时大额对账 | 保证资金准确性 |
| 风控 | 规则引擎 + ML模型双层 | 实时拦截 + 异步分析 |
| 渠道路由 | 加权随机 + 熔断降级 | 优化费率和成功率 |
| 通知 | Outbox Pattern + MQ 重试 | 保证通知送达 |
| 灾备 | 双活/主备 + 异地多活 | 99.999% 可用性 |
| 缓存 | Redis (幂等键/限额/风控特征) | 低延迟查询 |

核心设计要点:
1. **资金一致性高于一切**: CP 系统，使用 TCC/Saga + 最终对账
2. **幂等是防错的基石**: 多层幂等(ID、DB、渠道)，网络超时不可怕
3. **对账是最后防线**: 每日与渠道对账，发现不一致自动告警+补账
4. **渠道降级保证可用性**: 多渠道 + 动态路由 + 熔断
5. **风控多层防御**: 规则引擎(快速) + ML模型(精准) + 人工审核(兜底)
6. **Outbox模式解耦**: 支付完成和通知解耦, 保证最终一致
