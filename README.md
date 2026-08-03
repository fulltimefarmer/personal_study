# Study Algorithms & System Design

个人面试准备知识库，涵盖算法、数据结构、SQL、系统设计、计算机基础与 Java 工程实践。

---

## 目录结构

```
personal_study/
├── coding/              # Java 编程面试题（Maven）
├── fundamentals/        # 计算机基础知识笔记
├── leetcode/            # LeetCode 题解（Python + TypeScript）
├── sql/                 # SQL 题解
└── system-design/       # 系统设计题解
```

---

## 模块概览

### coding/ — Java 编程面试题

10 道生产级 Java 面试题，Maven 项目，JUnit 5 测试。

| # | 题目 | 领域 |
|---|------|------|
| 1 | LRU Cache | 数据结构（HashMap + 双向链表） |
| 2 | 线程安全有界阻塞队列 | 并发（ReentrantLock + Condition） |
| 3 | 带 TTL 的内存 KV 存储 | 存储引擎 |
| 4 | 文本左右对齐 | 字符串 / 贪心 |
| 5 | 滑动窗口限流器 | 分布式系统 |
| 6 | 大文件词频统计 Top-K | 大数据 / 堆 |
| 7 | 线程安全连接池 | 并发 / 资源管理 |
| 8 | 事件总线 | 设计模式（观察者） |
| 9 | 简易 JSON 解析器 | 编译原理（递归下降） |
| 10 | 延时任务调度器 | 并发（PriorityBlockingQueue） |

```bash
cd coding
mvn test
```

**技术栈：** Java 17, Maven, JUnit Jupiter 5.10

---

### fundamentals/ — 计算机基础知识

16 篇笔记，覆盖 4 个方向：

| 方向 | 主题 |
|------|------|
| **Database** | 索引原理、事务隔离、SQL vs NoSQL、Redis 数据结构 |
| **Network** | OSI vs TCP/IP、TCP vs UDP、HTTP vs HTTPS、负载均衡 |
| **OOP** | 四大特性、抽象类 vs 接口、单例模式、SOLID 原则、不可变对象 |
| **OS** | 进程 vs 线程、死锁、同步 |

---

### leetcode/ — LeetCode 题解

**261 道不重复题目**，双语言实现，含滑动窗口指针移动图解。

```
leetcode/
├── leecode1/        # 含 problem.md + solution.py + solution.ts
├── leecode2/        #   (198 个目录，Python + TypeScript 双语言)
├── ...
├── leetcode1/       # 含 solution.ts
├── leetcode2/       #   (98 个目录，仅 TypeScript)
├── ...
├── package.json     # TypeScript 5.9 / ES2022 / strict
├── tsconfig.json
├── pyproject.toml   # Python >=3.12
└── .python-version
```

**运行方式：**

```bash
cd leetcode

# Python 题解
python leecode3/solution.py

# TypeScript 题解（类型检查）
npx tsc --noEmit
```

**技术栈：** Python 3.12（uv）, TypeScript 5.9（strict mode）
**图解说明：** 滑动窗口类题目的 `problem.md` 中均包含 Mermaid 指针移动图解。

---

### sql/ — SQL 题解

30 道 SQL 题，覆盖常见面试场景。每题含 `question.md` + `solution.sql`。

| 典型题目 |
|----------|
| Second / Nth Highest Salary |
| Consecutive Numbers / Consecutive Login Days |
| Department Highest Salary |
| Trips Cancellation Rate |
| Cumulative Sales |
| User Behavior Funnel |
| Recursive Org Tree |

---

### system-design/ — 系统设计题解

4 个完整设计方案，每个包含需求澄清、API 设计、数据模型、架构图、扩展方案。

| 题目 | 设计要点 |
|------|---------|
| URL Shortener | 短链生成算法、Base62、分库分表 |
| Rate Limiter | 令牌桶 vs 滑动窗口、Redis + Lua |
| Key-Value Store | LSM-Tree、一致性哈希、CAP 取舍 |
| File Storage System | 分块上传、去重、副本策略 |

每个方案均包含 ASCII 架构图和分步骤设计推导。

---

## 技术栈总览

| 语言 / 工具 | 用途 |
|-------------|------|
| Java 17 | coding/ 编程练习 |
| Python 3.12 | leetcode/ Python 题解 |
| TypeScript 5.9 | leetcode/ TypeScript 题解 |
| SQL | sql/ 数据库题解 |
| Maven + JUnit 5 | Java 构建与测试 |
| Mermaid | 算法图解（滑动窗口指针移动） |

---

## 统计

| 模块 | 数量 |
|------|------|
| Java 编程题 | 10 |
| 基础知识笔记 | 16 |
| LeetCode 题解 | 261 |
| SQL 题解 | 30 |
| 系统设计方案 | 4 |
| **合计** | **321** |
