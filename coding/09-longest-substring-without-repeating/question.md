# 第 9 题：无重复字符的最长子串（Longest Substring Without Repeating Characters）

## 题目描述

给定一个字符串 `s`，请你找出其中不含有重复字符的**最长子串**的长度。

### 示例

```text
s = "abcabcbb"   -> 3    # "abc"
s = "bbbbb"      -> 1    # "b"
s = "pwwkew"     -> 3    # "wke"（"pwke" 是子序列，不是子串）
```

## 考察点

- 滑动窗口（双指针）
- 哈希表记录字符最近一次出现的位置

## 解题思路

维护一个窗口 `[left, right]`，保证窗口内无重复字符：

1. 用哈希表 `char_index` 记录每个字符**最近一次**出现的下标。
2. 右指针 `right` 向右扩张，若字符 `s[right]` 上次出现位置 `>= left`，说明重复，左指针跳到 `char_index[ch] + 1`。
3. 更新 `char_index[ch] = right`，并用 `right - left + 1` 更新最长长度。

### 复杂度

| 项 | 复杂度 |
|----|--------|
| 时间复杂度 | O(n)，每个字符至多访问一次 |
| 空间复杂度 | O(min(n, m))，m 为字符集大小 |
