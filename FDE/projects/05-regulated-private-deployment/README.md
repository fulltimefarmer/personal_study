# 05 · Regulated Private Deployment

> 面向金融/医疗/政务客户的私有化交付。重点不是“上 K8s”，而是离线部署、SSO、审计、升级、回滚、合规和客户运维交接。  
> 技术栈：**Python/FastAPI 控制面 + Next.js 运维台**。详细方案见 `../../06-FDE项目实战指南.docx` 第 7 章。

## 1. 业务背景

银行/医疗/政务客户不允许公有云，要求数据不出域、离线安装、统一登录、审计、可升级、可回滚。FDE 需要把一套 AI/数据应用交付到客户机房，并让客户 IT 能长期运维。

## 2. 为什么这个项目有竞争力

- 这是 FDE 与普通研发差距最大的场景：客户环境、网络、安全、合规、升级、现场排障。
- 覆盖私有化/离线/信创/等保/审计等企业硬门槛。
- 不是“把 Java 单体塞进 K8s”，而是设计一套可复制的交付控制面。
- 能讲清交付工程、发布工程、客户成功和运维交接。

## 3. 用户与场景

| 用户 | 场景 | 痛点 |
|------|------|------|
| 客户 IT | 安装/升级/排障 | 无外网、文档少 |
| 安全/合规 | 审计/权限 | 数据不出域 |
| 业务用户 | 登录/使用 | 多套账号 |
| FDE | 交付/升级 | 环境差异、回滚难 |

## 4. 目标与非目标

### 目标

- 离线安装包/镜像仓库
- K8s/Helm 部署，多环境 values
- OIDC/SAML SSO、RBAC、审计
- 升级/回滚/备份/恢复
- 健康检查/监控/日志
- 客户运维手册和交接
- 许可证/版本管理

### 非目标

- 不重写客户核心业务
- 不做公有云 SaaS
- 不做完整安全产品

## 5. 技术栈

### 控制面/后端

- Python 3.12+ + FastAPI + Pydantic v2
- PostgreSQL + Redis
- 任务队列 Celery/Arq
- OIDC：Authlib/python-jose
- 对象存储/本地文件
- pytest + ruff
- uv / Docker

### 前端

- Next.js 15+ 运维台
- TypeScript + Tailwind CSS
- Auth.js（OIDC）
- 部署/升级/审计/健康页面
- Playwright

### 交付

- Docker / Helm / K8s
- 离线镜像仓库（Harbor）
- Keycloak/客户 OIDC
- Prometheus/Grafana/Loki/Tempo
- 备份/恢复脚本

## 6. 架构

```text
客户浏览器 -> Next.js 运维台 -> Python FastAPI 控制面
                                   ├── 部署/升级/回滚
                                   ├── SSO/审计/许可证
                                   ├── 健康检查/日志
                                   └── 业务应用（容器化）
                                          │
                                   K8s / 离线镜像仓库
```

## 7. 项目结构

```text
05-regulated-private-deployment/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/              # deployments, upgrades, audit, health
│   │   ├── core/                # config, auth, license, audit
│   │   ├── domain/              # release, environment, upgrade
│   │   ├── services/            # helm/k8s/backup adapters
│   │   ├── models/
│   │   └── schemas/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/(ops)/page.tsx
│   ├── app/deployments/page.tsx
│   ├── app/audit/page.tsx
│   ├── app/health/page.tsx
│   ├── components/
│   ├── lib/api.ts
│   └── package.json
├── deploy/
│   ├── offline-bundle/
│   ├── helm/
│   ├── k8s/
│   └── scripts/
└── docs/
    ├── 01-discovery.docx
    ├── 02-architecture.docx
    └── 03-acceptance.docx
```

## 8. 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/environments` | 环境/版本 |
| POST | `/api/v1/deployments` | 部署 |
| POST | `/api/v1/upgrades` | 升级 |
| POST | `/api/v1/rollbacks` | 回滚 |
| GET | `/api/v1/audit` | 审计 |
| GET | `/api/v1/health` | 健康 |
| GET | `/healthz` | 自身健康 |

## 9. 数据模型

| 表 | 关键字段 |
|----|----------|
| environment | id, name, customer, k8s_version, network_mode |
| release | id, version, images, chart, checksum |
| deployment | id, env_id, release_id, status, started_at |
| upgrade | id, env_id, from_version, to_version, status |
| audit_log | user_id, action, resource, result |
| license | customer, expires_at, features |
| backup | env_id, type, location, created_at |

## 10. 实现步骤

### 阶段 1：客户环境尽调（3–5 天）

1. 网络/代理/离线/证书/域名。
2. K8s/VM/存储/数据库/镜像仓库。
3. SSO/权限/审计/合规。
4. 升级窗口/回滚要求。

### 阶段 2：离线包与控制面（5–7 天）

1. 镜像/Chart/依赖打包。
2. FastAPI 控制面：环境/版本/部署。
3. 许可证/审计/健康。
4. 离线安装脚本。

### 阶段 3：K8s/SSO/监控（5–7 天）

1. Helm chart + values。
2. OIDC 登录/角色映射。
3. Prometheus/Loki/Tempo。
4. 探针/资源/PDB/NetworkPolicy。

### 阶段 4：升级/回滚/备份（4–5 天）

1. 升级流程和版本校验。
2. 回滚和备份恢复。
3. 失败演练。
4. 客户运维手册。

### 阶段 5：交付与交接（3–5 天）

1. 安装/升级/回滚演练。
2. 客户培训。
3. 交接清单。
4. Demo/复盘。

## 11. 里程碑（5 周）

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | 环境尽调 | 网络/依赖/风险 |
| 2 | 离线包/控制面 | 可安装 |
| 3 | K8s/SSO/监控 | 可登录/可观测 |
| 4 | 升级/回滚/备份 | 可运维 |
| 5 | 交付/培训/复盘 | 项目包 |

## 12. 验收标准

- [ ] 离线环境可安装
- [ ] SSO 登录/角色映射
- [ ] 升级/回滚成功
- [ ] 备份/恢复演练
- [ ] 监控/日志/告警
- [ ] 审计/许可证
- [ ] 客户运维手册/交接

## 13. 面试讲法

“私有化交付不是把镜像拷过去。客户没有外网、没有你熟悉的工具、安全要求高，FDE 要设计离线包、SSO、审计、升级和回滚，并让客户 IT 能接得住。”
