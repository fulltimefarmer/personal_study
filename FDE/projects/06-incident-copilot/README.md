# 06 · Incident Copilot

> AI SRE / 事故 Copilot。把日志、指标、链路、变更和 Runbook 串起来，帮助值班人员定位和止损。  
> 技术栈：**Python/FastAPI 后端 + Next.js 前端**。详细方案见 `../../06-FDE项目实战指南.docx` 第 8 章。

## 1. 业务背景

客户上线后，值班人员面对大量告警、日志、指标、链路和变更记录，定位慢、交接乱、复盘难。需要一个 Copilot：汇总上下文、给出假设、调用只读工具验证、生成时间线和复盘草稿。

## 2. 为什么这个项目有竞争力

- 不是“又一个 RAG 问答”，而是 **Agent + 工具调用 + 可观测性 + 安全边界**，更贴近 AI FDE 的前沿。
- 能讲清“只读工具、权限、幻觉、确认、审计、MTTR”这些客户真正关心的点。
- 与你的高并发、线上排障、7x24 经历强相关。
- 适合 AI 平台、云厂商、SRE/可观测性、企业 AI FDE。

## 3. 用户与场景

| 用户 | 场景 | 痛点 |
|------|------|------|
| 值班工程师 | 告警定位 | 工具多、上下文散 |
| SRE | 复盘 | 时间线靠回忆 |
| 研发 | 看变更/日志 | 不知道哪次发布 |
| 管理者 | MTTR/复盘 | 缺少结构化记录 |

## 4. 目标与非目标

### 目标

- 接入日志/指标/链路/变更/Runbook
- 告警上下文聚合
- 只读工具调用（查日志、查指标、查 Trace、查变更）
- 假设生成 + 证据引用
- 事故时间线/复盘草稿
- 权限/审计/Guardrails
- 评估定位准确率、MTTR、工具成功率

### 非目标

- 不自动执行高风险修复
- 不替代监控平台
- 不承诺自动根因
- 不做通用聊天

## 5. 技术栈

### 后端

- Python 3.12+ + FastAPI + Pydantic v2
- PostgreSQL + pgvector（Runbook/历史事故）
- Redis（会话/缓存/限流）
- Celery/Arq（告警聚合、评估）
- httpx（Prometheus/Loki/Tempo/Git API）
- 只读工具封装 + 审计
- pytest + ruff
- uv / Docker

### 前端

- Next.js 15+ App Router
- TypeScript + Tailwind CSS
- TanStack Query
- 事故时间线/证据卡片/工具调用面板
- Auth.js
- Playwright

## 6. 架构

```text
告警/日志/指标/链路/变更/Runbook
        │ API/Webhook
        ▼
Python 聚合/索引 -> 事故会话
        │
Next.js 事故台 -> FastAPI -> LLM 规划 -> 只读工具调用
        │                         │
        │                         ├── Prometheus/Loki/Tempo/Git
        │                         └── 证据/引用/审计
        ▼
时间线/假设/复盘草稿
```

## 7. 项目结构

```text
06-incident-copilot/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/              # incidents, alerts, tools, postmortem
│   │   ├── core/                # config, auth, audit, guardrails
│   │   ├── domain/              # incident, evidence, hypothesis
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── integrations/        # Prometheus/Loki/Tempo/Git
│   │   ├── tools/               # 只读工具 + 权限
│   │   ├── agent/               # 规划/工具选择/证据
│   │   └── evaluation/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/incidents/page.tsx
│   ├── app/incidents/[id]/page.tsx
│   ├── app/postmortem/page.tsx
│   ├── components/Timeline.tsx
│   ├── components/EvidenceCard.tsx
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
| POST | `/api/v1/incidents` | 创建事故 |
| POST | `/api/v1/incidents/{id}/ask` | 提问/分析 |
| GET | `/api/v1/incidents/{id}/timeline` | 时间线 |
| POST | `/api/v1/tools/{tool}` | 只读工具调用 |
| POST | `/api/v1/incidents/{id}/postmortem` | 复盘草稿 |
| GET | `/healthz` | 健康检查 |

## 9. 数据模型

| 表 | 关键字段 |
|----|----------|
| incident | id, title, severity, status, started_at, resolved_at |
| alert | id, source, severity, payload, incident_id |
| evidence | incident_id, type, source, content, link |
| hypothesis | incident_id, text, confidence, status |
| tool_call | incident_id, tool, params, result, status |
| timeline_event | incident_id, time, type, description |
| postmortem | incident_id, draft, review_status |
| audit_log | user_id, action, resource, result |

## 10. 实现步骤

### 阶段 1：事故场景（3–5 天）

1. 选 3 类事故：超时、错误率飙升、依赖故障。
2. 准备日志/指标/Trace/变更样例。
3. 定义工具和只读权限。
4. 定义评估（定位准确、MTTR、工具成功率）。

### 阶段 2：上下文聚合（5–7 天）

1. 告警/日志/指标/Trace/变更接入。
2. 事故会话和时间线。
3. Runbook/历史事故检索。
4. 证据卡片。

### 阶段 3：Agent/工具（5–7 天）

1. 只读工具：查日志、指标、Trace、变更。
2. LLM 规划/工具选择/证据引用。
3. 超时/重试/终止/人工确认。
4. 审计和 Guardrails。

### 阶段 4：前端（4–5 天）

1. 事故列表/详情。
2. 时间线/证据/假设。
3. 工具调用面板。
4. 复盘草稿。

### 阶段 5：评估与部署（3–5 天）

1. 3 类事故评估集。
2. 定位准确率/MTTR/工具成功率。
3. Docker Compose。
4. Demo/复盘。

## 11. 里程碑（5 周）

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | 事故场景/样例/工具 | 问题陈述、评估集 |
| 2 | 上下文聚合 | 事故时间线 |
| 3 | Agent + 只读工具 | 分析 Demo |
| 4 | 前端/Guardrails | 端到端 |
| 5 | 评估/部署/复盘 | 项目包 |

## 12. 验收标准

- [ ] 3 类事故可复现
- [ ] 工具只读、权限/审计
- [ ] 证据引用可追溯
- [ ] 有假设和置信度
- [ ] 不执行高风险操作
- [ ] 时间线/复盘草稿可用
- [ ] 有评估报告

## 13. 面试讲法

“Incident Copilot 的价值不是让 AI 自动修故障，而是让值班人员更快拿到上下文、证据和下一步建议。FDE 要设计只读边界、工具权限、审计和人工确认，避免 AI 把故障放大。”
