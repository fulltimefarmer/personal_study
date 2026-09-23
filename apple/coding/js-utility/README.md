# JS/TS 手写实现题 · Mock Practical Coding Questions（非算法）

> 本目录包含 5 道**非算法类**编程题——JS/TypeScript 手写工具函数/实现题。
> 来源：frontendinterviewhandbook（Apple 专区）、Apple 全栈/前端面经（PracHub、Frontend Junction、interviewexperiences.in）、interviewkickstart 等 2026 数据汇总。
> 与本岗位 JD（Node.js/TypeScript 全栈）高度相关，Apple 面试中常与算法题并行出现。
>
> 每题一个文件夹，含三个文件：
> - `problem.md` — 题干（中英双语）
> - `solution.md` — 解答（考点分析 + 思路 + 参考代码 + 复杂度 + 追问）
> - `solution.ts` — 代码空壳（函数签名 + 测试骨架，可直接用 `bun run solution.ts` 验证）

## 题目清单 / Problem Index

| # | 题目 | 类型 | 核心考点 | 难度 |
| --- | --- | --- | --- | --- |
| 01 | Debounce | 工具函数 | 闭包 / 定时器 / leading+trailing / cancel | Easy |
| 02 | Throttle | 工具函数 | 闭包 / 定时器 / 固定节奏触发 | Easy |
| 03 | Promise.all | 手写 Polyfill | Promise / 结果有序 / fail-fast | Medium |
| 04 | Event Emitter | 手写实现 | 观察者模式 / Set / once / 快照遍历 | Medium |
| 05 | Flatten Array | 手写实现 | 递归 / 深度控制 / Array.prototype.flat | Easy |

## 答题建议 / Interview Tips

1. 先**澄清需求**：是否需要 leading/trailing、是否要 cancel、`this` 与返回值是否保留、深度默认值等。
2. 讲清**闭包、事件循环（宏任务/微任务）**——Apple 前端/全栈面试格外看重 JS 运行机制。
3. 主动讨论边界（空输入、并发顺序、emit 中删除监听器）与 trade-off。
4. 每题 15–25 分钟；这些题适合做算法题的「热身」或作为 phone screen 的独立一轮。

## 苹果非算法题常见清单（速查）

据 frontendinterviewhandbook（Apple 专区）与多篇面经，除本目录 5 题外，还常出现：

- 手写 `Array.prototype.map / reduce / filter / concat`（注意稀疏数组、`thisArg`）
- `Function.prototype.bind / call / apply`
- 深拷贝 `cloneDeep`、深比较 `deepEqual`
- 顺序执行 promise 数组 / 并发限流（mapAsync）
- `memoize`（缓存）、`curry`（柯里化）
- DOM：`getElementByClassName`、事件委托
- React/Angular 组件：可折叠组件、分页表格、层级树（文件结构/员工汇报关系）、自动补全搜索框

> 组件类题目依赖框架环境，本目录以**框架无关、可直接运行的 TS** 为主；如需 React/Angular 组件题可另行补充。
