# 03 · Order Exception Hub

> 全渠道订单异常与对账中心。不是普通 OMS，而是 FDE 在企业集成现场最常遇到的“订单卡住、库存不一致、渠道对不上”的运营闭环。  
> 技术栈：**Python/FastAPI 后端 + Next.js 运营台**。详细方案见 `../../06-FDE项目实战指南.docx` 第 5 章。

## 1. 业务背景

零售/餐饮品牌接入美团、饿了么、京东、小程序、门店 POS 等多渠道订单。真正的痛点不是“下单”，而是异常：渠道订单重复、支付成功但订单未创建、库存预占失败、门店未接单、配送超时、渠道金额与本地对不上。

## 2. 为什么这个项目有竞争力

- 避开“再写一个订单系统”的同质化，聚焦 **异常检测、补偿、对账、运营处置**。
- 这是企业集成 FDE 的高频现场：多系统、脏数据、弱接口、对不上账。
- 能讲清一致性、幂等、补偿、SLA、运营闭环，而不是只讲 Kafka。
- 与你的 LEGO 全渠道订单、Tesla 库存经历直接对应。

## 3. 用户与场景

| 用户 | 场景 | 痛点 |
|------|------|------|
| 运营 | 看异常队列、处理卡单 | 多渠道后台分散 |
| 客服 | 查订单为什么没发货 | 不知道卡在哪 |
| 财务 | 对账差异 | 渠道金额/状态不一致 |
| 门店 | 接单/拒单/缺货 | 重复单、漏单 |

## 4. 目标与非目标

### 目标

- 多渠道订单事件接入与统一模型
- 异常规则引擎：重复、超时、库存、支付、履约、金额
- 异常队列、SLA、分派、备注、补偿
- 自动补偿 + 人工处置
- 渠道对账和差异报告
- 全链路追踪和审计

### 非目标

- 不做完整 OMS
- 不做支付通道实现（模拟）
- 不做物流轨迹全链路
- 不替代财务系统

## 5. 技术栈

### 后端

- Python 3.12+ + FastAPI + Pydantic v2
- PostgreSQL + Redis
- Kafka（aiokafka）事件接入
- Celery/Arq（补偿、对账、SLA 扫描）
- SQLAlchemy 2 + Alembic
- pytest + ruff
- uv / Docker

### 前端

- Next.js 15+ App Router
- TypeScript + Tailwind CSS
- TanStack Query
- 表格/筛选/详情/时间线
- Auth.js
- Playwright

## 6. 架构

```text
渠道订单/支付/库存/履约事件
        │ API/Kafka
        ▼
Python 接入/统一模型 -> 异常规则 -> 异常队列/SLA
        │                         │
        ├── 自动补偿（重试/回滚/补单）
        ├── 人工处置（分派/备注/关闭）
        └── 对账（渠道账单 vs 本地）
        │
Next.js 运营台 <- FastAPI 查询/操作 API
```

## 7. 项目结构

```text
03-order-exception-hub/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/              # exceptions, orders, reconciliation, admin
│   │   ├── core/                # config, auth, audit, sla, logging
│   │   ├── domain/              # order, exception, compensation, reconciliation
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── rules/               # 异常规则引擎
│   │   ├── workers/             # Kafka, compensation, reconciliation, SLA
│   │   └── integrations/        # 渠道/支付/库存/履约
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/exceptions/page.tsx
│   ├── app/exceptions/[id]/page.tsx
│   ├── app/orders/page.tsx
│   ├── app/reconciliation/page.tsx
│   ├── components/
│   ├── lib/api.ts
│   └── package.json
├── infra/
│   ├── docker-compose.yml
│   └── .env.example
└── docs/
    ├── 01-discovery.docx
    ├── 02-architecture.docx
    └── 03-acceptance.docx
```

## 8. 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/events/order` | 渠道订单事件 |
| GET | `/api/v1/exceptions` | 异常队列（筛选/SLA） |
| POST | `/api/v1/exceptions/{id}/assign` | 分派 |
| POST | `/api/v1/exceptions/{id}/resolve` | 处置/补偿 |
| GET | `/api/v1/reconciliation` | 对账差异 |
| POST | `/api/v1/reconciliation/run` | 触发对账 |
| GET | `/healthz` | 健康检查 |

## 9. 数据模型

| 表 | 关键字段 |
|----|----------|
| orders | id, channel, channel_order_no, status, amount, store_id |
| order_events | id, order_id, type, payload, event_time |
| exceptions | id, order_id, type, severity, status, sla_due_at, assignee |
| exception_actions | exception_id, action, note, operator, created_at |
| compensations | id, exception_id, type, status, retry_count |
| reconciliation_runs | id, channel, biz_date, status, diff_count |
| reconciliation_diffs | run_id, order_id, type, local_value, channel_value |
| audit_log | user_id, action, resource, result |

## 10. 实现步骤

### 阶段 1：异常场景建模（3–5 天）

1. 列 8 类异常：重复、超时、库存、支付、履约、金额、状态、门店。
2. 定义严重级别、SLA、处置动作。
3. 准备样例事件。
4. 定义成功指标（异常发现时间、解决时长、自动解决率）。

### 阶段 2：事件接入与规则（5–7 天）

1. Kafka/HTTP 接入订单/支付/库存事件。
2. 统一订单模型和幂等。
3. 规则引擎：匹配、聚合、窗口、去重。
4. 生成异常记录。

### 阶段 3：运营台（4–5 天）

1. 异常队列：筛选、排序、SLA。
2. 详情：订单、事件时间线、建议动作。
3. 分派/备注/关闭。
4. 权限和审计。

### 阶段 4：补偿与对账（4–5 天）

1. 自动重试/补单/回滚。
2. 补偿幂等和失败升级。
3. 渠道账单导入和差异计算。
4. 差异报告和人工处理。

### 阶段 5：部署与演练（3–5 天）

1. Docker Compose。
2. 监控/告警。
3. 重复/乱序/超时演练。
4. Demo/复盘。

## 11. 里程碑（5 周）

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | 异常场景 + 样例 | 规则清单、SLA、评估集 |
| 2 | 事件接入 + 规则 | 异常队列 |
| 3 | 运营台 + 处置 | 端到端 Demo |
| 4 | 补偿 + 对账 | 自动/人工闭环 |
| 5 | 部署/演练/复盘 | 项目包 |

## 12. 验收标准

- [ ] 8 类异常能识别
- [ ] 异常队列按 SLA/严重级别排序
- [ ] 处置动作有审计
- [ ] 补偿幂等、失败可升级
- [ ] 对账能发现差异
- [ ] 重复/乱序事件不重复处理
- [ ] 运营台可筛选/详情/时间线

## 13. 面试讲法

“企业集成项目真正难的不是下单，而是异常和对账。这个项目让我把 LEGO 全渠道订单和 Tesla 库存经验，升级成可运营的异常闭环。”
