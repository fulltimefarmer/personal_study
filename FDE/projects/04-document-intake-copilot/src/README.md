# Document Intake Copilot · src

## 后端（Python / FastAPI）

```text
backend/app/
├── main.py
├── api/v1/              # documents, extractions, review, admin
├── core/                # config, auth, audit, storage
├── domain/              # document, extraction, field, review
├── models/
├── schemas/
├── repositories/
├── ocr/                 # OCR/版面
├── extraction/          # LLM/Prompt/规则
├── workers/             # 异步任务
└── evaluation/
```

## 前端（Next.js）

```text
frontend/
├── app/upload/page.tsx
├── app/documents/page.tsx
├── app/review/[id]/page.tsx
├── components/FieldHighlight.tsx
├── lib/api.ts
└── tests/
```

## 最小实现顺序

1. 上传 + 对象存储 + 任务队列。
2. OCR/版面 + 字段定义。
3. LLM 抽取 + 规则校验 + 置信度。
4. Next.js 复核台 + 原文高亮。
5. 评估集/准确率/复核率。
6. 权限/审计/Docker Compose。
