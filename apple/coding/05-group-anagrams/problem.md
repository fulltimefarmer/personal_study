# Group Anagrams · 字母异位词分组

- **LeetCode:** 49
- **难度 Difficulty:** Medium
- **标签 Topics:** 哈希表 / 字符串 / 计数 / Hash Table / String
- **苹果频率:** 高频（Apple #10）

## 题干（中文）

给你一个字符串数组，请你将**字母异位词**组合在一起。可以按任意顺序返回结果列表。

字母异位词是由重新排列源单词的所有字母得到的一个新单词（即两个字符串包含的每个字符及出现次数完全相同，只是顺序可能不同）。

## Problem Statement (English)

Given an array of strings `strs`, group the **anagrams** together. You can return the answer in any order.

An anagram is a word or phrase formed by rearranging the letters of a different word or phrase, using all the original letters exactly once.

## 示例 / Examples

```
输入 / Input:  strs = ["eat","tea","tan","ate","nat","bat"]
输出 / Output: [["bat"],["nat","tan"],["ate","eat","tea"]]

输入 / Input:  strs = [""]
输出 / Output: [[""]]

输入 / Input:  strs = ["a"]
输出 / Output: [["a"]]
```

## 约束 / Constraints

- `1 <= strs.length <= 10^4`
- `0 <= strs[i].length <= 100`
- `strs[i]` 仅包含小写英文字母
