# Task Scheduler · 任务调度器

- **LeetCode:** 621
- **难度 Difficulty:** Medium
- **标签 Topics:** 贪心 / 计数 / 堆 / 队列 / Greedy / Counting / Heap / Queue
- **苹果频率:** 高频（调度类经典题，考查贪心与公式推导）

## 题干（中文）

给你一个用字符数组 `tasks` 表示的 CPU 需要执行的任务列表，其中每个字母表示一种任务。任务可以以任意顺序执行，每个单位时间执行一个任务。在任意两个**相同种类**的任务之间，必须有长度为整数 `n` 的冷却时间（即两个相同任务之间至少要间隔 `n` 个单位时间）。

你需要计算完成所有任务所需要的**最短时间**。

## Problem Statement (English)

Given a character array `tasks`, representing the tasks a CPU needs to do, where each letter represents a different kind of task. Tasks can be done in any order. There is a non-negative integer `n` that represents the cooldown period between two **same tasks** (the CPU must idle for at least `n` units between them).

Return the **least number of units of time** the CPU will take to finish all the given tasks.

## 示例 / Examples

```
输入 / Input:  tasks = ["A","A","A","B","B","B"], n = 2
输出 / Output: 8
// 执行顺序：A -> B -> 空闲 -> A -> B -> 空闲 -> A -> B

输入 / Input:  tasks = ["A","A","A","B","B","B"], n = 0
输出 / Output: 6
// n=0 时无冷却，直接顺序执行即可

输入 / Input:  tasks = ["A","A","A","A","A","A","B","C","D","E","F","G"], n = 2
输出 / Output: 16
// 一种最优解：A -> B -> C -> A -> D -> E -> A -> F -> G -> A -> 空闲 -> 空闲 -> A -> 空闲 -> 空闲 -> A
```

## 约束 / Constraints

- `1 <= task.length <= 10^4`
- `tasks[i]` 是大写英文字母
- `0 <= n <= 100`
