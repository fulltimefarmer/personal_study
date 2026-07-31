# 连续出现的数字 (Consecutive Numbers)

## 题目描述

Logs 表：

| Id | Num |
|----|-----|
| 1  | 1   |
| 2  | 1   |
| 3  | 1   |
| 4  | 2   |
| 5  | 1   |
| 6  | 2   |
| 7  | 2   |

编写一个 SQL 查询，查找所有至少连续出现三次的数字。

**期望输出：**

| ConsecutiveNums |
|-----------------|
| 1               |

说明：Num=1 在 Id=1,2,3 处连续出现了三次，符合条件。2 没有连续出现三次。

## 考察点

- 窗口函数 LAG() / LEAD() 进行行间比较
- 自连接（连续条件：Id 差为 1 且 Num 相同）
- 变量法（MySQL 用户变量模拟行间比较）
- 连续序列问题的一般解法

## 解题思路详解

### 思路核心：什么是"连续"？

连续 = Id 连续（或时间戳连续）且值相同。本题中 Id 自增且无间断，所以：
- Id=i, Id=i+1, Id=i+2 三条记录的 Num 相同 → Num 连续出现三次

### 解法一：窗口函数 LAG() / LEAD()（MySQL 8.0+ / PostgreSQL）

```sql
SELECT DISTINCT Num AS ConsecutiveNums
FROM (
  SELECT Num,
         LAG(Num, 1) OVER (ORDER BY Id) AS prev1,
         LAG(Num, 2) OVER (ORDER BY Id) AS prev2
  FROM Logs
) t
WHERE Num = prev1 AND Num = prev2;
```

**LAG 函数详解**：

`LAG(column, offset, default) OVER (ORDER BY ...)`

- `column`：要取值的列
- `offset`：向前看几行（1 表示前一行的值）
- `default`：越界时的默认值（可选，默认为 NULL）

以题目数据为例：

| Id | Num | LAG(Num,1) | LAG(Num,2) | 判断 |
|----|-----|-----------|-----------|------|
| 1  | 1   | NULL       | NULL       | -    |
| 2  | 1   | 1          | NULL       | -    |
| 3  | 1   | 1          | 1          | ✓    |
| 4  | 2   | 1          | 1          | -    |
| 5  | 1   | 2          | 1          | -    |
| 6  | 2   | 1          | 2          | -    |
| 7  | 2   | 2          | 1          | -    |

Id=3 时：Num=1, prev1=1, prev2=1，三者相等，命中。

### 解法二：自连接（兼容所有数据库）

```sql
SELECT DISTINCT l1.Num AS ConsecutiveNums
FROM Logs l1
JOIN Logs l2 ON l1.Id = l2.Id - 1 AND l1.Num = l2.Num
JOIN Logs l3 ON l2.Id = l3.Id - 1 AND l2.Num = l3.Num;
```

**原理**：
- `l1.Id = l2.Id - 1` 保证 l2 是 l1 的下一行
- `l2.Id = l3.Id - 1` 保证 l3 是 l2 的下一行
- `l1.Num = l2.Num AND l2.Num = l3.Num` 保证三个连续值相等

三次 JOIN 确保三行连续同值。这种方法可扩展到 N 次连续出现（加 N-1 次 JOIN）。

### 解法三：MySQL 用户变量法（兼容 MySQL 5.x）

```sql
SELECT DISTINCT Num AS ConsecutiveNums
FROM (
  SELECT Num,
         @cnt := IF(@prev = Num, @cnt + 1, 1) AS cnt,
         @prev := Num
  FROM Logs, (SELECT @cnt := 0, @prev := NULL) init
  ORDER BY Id
) t
WHERE cnt >= 3;
```

**原理**：
- `@prev` 记录上一行的 Num 值
- `@cnt` 记录当前连续计数器
- 如果当前 Num 等于上一行则计数器 +1，否则重置为 1
- 最后筛选 cnt >= 3 的记录

注意：MySQL 8.0+ 不推荐使用用户变量，建议用窗口函数替代。

## 执行计划与性能

- 窗口函数方案：一次全表扫描 + 排序（按 Id），O(n log n)
- 自连接方案：三次扫描（或多表 JOIN），索引（Id）可加速
- 用户变量方案：一次全表扫描，O(n)，最快但依赖 MySQL 特性

## 扩展

- 如果 Id 不是连续的（有删除）怎么办？——需要在子查询中用 `ROW_NUMBER() OVER (ORDER BY Id)` 生成连续序号。
- 如果要查"连续出现 N 次"的通用解？——窗口函数方案只需增加 LAG(2) ... LAG(N-1)；自连接方案需要 N-1 次 JOIN。
- 如果要查"至少出现三次但不要求连续"？——用 GROUP BY + HAVING COUNT(*) >= 3。
- LEAD 函数是向前看下一行（LAG 的反向操作）：
  ```sql
  SELECT Num,
         LEAD(Num, 1) OVER (ORDER BY Id) AS next1,
         LEAD(Num, 2) OVER (ORDER BY Id) AS next2
  FROM Logs;
  ```

## 通用连续序列问题的解题框架

这是一类经典问题。核心思路是分组标记法：

```sql
-- 用 ROW_NUMBER 识别连续的组
-- 原理：连续序列中 (Id - ROW_NUMBER) 的结果相同
SELECT Num,
       Id - ROW_NUMBER() OVER (PARTITION BY Num ORDER BY Id) AS grp
FROM Logs;
-- 再按 Num 和 grp 分组，COUNT >= 3 即连续出现 3 次以上
```

这是"连续序列分组"的通用技巧（gaps and islands problem）。
