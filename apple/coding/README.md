# CoderPad 模拟编程题 · Mock Coding Questions

> 本目录包含 8 道基于**苹果高频题库**（据 LeetCode 标签 + 候选者反馈，2026）与**本岗位 JD**（Node.js/TypeScript 全栈）精选的编程题。
> 每题一个文件夹，含三个文件：
> - `problem.md` — 题干（中英双语）
> - `solution.md` — 解答（中文考点分析 + 解题思路 + 参考代码 + 复杂度 + 追问）
> - `solution.ts` — 代码空壳（预生成函数签名、类型与测试骨架，供 CoderPad 直接填充）

## 题目清单 / Problem Index

| # | 题目 | LeetCode | 模式 | 难度 | 频率 |
| --- | --- | --- | --- | --- | --- |
| 01 | LRU Cache | 146 | 设计 + 哈希 + 双向链表 | Medium | 最高频 |
| 02 | Two Sum | 1 | 哈希表 | Easy | 高频 |
| 03 | Merge Intervals | 56 | 排序 | Medium | 高频 |
| 04 | Number of Islands | 200 | 图 DFS/BFS | Medium | 高频 |
| 05 | Group Anagrams | 49 | 哈希/计数 | Medium | 高频 |
| 06 | Course Schedule | 207 | 图拓扑排序/判环 | Medium | 高频 |
| 07 | Product of Array Except Self | 238 | 前缀积 | Medium | 高频 |
| 08 | Top K Frequent Elements | 347 | 堆/桶排序 | Medium | 高频 |

## 答题建议 / Interview Tips

1. 先**复述题目 + 澄清边界**（输入规模、重复元素、原地与否）。
2. 说清**思路与复杂度**再动手写代码（Apple 看重沟通与思路，而非只跑通）。
3. 主动跑测试用例、处理边界、谈 trade-off。
4. 每题 30–45 分钟；先自己做 → 看 `solution.md` → 复述 → 重写一遍。

## 苹果高频题速查 / Apple High-Frequency Cheat Sheet

据 crackedprep（303 题）、dsaprep（375 题）、PracHub、Exponent 等 2026 数据汇总：

| 题目 | 难度 | 核心思路 |
| --- | --- | --- |
| LRU Cache | Medium | 哈希表 + 双向链表（或 `Map` 顺序） |
| Two Sum | Easy | 哈希表一次遍历 |
| Merge Intervals | Medium | 排序 + 线性合并 |
| Number of Islands | Medium | DFS/BFS 淹没陆地 |
| Group Anagrams | Medium | 排序/计数作为 key |
| Course Schedule I/II | Medium | 拓扑排序 / DFS 判环 |
| Product of Array Except Self | Medium | 左右前缀积 |
| Top K Frequent Elements | Medium | 哈希计数 + 堆/桶 |
| Reverse Linked List | Easy | 迭代三指针 |
| Valid Parentheses | Easy | 栈匹配 |
| 3Sum | Medium | 排序 + 双指针 |
| Clone Graph | Medium | DFS/BFS + visited 哈希 |
| Meeting Rooms | Easy | 排序比较 |
| Design Hit Counter | Medium | 队列/时间戳 |
| Task Scheduler | Medium | 贪心/计数 |
| Best Time to Buy and Sell Stock | Easy | 前缀最小值 |
| Valid Palindrome | Easy | 双指针 |
| Longest Substring Without Repeating Characters | Medium | 滑动窗口 |

**高频模式占比：** Array 49%、String 27%、Hash Table 18%、DP 18%、Two Pointers 17%、Math 14%、Linked List 11%、Sorting/DFS/Tree 各约 10%。
