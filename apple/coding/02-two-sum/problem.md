# Two Sum · 两数之和

- **LeetCode:** 1
- **难度 Difficulty:** Easy
- **标签 Topics:** 数组 / 哈希表 / Array / Hash Table
- **苹果频率:** 高频（Apple #2）

## 题干（中文）

给定一个整数数组 `nums` 和一个目标值 `target`，请你在数组中找出**和为目标值**的那两个整数，并返回它们的数组下标。

你可以假设每种输入只会对应一个答案，且同一个元素不能使用两次。返回顺序不限。

## Problem Statement (English)

Given an array of integers `nums` and an integer `target`, return the indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice. Return the answer in any order.

## 示例 / Examples

```
输入 / Input:  nums = [2,7,11,15], target = 9
输出 / Output: [0,1]     // 2 + 7 = 9

输入 / Input:  nums = [3,2,4], target = 6
输出 / Output: [1,2]     // 2 + 4 = 6

输入 / Input:  nums = [3,3], target = 6
输出 / Output: [0,1]     // 重复元素也适用
```

## 约束 / Constraints

- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i] <= 10^9`
- `-10^9 <= target <= 10^9`
- 有且仅有一个有效答案
