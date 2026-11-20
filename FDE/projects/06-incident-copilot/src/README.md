# Incident Copilot · src

## 后端（Python / FastAPI）

```text
backend/app/
├── main.py
├── api/v1/              # incidents, alerts, tools, postmortem
├── core/                # config, auth, audit, guardrails
├── domain/              # incident, evidence, hypothesis
├── models/
├── schemas/
├── integrations/        # Prometheus/Loki/Tempo/Git
├── tools/               # 只读工具 + 权限
├── agent/               # 规划/工具选择/证据
└── evaluation/
```

## 前端（Next.js）

```text
frontend/
├── app/incidents/page.tsx
├── app/incidents/[id]/page.tsx
├── app/postmortem/page.tsx
├── components/Timeline.tsx
├── components/EvidenceCard.tsx
├── components/ToolCallPanel.tsx
├── lib/api.ts
└── tests/
```

## 最小实现顺序

1. 事故/告警/证据模型。
2. 接日志/指标/Trace/变更（可先 Mock）。
3. 只读工具 + 权限 + 审计。
4. Agent 规划/证据引用。
5. Next.js 事故台/时间线/复盘。
6. 3 类事故评估集。
7. Docker Compose + Guardrails。
