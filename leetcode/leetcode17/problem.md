# LeetCode 17. Letter Combinations of a Phone Number（电话号码的字母组合）

## 考点
Hash Table, String, Backtracking

## 题目描述
给定一个仅包含数字 `2-9` 的字符串，返回所有它能表示的字母组合。答案可以按任意顺序返回。

手机按键映射：
```
2: abc, 3: def, 4: ghi, 5: jkl, 6: mno, 7: pqrs, 8: tuv, 9: wxyz
```

### 示例 1
```
输入：digits = "23"
输出：["ad","ae","af","bd","be","bf","cd","ce","cf"]
```

### 约束
- `0 <= digits.length <= 4`
- `digits[i]` 是范围 `['2', '9']` 的数字

## 解题思路

### 方法：回溯
核心思想：DFS 遍历所有数字对应的字母组合，构建路径，到达末尾时加入结果。

**步骤：**
1. 建立数字到字母的映射表。
2. 递归回溯函数 `backtrack(index, path)`：
   - 如果 `index === digits.length`，将当前 `path` 加入结果并返回。
   - 获取 `digits[index]` 对应的字母列表。
   - 遍历每个字母，将其加入 `path`，递归处理下一个数字。
3. 从 `backtrack(0, "")` 开始。

**关键点：**
- 回溯本质上是多叉树的 DFS。
- 输入为空时返回 `[]`。
- 回溯时用字符串拼接即可，不需要显式撤销操作（因为字符串不可变，每次都创建新字符串）。

时间复杂度：O(4^n)，n 是 digits 长度（最坏情况每位有 4 个字母）
空间复杂度：O(n)（递归栈深度）
