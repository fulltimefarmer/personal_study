
# 第 24 题：好友申请通过率

## 题目描述

在社交网络中，有一张 `FriendRequest` 表和一张 `RequestAccepted` 表：

**FriendRequest 表（好友申请）：**

| 列名       | 类型    | 说明         |
|------------|---------|--------------|
| sender_id  | INT     | 发送者 ID    |
| send_to_id | INT     | 接收者 ID    |
| request_date | DATE  | 申请日期     |

**RequestAccepted 表（申请通过）：**

| 列名       | 类型    | 说明         |
|------------|---------|--------------|
| requester_id | INT   | 申请人 ID    |
| accepter_id  | INT   | 接受人 ID    |
| accept_date  | DATE  | 接受日期     |

请编写 SQL，计算好友申请的**总体通过率**，即：通过的申请数 / 总申请数（去重），保留两位小数。

注意：同一个 `(sender_id, send_to_id)` 组合可能被多次申请，但只算一次。

### 示例

**FriendRequest 输入：**

| sender_id | send_to_id | request_date |
|-----------|------------|-------------|
| 1         | 2          | 2024-01-01  |
| 1         | 3          | 2024-01-02  |
| 1         | 4          | 2024-01-03  |
| 2         | 3          | 2024-01-04  |
| 1         | 2          | 2024-01-05  |
| 2         | 4          | 2024-01-06  |

**RequestAccepted 输入：**

| requester_id | accepter_id | accept_date |
|-------------|-------------|-------------|
| 1           | 2           | 2024-01-06 |
| 1           | 3           | 2024-01-07 |
| 2           | 4           | 2024-01-07 |

**输出：**

| accept_rate |
|-------------|
| 0.60        |

**解释：**
总申请（去重）有 5 组：`(1,2), (1,3), (1,4), (2,3), (2,4)`；通过的有 3 组：`(1,2), (1,3), (2,4)`；3/5 = 0.60。

## 考察点

- `COUNT(DISTINCT ...)` 去重计数
- 跨表统计比例
- 处理分母为 0 的情况（如果没有任何申请，应该返回 0）
- `ROUND()` 保留小数

## 解题思路

```sql
SELECT ROUND(
    CASE
        WHEN (SELECT COUNT(DISTINCT sender_id, send_to_id) FROM FriendRequest) = 0 THEN 0
        ELSE (SELECT COUNT(DISTINCT requester_id, accepter_id) FROM RequestAccepted) * 1.0
             / (SELECT COUNT(DISTINCT sender_id, send_to_id) FROM FriendRequest)
    END,
    2
) AS accept_rate;
```

或使用 PostgreSQL 的行构造器去重：

```sql
SELECT ROUND(
    COALESCE(
        (SELECT COUNT(DISTINCT (requester_id, accepter_id)) FROM RequestAccepted) * 1.0
        / NULLIF(
            (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest), 0
        ),
        0
    ),
    2
) AS accept_rate;
```

### 关键点

- `COUNT(DISTINCT (col1, col2))` 是 PostgreSQL 特有语法，对组合去重
- `NULLIF(x, 0)` 可以在分母为 0 时返回 `NULL`，配合 `COALESCE` 返回 0
- 不同数据库中，组合去重的写法不同。MySQL 中需要用 `COUNT(DISTINCT col1, col2)`（无括号），有些数据库需要子查询先 `SELECT DISTINCT` 两层
