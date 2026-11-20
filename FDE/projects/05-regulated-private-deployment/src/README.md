# Regulated Private Deployment · src

## 控制面（Python / FastAPI）

```text
backend/app/
├── main.py
├── api/v1/              # environments, deployments, upgrades, audit, health
├── core/                # config, auth, license, audit
├── domain/              # release, environment, upgrade
├── services/            # helm/k8s/backup adapters
├── models/
└── schemas/
```

## 前端（Next.js）

```text
frontend/
├── app/(ops)/page.tsx
├── app/deployments/page.tsx
├── app/audit/page.tsx
├── app/health/page.tsx
├── components/
├── lib/api.ts
└── tests/
```

## 交付（离线 / Helm / K8s）

```text
deploy/
├── offline-bundle/      # 镜像、chart、依赖
├── helm/
├── k8s/
└── scripts/             # install/upgrade/rollback/backup
```

## 最小实现顺序

1. 客户环境尽调表。
2. 离线镜像/Chart/依赖打包。
3. FastAPI 环境/版本/部署 API。
4. Next.js 运维台/审计/健康。
5. OIDC/角色映射。
6. 升级/回滚/备份演练。
7. 监控/交接文档。
