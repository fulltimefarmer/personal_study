
# 第 6 题：上升的温度

## 题目描述

有一张 `Weather` 表，记录每天的温度：

| 列名        | 类型    | 说明         |
|-------------|---------|--------------|
| id          | INT     | 主键，记录 ID |
| recordDate  | DATE    | 日期         |
| temperature | INT     | 当天温度（摄氏度） |

请编写 SQL，找出所有满足以下条件的日期 ID：**当天温度比前一天的温度高**。

注意：`id` 的顺序不一定和日期顺序一致，必须以 `recordDate` 为准判断"前一天"。

### 示例

**输入：**

| id | recordDate | temperature |
|----|------------|-------------|
| 1  | 2024-01-01 | 10          |
| 2  | 2024-01-02 | 25          |
| 3  | 2024-01-03 | 20          |
| 4  | 2024-01-04 | 30          |
| 5  | 2024-01-06 | 28          |

**输出：**

| id |
|----|
| 2  |
| 4  |

**解释：**
- 1 月 2 日温度 25 比 1 月 1 日温度 10 高，返回 id=2
- 1 月 3 日温度 20 比 1 月 2 日温度 25 低，不返回
- 1 月 4 日温度 30 比 1 月 3 日温度 20 高，返回 id=4
- 1 月 6 日的前一天 1 月 5 日没有记录，不参与比较

## 考察点

- 自连接（`JOIN` 同一张表自身）
- 日期比较：`DATEDIFF` / 日期加减运算
- PostgreSQL 中的日期计算：`recordDate - INTERVAL '1 day'`
- `LAG()` 窗口函数的替代解法

## 解题思路

### 思路一：自连接（推荐）

将 `Weather` 表与自身做连接，连接条件是当天的日期和"前一天"的日期匹配：

```sql
SELECT w1.id
FROM Weather w1
JOIN Weather w2 ON w1.recordDate = w2.recordDate + INTERVAL '1 day'
WHERE w1.temperature > w2.temperature;
```

这里 `w1` 代表"当天"，`w2` 代表"前一天"。通过 `w2.recordDate + INTERVAL '1 day'` 等于 `w1.recordDate` 来建立关联。

在 PostgreSQL 中，也可以写成：`ON w1.recordDate - w2.recordDate = 1`

### 思路二：窗口函数 LAG()

```sql
WITH t AS (
    SELECT id, recordDate, temperature,
           LAG(temperature) OVER (ORDER BY recordDate) AS prev_temp,
           LAG(recordDate) OVER (ORDER BY recordDate) AS prev_date
    FROM Weather
)
SELECT id
FROM t
WHERE temperature > prev_temp
  AND recordDate - prev_date = 1;
```

`LAG()` 可以取出按照日期排序后的上一行的温度，再判断是否比前一天高，并且确保日期是连续的前一天（避免跳日期的情况）。
