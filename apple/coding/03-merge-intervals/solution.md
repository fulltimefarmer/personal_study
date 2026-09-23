# Merge Intervals — 考点分析与解题思路

## 考点分析

1. **排序是区间问题的第一步**：区间重叠判断依赖相对位置，先按 `start` 升序排序，使「可能重叠的区间」相邻，问题退化为线性扫描。
2. **贪心合并**：维护结果数组，逐个判断「当前区间是否与结果最后一项重叠」，重叠则扩大 `end`，否则追加。这是「贪心 + 一次扫描」的经典模式。
3. **重叠判定**：排序后只需判断 `current.start <= last.end`（因为 `last.start <= current.start` 已由排序保证）。
4. **边界**：首尾相接（`[1,4]` 与 `[4,5]` 要合并成 `[1,5]`，用 `<=`）；空数组/单区间；`start` 相同但 `end` 不同；负数区间。
5. **Apple 电商场景**：合并员工排班、门店营业时段、促销时段、会议时间，是内部工具的真实需求。

## 解题思路

1. 若 `intervals.length <= 1` 直接返回。
2. 按 `start` 升序排序（注意 `a[0] - b[0]` 数值相减）。
3. 初始化 `result = [intervals[0]]`。
4. 从 `i = 1` 遍历：
   - 取 `last = result[result.length - 1]`、`[start, end] = intervals[i]`。
   - 若 `start <= last[1]`：重叠 → `last[1] = max(last[1], end)`。
   - 否则：追加 `[start, end]`。
5. 返回 `result`。

## 复杂度

- 时间：O(n log n)，排序主导。
- 空间：O(n)，结果数组（或 O(log n) 若忽略结果、只算排序栈）。

## 参考代码

```ts
function merge(intervals: number[][]): number[][] {
  if (intervals.length <= 1) return intervals;

  intervals.sort((a, b) => a[0] - b[0]);   // 按 start 升序

  const result: number[][] = [intervals[0]];

  for (let i = 1; i < intervals.length; i++) {
    const last = result[result.length - 1];
    const [start, end] = intervals[i];

    if (start <= last[1]) {                 // 重叠 → 合并
      last[1] = Math.max(last[1], end);
    } else {                                // 不重叠 → 追加
      result.push([start, end]);
    }
  }

  return result;
}
```

## 追问 / Follow-ups

1. **插入区间**（LeetCode 57）：给定一个新区间插入到已排序不重叠列表 → 先定位再合并，一次遍历。
2. **区间数量极大无法载入内存** → 外部排序 / 按 start 分桶流式合并。
3. **判断某个时刻是否被覆盖** → 合并后二分查找落在哪个区间。
4. **会议室 II**（最少需要几个会议室，LeetCode 253）→ 把 start/end 分别排序，用扫描线（start 需要新房间，end 释放房间）。
5. **区间交集**（LeetCode 986）→ 双指针求两列表的公共交集。
