
# 第 26 题：累计销售额（窗口函数）

## 题目描述

有一张 `Orders` 表，记录每日订单销售额：

| 列名       | 类型    | 说明     |
|------------|---------|----------|
| order_id   | INT     | 主键     |
| order_date | DATE    | 订单日期 |
| amount     | DECIMAL | 订单金额 |

请编写 SQL，查询每一天的**累计销售额**（从第一天到当天的总销售额）。如果某天没有订单，当天不会出现在结果中。结果按日期升序排列。

### 示例

**输入：**

| order_id | order_date | amount |
|----------|------------|--------|
| 1        | 2024-01-01 | 100    |
| 2        | 2024-01-03 | 200    |
| 3        | 2024-01-04 | 150    |
| 4        | 2024-01-05 | 50     |
| 5        | 2024-01-05 | 100    |

**输出：**

| order_date | daily_total | cumulative_total |
|------------|-------------|------------------|
| 2024-01-01 | 100         | 100              |
| 2024-01-03 | 200         | 300              |
| 2024-01-04 | 150         | 450              |
| 2024-01-05 | 150         | 600              |

**解释：**
- 01-01 当天总额 100，累计 100
- 01-02 没有订单，不出现在结果中
- 01-03 当天总额 200，累计 100+200=300
- 01-04 当天总额 150，累计 300+150=450
- 01-05 当天有两笔订单：50+100=150，累计 450+150=600

## 考察点

- 窗口函数 `SUM() OVER (ORDER BY ...)` 计算累计值
- 窗口函数的 `RANGE` / `ROWS` 子句
- 先按天聚合再累计 vs 直接对每笔订单累计

## 解题思路

### 思路一：先聚合再累计（推荐）

```sql
SELECT order_date,
       daily_total,
       SUM(daily_total) OVER (ORDER BY order_date) AS cumulative_total
FROM (
    SELECT order_date, SUM(amount) AS daily_total
    FROM Orders
    GROUP BY order_date
) t
ORDER BY order_date;
```

1. 内层子查询先按日期聚合每天的销售总额
2. 外层用 `SUM() OVER (ORDER BY order_date)` 计算累计值
3. `ORDER BY order_date` 指定按日期顺序累加

### 思路二：直接对每笔订单累计

```sql
SELECT order_date,
       amount,
       SUM(amount) OVER (ORDER BY order_date, order_id) AS cumulative_total
FROM Orders
ORDER BY order_date, order_id;
```

这会对每一笔订单输出一行，每行的累计值是到该笔订单为止的总额。如果需要按天显示，内层聚合更合适。

### 关键概念

`SUM() OVER (ORDER BY ...)` 是整个窗口函数的默认行为，等于：
```sql
SUM(daily_total) OVER (ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```
从窗口的第一行累加到当前行。

### 扩展：移动平均

如果要求计算**近 3 天的移动平均**：

```sql
SELECT order_date,
       daily_total,
       AVG(daily_total) OVER (ORDER BY order_date
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3d
FROM daily_sales;
```
