
# 第 25 题：产品销售分析 - 分组 TopN

## 题目描述

有两张表 `Product` 和 `Sales`：

**Product 表：**

| 列名         | 类型    | 说明     |
|--------------|---------|----------|
| product_id   | INT     | 主键     |
| product_name | VARCHAR | 产品名称 |
| category     | VARCHAR | 产品类别 |

**Sales 表：**

| 列名       | 类型    | 说明     |
|------------|---------|----------|
| sale_id    | INT     | 主键     |
| product_id | INT     | 产品 ID  |
| sale_date  | DATE    | 销售日期 |
| quantity   | INT     | 销售数量 |
| revenue    | DECIMAL | 销售金额 |

请编写 SQL，查询**每个产品品类中，总销售额排名第一的产品**。如果并列第一，全部返回。输出列：类别名称、产品名称、总销售额。

### 示例

**Product 输入：**

| product_id | product_name | category |
|------------|--------------|----------|
| 1          | 手机A        | 电子产品 |
| 2          | 手机B        | 电子产品 |
| 3          | T恤          | 服装     |
| 4          | 裤子         | 服装     |
| 5          | 手机C        | 电子产品 |

**Sales 输入：**

| sale_id | product_id | sale_date  | quantity | revenue |
|---------|------------|------------|----------|---------|
| 1       | 1          | 2024-01-01 | 10       | 50000   |
| 2       | 1          | 2024-01-02 | 5        | 25000   |
| 3       | 2          | 2024-01-03 | 8        | 40000   |
| 4       | 3          | 2024-01-01 | 20       | 2000    |
| 5       | 4          | 2024-01-02 | 15       | 3000    |
| 6       | 5          | 2024-01-03 | 3        | 18000   |
| 7       | 2          | 2024-01-04 | 15       | 75000   |

**输出：**

| category | product_name | total_revenue |
|----------|--------------|---------------|
| 电子产品 | 手机B        | 115000        |
| 服装     | 裤子         | 3000          |

**解释：**
- 电子产品：手机A = 75000，手机B = 115000，手机C = 18000。手机B 最高，115000
- 服装：T恤 = 2000，裤子 = 3000。裤子最高，3000

## 考察点

- 多表 `JOIN` + 分组聚合
- `PARTITION BY` + `RANK()` 窗口函数做分组 TopN
- `SUM()` 聚合与窗口函数的结合

## 解题思路

### 思路一：RANK() 窗口函数（推荐）

```sql
WITH product_revenue AS (
    SELECT p.product_name, p.category,
           COALESCE(SUM(s.revenue), 0) AS total_revenue
    FROM Product p
    LEFT JOIN Sales s ON p.product_id = s.product_id
    GROUP BY p.product_id, p.product_name, p.category
),
ranked AS (
    SELECT category, product_name, total_revenue,
           RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rnk
    FROM product_revenue
)
SELECT category, product_name, total_revenue
FROM ranked
WHERE rnk = 1
ORDER BY category;
```

关键步骤：
1. 先按产品聚合总销售额
2. 用 `RANK() OVER(PARTITION BY category ORDER BY total_revenue DESC)` 在每个品类内按销售额排名
3. 取 `rnk = 1` 的产品
4. 使用 `RANK()`（而不是 `ROW_NUMBER()`）确保并列第一都被保留

### 思路二：关联子查询

```sql
WITH product_revenue AS (
    SELECT p.product_name, p.category, COALESCE(SUM(s.revenue), 0) AS total_revenue
    FROM Product p
    LEFT JOIN Sales s ON p.product_id = s.product_id
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT category, product_name, total_revenue
FROM product_revenue pr
WHERE total_revenue = (
    SELECT MAX(total_revenue)
    FROM product_revenue pr2
    WHERE pr2.category = pr.category
);
```

### 对比
- 思路一（窗口函数）：可读性好，容易扩展到 TopN（`rnk <= N`）
- 思路二（关联子查询）：兼容性好，但每行都要执行一次子查询，数据量大时性能较差
