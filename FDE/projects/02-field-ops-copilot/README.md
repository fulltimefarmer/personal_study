# 02 · Field Ops Copilot

> 工业/能源现场工程师 Copilot。离线优先、移动端、设备手册 RAG、工单、IoT 告警、安全合规。  
> 技术栈：**Python/FastAPI 后端 + Next.js PWA 前端**。详细方案见 `../../06-FDE项目实战指南.docx` 第 4 章。

## 1. 业务背景

制造/能源企业的现场工程师在工厂、基站、风场等弱网/无网环境工作。需要查设备手册、历史工单、安全规程，记录维修结果，接收 IoT 告警。现有系统是 PC 端，现场不好用。

## 2. 为什么这个项目有竞争力

- 不是又一个通用 RAG：它包含 **离线同步、移动 PWA、IoT、安全规程、工单闭环**，更接近真实 FDE 现场。
- 能讲清“弱网/无网、现场人员、合规、设备数据”这些客户约束。
- 体现 FDE 的现场交付能力：部署、培训、离线包、设备兼容、故障兜底。
- 适合制造、能源、汽车、工业软件等 FDE 岗位。

## 3. 用户与场景

| 用户 | 场景 | 痛点 |
|------|------|------|
| 现场工程师 | 查手册、报修、填工单 | 弱网、PC 不便、知识找不到 |
| 值班经理 | 看告警、派单 | 信息分散、响应慢 |
| 安全员 | 检查规程 | 版本多、执行难追踪 |
| 知识管理员 | 维护手册 | 更新不同步 |

## 4. 目标与非目标

### 目标

- 设备手册/安全规程 RAG，带引用
- 工单创建/更新/关闭，离线可写
- 离线缓存和恢复后同步
- IoT 告警接入和派单
- PWA 移动端，弱网可用
- 权限/审计/安全合规
- 评估回答准确率和现场任务完成率

### 非目标

- 不做完整 EAM/CMMS
- 不做设备控制闭环
- 不做高精度室内定位

## 5. 技术栈

### 后端

- Python 3.12+ + FastAPI + Pydantic v2
- PostgreSQL + pgvector（手册/工单检索）
- Redis（缓存/会话/限流）
- SQLite（边缘/离线包，可选）
- Celery/Arq（同步、索引、告警）
- httpx（IoT/设备/工单 API）
- pytest + ruff
- uv / Docker

### 前端

- Next.js 15+ App Router + PWA
- TypeScript + Tailwind CSS
- IndexedDB / Service Worker（离线缓存）
- TanStack Query
- Auth.js
- Playwright（含离线场景）

### 集成

- MQTT/Kafka（IoT 告警）
- 设备手册 PDF/Word
- 工单系统 API
- 对象存储（图片/视频）

## 6. 架构

```text
设备手册/安全规程/历史工单
        │ 批/增量
        ▼
Python ingestion -> 切分/Embedding -> pgvector
        │
Next.js PWA（离线缓存/IndexedDB）
        │ 在线/离线
        ▼
FastAPI -> 检索/引用 -> 工单/告警/审计
        │
        ├── MQTT/Kafka IoT 告警
        └── 对象存储（现场图片/视频）
```

## 7. 项目结构

```text
02-field-ops-copilot/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/              # manuals, workorders, alerts, sync
│   │   ├── core/                # config, auth, audit, offline token
│   │   ├── domain/              # workorder, asset, alert, citation
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── integrations/        # IoT, workorder, object storage
│   │   ├── workers/             # sync, index, alert
│   │   └── evaluation/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/(field)/page.tsx
│   ├── app/manuals/page.tsx
│   ├── app/workorders/page.tsx
│   ├── app/alerts/page.tsx
│   ├── components/OfflineBanner.tsx
│   ├── lib/offline.ts           # IndexedDB/同步
│   ├── lib/api.ts
│   ├── public/manifest.json
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
| POST | `/api/v1/ask` | 手册/规程问答 |
| GET | `/api/v1/workorders` | 工单列表（离线缓存） |
| POST | `/api/v1/workorders` | 创建工单 |
| PATCH | `/api/v1/workorders/{id}` | 更新/关闭 |
| POST | `/api/v1/sync` | 离线数据同步 |
| GET | `/api/v1/alerts` | IoT 告警 |
| GET | `/healthz` | 健康检查 |

## 9. 数据模型

| 表 | 关键字段 |
|----|----------|
| asset | id, name, model, site, status |
| manual | id, asset_model, title, version, acl |
| chunk | id, manual_id, content, embedding |
| workorder | id, asset_id, assignee, status, priority, description |
| workorder_event | workorder_id, type, payload, created_at |
| alert | id, asset_id, severity, status, source |
| sync_log | device_id, user_id, last_sync_at, conflict |
| audit_log | user_id, action, resource, result |

## 10. 实现步骤

### 阶段 1：现场发现（3–5 天）

1. 访谈 2–3 个现场角色，记录弱网/离线流程。
2. 定义工单状态机和安全规程。
3. 准备 20 份手册/规程/历史工单。
4. 定义成功指标（查找时间、工单完成率、告警响应）。

### 阶段 2：后端与检索（5–7 天）

1. FastAPI 骨架、配置、日志、权限。
2. 手册解析/切分/embedding。
3. 检索 + 引用 + 拒答。
4. 工单 CRUD 和审计。

### 阶段 3：离线 PWA（5–7 天）

1. Next.js PWA + Service Worker。
2. IndexedDB 缓存手册摘要/工单。
3. 离线创建/更新工单。
4. 恢复后同步和冲突处理。
5. 弱网提示和重试。

### 阶段 4：IoT 与告警（3–5 天）

1. MQTT/Kafka 模拟告警。
2. 告警 -> 派单。
3. 通知和升级。
4. 告警降噪/静默。

### 阶段 5：部署与现场演练（3–5 天）

1. Docker Compose。
2. 离线安装包/网络受限部署。
3. 现场演练：断网、恢复、冲突。
4. Demo/复盘。

## 11. 里程碑（5 周）

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | 现场发现 + 手册样例 | 问题陈述、指标、评估集 |
| 2 | 检索 + 工单 API | 后端 MVP |
| 3 | PWA + 离线缓存 | 断网可用 |
| 4 | 同步/冲突/IoT | 闭环 Demo |
| 5 | 部署/演练/复盘 | 项目包 |

## 12. 验收标准

- [ ] 断网时可查最近手册/工单
- [ ] 离线创建工单，恢复后同步且不重复
- [ ] 回答带手册/规程引用
- [ ] IoT 告警可派单/关闭
- [ ] 权限和审计
- [ ] 移动端可用
- [ ] 有冲突处理和失败兜底

## 13. 面试讲法

“这个项目不是普通 RAG，而是现场 FDE 的缩影：弱网、离线、设备、工单、安全规程、IoT。客户不会因为模型回答漂亮就买单，他们关心现场工程师能不能用、断网会不会丢数据。”
