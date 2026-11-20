# 04 · Document Intake Copilot

> 企业单据/合同智能录入。OCR + LLM 抽取 + 置信度 + 人工复核 + 审计，是金融、采购、保险、物流 FDE 的高频场景。  
> 技术栈：**Python/FastAPI 后端 + Next.js 前端**。详细方案见 `../../06-FDE项目实战指南.docx` 第 6 章。

## 1. 业务背景

企业每天收到大量发票、合同、运单、理赔单。人工录入慢、错误多、合规风险高。客户希望自动抽取关键字段，低置信度转人工，保留审计和原文对照。

## 2. 为什么这个项目有竞争力

- 不是聊天机器人，而是 **有明确 ROI 的企业流程自动化**：减少录入时间、提高准确率、降低合规风险。
- 覆盖 FDE 常见的非结构化数据、OCR、LLM、人工复核、权限、审计、评估。
- 可跨行业复用：财务、采购、保险、物流、医疗。
- 能讲清“准确率/置信度/人工复核/审计”这些客户真正关心的指标。

## 3. 用户与场景

| 用户 | 场景 | 痛点 |
|------|------|------|
| 财务 | 发票录入/校验 | 人工慢、税号/金额错 |
| 采购 | 合同抽取 | 条款多、版本乱 |
| 运营 | 运单/回单 | 格式不一 |
| 合规 | 审计 | 无法追溯 |

## 4. 目标与非目标

### 目标

- 上传 PDF/图片/扫描件
- OCR + 版面分析
- LLM 抽取结构化字段
- 置信度和人工复核
- 原文对照/高亮
- 规则校验（税号、金额、日期）
- 审计和权限
- 评估字段准确率/人工工作量

### 非目标

- 不做完整 ERP
- 不做通用 OCR 平台
- 不自动付款/审批
- 不承诺 100% 准确

## 5. 技术栈

### 后端

- Python 3.12+ + FastAPI + Pydantic v2
- PostgreSQL + SQLAlchemy 2 + Alembic
- Redis（任务/缓存/限流）
- Celery/Arq（OCR/抽取异步任务）
- OCR：PaddleOCR/Tesseract/云 OCR（按客户环境）
- LLM：GPT/Qwen/私有化模型
- 对象存储（原文件/预览）
- pytest + ruff
- uv / Docker

### 前端

- Next.js 15+ App Router
- TypeScript + Tailwind CSS
- TanStack Query
- PDF/图片预览 + 字段高亮
- Auth.js
- Playwright

## 6. 架构

```text
上传 PDF/图片 -> 对象存储 -> 任务队列 -> OCR/版面分析
        │                              │
        │                              ▼
        │                         LLM 抽取 -> 规则校验
        │                              │
        └── Next.js 复核台 <- FastAPI <- 置信度/结果
                              │
                              └── 审计/导出/评估
```

## 7. 项目结构

```text
04-document-intake-copilot/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/              # documents, extractions, review, admin
│   │   ├── core/                # config, auth, audit, storage
│   │   ├── domain/              # document, extraction, field, review
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── ocr/                 # OCR/版面
│   │   ├── extraction/          # LLM/Prompt/规则
│   │   ├── workers/             # 异步任务
│   │   └── evaluation/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/upload/page.tsx
│   ├── app/documents/page.tsx
│   ├── app/review/[id]/page.tsx
│   ├── components/FieldHighlight.tsx
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
| POST | `/api/v1/documents` | 上传 |
| GET | `/api/v1/documents/{id}` | 状态/结果 |
| GET | `/api/v1/documents/{id}/fields` | 字段/置信度 |
| POST | `/api/v1/review/{id}` | 人工复核 |
| GET | `/api/v1/admin/eval` | 评估 |
| GET | `/healthz` | 健康检查 |

## 9. 数据模型

| 表 | 关键字段 |
|----|----------|
| document | id, filename, type, status, storage_key, uploaded_by |
| extraction | id, document_id, model, status, raw_json |
| field | extraction_id, name, value, confidence, bbox, page |
| review | document_id, reviewer, decision, note, reviewed_at |
| rule | name, field, rule_type, expression, active |
| eval_case | document_id, expected_fields |
| eval_run | run_id, field_accuracy, review_rate, latency |
| audit_log | user_id, action, resource, result |

## 10. 实现步骤

### 阶段 1：场景与样例（3–5 天）

1. 选 1 类单据（发票/合同/运单）。
2. 准备 20–50 份脱敏样例。
3. 定义字段、规则、置信度阈值。
4. 定义成功指标（字段准确率、人工复核率、处理时长）。

### 阶段 2：OCR + 抽取（5–7 天）

1. 上传/对象存储/任务队列。
2. OCR/版面分析。
3. LLM 结构化抽取。
4. 规则校验（税号/金额/日期）。
5. 置信度和失败分类。

### 阶段 3：复核台（4–5 天）

1. Next.js 上传/列表/详情。
2. 原文件预览 + 字段高亮。
3. 人工修改/确认/拒绝。
4. 审计。

### 阶段 4：评估与权限（4–5 天）

1. 字段准确率、复核率、处理时长。
2. 低置信度路由。
3. 权限/脱敏/审计。
4. 失败分析。

### 阶段 5：部署与 Demo（3–4 天）

1. Docker Compose。
2. 监控/日志。
3. 5 分钟 Demo。
4. 复盘。

## 11. 里程碑（5 周）

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | 场景/样例/字段 | 问题陈述、评估集 |
| 2 | OCR + 抽取 | 结构化结果 |
| 3 | 复核台 | 人工闭环 |
| 4 | 评估/权限 | 报告 |
| 5 | 部署/Demo | 项目包 |

## 12. 验收标准

- [ ] 20 份样例可上传/处理
- [ ] 关键字段准确率 ≥ 85%（按场景）
- [ ] 低置信度转人工
- [ ] 原文高亮/可追溯
- [ ] 规则校验
- [ ] 权限/审计
- [ ] 有评估报告

## 13. 面试讲法

“Document Intake 是企业 AI 最容易算清 ROI 的场景：减少录入时间、提高准确率、降低合规风险。FDE 要做的不是模型多强，而是置信度、人工复核、审计和客户流程真正接上。”
