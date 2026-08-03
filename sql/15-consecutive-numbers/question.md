
# 第 15 题：连续出现的数字

## 题目描述

有一张 `Logs` 表，记录数字出现的顺序：

| 列名 | 类型    | 说明           |
|------|---------|----------------|
| id   | INT     | 主键，自增ID（视为顺序） |
| num  | VARCHAR | 数字（字符串格式） |

请编写 SQL，找出所有**至少连续出现 3 次**的数字。返回的结果表中的每一列不需要排序，去重即可。

### 示例

**输入：**

| id | num |
|----|-----|
| 1  | 1   |
| 2  | 1   |
| 3  | 1   |
| 4  | 2   |
| 5  | 1   |
| 6  | 2   |
| 7  | 2   |

**输出：**

| ConsecutiveNums |
|-----------------|
| 1               |

**解释：** 数字 1 在 id=1,2,3 处连续出现 3 次，符合条件。后面 id=5 处的 1 只有一次，不连续。数字 2 在 id=6,7 只出现了 2 次，不符合。

## 考察点

- 窗口函数 `LAG()` / `LEAD()` 进行前后行比较
- 自连接（连续条件 `id` 差值为 1）
- GAP/ISLAND 问题的入门

## 解题思路

### 思路一：LAG() 窗口函数（推荐）

```sql
SELECT DISTINCT num AS "ConsecutiveNums"
FROM (
    SELECT num,
           LAG(num, 1) OVER (ORDER BY id) AS prev1,
           LAG(num, 2) OVER (ORDER BY id) AS prev2
    FROM Logs
) t
WHERE num = prev1 AND num = prev2;
```

`LAG(num, 1)` 取上一行的 num，`LAG(num, 2)` 取上两行的 num。如果当前行的 num 等于前两行的 num，说明连续出现了 3 次。

### 思路二：自连接

```sql
SELECT DISTINCT l1.num AS "ConsecutiveNums"
FROM Logs l1
JOIN Logs l2 ON l1.id = l2.id - 1 AND l1.num = l2.num
JOIN Logs l3 ON l2.id = l3.id - 1 AND l2.num = l3.num;
```

将表本身连接三次：`l1`、`l2`、`l3` 分别代表连续三行。条件是 ID 连续（差值为 1）且数字相同。

### 对比

| 方式       | 优点                 | 缺点               |
|-----------|---------------------|--------------------|
| LAG()     | 简洁清晰，容易扩展到 N 次 | 需要窗口函数支持   |
| 自连接     | 不需要窗口函数，兼容性好 | 连续 N 次需要 N-1 次连接 |

### 扩展

- 如果需要找**至少连续出现 N 次**的数字，`LAG` 解法需要 N-1 个 `LAG`，但可以配合 CTE + `COUNT(*) OVER` 的 GAP/ISLAND 解法
- 本题是 GAP/ISLAND 问题的简化版，更复杂的场景（如连续登录天数）需要用到分组技巧
