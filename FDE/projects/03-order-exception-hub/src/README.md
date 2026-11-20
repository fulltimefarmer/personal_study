# Order Exception Hub · src

## 后端（Python / FastAPI）

```text
backend/app/
├── main.py
├── api/v1/              # events, exceptions, orders, reconciliation
├── core/                # config, auth, audit, sla, logging
├── domain/              # order, exception, compensation, reconciliation
├── models/
├── schemas/
├── repositories/
├── rules/               # 异常规则引擎
├── workers/             # Kafka, compensation, reconciliation, SLA
└── integrations/        # 渠道/支付/库存/履约
```

## 前端（Next.js）

```text
frontend/
├── app/exceptions/page.tsx
├── app/exceptions/[id]/page.tsx
├── app/orders/page.tsx
├── app/reconciliation/page.tsx
├── components/
├── lib/api.ts
└── tests/
```

## 最小实现顺序

1. 定义 8 类异常和 SLA。
2. 模拟渠道/支付/库存事件。
3. 规则引擎生成异常。
4. 异常队列 + 详情 + 处置。
5. 自动补偿 + 审计。
6. 对账差异。
7. Docker Compose + 监控。
