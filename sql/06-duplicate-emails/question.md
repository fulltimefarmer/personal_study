# 重复的邮箱 (Duplicate Emails)

## 题目描述

Person 表：

| Id | Email            |
|----|------------------|
| 1  | a@b.com          |
| 2  | c@d.com          |
| 3  | a@b.com          |

编写一个 SQL 查询，查找 Person 表中所有重复的邮箱。

**期望输出：**

| Email   |
|---------|
| a@b.com |

说明：a@b.com 出现了两次，是重复的。

## 考察点

- GROUP BY + HAVING（聚合过滤）
- COUNT() 聚合函数
- GROUP BY 的执行顺序与原理

## 解题思路详解

### 核心查询

```sql
SELECT Email
FROM Person
GROUP BY Email
HAVING COUNT(Id) > 1;
```

### SQL 查询执行顺序回顾

SQL 语句的逻辑执行顺序（不是物理执行顺序）：
```
FROM → WHERE → GROUP BY → 聚合函数(COUNT/SUM/...) → HAVING → SELECT → ORDER BY → LIMIT
```

关键理解：
1. **WHERE 在 GROUP BY 之前**：WHERE 不能使用聚合函数，因为分组还没发生
2. **HAVING 在 GROUP BY 之后**：HAVING 专门用于过滤分组后的聚合结果

所以 `WHERE COUNT(*) > 1` 会报错，必须用 `HAVING COUNT(*) > 1`。

### COUNT 的几种形式

| 写法 | 含义 |
|------|------|
| COUNT(*) | 统计行数（包括 NULL 行） |
| COUNT(Id) | 统计 Id 不为 NULL 的行数 |
| COUNT(DISTINCT Email) | 统计去重后的 Email 数量 |
| COUNT(1) | 等价于 COUNT(*)，常数占位 |

本题三种都行（Id 通常非空），但 `COUNT(*)` 最通用。

### MySQL 扩展语法（不推荐）

MySQL 允许 SELECT 非聚合列而不报错：
```sql
SELECT Id, Email FROM Person GROUP BY Email HAVING COUNT(*) > 1;
```
但这在标准 SQL 和其他数据库（PostgreSQL）中会报错，因为它不确定返回哪个 Id。应避免依赖这种行为。如果确实需要返回 Id，可用窗口函数先标记重复行再筛选。

## 执行计划与性能

- GROUP BY Email 如果 Email 列有索引，可以利用索引加速分组
- 如果数据量极大，可考虑在 Email 上建唯一索引来从源头防止重复
- HAVING 过滤发生在分组之后，不是性能瓶颈

## 扩展

- 如何同时返回重复邮箱及其出现次数？
  ```sql
  SELECT Email, COUNT(*) AS cnt FROM Person GROUP BY Email HAVING COUNT(*) > 1;
  ```
- 如何找出没有重复的邮箱（只出现一次）？
  ```sql
  SELECT Email FROM Person GROUP BY Email HAVING COUNT(*) = 1;
  ```
- 如何找出重复邮箱中所有相关行的完整信息？
  ```sql
  SELECT * FROM Person WHERE Email IN (
    SELECT Email FROM Person GROUP BY Email HAVING COUNT(*) > 1
  );
  ```
