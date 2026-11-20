# AI Shopping Assistant · src

## 后端（Python / FastAPI）

```text
backend/app/
├── main.py
├── api/v1/                 # chat, products, feedback, admin
├── core/                   # config, security, logging, deps
├── domain/                 # 商品/会话/引用/评估
├── models/                 # SQLAlchemy
├── schemas/                # Pydantic
├── repositories/           # Postgres/vector store
├── integrations/           # LLM, embedding, 商品 API
├── workers/                # 索引、评估、清理
└── evaluation/
```

## 前端（Next.js）

```text
frontend/
├── app/(chat)/page.tsx
├── app/admin/eval/page.tsx
├── components/Chat.tsx
├── components/Citation.tsx
├── components/ProductCard.tsx
├── lib/api.ts
├── hooks/
└── tests/
```

## 最小实现顺序

1. FastAPI 健康检查 + 配置 + 日志。
2. Postgres/pgvector + 商品样例。
3. 解析/切分/embedding 脚本。
4. `/chat` 检索 + 引用。
5. Next.js Chat UI 接 API。
6. 30 条评估集 + 指标。
7. 权限、反馈、Docker Compose。
