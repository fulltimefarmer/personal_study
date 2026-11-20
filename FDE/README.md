# FDE 转型学习路径（Java 后端 → Forward Deployed Engineer）

> 基于你的简历定制：13+ 年全栈经验，LEGO / Tesla / Nike / eBay / EA，零售电商、高并发、Spring Cloud、SSO、数据治理，以及 BGE + Milvus + Qwen 的 RAG 购物助手落地经验。  
> 目标不是“从零学技术”，而是把已有的工程能力重新包装成 FDE 的客户价值交付能力。

---

## 1. 你的定位

### 推荐主定位

**Retail / Enterprise AI Forward Deployed Engineer**

也可以投：

- Forward Deployed AI Engineer
- Solutions Architect / Solution Engineer
- Technical Account / Customer Engineer
- AI Application Delivery Lead
- 企业 AI 解决方案工程师

### 你的差异化

| 优势 | 如何在 FDE 面试中使用 |
|------|----------------------|
| 13+ 年全栈 | 证明能独立从需求到上线，不依赖大量支持 |
| LEGO/Tesla/Nike/eBay | 证明能适应高标准、跨团队、全球协作 |
| 电商高并发 | 能处理峰值、稳定性、库存和订单一致性 |
| Spring Cloud / 微服务 | 能设计企业集成、服务治理和后台系统 |
| RAG 购物助手 | 直接命中 AI FDE 的核心叙事 |
| 带团队 / 7x24 值班 | 能承担客户现场交付和故障处理 |
| 英语 + 海外硕士 | 能服务全球客户和英文环境 |

### 需要补的短板

- 客户访谈、需求澄清、范围与预期管理
- 方案表达、Demo、向非技术客户讲取舍
- 云平台（AWS/Azure/GCP）与 Kubernetes 的生产交付
- Python 数据工程与 LLM 评估/Guardrails
- 安全、合规、私有化部署
- FDE 商业意识：续约、扩展、客户成功

> 39 岁不是问题，关键是不能被定位成“只会写代码的资深开发”。你的叙事应该是：**能写、能讲、能带、能对客户结果负责的交付型工程师。**

---

## 2. 文件夹内容

除本 README 外，所有学习文档均为 **docx**。

| 文件 | 内容 |
|------|------|
| `01-FDE转型定位与能力差距.docx` | 简历解读、岗位匹配、39 岁定位、能力雷达、目标市场、90 天计划 |
| `02-FDE学习路线图.docx` | 24 周逐周计划、12 周冲刺版、36 周深度版、检查点 |
| `03-FDE知识缺口补足手册.docx` | 10 大领域、100+ 知识点、P0/P1/P2、练习与验收 |
| `04-FDE面试题库.docx` | 120 道题：定位、客户、零售、架构、Java、数据、云、AI、安全、交付 |
| `05-FDE认证与学习资源.docx` | 认证组合、成本/周期、官方资源、简历写法 |
| `06-FDE项目实战指南.docx` | 6 个通用实战项目的背景、架构、里程碑、验收、Demo |
| `07-FDE简历与面试表达.docx` | FDE 版简历、30 秒/2 分钟自我介绍、STAR 故事、谈薪 |
| `08-FDE交付模板与工具包.docx` | 访谈、范围、评审、上线、复盘、周报、交接模板 |
| `projects/` | 6 个项目骨架，每个含 README 和 src 占位说明 |

---

## 3. 24 周路线概览

默认每周 10–12 小时，适合在职转型。全职可压缩到 12–16 周。

| 阶段 | 周次 | 目标 | 产出 |
|------|------|------|------|
| 定位与基础 | 1–3 | FDE 认知、简历定位、SQL/Python 复习 | 定位陈述、简历 v1、SQL/Python 练习 |
| 客户与方案 | 4–6 | 客户发现、方案设计、Demo | 访谈记录、方案文档、3 分钟 Demo |
| 数据与集成 | 7–10 | 数据建模、FastAPI 集成、Kafka | Order Exception Hub MVP |
| 云原生交付 | 11–14 | Docker、K8s、云网络、可观测性 | 可部署服务 + 监控 |
| AI FDE | 15–18 | RAG、评估、Guardrails、Agent | AI Shopping Assistant |
| 主项目冲刺 | 19–21 | 端到端交付、验收、复盘 | 主项目 + Demo + 文档 |
| 求职冲刺 | 22–24 | 面试、networking、谈薪 | 120 题、8 个故事、投递清单 |

详细计划见 `02-FDE学习路线图.docx`。

---

## 4. 六个实战项目

项目按“企业常见 + 你的背景可讲”设计，当前为骨架，后续补代码。所有项目统一采用 **Python/FastAPI 后端 + Next.js 前端**（部分项目前端可选）。

| 项目 | 场景 | 核心能力 | 适合作为 |
|------|------|----------|----------|
| [01-ai-shopping-assistant](projects/01-ai-shopping-assistant/) | 零售 AI 导购 | RAG、评估、Milvus/pgvector、推荐 | 主项目/AI FDE |
| [02-field-ops-copilot](projects/02-field-ops-copilot/) | 工业现场工程师 Copilot | 离线 PWA、IoT、工单、手册 RAG | 主项目/工业 FDE |
| [03-order-exception-hub](projects/03-order-exception-hub/) | 全渠道订单异常与对账 | Kafka、异常规则、补偿、对账 | 主项目/企业集成 |
| [04-document-intake-copilot](projects/04-document-intake-copilot/) | 单据/合同智能录入 | OCR、LLM、人工复核、审计 | 主项目/流程自动化 |
| [05-regulated-private-deployment](projects/05-regulated-private-deployment/) | 金融/医疗私有化交付 | 离线包、K8s、SSO、升级回滚 | 主项目/平台 FDE |
| [06-incident-copilot](projects/06-incident-copilot/) | AI SRE 事故 Copilot | Agent、只读工具、可观测性、Guardrails | 主项目/AI 运维 |

建议：**1 个主项目 + 1 个辅助项目**，不要六个都做。

推荐组合：

- **AI 产品方向**：01 AI Shopping Assistant（主）+ 05 Regulated Private Deployment（辅）
- **企业集成方向**：03 Order Exception Hub（主）+ 06 Incident Copilot（辅）
- **工业/现场方向**：02 Field Ops Copilot（主）+ 04 Document Intake Copilot（辅）

---

## 5. 推荐执行方式

### 第 1 周就做三件事

1. 读 `01-FDE转型定位与能力差距.docx`，写出你的 30 秒定位。
2. 用 `03-FDE知识缺口补足手册.docx` 做自评，圈出 5 个 P0。
3. 选一个主项目，写 1 页问题陈述。

### 每周固定节奏

- 2 次学习块（各 2 小时）：文档/课程 + 笔记。
- 1 次动手块（3–4 小时）：项目代码/实验。
- 1 次输出块（1–2 小时）：Demo、文档或录音。
- 1 次复盘（30 分钟）：本周证据、下周调整。

### 求职启动时间

- 第 10 周开始更新 LinkedIn/简历。
- 第 16 周开始小规模投递和约咖啡。
- 第 20 周主项目可演示后全力投递。

---

## 6. 39 岁转型策略

### 要强调的

- **交付成熟度**：带过团队、扛过 7x24、经历过大促。
- **客户可信度**：全球公司、跨团队、英语沟通。
- **技术深度 + 广度**：Java 高并发 + AI RAG + 全栈。
- **AI-native**：用 AI 工具快速验证，不是“年龄大不接受新东西”。

### 要避免的

- 只讲技术栈，不讲业务结果。
- 把自己包装成“纯管理”，FDE 需要动手。
- 对出差/驻场/客户压力含糊。
- 简历写成 13 年流水账，没有 FDE 主线。
- 和年轻人拼“加班时长”，要拼判断力、交付确定性和客户信任。

---

## 7. 转型成功的判断标准

- 能独立主持 45 分钟客户访谈并输出问题陈述。
- 能画出端到端方案并讲清取舍。
- 能用 Java + Python + SQL 做出可运行 MVP。
- 能在 Docker/K8s 部署并排查常见问题。
- 能讲清一个 RAG 项目的检索、评估、失败和成本。
- 能用英文做 2 分钟自我介绍和项目介绍。
- 有 1 个主项目 + 1 个辅助项目 + 8 个 STAR 故事。

---

## 8. 文档使用顺序

1. `01-FDE转型定位与能力差距.docx`
2. `03-FDE知识缺口补足手册.docx`
3. `02-FDE学习路线图.docx`
4. `06-FDE项目实战指南.docx`
5. `07-FDE简历与面试表达.docx`
6. `04-FDE面试题库.docx`
7. `05-FDE认证与学习资源.docx`
8. `08-FDE交付模板与工具包.docx`

> 先定位，再补缺口，再按周执行；项目是主线，文档和认证是支撑。
