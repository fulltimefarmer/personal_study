# FDE 实战项目

六个项目，建议选 **1 个主项目 + 1 个辅助项目**，不要全部做。所有项目统一采用 **Python/FastAPI 后端 + Next.js 前端**（部分项目前端可选）。

| 项目 | 场景 | 核心能力 | 适合 |
|------|------|----------|------|
| [01-ai-shopping-assistant](01-ai-shopping-assistant/) | 零售 AI 导购 | RAG、评估、Milvus/pgvector、权限 | 主项目（最贴简历） |
| [02-field-ops-copilot](02-field-ops-copilot/) | 工业现场工程师 Copilot | 离线 PWA、IoT、工单、手册 RAG | 工业/现场 FDE |
| [03-order-exception-hub](03-order-exception-hub/) | 全渠道订单异常与对账 | Kafka、异常规则、补偿、对账 | 企业集成 FDE |
| [04-document-intake-copilot](04-document-intake-copilot/) | 单据/合同智能录入 | OCR、LLM、人工复核、审计 | 流程自动化 FDE |
| [05-regulated-private-deployment](05-regulated-private-deployment/) | 金融/医疗私有化交付 | 离线包、K8s、SSO、升级回滚 | 平台交付 FDE |
| [06-incident-copilot](06-incident-copilot/) | AI SRE 事故 Copilot | Agent、只读工具、可观测性 | AI 运维 FDE |

## 推荐组合

- **AI 产品方向**：01 AI Shopping Assistant（主）+ 05 Regulated Private Deployment（辅）
- **企业集成方向**：03 Order Exception Hub（主）+ 06 Incident Copilot（辅）
- **工业/现场方向**：02 Field Ops Copilot（主）+ 04 Document Intake Copilot（辅）

## 每个项目至少完成

- 一页问题陈述和成功指标
- 架构图/数据流
- 可运行 MVP
- Docker Compose 或 K8s 部署
- 监控/日志/健康检查
- 验收标准和 5 分钟 Demo
- 复盘和面试故事

## 当前状态

项目为骨架：已有 README、业务背景、需求、技术栈、项目结构、实现步骤、里程碑、验收和面试讲法。代码需要你逐步补全。
