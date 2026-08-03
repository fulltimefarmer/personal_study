# LeetCode 6. Zigzag Conversion（Z字形变换）

## 考点
String

## 题目描述
将一个给定字符串 `s` 根据给定的行数 `numRows`，以从上往下、从左到右进行 Z 字形排列。

比如输入字符串为 `"PAYPALISHIRING"` 行数为 3 时，排列如下：
```
P   A   H   N
A P L S I I G
Y   I   R
```

之后，你的输出需要从左往右逐行读取，产生出一个新的字符串，比如：`"PAHNAPLSIIGYIR"`。

### 示例 1
```
输入：s = "PAYPALISHIRING", numRows = 3
输出："PAHNAPLSIIGYIR"
```

### 示例 2
```
输入：s = "PAYPALISHIRING", numRows = 4
输出："PINALSIGYAHRPI"
解释：
P     I    N
A   L S  I G
Y A   H R
P     I
```

### 约束
- `1 <= s.length <= 1000`
- `s` 由英文字母（小写和大写）、',' 和 '.' 组成
- `1 <= numRows <= 1000`

## 解题思路

### 方法：按行模拟
核心思想：使用 `numRows` 个字符串构建器，遍历原字符串，按 Z 字形顺序将字符放入对应行，最后拼接所有行。

**步骤：**
1. 如果 `numRows === 1`，直接返回 `s`。
2. 创建长度为 `numRows` 的字符串数组 `rows`。
3. 使用 `curRow` 记录当前行号，`goingDown` 表示方向（向下为 true）。
4. 遍历字符串每个字符：
   - 将当前字符追加到 `rows[curRow]`。
   - 如果 `curRow === 0`，方向改为向下。
   - 如果 `curRow === numRows - 1`，方向改为向上。
   - 根据方向更新 `curRow += goingDown ? 1 : -1`。
5. 拼接所有行并返回。

**关键点：**
- Z 字形遍历的本质是在 `[0, numRows-1]` 之间来回移动。
- `numRows === 1` 时需要特殊处理，否则会出现死循环。
- 时间复杂度 O(n)，每个字符只处理一次。

时间复杂度：O(n)
空间复杂度：O(n)（存储结果）
