# Top K Frequent Elements · 前 K 个高频元素

- **LeetCode:** 347
- **难度 Difficulty:** Medium
- **标签 Topics:** 哈希表 / 堆 / 桶排序 / Hash Table / Heap / Bucket Sort
- **苹果频率:** 高频（Apple #20）

## 题干（中文）

给你一个整数数组 `nums` 和一个整数 `k`，请你返回其中出现频率**前 `k` 高**的元素。你可以按任意顺序返回答案。

## Problem Statement (English)

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. You may return the answer in any order.

## 示例 / Examples

```
输入 / Input:  nums = [1,1,1,2,2,3], k = 2
输出 / Output: [1,2]

输入 / Input:  nums = [1], k = 1
输出 / Output: [1]
```

## 约束 / Constraints

- `1 <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `k` 的取值范围是 `[1, 数组中不相同的元素的个数]`
- 题目数据保证答案唯一；换句话说，前 `k` 个高频元素的集合是唯一的
