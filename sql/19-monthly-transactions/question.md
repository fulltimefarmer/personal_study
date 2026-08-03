
# 第 19 题：每月交易统计

## 题目描述

有一张 `Transactions` 表：

| 列名         | 类型    | 说明                   |
|--------------|---------|------------------------|
| id           | INT     | 主键                   |
| country      | VARCHAR | 国家                   |
| state        | VARCHAR | 交易状态：`"approved"`（批准）或 `"declined"`（拒绝） |
| amount       | INT     | 交易金额               |
| trans_date   | DATE    | 交易日期               |

请编写 SQL，按月和国家统计：
- 月份（格式：`YYYY-MM`）
- 国家
- 交易总数（`trans_count`）
- 批准的交易数（`approved_count`）
- 交易总金额（`trans_total_amount`）
- 批准的交易总金额（`approved_total_amount`）

### 示例

**输入：**

| id | country | state    | amount | trans_date |
|----|---------|----------|--------|------------|
| 1  | 中国    | approved | 1000   | 2024-01-15 |
| 2  | 中国    | declined | 2000   | 2024-01-20 |
| 3  | 中国    | approved | 3000   | 2024-02-10 |
| 4  | 美国    | approved | 5000   | 2024-01-10 |
| 5  | 美国    | declined | 6000   | 2024-01-25 |
| 6  | 美国    | approved | 2000   | 2024-02-05 |

**输出：**

| month   | country | trans_count | approved_count | trans_total_amount | approved_total_amount |
|---------|---------|-------------|----------------|--------------------|-----------------------|
| 2024-01 | 中国    | 2           | 1              | 3000               | 1000                  |
| 2024-01 | 美国    | 2           | 1              | 11000              | 5000                  |
| 2024-02 | 中国    | 1           | 1              | 3000               | 3000                  |
| 2024-02 | 美国    | 1           | 1              | 2000               | 2000                  |

## 考察点

- `TO_CHAR(date, 'YYYY-MM')` 日期格式化
- `GROUP BY` 多列分组
- `COUNT` + `SUM` + `CASE WHEN` 的条件聚合

## 解题思路

核心是条件聚合：在 `SUM` 和 `COUNT` 中使用 `CASE WHEN` 条件。

```sql
SELECT TO_CHAR(trans_date, 'YYYY-MM') AS month,
       country,
       COUNT(*) AS trans_count,
       SUM(CASE WHEN state = 'approved' THEN 1 ELSE 0 END) AS approved_count,
       SUM(amount) AS trans_total_amount,
       SUM(CASE WHEN state = 'approved' THEN amount ELSE 0 END) AS approved_total_amount
FROM Transactions
GROUP BY TO_CHAR(trans_date, 'YYYY-MM'), country
ORDER BY month, country;
```

### 关键技巧

- `SUM(CASE WHEN state = 'approved' THEN 1 ELSE 0 END)`：条件计数。当 `state = 'approved'` 时计 1，否则计 0，求和即为批准交易数
- `SUM(CASE WHEN state = 'approved' THEN amount ELSE 0 END)`：条件求和。只对批准交易的金额求和
- 这种"在聚合函数中嵌入 CASE WHEN"的模式，是 SQL 面试中最常用的技巧之一

### 扩展

如果不想在 `GROUP BY` 中重复 `TO_CHAR`，可以用子查询或 CTE 先转换日期格式：

```sql
WITH t AS (
    SELECT TO_CHAR(trans_date, 'YYYY-MM') AS month, *
    FROM Transactions
)
SELECT month, country, ...
FROM t
GROUP BY month, country;
```
