# Apple 面试准备指南 · Apple Interview Prep Guide（12 小时版）

> **岗位 / Role:** Full-Stack Engineer — Apple Store Online, Rapid Application Development (RAD)
> **Role Number:** 200679391-3715
> **JD 来源 / Source:** https://jobs.apple.com/zh-cn/details/200679391-3715

---

## 目录 / Table of Contents

| 文件 / File | 内容 / Content |
| --- | --- |
| `README.md` | 本文件：12 小时准备计划 + 面试流程概览 |
| `01-javascript-typescript.md` | JavaScript / TypeScript 深度问答（中英双语） |
| `02-angular.md` | Angular 深度问答（中英双语） |
| `03-nestjs-node.md` | NestJS / Node.js 深度问答（中英双语） |
| `04-postgresql-sql.md` | PostgreSQL / SQL 深度问答（中英双语） |
| `05-cloud-devops-genai-system-design.md` | 云/DevOps + GenAI/Agentic + 系统设计（中英双语） |
| `06-behavioral-qa.md` | 行为面试问答（STAR 方法，中英双语） |
| `coding/` | 8 道 CoderPad 模拟编程题（每题含题干 + 解答 + 代码空壳） |
| `basic/` | TS + React 基础语法教学（带中文注解、可运行、可动手练习） |

---

## 岗位关键信息速览 / Role Snapshot

**技术栈 (Tech Stack):**
- 前端: **Angular** (或 React)、TypeScript、JavaScript
- 后端: **NestJS** (或类似)、Node.js、RESTful APIs
- 数据库: **PostgreSQL**、SQL
- 云/基础设施: **AliCloud**、Docker、Kubernetes、CI/CD、DevOps
- AI: **Generative AI / Agentic workflows** (1-2 年为最低要求，2+ 年为优先项)
- 经验要求: 7+ 年（最低）/ 8+ 年（优先）

**团队定位 (Team Context):**
Apple Store Online (ASO) 是 Apple 最大的线上商店。RAD 团队负责开发内部工具应用，自动化、流程化、增值服务于 ASO 内部各团队与 Retail Customer Care。工作内容包括全栈开发（UI/UX、后端、数据库）、AliCloud 基础设施维护、测试策略（单元 + E2E）、生产支持（需配合 AMR 区域时差）。

**JD 特别强调的能力点:**
1. 全栈端到端能力（前端 UI/UX 到后端到数据库）
2. 云基础设施管理（AliCloud + 容器 + CI/CD）
3. 测试策略（单元测试 + E2E）
4. **Agentic workflows**（把 GenAI 嵌入流水线，自动生成 PR，human-in-the-loop）
5. 数据与隐私合规（Apple 对隐私极其重视）
6. 生产支持下的分析与问题解决能力

---

## 12 小时准备计划 / 12-Hour Prep Plan

> 建议分 3 天、每天 4 小时。每天「先自测 → 看答案 → 复述 → 做配套编程题」。所有问答均为中英双语，面试时按需切换语言。

### Day 1（4 小时）：JavaScript / TypeScript 深度

| 时间 | 模块 | 内容 | 参考 |
| --- | --- | --- | --- |
| 0:00–0:30 | 热身 | 通读 JD、提炼关键词、准备中英自我介绍 | `README` + `06` |
| 0:30–2:15 | JavaScript 核心 | 事件循环、闭包、this、原型链、Promise/async、事件委托、防抖节流、深拷贝、模块化等 | `01` §JS |
| 2:15–4:00 | TypeScript 进阶 | 泛型、类型收窄、工具类型、`type` vs `interface`、`unknown` vs `any`、条件/映射类型、装饰器、类型体操入门 | `01` §TS |
| 课后 | 编程 | 做 1 道 Hash 类题（Two Sum / Group Anagrams） | `coding/02`、`coding/05` |

### Day 2（4 小时）：Angular + NestJS/Node + PostgreSQL

| 时间 | 模块 | 内容 | 参考 |
| --- | --- | --- | --- |
| 0:00–1:30 | Angular | 变更检测、OnPush、RxJS、组件通信、生命周期、性能优化、Signals | `02` |
| 1:30–3:00 | NestJS + Node | DI、模块、请求生命周期、Guard/Interceptor/Pipe/Filter、微服务、事件循环、内存泄漏 | `03` |
| 3:00–4:00 | PostgreSQL | 索引、事务隔离、MVCC、慢查询优化、JOIN、连接池、窗口函数 | `04` |
| 课后 | 编程 | 做 1 道设计题（LRU Cache）+ 1 道区间题（Merge Intervals） | `coding/01`、`coding/03` |

### Day 3（4 小时）：云/DevOps + GenAI + 系统设计 + 行为 + 编程

| 时间 | 模块 | 内容 | 参考 |
| --- | --- | --- | --- |
| 0:00–1:00 | 云/DevOps | Docker、K8s、CI/CD、AliCloud、滚动/蓝绿/金丝雀、可观测性 | `05` §云 |
| 1:00–2:00 | GenAI/Agentic | RAG、微调、agentic workflow、human-in-the-loop、评估、隐私合规 | `05` §AI |
| 2:00–3:00 | 系统设计 | 电商商品/购物车/下单、限流器、幂等、CAP | `05` §设计 |
| 3:00–3:30 | 行为面试 | 复盘 6–8 个 STAR 故事 | `06` |
| 3:30–4:00 | 编程收尾 | 做图类 + 堆/前缀题（Number of Islands / Top K / Product Except Self） | `coding/04`、`coding/07`、`coding/08` |

### 编程题分配建议 / Coding Schedule
8 道题按 Day1–Day3 分散练习，每道 30–45 分钟（先自己做 → 看解答 → 复述思路 → 重写一遍）：

| 题号 | 题目 | 模式 | 难度 |
| --- | --- | --- | --- |
| 01 | LRU Cache | 设计 + 哈希 + 双向链表 | Medium |
| 02 | Two Sum | 哈希表 | Easy |
| 03 | Merge Intervals | 排序 | Medium |
| 04 | Number of Islands | 图 DFS/BFS | Medium |
| 05 | Group Anagrams | 哈希/计数 | Medium |
| 06 | Course Schedule | 图拓扑排序/判环 | Medium |
| 07 | Product of Array Except Self | 前缀积 | Medium |
| 08 | Top K Frequent Elements | 堆/桶排序 | Medium |

> **时间紧张怎么办?** 优先保证 Day1（JS/TS 是基础）、Day2 的 `03-nestjs-node`、Day3 的 `05` 系统设计 + GenAI、`06` 行为 TOP 8 题、`coding/01`(LRU)、`coding/03`(Merge Intervals)、`coding/04`(Number of Islands)。

---

## 面试流程概览 / Apple Interview Process (from research)

苹果面试高度「团队化」，没有统一题库，但典型流程为 3–6 周、4–8 轮：

1. **Recruiter Screen（HR 电话/视频）** — 背景、动机、薪资期望、签证/地点。
2. **Technical Phone Screen（技术电面）** — 1–2 轮，通常含 CoderPad 在线编码 + 技术栈深挖。
3. **Virtual Onsite Loop（虚拟现场，4–6 轮）**：
   - 2–3 轮 **Coding**（CoderPad，偏 medium，强调正确性 + 可读性 + 边界 + 沟通）
   - 1 轮 **System Design**（电商/内部工具场景，强调隐私、可靠性、可维护性）
   - 1 轮 **Behavioral**（STAR，协作、冲突、ownership、产品判断）
   - 可能 1 轮 **Hiring Manager / 项目经历深挖**

**苹果高频编程题（据 LeetCode 标签与候选者反馈，按频率）：**
`LRU Cache`(最高频)、`Two Sum`、`Merge Intervals`、`Number of Islands`、`Group Anagrams`、`Course Schedule`、`Product of Array Except Self`、`Top K Frequent Elements`、`Reverse Linked List`、`Valid Parentheses`、`3Sum`、`Clone Graph`、`Meeting Rooms`、`Design Hit Counter`、`Task Scheduler`。详见 `coding/`。

**高频模式占比（据 dsaprep 统计 375 题）：** Array 49%、String 27%、Hash Table 18%、DP 18%、Two Pointers 17%、Math 14%、Linked List 11%、Sorting/DFS/Tree 各约 10%。

---

## 快速自测清单 / Quick Self-Check

- [ ] 能解释 JS 事件循环 + 微任务/宏任务 + 浏览器 vs Node 差异
- [ ] 能手写 `debounce` / `throttle` / `deepClone` / `Promise.all`
- [ ] 能解释原型链与 `class` 的底层关系
- [ ] 能用泛型 + 条件类型写一个类型安全的 API 封装
- [ ] 能解释 Angular 变更检测 + `OnPush` + `trackBy`
- [ ] 能解释 NestJS 请求生命周期（Middleware → Guard → Interceptor → Pipe → Handler）
- [ ] 能解释 PostgreSQL MVCC、事务隔离级别、索引类型
- [ ] 能画出电商「购物车/下单」系统设计草图（含幂等、防超卖）
- [ ] 能讲清 agentic workflow + human-in-the-loop + RAG 评估
- [ ] 准备了 6–8 个 STAR 故事（协作、冲突、失败、生产事故、跨团队、跨时区）
