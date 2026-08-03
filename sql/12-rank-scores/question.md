
# 第 12 题：分数排名

## 题目描述

有一张 `Scores` 表，记录学生的考试成绩：

| 列名  | 类型    | 说明       |
|-------|---------|------------|
| id    | INT     | 主键       |
| score | DECIMAL | 考试分数（可以是小数） |

请编写 SQL 查询，对分数进行排名。排名规则如下：
- 分数按从高到低排序
- 如果两个分数相同，则排名相同
- 相同分数后，下一个排名应该是**连续的**（即 `DENSE_RANK` 语义）

例如，分数为 `[100, 100, 90]` 时，排名应为 `[1, 1, 2]`，而不是 `[1, 1, 3]`。

输出结果应包含 `score`（分数）和 `rank`（排名），按分数降序排列。

### 示例

**输入：**

| id | score |
|----|-------|
| 1  | 95.0  |
| 2  | 85.0  |
| 3  | 85.0  |
| 4  | 76.0  |
| 5  | 60.0  |

**输出：**

| score | rank |
|-------|------|
| 95.0  | 1    |
| 85.0  | 2    |
| 85.0  | 2    |
| 76.0  | 3    |
| 60.0  | 4    |

**解释：** 两个 85.0 并列第 2，下一个分数 76.0 排名为 3（而不是 4）。

## 考察点

- `DENSE_RANK()` 窗口函数
- `RANK()` vs `DENSE_RANK()` vs `ROW_NUMBER()` 的区别
- 窗口函数的基本语法：`OVER (ORDER BY ...)`

## 解题思路

### 思路一：DENSE_RANK() 窗口函数（推荐）

```sql
SELECT score,
       DENSE_RANK() OVER (ORDER BY score DESC) AS rank
FROM Scores
ORDER BY score DESC;
```

这是最简洁的写法。`DENSE_RANK()` 按 `score DESC` 降序排名，相同分数排名相同，且排名连续。

### 思路二：子查询（不使用窗口函数，兼容老数据库）

```sql
SELECT s1.score,
       (SELECT COUNT(DISTINCT s2.score)
        FROM Scores s2
        WHERE s2.score >= s1.score) AS rank
FROM Scores s1
ORDER BY s1.score DESC;
```

对于每个分数，统计大于等于它的**不同分数**的个数，这就是它的排名。比如 85 分，大于等于它的不同分数有 `[95, 85]`，共 2 个，所以排名为 2。

### 三种排名函数的区别

| 分数 | ROW_NUMBER | RANK | DENSE_RANK |
|------|-----------|------|------------|
| 100  | 1         | 1    | 1          |
| 100  | 2         | 1    | 1          |
| 90   | 3         | 3    | 2          |
| 80   | 4         | 4    | 3          |

记住：`ROW_NUMBER` 无并列；`RANK` 有并列但跳跃；`DENSE_RANK` 有并列且连续。
