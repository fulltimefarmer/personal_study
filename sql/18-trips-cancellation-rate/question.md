
# 第 18 题：行程和用户（取消率）

## 题目描述

有两张表 `Trips` 和 `Users`：

**Trips 表（出租车行程）：**

| 列名         | 类型    | 说明                                 |
|--------------|---------|--------------------------------------|
| id           | INT     | 主键                                 |
| client_id    | INT     | 乘客 ID（关联 Users 表）              |
| driver_id    | INT     | 司机 ID（关联 Users 表）              |
| city_id      | INT     | 城市 ID（忽略）                       |
| status       | VARCHAR | 行程状态：`'completed'`（完成）或 `'cancelled_by_driver'`、`'cancelled_by_client'`（取消） |
| request_at   | DATE    | 行程日期                             |

**Users 表（用户）：**

| 列名     | 类型    | 说明                           |
|----------|---------|--------------------------------|
| users_id | INT     | 用户 ID                        |
| banned   | VARCHAR | `'Yes'` 表示被禁止，`'No'` 表示正常 |
| role     | VARCHAR | `'client'`（乘客）/ `'driver'`（司机）/ `'partner'` |

请编写 SQL，查询 **2013-10-01 至 2013-10-03** 期间内，**每天**的取消率。取消率 = 当天被取消的行程数 / 当天总行程数（乘客和司机都必须**没有被 ban**），结果保留两位小数。

### 示例

**Trips 输入：**

| id | client_id | driver_id | status              | request_at |
|----|-----------|-----------|---------------------|------------|
| 1  | 1         | 10        | completed           | 2013-10-01 |
| 2  | 2         | 11        | cancelled_by_driver | 2013-10-01 |
| 3  | 3         | 12        | completed           | 2013-10-01 |
| 4  | 4         | 13        | cancelled_by_client | 2013-10-01 |
| 5  | 1         | 10        | completed           | 2013-10-02 |
| 6  | 2         | 11        | completed           | 2013-10-02 |
| 7  | 3         | 12        | completed           | 2013-10-02 |
| 8  | 1         | 12        | completed           | 2013-10-03 |
| 9  | 3         | 10        | cancelled_by_driver | 2013-10-03 |

**Users 输入：**

| users_id | banned | role   |
|----------|--------|--------|
| 1        | No     | client |
| 2        | Yes    | client |
| 3        | No     | client |
| 4        | No     | client |
| 10       | No     | driver |
| 11       | No     | driver |
| 12       | No     | driver |
| 13       | No     | driver |

**输出：**

| Day        | Cancellation Rate |
|------------|-------------------|
| 2013-10-01 | 0.33              |
| 2013-10-02 | 0.00              |
| 2013-10-03 | 0.50              |

**解释：**
- 10-01：排除 client_id=2（被 ban），剩余 3 个行程，1 个取消 → 1/3 = 0.33
- 10-02：排除 client_id=2，剩余 2 个行程，0 个取消 → 0/2 = 0.00
- 10-03：剩余 2 个行程，1 个取消 → 1/2 = 0.50

## 考察点

- 多表 `JOIN` 关联过滤
- `CASE WHEN` 条件计数：`SUM(CASE WHEN status LIKE 'cancelled%' THEN 1 ELSE 0 END)`
- `ROUND()` 保留小数
- 按日期分组 `GROUP BY`

## 解题思路

1. 先把被 ban 的用户筛选出来，排除这些用户的行程
2. 按日期分组，统计每天的总行程数和取消数
3. 计算比例并四舍五入

```sql
SELECT t.request_at AS "Day",
       ROUND(
           SUM(CASE WHEN t.status LIKE 'cancelled%' THEN 1 ELSE 0 END) * 1.0
           / COUNT(*),
           2
       ) AS "Cancellation Rate"
FROM Trips t
JOIN Users u_client ON t.client_id = u_client.users_id
JOIN Users u_driver ON t.driver_id = u_driver.users_id
WHERE u_client.banned = 'No'
  AND u_driver.banned = 'No'
  AND t.request_at BETWEEN '2013-10-01' AND '2013-10-03'
GROUP BY t.request_at
ORDER BY t.request_at;
```

要点：
- 需要分别 `JOIN Users` 两次——一次检查乘客是否被 ban，一次检查司机是否被 ban
- `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` 是 SQL 中做条件计数的经典写法
- `* 1.0` 强制转换为浮点数，避免整数除法
