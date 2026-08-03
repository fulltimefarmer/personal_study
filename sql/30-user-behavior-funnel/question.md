
# 第 30 题：用户行为漏斗分析

## 题目描述

有一张 `UserBehavior` 表，记录用户在电商平台上的行为：

| 列名       | 类型    | 说明                                            |
|------------|---------|------------------------------------------------|
| user_id    | INT     | 用户 ID                                         |
| page       | VARCHAR | 用户访问的页面：home（首页）、search（搜索）、product（商品详情）、cart（购物车）、pay（支付） |
| timestamp  | TIMESTAMP | 行为发生时间                                  |

请编写 SQL，计算漏斗各环节的**用户数**和**转化率**：
- 访问首页的用户数
- 从首页进入搜索页的用户数
- 从搜索页进入商品详情页的用户数
- 从商品详情页加入购物车的用户数
- 从购物车到支付的用户数

漏斗顺序：`home -> search -> product -> cart -> pay`

转化率 = 当前环节用户数 / 上一环节用户数 * 100，保留两位小数。

### 示例

**输入：**

| user_id | page    | timestamp           |
|---------|---------|---------------------|
| 1       | home    | 2024-01-01 08:00:00 |
| 1       | search  | 2024-01-01 08:05:00 |
| 1       | product | 2024-01-01 08:10:00 |
| 1       | cart    | 2024-01-01 08:15:00 |
| 1       | pay     | 2024-01-01 08:20:00 |
| 2       | home    | 2024-01-01 09:00:00 |
| 2       | search  | 2024-01-01 09:05:00 |
| 3       | home    | 2024-01-01 10:00:00 |
| 3       | search  | 2024-01-01 10:05:00 |
| 3       | product | 2024-01-01 10:10:00 |
| 3       | cart    | 2024-01-01 10:15:00 |
| 4       | home    | 2024-01-01 11:00:00 |

**输出：**

| step     | user_count | conversion_rate |
|----------|------------|-----------------|
| home     | 4          | 100.00          |
| search   | 3          | 75.00           |
| product  | 2          | 66.67           |
| cart     | 2          | 100.00          |
| pay      | 1          | 50.00           |

**解释：** 4 人访问首页，3 人进入搜索（转化率 75%），2 人进入商品详情（转化率 66.67%），2 人加入购物车（转化率 100%），1 人支付（转化率 50%）。

## 考察点

- 条件聚合与去重计数
- 复杂的漏斗逻辑：不仅要统计访问某页面的用户，还要判断是否访问过"上一个环节"的页面
- 窗口函数 `LAG()` 计算相邻环节转化率
- CTE 组织多步骤逻辑

## 解题思路

漏斗分析的关键是：统计的是**按顺序完成过前面所有环节**的用户数，而不是简单地统计独立访问某页面的用户数。

```sql
WITH page_users AS (
    SELECT user_id,
           MAX(CASE WHEN page = 'home' THEN 1 ELSE 0 END) AS has_home,
           MAX(CASE WHEN page = 'search' THEN 1 ELSE 0 END) AS has_search,
           MAX(CASE WHEN page = 'product' THEN 1 ELSE 0 END) AS has_product,
           MAX(CASE WHEN page = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN page = 'pay' THEN 1 ELSE 0 END) AS has_pay
    FROM UserBehavior
    GROUP BY user_id
),
funnel AS (
    SELECT
        COUNT(*) FILTER (WHERE has_home = 1)                                            AS home_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1)                        AS search_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1 AND has_product = 1)    AS product_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1 AND has_product = 1 AND has_cart = 1) AS cart_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1 AND has_product = 1 AND has_cart = 1 AND has_pay = 1) AS pay_count
    FROM page_users
)
SELECT UNNEST(ARRAY['home', 'search', 'product', 'cart', 'pay']) AS step,
       UNNEST(ARRAY[home_count, search_count, product_count, cart_count, pay_count]) AS user_count,
       UNNEST(ARRAY[
           100.00,
           ROUND(search_count * 100.0 / home_count, 2),
           ROUND(product_count * 100.0 / search_count, 2),
           ROUND(cart_count * 100.0 / product_count, 2),
           ROUND(pay_count * 100.0 / cart_count, 2)
       ]) AS conversion_rate
FROM funnel;
```

### 关键技巧

1. **行转列**：用 `MAX(CASE WHEN ...)` 将用户的多个页面访问行为转为一行中的 0/1 标记
2. **FILTER 子句**：PostgreSQL 的 `COUNT(*) FILTER (WHERE ...)` 是比 `CASE WHEN` 更优雅的条件计数方式
3. **UNNEST**：将一行数据转为多行，形成最终的漏斗表格

### 注意

- 这个解法没有考虑行为的时间顺序（只看用户是否访问过各页面，不管先后）。如果面试官要求严格按时间顺序，需要改用窗口函数标记每个用户的最早访问时间再做判断
- `FILTER` 是 PostgreSQL 特有的语法，在其他数据库中可以替换为 `SUM(CASE WHEN ...)`
