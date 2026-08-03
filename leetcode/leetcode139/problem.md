# LeetCode 139. Word Break（单词拆分）

## 考点
字典树、记忆化搜索、数组、哈希表、字符串、动态规划

## 题目描述
给你一个字符串 `s` 和一个字符串列表 `wordDict` 作为字典。如果可以利用字典中出现的一个或多个单词拼接出 `s` 则返回 `true`。

**注意：** 不要求字典中出现的单词全部都使用，并且字典中的单词可以重复使用。

**示例 1：**
```
输入：s = "leetcode", wordDict = ["leet","code"]
输出：true
解释：返回 true 因为 "leetcode" 可以由 "leet" 和 "code" 拼接成。
```

**示例 2：**
```
输入：s = "applepenapple", wordDict = ["apple","pen"]
输出：true
```

**示例 3：**
```
输入：s = "catsandog", wordDict = ["cats","dog","sand","and","cat"]
输出：false
```

**提示：**
- `1 <= s.length <= 300`
- `1 <= wordDict.length <= 1000`
- `1 <= wordDict[i].length <= 20`
- s 和 wordDict[i] 仅由小写英文字母组成
- wordDict 中的所有字符串互不相同

## 解题思路
**动态规划。**

定义 `dp[i]` 表示 `s[0..i-1]`（前 i 个字符）是否可以被字典中的单词拼接而成。

**初始化：** `dp[0] = true`（空字符串可以被拼接）

**状态转移：**
遍历 `i` 从 `1` 到 `n`：
- 遍历 `j` 从 `0` 到 `i-1`：
  - 如果 `dp[j] === true` 且 `s[j..i-1]` 在字典中，则 `dp[i] = true`

**优化：**
- 将 `wordDict` 转为 `Set` 以实现 O(1) 查找
- 内层循环可以限制在字典中最长单词长度的范围内

**关键点：**
- 单词可以重复使用
- `dp` 数组比 `s` 长度多 1

时间复杂度：O(n²)，n 为 s 的长度（可通过限制单词最大长度优化）  
空间复杂度：O(n + m)，m 为字典单词集合大小
