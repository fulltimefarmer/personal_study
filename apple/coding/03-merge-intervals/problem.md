# Merge Intervals · 合并重叠区间

- **LeetCode:** 56
- **难度 Difficulty:** Medium
- **标签 Topics:** 数组 / 排序 / Array / Sorting
- **苹果频率:** 高频（Apple #3）

## 题干（中文）

Apple Store 某内部工具需要合并门店的「活动/促销时间段」。给定一个区间数组 `intervals`，其中 `intervals[i] = [start_i, end_i]` 表示一个时间段。请合并所有重叠的区间，返回一个**不重叠**的区间数组，覆盖输入中的所有区间。

两个区间 `[a, b]` 与 `[c, d]` 重叠当且仅当 `a <= d` 且 `c <= b`（首尾相接也算重叠，如 `[1,2]` 与 `[2,3]`）。

## Problem Statement (English)

An internal tool at Apple Store needs to merge "campaign/promotion time slots." Given an array of intervals `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals and return an array of non-overlapping intervals that cover all intervals in the input.

Two intervals `[a, b]` and `[c, d]` overlap if and only if `a <= d` and `c <= b` (touching counts, e.g. `[1,2]` and `[2,3]`).

## 示例 / Examples

```
输入 / Input:  [[1,3],[2,6],[8,10],[15,18]]
输出 / Output: [[1,6],[8,10],[15,18]]

输入 / Input:  [[1,4],[4,5]]
输出 / Output: [[1,5]]
```

## 约束 / Constraints

- `1 <= intervals.length <= 10^4`
- `intervals[i].length == 2`
- `0 <= start_i <= end_i <= 10^4`
