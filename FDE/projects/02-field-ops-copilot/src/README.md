# Field Ops Copilot · src

## 后端（Python / FastAPI）

```text
backend/app/
├── main.py
├── api/v1/              # ask, workorders, alerts, sync
├── core/                # config, auth, audit, offline token
├── domain/              # workorder, asset, alert, citation
├── models/
├── schemas/
├── repositories/
├── integrations/        # IoT, workorder, object storage
├── workers/             # sync, index, alert
└── evaluation/
```

## 前端（Next.js PWA）

```text
frontend/
├── app/(field)/page.tsx
├── app/manuals/page.tsx
├── app/workorders/page.tsx
├── app/alerts/page.tsx
├── components/OfflineBanner.tsx
├── lib/offline.ts       # IndexedDB/同步/冲突
├── lib/api.ts
├── public/manifest.json
└── tests/
```

## 最小实现顺序

1. FastAPI + Postgres + pgvector + 手册样例。
2. 检索 + 引用 + 工单 API。
3. Next.js PWA + Service Worker + IndexedDB。
4. 离线工单创建/更新/同步/冲突。
5. IoT 告警 -> 派单。
6. 权限/审计/Docker Compose。
