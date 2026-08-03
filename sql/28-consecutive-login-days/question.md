
# 第 28 题：连续登录天数（GAP/ISLAND）

## 题目描述

有一张 `Login` 表，记录用户登录日志：

| 列名       | 类型    | 说明     |
|------------|---------|----------|
| user_id    | INT     | 用户 ID  |
| login_date | DATE    | 登录日期 |

同一个用户在同一天可能有多条登录记录（只需视为一天）。

请编写 SQL，统计**每个用户的最长连续登录天数**。

### 示例

**输入：**

| user_id | login_date |
|---------|------------|
| 1       | 2024-01-01 |
| 1       | 2024-01-02 |
| 1       | 2024-01-03 |
| 1       | 2024-01-05 |
| 1       | 2024-01-06 |
| 2       | 2024-01-01 |
| 2       | 2024-01-02 |
| 2       | 2024-01-04 |
| 3       | 2024-01-01 |
| 3       | 2024-01-01 |

**输出：**

| user_id | max_consecutive_days |
|---------|---------------------|
| 1       | 3                   |
| 2       | 2                   |
| 3       | 1                   |

**解释：**
- user 1：登录日期 01-01, 01-02, 01-03 连续 3 天；01-05, 01-06 连续 2 天 → 最长 3 天
- user 2：登录日期 01-01, 01-02 连续 2 天；01-04 单独 1 天 → 最长 2 天
- user 3：只在 01-01 有记录（即使是两条，去重后算一天）→ 最长 1 天

## 考察点

- 经典的 **GAP/ISLAND**（连续区间）问题
- `ROW_NUMBER()` 差值分组技巧
- 先对用户+日期去重
- `DENSE_RANK()` 或 `ROW_NUMBER()` 的选择
- CTE 多层嵌套

## 解题思路

核心技巧：用日期与行号的差值来识别连续区间。

```sql
WITH distinct_days AS (
    SELECT DISTINCT user_id, login_date
    FROM Login
),
numbered AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM distinct_days
),
grouped AS (
    SELECT user_id,
           login_date - rn * INTERVAL '1 day' AS grp
    FROM numbered
)
SELECT user_id, MAX(consecutive_days) AS max_consecutive_days
FROM (
    SELECT user_id, grp, COUNT(*) AS consecutive_days
    FROM grouped
    GROUP BY user_id, grp
) t
GROUP BY user_id
ORDER BY user_id;
```

### 原理说明

以 user 1 为例，去重后的登录日期为：`[01-01, 01-02, 01-03, 01-05, 01-06]`

| login_date | rn | login_date - rn (grp) |
|------------|----|----------------------|
| 2024-01-01 | 1  | 2023-12-31            |
| 2024-01-02 | 2  | 2023-12-31            |
| 2024-01-03 | 3  | 2023-12-31            |
| 2024-01-05 | 4  | 2024-01-01            |
| 2024-01-06 | 5  | 2024-01-01            |

连续日期的 `login_date - rn` 结果相同！因此按 `(user_id, grp)` 分组，每组内的行数就是连续天数。

### 要点

1. 必须先 `DISTINCT` 去重（同一天多次登录算一天）
2. 使用 `PARTITION BY user_id` 在每个用户内独立编号
3. 最后 `MAX(consecutive_days)` 取每个用户的最长连续登录天数

### GAP/ISLAND 问题通用解法

对于"连续"类问题（连续登录、连续签到、连续达标等），核心流程：
1. 筛选出目标行（如有条件）
2. 用 `ROW_NUMBER()` 编号
3. 计算"基准列 - 行号"得到分组标识
4. 按分组标识统计每组大小
