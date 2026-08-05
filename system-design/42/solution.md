# 42. 设计数字钱包 (Design Digital Wallet like Alipay/WeChat Pay Wallet)

## 题目

设计一个数字钱包系统，类似支付宝/微信支付的钱包功能。支持充值、消费、转账、提现、账单查询等核心功能。要求系统高度可靠，保证资金安全，做到账务绝对准确。

## 需求澄清

### 功能性需求

1. **账户管理 (Account Management)**: 创建钱包账户、实名认证、绑定银行卡
2. **充值 (Top-up/Deposit)**: 通过银行卡/第三方支付向钱包充值
3. **消费 (Payment)**: 使用钱包余额支付（扫码支付、在线支付）
4. **转账 (Transfer)**: 钱包之间相互转账
5. **提现 (Withdraw)**: 将钱包余额提现到银行卡
6. **账单查询 (Transaction History)**: 查询交易记录、月账单
7. **退款 (Refund)**: 对已完成的交易发起退款
8. **冻结/解冻 (Freeze/Unfreeze)**: 争议交易时冻结资金
9. **余额查询 (Balance Inquiry)**: 实时查询可用余额和冻结余额

### 非功能性需求

1. **强一致性 (Strong Consistency)**: 资金绝对不能出现负数、重复扣款、丢失
2. **高可用 (High Availability)**: 99.999%（5个9），支付链路不可中断
3. **高并发 (High Throughput)**: 双十一峰值 500K+ TPS
4. **幂等性 (Idempotency)**: 所有写操作严格幂等，防止重复扣款
5. **审计追踪 (Auditability)**: 所有资金变动可追溯，满足金融监管要求
6. **安全性 (Security)**: 交易加密、风控、反洗钱(AML)
7. **低延迟 (Low Latency)**: 支付确认 P99 < 200ms

### 容量估算

```
假设 5 亿注册用户，日活 1 亿

日常 TPS:
  平均每用户每天 3 笔交易
  日均交易量 = 1亿 * 3 = 3亿笔/天
  平均 TPS = 3亿 / 86400 ≈ 3,500 TPS
  峰值 TPS (10x) ≈ 35,000 TPS
  双十一峰值 ≈ 200,000 - 500,000 TPS

账户表存储:
  5亿用户 * 1KB/用户 ≈ 500GB

交易流水存储:
  日均 3亿笔 * 500B/笔 ≈ 150GB/天
  保留 3 年 ≈ 150GB * 365 * 3 ≈ 164TB
  加上备份和索引 ≈ 500TB

余额缓存:
  1亿日活 * 200B ≈ 20GB (Redis Cluster)
```

## API设计

### 核心 API

```protobuf
service WalletService {
  // 账户管理
  rpc CreateWallet(CreateWalletRequest) returns (CreateWalletResponse);
  rpc GetWalletInfo(GetWalletInfoRequest) returns (GetWalletInfoResponse);
  rpc GetBalance(GetBalanceRequest) returns (GetBalanceResponse);
  rpc KYCVerify(KYCVerifyRequest) returns (KYCVerifyResponse);

  // 交易操作
  rpc Deposit(DepositRequest) returns (TransactionResponse);
  rpc Withdraw(WithdrawRequest) returns (TransactionResponse);
  rpc Transfer(TransferRequest) returns (TransactionResponse);
  rpc Pay(PayRequest) returns (TransactionResponse);
  rpc Refund(RefundRequest) returns (TransactionResponse);

  // 冻结管理
  rpc FreezeAmount(FreezeRequest) returns (FreezeResponse);
  rpc UnfreezeAmount(UnfreezeRequest) returns (UnfreezeResponse);

  // 账单查询
  rpc QueryTransactions(QueryTransactionsRequest) returns (QueryTransactionsResponse);
}

message TransferRequest {
  string request_id = 1;       // 幂等键
  string from_wallet_id = 2;
  string to_wallet_id = 3;
  int64 amount = 4;            // 单位：分（避免浮点精度问题）
  string currency = 5;         // 默认 CNY
  string remark = 6;
  string payment_password = 7; // 支付密码/生物识别
}

message TransactionResponse {
  string transaction_id = 1;
  string request_id = 2;
  TransactionStatus status = 3; // PENDING / SUCCESS / FAILED / PROCESSING
  int64 amount = 4;
  int64 balance_after = 5;      // 交易后余额
  int64 created_at = 6;
}
```

### 幂等性设计

```python
class IdempotencyManager:
    """
    幂等性保证层
    在业务逻辑执行前，先检查 request_id 是否已处理
    """

    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session

    def process_with_idempotency(self, request_id: str, operation_func, *args):
        # Step 1: Redis 快速幂等检查
        idem_key = f"idempotency:{request_id}"
        result = self.redis.get(idem_key)

        if result:
            return json.loads(result)  # 返回之前缓存的结果

        # Step 2: 使用 Redis SETNX 实现分布式锁
        lock_key = f"idempotency_lock:{request_id}"
        acquired = self.redis.set(lock_key, "1", nx=True, ex=60)

        if not acquired:
            raise DuplicateRequestError("Request is being processed")

        try:
            # Step 3: 数据库二次确认
            existing = self.db.query(Transaction).filter_by(
                request_id=request_id
            ).first()

            if existing:
                return self._cache_and_return(idem_key, existing)

            # Step 4: 执行实际业务逻辑
            result = operation_func(*args)

            # Step 5: 缓存结果
            self.redis.setex(idem_key, 86400, json.dumps(result))
            return result

        finally:
            self.redis.delete(lock_key)
```

## 数据模型

### 核心表结构（MySQL/分库分表）

```sql
-- 钱包账户表 (wallet_accounts)
-- 按 wallet_id 哈希分库分表
CREATE TABLE wallet_accounts (
    wallet_id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    balance BIGINT NOT NULL DEFAULT 0 COMMENT '可用余额(分)',
    frozen_balance BIGINT NOT NULL DEFAULT 0 COMMENT '冻结余额(分)',
    total_deposit BIGINT NOT NULL DEFAULT 0 COMMENT '累计充值',
    total_withdraw BIGINT NOT NULL DEFAULT 0 COMMENT '累计提现',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1:正常 2:冻结 3:注销',
    version INT NOT NULL DEFAULT 0 COMMENT '乐观锁版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;

-- 交易流水表 (transactions)
-- 按交易日期范围分区 + 按 wallet_id 分库
CREATE TABLE transactions (
    transaction_id VARCHAR(32) PRIMARY KEY,
    request_id VARCHAR(64) NOT NULL UNIQUE COMMENT '幂等键',
    from_wallet_id VARCHAR(32) NOT NULL,
    to_wallet_id VARCHAR(32) NOT NULL,
    transaction_type ENUM('DEPOSIT','WITHDRAW','TRANSFER','PAYMENT','REFUND','FEE') NOT NULL,
    amount BIGINT NOT NULL COMMENT '金额(分)',
    currency VARCHAR(3) DEFAULT 'CNY',
    status ENUM('PENDING','PROCESSING','SUCCESS','FAILED','CANCELLED') NOT NULL,
    fee_amount BIGINT DEFAULT 0 COMMENT '手续费',
    balance_before BIGINT COMMENT '交易前余额',
    balance_after BIGINT COMMENT '交易后余额',
    remark VARCHAR(255),
    channel VARCHAR(32) COMMENT '渠道: BANK/ALIPAY/WECHAT/WALLET',
    channel_transaction_id VARCHAR(128) COMMENT '外部渠道交易ID',
    risk_level VARCHAR(8) COMMENT '风控等级: LOW/MEDIUM/HIGH',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_from_wallet (from_wallet_id, created_at),
    INDEX idx_to_wallet (to_wallet_id, created_at),
    INDEX idx_request_id (request_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB
PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01'))
    -- ... 按月分区
);

-- 对账表 (reconciliation)
CREATE TABLE reconciliation (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(32) NOT NULL,
    wallet_id VARCHAR(32) NOT NULL,
    expected_balance BIGINT NOT NULL,
    actual_balance BIGINT NOT NULL,
    diff BIGINT NOT NULL,
    reconciliation_date DATE NOT NULL,
    status ENUM('MATCHED','MISMATCHED','FIXED') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_wallet_date (wallet_id, reconciliation_date)
) ENGINE=InnoDB;

-- 订单表（关联支付）
CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    wallet_id VARCHAR(32) NOT NULL,
    merchant_id VARCHAR(32) NOT NULL,
    amount BIGINT NOT NULL,
    status ENUM('CREATED','PAID','REFUNDING','REFUNDED','CLOSED') NOT NULL,
    transaction_id VARCHAR(32) COMMENT '关联交易ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_wallet_id (wallet_id),
    INDEX idx_merchant_id (merchant_id)
) ENGINE=InnoDB;
```

### 余额设计：为什么用分而不是元

| 方案 | 问题 |
|------|------|
| DECIMAL(10,2) | 除法舍入、跨语言精度不一致 |
| FLOAT/DOUBLE | 浮点精度丢失（0.1 + 0.2 ≠ 0.3） |
| **BIGINT (分)** | 整数运算，无精度问题 ⭐ |

## 高层次架构

```
                          ┌─────────────────────────┐
                          │      API Gateway        │
                          │   (限流/鉴权/风控前置)     │
                          └───────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
              ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼──────┐
              │  Payment  │    │  Account  │    │    Risk     │
              │  Gateway  │    │  Service  │    │  Control    │
              │  (支付网关) │    │  (账户服务) │    │  (风控服务)  │
              └─────┬─────┘    └─────┬─────┘    └──────┬──────┘
                    │                │                  │
                    │         ┌──────▼──────┐           │
                    │         │  Wallet     │           │
                    │         │  Service    │           │
                    │         │  (核心钱包)   │◄──────────┘
                    │         └──────┬──────┘
                    │                │
         ┌──────────┼──────────┬─────┼──────┬──────────┐
         │          │          │     │      │          │
   ┌─────▼─────┐ ┌──▼───┐ ┌───▼──┐ ┌▼──────▼─┐ ┌─────▼─────┐
   │  外部渠道  │ │Redis │ │MySQL │ │  MQ     │ │   ES      │
   │ (银行/网联)│ │Cluster│ │Shard │ │(Kafka) │ │ (账单搜索) │
   └───────────┘ └──────┘ └──────┘ └─────────┘ └───────────┘
```

### 核心交易流程 — 转账

```
用户A转账100元给用户B:

┌──────────────────────────────────────────────────────────────┐
│ Step 1: 风控检查                                              │
│   - 金额是否超限？频率是否异常？                                 │
│   - 设备/位置是否可信？                                        │
├──────────────────────────────────────────────────────────────┤
│ Step 2: 参数校验 + 幂等检查                                    │
│   - request_id 是否已处理？                                    │
│   - A账户是否存在且正常？                                      │
│   - B账户是否存在且正常？                                      │
├──────────────────────────────────────────────────────────────┤
│ Step 3: 扣款 (A钱包)                                          │
│   UPDATE wallet_accounts                                      │
│   SET balance = balance - 100, version = version + 1          │
│   WHERE wallet_id = 'A' AND balance >= 100                    │
│     AND version = expected_version                            │
│   (乐观锁 + 余额充足检查在一个 SQL 中原子完成)                  │
├──────────────────────────────────────────────────────────────┤
│ Step 4: 入账 (B钱包)                                           │
│   UPDATE wallet_accounts                                      │
│   SET balance = balance + 100, version = version + 1          │
│   WHERE wallet_id = 'B' AND version = expected_version        │
├──────────────────────────────────────────────────────────────┤
│ Step 5: 记录流水                                               │
│   INSERT INTO transactions (...)                              │
│   VALUES (transaction_id, request_id, 'A', 'B', ...)          │
├──────────────────────────────────────────────────────────────┤
│ Step 6: 通知 + 缓存更新                                        │
│   - Kafka 发送交易成功事件                                     │
│   - Redis 更新余额缓存                                        │
│   - 推送通知给用户A和B                                         │
└──────────────────────────────────────────────────────────────┘
```

## 核心深入

### 余额一致性保证

#### 方案A: 悲观锁 (SELECT FOR UPDATE)

```sql
START TRANSACTION;
SELECT balance FROM wallet_accounts WHERE wallet_id = 'A' FOR UPDATE;
-- 检查余额
UPDATE wallet_accounts SET balance = balance - 100 WHERE wallet_id = 'A';
COMMIT;
```

**优点**: 强一致，不会超扣
**缺点**: 锁粒度大，高并发下性能差，容易死锁

#### 方案B: 乐观锁 (CAS - Compare And Swap) ⭐ 推荐

```sql
-- 扣款: 一个 SQL 原子完成余额检查 + 扣款
UPDATE wallet_accounts
SET balance = balance - ?, version = version + 1
WHERE wallet_id = ? AND balance >= ? AND version = ?;

-- 判断 affected_rows:
-- = 1: 成功
-- = 0: 余额不足 或 版本冲突 -> 重试
```

#### 方案C: Redis + Lua 原子操作

适合极高并发但允许异步同步到 MySQL 的场景（需权衡一致性）：

```lua
-- Lua 脚本在 Redis 服务端原子执行
-- 扣款脚本
local wallet_key = KEYS[1]              -- "wallet:A"
local amount = tonumber(ARGV[1])        -- 100
local balance = tonumber(redis.call('GET', wallet_key) or "0")

if balance >= amount then
    redis.call('DECRBY', wallet_key, amount)
    return 1  -- 成功
else
    return 0  -- 余额不足
end
```

**⚠️ 注意**: Redis 方案需要配合持久化策略（AOF + 定期同步 MySQL），否则宕机丢数据。

### TCC 分布式事务（转账场景）

对于跨钱包、跨系统的转账，使用 TCC (Try-Confirm-Cancel) 模式：

```
Try 阶段 (预留资源):
  系统A: 冻结用户A的100元
  系统B: 预增加用户B的100元(不可用状态)

Confirm 阶段 (确认):
  系统A: 扣减冻结的100元
  系统B: 确认增加的100元可用

Cancel 阶段 (回滚):
  系统A: 解冻100元
  系统B: 撤销预增加

─────────────────────────────────────
如果 Try 任一失败 -> 全部 Cancel
如果 Try 全部成功 -> 全部 Confirm
如果 Confirm 部分失败 -> 重试 + 人工介入
─────────────────────────────────────
```

```python
class TCCTransfer:
    """TCC 转账协调器"""

    def transfer(self, from_wallet, to_wallet, amount):
        transaction_id = generate_transaction_id()

        # Try Phase
        try:
            freeze_result = self.try_freeze(from_wallet, amount, transaction_id)
            if not freeze_result.success:
                return TransferResult.failed("冻结失败")

            pre_add_result = self.try_pre_add(to_wallet, amount, transaction_id)
            if not pre_add_result.success:
                # 回滚冻结
                self.cancel_freeze(from_wallet, amount, transaction_id)
                return TransferResult.failed("预增失败")
        except Exception:
            # 任一 Try 失败，Cancel 已执行的 Try
            self.cancel_freeze(from_wallet, amount, transaction_id)
            self.cancel_pre_add(to_wallet, amount, transaction_id)
            raise

        # Confirm Phase
        try:
            self.confirm_deduct(from_wallet, amount, transaction_id)
            self.confirm_add(to_wallet, amount, transaction_id)
        except Exception:
            # Confirm 失败，记录到异常表，触发人工处理/自动重试
            self.record_exception(transaction_id, from_wallet, to_wallet, amount)
            raise

        return TransferResult.success(transaction_id)
```

### 对账系统 (Reconciliation)

```
                    ┌──────────────────────┐
                    │   T+1 批量对账任务      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │ 内部流水   │   │ 渠道流水   │   │ 清算文件   │
        │ (DB)      │   │ (银行接口) │   │ (对账单)   │
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │               │                │
              └───────────────┼────────────────┘
                              │
                     ┌────────▼────────┐
                     │  对账引擎         │
                     │  - 逐笔匹配       │
                     │  - 金额核对       │
                     │  - 状态核对       │
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │  差异处理         │
                     │  - 长款(我方多)   │
                     │  - 短款(我方少)   │
                     │  - 金额不一致     │
                     │  - 状态不一致     │
                     └─────────────────┘
```

**对账关键规则**:
- 以三方（我方、渠道、清算）为准，多边对账
- 差异分类：挂账（等渠道结果）、调账（自动/人工）
- T+1 日完成对账，异常挂起不超过 T+3

### 分库分表策略

```
分片键选择: wallet_id

水平拆分规则:
  DB 数量: 16 个库 (wallet_db_00 ~ wallet_db_15)
  每个库 1 个表或更多

  shard_key = hash(wallet_id) % 16

跨分片转账问题:
  系统内钱包转账: 拆分为两个独立的单分片操作
  A(wallet_db_03) -> B(wallet_db_11):
    - 先扣 A(在 db_03)
    - 再增 B(在 db_11)
    - 使用 TCC 或 MQ 事务消息保证最终一致性
```

### 账户表冷热分离

```
热数据 (近 90 天交易):
  - 存储在 MySQL SSD 主库
  - Redis 缓存余额

温数据 (90天 - 1年):
  - 存储在 MySQL HDD 从库
  - 按需查询

冷数据 (1年以上):
  - 归档到 Hive/HBase/对象存储
  - 用于审计和历史账单
  - 提供异步查询接口
```

### 风控策略

```python
class RiskControlEngine:
    """实时风控引擎"""

    def evaluate_transaction(self, transaction):
        risk_score = 0

        # 规则引擎
        rules = [
            AmountLimitRule(50000),        # 单笔 5 万限额
            DailyLimitRule(200000),        # 日累计 20 万限额
            FrequencyRule(max_per_sec=5),  # 每秒最多 5 笔
            GeographyRule(),               # 异地登录检测
            DeviceFingerprintRule(),        # 设备指纹
            BlacklistRule(),                # 黑名单
            BehaviorAnomalyRule(),          # 行为异常(ML模型)
        ]

        for rule in rules:
            score = rule.evaluate(transaction)
            risk_score += score

        if risk_score >= 80:
            return RiskAction.BLOCK      # 阻断交易
        elif risk_score >= 50:
            return RiskAction.CHALLENGE  # 需要二次验证(短信/人脸)
        elif risk_score >= 30:
            return RiskAction.REVIEW     # 标记人工审核
        else:
            return RiskAction.PASS       # 放行
```

### 监控告警

| 监控项 | 阈值 | 级别 |
|--------|------|------|
| 交易成功率 | < 99.9% | P0 |
| 扣款成功/入账不一致 | any | P0 |
| 对账不平金额 | > 0 元 | P0 |
| 余额为负 | any | P0 |
| 交易延迟 P99 | > 500ms | P1 |
| 数据库主从延迟 | > 5s | P1 |
| 风控拦截率突变 | > 2x baseline | P1 |
| Redis 内存使用 | > 80% | P2 |

## 扩展性与高可用

### 多活架构

```
            ┌──────────────────────┐
            │   全局路由层 (GSLB)   │
            │   用户 -> 就近机房    │
            └──────────┬───────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼───┐          ┌───▼───┐         ┌───▼───┐
│机房A   │  双向同步 │机房B   │ 双向同步 │机房C   │
│(华东)  │◄────────►│(华南)  │◄────────►│(华北)  │
│       │          │       │          │       │
│用户分片│          │用户分片│          │用户分片│
│A-M    │          │N-Z    │          │A-M    │
│(Master)│         │(Master)│         │(Slave) │
└───────┘          └───────┘          └───────┘

用户根据 user_id 哈希到不同机房
每个用户只有一个主写机房
其他机房为只读备份
```

**资金账户多活的核心难点**: 
- 不允许双写，同一用户同一时刻只能在一个机房写入
- 通过用户分片 + 机房故障时的分片漂移实现

### 降级策略

```
Level 0 (正常):
  全部功能可用

Level 1 (轻微降级):
  - 关闭账单查询的非核心功能
  - 延长对账周期

Level 2 (中度降级):
  - 关闭非必要的实时风控检查
  - 降低 Redis 查询，直接用 DB

Level 3 (严重降级):
  - 仅保留核心支付、转账
  - 关闭提现、充值
  - 所有非核心服务熔断

Level 4 (极限降级):
  - 关闭所有写操作
  - 仅返回"服务繁忙，请稍后重试"
```

## 总结

数字钱包系统设计的核心要点：

1. **资金安全第一**: 余额字段用 BIGINT（分），绝不使用浮点数；扣款必须在 SQL 中原子检查余额
2. **乐观锁优于悲观锁**: 对于钱包这种低冲突场景，CAS 乐观锁性能远好于 SELECT FOR UPDATE
3. **幂等性层层设防**: request_id + Redis 缓存 + DB 唯一约束，三道防线
4. **TCC 分布式事务**: 跨系统转账的银弹，Try-Confirm-Cancel 模式保证最终一致性
5. **对账是最后底线**: 自动化 T+1 对账，发现任何资金不平立即告警
6. **分库分表**: 按 wallet_id 哈希分库，避免跨分片事务
7. **冷热分离**: 交易流水按月分区，热数据 SSD 冷数据归档
8. **风控前置**: 交易进入系统前先过风控，高风险交易直接阻断
9. **多活但要避免双写**: 每个用户只有一个主写机房

面试中面试官可能追问：分布式事务失败后如何恢复？对账系统的具体匹配算法？以及如何处理银行的异步回调。
