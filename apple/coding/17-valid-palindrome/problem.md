# Valid Palindrome · 验证回文串

- **LeetCode:** 125
- **难度 Difficulty:** Easy
- **标签 Topics:** 双指针 / 字符串 / Two Pointers / String
- **苹果频率:** 高频（Apple Top 100，字符串 + 双指针热身题）

## 题干（中文）

如果在将所有大写字母转换为小写字母、并移除所有**非字母数字字符**之后，短语正着读和反着读都一样，则认为该短语是一个**回文串**。

给定一个字符串 `s`，如果它是回文串，返回 `true`；否则返回 `false`。

## Problem Statement (English)

A phrase is a **palindrome** if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string `s`, return `true` if it is a palindrome, or `false` otherwise.

## 示例 / Examples

```
输入 / Input:  s = "A man, a plan, a canal: Panama"
输出 / Output: true
// 规范化后："amanaplanacanalpanama" 是回文。

输入 / Input:  s = "race a car"
输出 / Output: false

输入 / Input:  s = " "
输出 / Output: true
// 移除所有非字母数字字符后是空串 ""，空串是回文。
```

## 约束 / Constraints

- `1 <= s.length <= 2 * 10^5`
- `s` 仅由可打印的 ASCII 字符组成
