# 删除重复的邮箱 (Delete Duplicate Emails)

## 题目描述

Person 表：

| Id | Email            |
|----|------------------|
| 1  | john@example.com |
| 2  | bob@example.com  |
| 3  | john@example.com |

编写一个 SQL 删除语句，删除所有重复的邮箱，只保留 Id 最小的那条记录。不按 Id 排序的 SELECT 行为不在题目要求范围内。

**操作前：**

```
+----+------------------+
| Id | Email            |
+----+------------------+
| 1  | john@example.com |
| 2  | bob@example.com  |
| 3  | john@example.com |
+----+------------------+
```

**操作后：**

```
+----+------------------+
| Id | Email            |
+----+------------------+
| 1  | john@example.com |
| 2  | bob@example.com  |
+----+------------------+
```

说明：john@example.com 出现了两次（Id=1 和 Id=3），保留 Id 最小的（Id=1），删除 Id=3。

## 考察点

- DELETE + 自连接
- DELETE + 子查询
- MySQL 的 DELETE 特性（不能直接 DELETE 和 SELECT 同一张表）
- 窗口函数在 DELETE 中的应用

## 解题思路详解

### 解法一：自连接删除（推荐）

```sql
DELETE p1
FROM Person p1
JOIN Person p2 ON p1.Email = p2.Email
WHERE p1.Id > p2.Id;
```

**原理**：
- p1 和 p2 是 Person 表的两份"副本"（同一个表的不同别名）
- `p1.Email = p2.Email` 匹配相同邮箱
- `WHERE p1.Id > p2.Id` 保证只删除 Id 较大的那些行
- Id 最小的行（比如 Id=1 的 john@example.com）没有比它更小的同邮箱行，所以不会被删除

**逐步推演**（以题目数据为例）：

| p1.Id | p1.Email | p2.Id | p2.Email | p1.Id > p2.Id? | 操作 |
|-------|----------|-------|----------|-----------------|------|
| 1 | john@... | 1 | john@... | FALSE (1 > 1) | 保留 |
| 1 | john@... | 3 | john@... | FALSE (1 > 3) | 保留 |
| 3 | john@... | 1 | john@... | TRUE  (3 > 1) | **删除** |
| 3 | john@... | 3 | john@... | FALSE (3 > 3) | 保留 |
| 2 | bob@...  | 2 | bob@...  | FALSE (2 > 2) | 保留 |

最终 Id=3 被删除，Id=1 和 Id=2 保留。

### 解法二：子查询 + 非最小 Id

```sql
DELETE FROM Person
WHERE Id NOT IN (
  SELECT * FROM (
    SELECT MIN(Id) FROM Person GROUP BY Email
  ) AS tmp
);
```

**MySQL 特有的"套层子查询"问题**：
MySQL 不允许在 DELETE 中直接子查询同一张表（错误：`You can't specify target table 'Person' for update in FROM clause`）。解决方案是再套一层子查询，让 MySQL 将其物化成临时表，从而规避限制。

### 解法三：CTE + DELETE（MySQL 8.0+ / PostgreSQL）

```sql
WITH duplicates AS (
  SELECT Id,
         ROW_NUMBER() OVER (PARTITION BY Email ORDER BY Id) AS rn
  FROM Person
)
DELETE FROM Person
WHERE Id IN (SELECT Id FROM duplicates WHERE rn > 1);
```

**原理**：ROW_NUMBER() 按邮箱分区，按 Id 升序编号。rn=1 的是每组最小的 Id（保留），rn>1 的是要删除的。

## 性能考量

- 自连接方式需要 JOIN，大表时可能需要临时表
- 如果 Email 列有索引，自连接的 JOIN 条件可以走索引
- 子查询方式有 GROUP BY，也需要排序或哈希聚合

## 扩展

- 如果要保留 Id 最大的记录而非最小的？——把 `p1.Id > p2.Id` 改为 `p1.Id < p2.Id`
- 如何删除重复行且保留最近创建的？——用 `ORDER BY created_at DESC` 配合 ROW_NUMBER
- PostgreSQL 中可以用 `ctid` 系统列直接去重：
  ```sql
  DELETE FROM Person WHERE ctid NOT IN (
    SELECT MIN(ctid) FROM Person GROUP BY Email
  );
  ```
