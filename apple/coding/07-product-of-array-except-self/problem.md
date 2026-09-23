# Product of Array Except Self · 除自身以外数组的乘积

- **LeetCode:** 238
- **难度 Difficulty:** Medium
- **标签 Topics:** 数组 / 前缀积 / Array / Prefix Sum
- **苹果频率:** 高频（Apple #19）

## 题干（中文）

给你一个整数数组 `nums`，返回数组 `answer`，其中 `answer[i]` 等于 `nums` 中除 `nums[i]` 之外其余各元素的乘积。

题目数据保证数组 `nums` 中任意元素的全部**前缀**元素和后缀的乘积都在 32 位整数范围内。

请**不要使用除法**，且在 **O(n)** 时间内完成，并尽量只使用**常数额外空间**（输出数组不计入额外空间）。

## Problem Statement (English)

Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product of all the elements of `nums` except `nums[i]`.

The product of any prefix or suffix of `nums` is **guaranteed to fit in a 32-bit integer**.

You must write an algorithm that runs in **O(n)** time and **without using the division** operation.

## 示例 / Examples

```
输入 / Input:  nums = [1,2,3,4]
输出 / Output: [24,12,8,6]

输入 / Input:  nums = [-1,1,0,-3,3]
输出 / Output: [0,0,9,0,0]
```

## 约束 / Constraints

- `2 <= nums.length <= 10^5`
- `-30 <= nums[i] <= 30`
- 保证乘积在 32 位整数范围内（不含除自身后的结果）
