# Longest Substring Without Repeating Characters · 无重复字符的最长子串

- **LeetCode:** 3
- **难度 Difficulty:** Medium
- **标签 Topics:** 哈希表 / 字符串 / 滑动窗口 / Hash Table / String / Sliding Window
- **苹果频率:** 高频（Apple Top 100 #5，滑动窗口经典题）

## 题干（中文）

给定一个字符串 `s`，请你找出其中**不含有重复字符**的**最长子串**的长度。

## Problem Statement (English)

Given a string `s`, find the length of the **longest substring** without repeating characters.

## 示例 / Examples

```
输入 / Input:  s = "abcabcbb"
输出 / Output: 3
// 最长无重复子串是 "abc"。

输入 / Input:  s = "bbbbb"
输出 / Output: 1

输入 / Input:  s = "pwwkew"
输出 / Output: 3
// 最长无重复子串是 "wke"（"pwke" 是子序列，不是子串）。
```

## 约束 / Constraints

- `0 <= s.length <= 5 * 10^4`
- `s` 由英文字母、数字、符号和空格组成
