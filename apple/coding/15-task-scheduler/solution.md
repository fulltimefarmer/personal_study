# Task Scheduler — 考点分析与解题思路

## 考点分析

1. **贪心 + 公式推导**：核心洞察是——时间下限由「出现次数最多的任务」决定。设出现次数最多的任务出现了 `maxCount` 次，共有 `numMax` 个任务并列最频繁。这些任务之间必须隔 `n` 个单位，形成 `(maxCount - 1)` 个「帧」，每帧长度 `n + 1`。
2. **公式法**：`answer = max(tasks.length, (maxCount - 1) * (n + 1) + numMax)`。
   - 前一项：所有「帧」填满 + 最后一轮并列最多任务排开；
   - 取 `max(tasks.length, ...)`：若任务种类足够多，能把空隙填满而不产生空闲，则答案就是任务总数。
3. **模拟法（更通用）**：用最大堆维护各任务剩余次数，配合冷却队列，逐单位时间模拟。适合 `n` 大、任务种类多且需要「打印具体顺序」的场景，但时间复杂度较高。
4. **边界**：`n = 0`（无冷却）、单种任务、多种任务并列最多。

## 解题思路

### 方案 A：公式法（推荐）

1. 统计每个任务出现次数，得 `maxCount` 与并列最多的数量 `numMax`。
2. 计算 `(maxCount - 1) * (n + 1) + numMax`，与 `tasks.length` 取较大者。

### 方案 B：最大堆 + 冷却队列模拟

- 建最大堆（按剩余次数），每单位时间取堆顶执行，次数减一后放入冷却队列，冷却期满再回堆；若堆空但有任务在冷却，则计入「空闲」。

## 复杂度

- 方案 A：时间 O(N)（统计），空间 O(1)（26 个字母）。
- 方案 B：时间 O(T·log 26)，T 为总时间。

## 参考代码（公式法）

```ts
function leastInterval(tasks: string[], n: number): number {
  const freq = new Array<number>(26).fill(0);
  for (const t of tasks) {
    freq[t.charCodeAt(0) - 65]++;
  }

  const maxCount = Math.max(...freq);
  const numMax = freq.filter(f => f === maxCount).length;

  return Math.max(tasks.length, (maxCount - 1) * (n + 1) + numMax);
}
```

## 追问 / Follow-ups

1. **要求输出一个具体的最优执行顺序**（而非仅时间）？→ 用最大堆 + 冷却队列模拟，按轮（每轮 `n+1`）依次取出现次数最多的任务执行。
2. **每种任务的冷却时间不同**（`n` 因任务而异）？→ 公式法不再适用，改用堆 + 各自冷却时间的模拟。
3. **分布式/多 CPU 并行调度**？→ 转化为区间/装箱问题，需讨论贪心的最优性边界。
