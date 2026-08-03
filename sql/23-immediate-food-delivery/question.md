
# 第 23 题：即时食物配送比例

## 题目描述

有一张 `Delivery` 表，记录食物配送订单：

| 列名               | 类型    | 说明                         |
|--------------------|---------|------------------------------|
| delivery_id        | INT     | 主键，配送单 ID               |
| customer_id        | INT     | 客户 ID                      |
| order_date         | DATE    | 下单日期                     |
| customer_pref_delivery_date | DATE   | 客户期望的配送日期 |

如果**下单日期与客户期望配送日期相同**，则该订单称为**即时订单**（immediate）；否则称为**计划订单**（scheduled）。

每个客户的首单，指的是该客户 `order_date` 最小的那个订单。

请编写 SQL，查询所有客户**首单中即时订单的比例**，保留两位小数。

### 示例

**输入：**

| delivery_id | customer_id | order_date | customer_pref_delivery_date |
|-------------|-------------|------------|------------------------------|
| 1           | 1           | 2024-08-01 | 2024-08-02                  |
| 2           | 2           | 2024-08-02 | 2024-08-02                  |
| 3           | 1           | 2024-08-11 | 2024-08-12                  |
| 4           | 3           | 2024-08-24 | 2024-08-25                  |
| 5           | 3           | 2024-08-26 | 2024-08-26                  |
| 6           | 2           | 2024-08-28 | 2024-08-29                  |

**输出：**

| immediate_percentage |
|----------------------|
| 33.33                |

**解释：**
- customer 1 首单：delivery_id=1，order_date=08-01，pref=08-02 → 非即时 ❌
- customer 2 首单：delivery_id=2，order_date=08-02，pref=08-02 → 即时 ✅
- customer 3 首单：delivery_id=4，order_date=08-24，pref=08-25 → 非即时 ❌

3 个客户中，1 个首单是即时订单。1/3 ≈ 33.33。

等等，重新核对数据：
- customer 1: delivery_id=1 (08-01, 08-02, 非即时) 和 delivery_id=3 (08-11, 08-12, 非即时)。首单是 08-01 的，非即时。
- customer 2: delivery_id=2 (08-02, 08-02, 即时) 和 delivery_id=6 (08-28, 08-29, 非即时)。首单是 08-02 的，即时。
- customer 3: delivery_id=4 (08-24, 08-24, 即时) 和 delivery_id=5 (08-26, 08-27, 非即时)。首单是 08-24 的，即时。

3 个客户，2 个即时首单。2/3 = 66.67%。

但示例输出是 33.33... 那是我写错了。让我换成 66.67。

不行，让我把数据调整一下，让结果是 33.33 或 66.67 都行。实际上，让我保持数据不变，把输出改成 66.67。

## 考察点

- `ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY order_date)` 找首单
- `CASE WHEN` + 条件聚合计算比例
- `ROUND()` 保留两位小数

## 解题思路

1. 用窗口函数给每个客户的订单按 `order_date` 排序，编号为 1 的即为首单
2. 对首单判断 `order_date = customer_pref_delivery_date`（即时订单）
3. 计算即时首单数 / 首单总数

```sql
WITH first_orders AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS rn
    FROM Delivery
)
SELECT ROUND(
    SUM(CASE WHEN order_date = customer_pref_delivery_date THEN 1 ELSE 0 END) * 100.0
    / COUNT(*),
    2
) AS immediate_percentage
FROM first_orders
WHERE rn = 1;
```

注意乘以 `100.0` 得到百分比形式（也可以乘以 `1.0` 得到小数形式，面试中和面试官确认格式要求）。
