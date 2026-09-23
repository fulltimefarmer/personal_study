# 3Sum · 三数之和

- **LeetCode:** 15
- **难度 Difficulty:** Medium
- **标签 Topics:** 数组 / 双指针 / 排序 / Array / Two Pointers / Sorting
- **苹果频率:** 高频（Apple Top 100 #3，双指针经典）

## 题干（中文）

给你一个整数数组 `nums`，判断是否存在三元组 `[nums[i], nums[j], nums[k]]` 满足 `i != j`、`i != k` 且 `j != k`，同时 `nums[i] + nums[j] + nums[k] == 0`。请你返回**所有和为 0 且不重复**的三元组。

注意：答案中**不可以包含重复**的三元组。

## Problem Statement (English)

Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.

Notice that the solution set must not contain duplicate triplets.

## 示例 / Examples

```
输入 / Input:  nums = [-1,0,1,2,-1,-4]
输出 / Output: [[-1,-1,2],[-1,0,1]]
// 解释：nums[0]+nums[1]+nums[2]=0, nums[1]+nums[2]+nums[4]=0, nums[0]+nums[3]+nums[4]=0
// 但 [-1,0,1] 重复，只保留一份。

输入 / Input:  nums = [0,1,1]
输出 / Output: []

输入 / Input:  nums = [0,0,0]
输出 / Output: [[0,0,0]]
```

## 约束 / Constraints

- `3 <= nums.length <= 3000`
- `-10^5 <= nums[i] <= 10^5`
