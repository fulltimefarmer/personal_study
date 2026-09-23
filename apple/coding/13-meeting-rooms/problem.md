# Meeting Rooms · 会议室

- **LeetCode:** 252
- **难度 Difficulty:** Easy
- **标签 Topics:** 数组 / 排序 / 区间 / Array / Sorting / Intervals
- **苹果频率:** 高频（区间类经典热身题，常作 Merge Intervals 的姊妹题）

## 题干（中文）

给定一个会议时间安排的数组 `intervals`，每个会议时间都包括开始和结束时间 `intervals[i] = [startᵢ, endᵢ]`，请你判断一个人**是否能参加这里面的全部会议**（即任意两个会议之间不存在时间重叠）。

## Problem Statement (English)

Given an array of meeting time `intervals` where `intervals[i] = [startᵢ, endᵢ]`, determine if a person could attend all meetings (i.e., no two meetings overlap).

## 示例 / Examples

```
输入 / Input:  intervals = [[0,30],[5,10],[15,20]]
输出 / Output: false
// [0,30] 与 [5,10] 重叠

输入 / Input:  intervals = [[7,10],[2,4]]
输出 / Output: true
```

## 约束 / Constraints

- `0 <= intervals.length <= 10^4`
- `intervals[i].length == 2`
- `0 <= startᵢ < endᵢ <= 10^6`

## 注意 / Note

会议 `[1,4]` 与 `[4,5]` **不重叠**（结束时间等于下一场开始时间可接受）。
