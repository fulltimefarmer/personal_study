# Meeting Rooms — 考点分析与解题思路

## 考点分析

1. **区间排序**：判断是否有重叠，最直观的思路是按**开始时间升序**排序，然后检查相邻两个区间：若当前区间开始时间 < 上一个区间结束时间，即重叠。
2. **正确性**：排序后，若存在任意重叠，它必然出现在相邻区间之间（否则跨越的区间也必然先与中间区间重叠）。
3. **边界**：`[1,4]` 与 `[4,5]` 不算重叠（`>=` 判断）；空数组与单区间直接返回 `true`。

## 解题思路

- 按 `start` 升序排序 `intervals`。
- 从第二个区间开始，比较 `intervals[i][0]`（当前开始）与 `intervals[i - 1][1]`（前一结束）：
  - 若 `<`，说明重叠，返回 `false`。
- 全部无重叠，返回 `true`。

## 复杂度

- 时间：O(n log n)，排序主导。
- 空间：O(1)（原地排序；若需保留原数组则 O(n)）。

## 参考代码

```ts
function canAttendMeetings(intervals: number[][]): boolean {
  intervals.sort((a, b) => a[0] - b[0]);
  for (let i = 1; i < intervals.length; i++) {
    if (intervals[i][0] < intervals[i - 1][1]) {
      return false;
    }
  }
  return true;
}
```

## 追问 / Follow-ups

1. **Meeting Rooms II**（LeetCode 253）：至少需要几间会议室？→ 把开始/结束时间分别排序，双指针扫描；或按开始时间扫描 + 最小堆维护最早结束。
2. **区间能否合并**（LeetCode 56 Merge Intervals）：→ 排序 + 线性合并（本目录 03 题）。
3. **插入新区间**（LeetCode 57 Insert Interval）：→ 定位到不重叠区段后合并插入。
