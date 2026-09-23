# 后端 / 基础设施 / TypeScript 实用题 · Mock Practical Coding Questions（非算法）

> 本目录包含 5 道**非算法类**编程题，覆盖后端、可靠性、缓存、限流与 TypeScript 类型等**分散技术点**（区别于 `../js-utility` 的前端/JS 工具题）。
> 与岗位 JD（Node.js/NestJS/TypeScript/PostgreSQL/AliCloud/RESTful API）高度相关。
>
> 每题一个文件夹，含三个文件：
> - `problem.md` — 题干（中英双语）
> - `solution.md` — 解答（考点分析 + 思路 + 参考代码 + 复杂度 + 追问）
> - `solution.ts` — 代码空壳（签名 + 测试骨架，可用 `bun run solution.ts` 验证）

## 题目清单 / Problem Index

| # | 题目 | 技术点 | 难度 |
| --- | --- | --- | --- |
| 01 | Promise Pool（并发任务池） | 并发控制 / 信号量 | Medium |
| 02 | Retry with Exponential Backoff | 可靠性 / 网络 / 容错 | Medium |
| 03 | In-Memory Cache with TTL | 缓存 / 过期策略 | Easy |
| 04 | Token Bucket Rate Limiter | 限流 / 基础设施 | Medium |
| 05 | DeepPartial（TypeScript 类型） | 泛型 / 映射类型 / 条件类型 | Medium |

## 答题建议 / Interview Tips

1. 先**澄清需求与边界**：并发上限、重试策略（是否幂等）、过期是惰性还是主动、限流模型选型、类型是否需处理数组/函数。
2. 说清**复杂度与 trade-off**（惰性 vs 主动过期、固定窗口 vs 滑动窗口 vs 令牌桶、并发限流 vs 速率限流）。
3. 主动联系**生产实践**：Redis 分布式缓存/限流、断路器、幂等键、AbortSignal 取消。
4. 每题 20–30 分钟；与算法题、前端题一起构成完整 mock 题库。

## 可扩展方向（速查）

- **Node.js**：流与背压（backpressure）、优雅关闭、`AbortController` 取消
- **API 设计**：幂等键、分页（cursor vs offset）、版本化、`Retry-After`/`429`
- **数据库**：连接池、事务隔离、N+1 问题
- **基础设施**：断路器（circuit breaker）、滑动窗口限流、分布式锁（Redis）
- **TypeScript**：`DeepReadonly`/`DeepRequired`、`PickByValue`、条件类型工具
