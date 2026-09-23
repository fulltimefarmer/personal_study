# Valid Parentheses · 有效的括号

- **LeetCode:** 20
- **难度 Difficulty:** Easy
- **标签 Topics:** 字符串 / 栈 / String / Stack
- **苹果频率:** 高频（Apple Top 100 #13，常见热身题）

## 题干（中文）

给定一个只包括 `'('`、`')'`、`'{'`、`'}'`、`'['`、`']'` 的字符串 `s`，判断字符串是否有效。

有效字符串需满足：

1. 左括号必须用**相同类型**的右括号闭合。
2. 左括号必须以**正确的顺序**闭合。
3. 每个右括号都有一个对应的相同类型的左括号。

## Problem Statement (English)

Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:

1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

## 示例 / Examples

```
输入 / Input:  s = "()"
输出 / Output: true

输入 / Input:  s = "()[]{}"
输出 / Output: true

输入 / Input:  s = "(]"
输出 / Output: false

输入 / Input:  s = "([)]"
输出 / Output: false

输入 / Input:  s = "{[]}"
输出 / Output: true
```

## 约束 / Constraints

- `1 <= s.length <= 10^4`
- `s` 仅由括号 `'()[]{}'` 组成
