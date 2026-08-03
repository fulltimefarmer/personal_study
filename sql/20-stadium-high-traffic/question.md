
# 第 20 题：体育馆人流量（连续多天）

## 题目描述

有一张 `Stadium` 表，记录某体育馆每天的人流量：

| 列名       | 类型    | 说明     |
|------------|---------|----------|
| id         | INT     | 主键，日期ID（连续递增） |
| visit_date | DATE    | 日期     |
| people     | INT     | 该天人流量 |

请编写 SQL，找出**人流量大于等于 100** 并且**连续 3 天及以上**的记录，按 `id` 升序输出所有满足条件的记录。

### 示例

**输入：**

| id | visit_date | people |
|----|------------|--------|
| 1  | 2024-01-01 | 10     |
| 2  | 2024-01-02 | 109    |
| 3  | 2024-01-03 | 150    |
| 4  | 2024-01-04 | 99     |
| 5  | 2024-01-05 | 145    |
| 6  | 2024-01-06 | 1455   |
| 7  | 2024-01-07 | 199    |
| 8  | 2024-01-08 | 188    |

**输出：**

| id | visit_date | people |
|----|------------|--------|
| 5  | 2024-01-05 | 145    |
| 6  | 2024-01-06 | 1455   |
| 7  | 2024-01-07 | 199    |
| 8  | 2024-01-08 | 188    |

**解释：** id=2,3 虽然 people ≥ 100，但只有连续 2 天（id=4 中断了）。id=5,6,7,8 连续 4 天 people ≥ 100，全部返回。

## 考察点

- 连续区间的经典 GAP/ISLAND 问题
- 窗口函数 `ROW_NUMBER()` 的差值分组技巧
- CTE 多层嵌套组织复杂逻辑

## 解题思路

这是典型的 GAP/ISLAND 问题。核心技巧是用行号差值来识别连续区间：

1. 筛选出 `people >= 100` 的行
2. 对这些行按 `id` 排序并计算行号
3. 计算 `id - row_number`，**同一连续区间的行，这个差值相同**
4. 找出包含至少 3 行的区间，返回这些区间的所有行

```sql
WITH filtered AS (
    SELECT id, visit_date, people
    FROM Stadium
    WHERE people >= 100
),
grouped AS (
    SELECT id, visit_date, people,
           id - ROW_NUMBER() OVER (ORDER BY id) AS grp
    FROM filtered
),
long_groups AS (
    SELECT grp
    FROM grouped
    GROUP BY grp
    HAVING COUNT(*) >= 3
)
SELECT g.id, g.visit_date, g.people
FROM grouped g
JOIN long_groups l ON g.grp = l.grp
ORDER BY g.id;
```

### 原理解析

假设筛选后剩余行 ID 为：`2, 3, 5, 6, 7, 8`

| id | ROW_NUMBER | id - ROW_NUMBER (grp) |
|----|-----------|----------------------|
| 2  | 1         | 1                    |
| 3  | 2         | 1                    |
| 5  | 3         | 2                    |
| 6  | 4         | 2                    |
| 7  | 5         | 2                    |
| 8  | 6         | 2                    |

`grp = 1` 只有 2 行（不连续，被 id=4 断开），`grp = 2` 有 4 行（连续），所以返回 `grp = 2` 的行。

这个差值技巧是解决**连续区间**问题的核心，务必掌握。
