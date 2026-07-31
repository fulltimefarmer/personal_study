# 从不订购的客户 (Customers Who Never Order)

## 题目描述

Customers 表：

| Id | Name  |
|----|-------|
| 1  | Joe   |
| 2  | Henry |
| 3  | Sam   |
| 4  | Max   |

Orders 表：

| Id | CustomerId |
|----|------------|
| 1  | 3          |
| 2  | 1          |

编写一个 SQL 查询，查找从不订购任何产品的客户。

**期望输出：**

| Customers |
|-----------|
| Henry     |
| Max       |

说明：Joe (Id=1) 和 Sam (Id=3) 在 Orders 表中有记录（下过订单），Henry (Id=2) 和 Max (Id=4) 没有。

## 考察点

- LEFT JOIN + IS NULL（反连接）
- NOT EXISTS 子查询
- NOT IN 子查询（及 NULL 陷阱）
- 三种反连接写法的对比与性能

## 解题思路详解

### 什么是"反连接"（Anti Join）？

反连接 = 找出在一张表中存在但在另一张表中不存在的记录。SQL 中没有原生的 ANTI JOIN 关键字，但可以用以下三种方式模拟。

### 解法一：LEFT JOIN + IS NULL（最推荐）

```sql
SELECT c.Name AS Customers
FROM Customers c
LEFT JOIN Orders o ON c.Id = o.CustomerId
WHERE o.CustomerId IS NULL;
```

**原理**：
- LEFT JOIN 保留左表（Customers）的所有行
- 对于没有匹配订单的客户，Orders 表的列全部为 NULL
- `WHERE o.CustomerId IS NULL` 刚好筛选出这些客户

**为什么用 `o.CustomerId IS NULL` 而不是 `o.Id IS NULL`？**

因为 CustomerId 是 JOIN 条件列，如果它本身可能为 NULL，过滤它更准确。但在这个场景中，Orders 表如果某行 CustomerId = NULL 是不太真实的（谁下的单？），所以 `o.Id IS NULL` 也行。最佳实践是用 JOIN 列来判断。

### 解法二：NOT EXISTS（性能通常最好）

```sql
SELECT c.Name AS Customers
FROM Customers c
WHERE NOT EXISTS (
  SELECT 1 FROM Orders o WHERE o.CustomerId = c.Id
);
```

**原理**：
- 对 Customers 的每一行，检查 Orders 中是否存在对应的 CustomerId
- NOT EXISTS 子查询只要找到一条匹配就会停止（短路优化），不再继续扫描

**NOT EXISTS 的优点**：
- 短路机制：一旦找到匹配就停止，对数据倾斜场景（有订单的客户占多数）很高效
- 不受 NULL 影响：EXISTS 只关心返回结果集是否为空
- 通常优化器会将其转换为 ANTI JOIN 执行计划

### 解法三：NOT IN（需注意 NULL 陷阱）

```sql
SELECT c.Name AS Customers
FROM Customers c
WHERE c.Id NOT IN (
  SELECT CustomerId FROM Orders WHERE CustomerId IS NOT NULL
);
```

**NOT IN 的 NULL 陷阱**：

```sql
-- 这个查询可能返回空结果！
SELECT 'found' WHERE 1 NOT IN (2, NULL);  -- 返回空
```

原因：`1 NOT IN (2, NULL)` 展开为 `1 != 2 AND 1 != NULL`，`1 != NULL` 的结果是 **UNKNOWN**（不是 TRUE 也不是 FALSE），在 SQL 的三值逻辑中，WHERE 只接受 TRUE 的结果，所以整行被丢弃。

因此使用 NOT IN 时应确保子查询不会返回 NULL，或加 `WHERE ... IS NOT NULL` 过滤。但即使如此，NOT IN 的性能通常也不如 NOT EXISTS。

### 三值逻辑回顾

SQL 的比较有三种结果：TRUE、FALSE、UNKNOWN。

| AND       | TRUE | FALSE | UNKNOWN |
|-----------|------|-------|---------|
| TRUE      | T    | F     | U       |
| FALSE     | F    | F     | F       |
| UNKNOWN   | U    | F     | U       |

| OR        | TRUE | FALSE | UNKNOWN |
|-----------|------|-------|---------|
| TRUE      | T    | T     | T       |
| FALSE     | T    | F     | U       |
| UNKNOWN   | T    | U     | U       |

WHERE 子句只保留结果为 TRUE 的行。

## 三种解法性能对比

| 解法 | 性能 | 可读性 | NULL 安全 | 推荐度 |
|------|------|--------|-----------|--------|
| LEFT JOIN + IS NULL | 中 | 高 | 安全 | ★★★★★ |
| NOT EXISTS | 高（短路） | 中 | 安全 | ★★★★ |
| NOT IN | 低 | 高 | 不安全 | ★★ |

实际中，大多数优化器会把 LEFT JOIN + IS NULL 和 NOT EXISTS 优化成相同的执行计划（ANTI JOIN），两者差距不大。NOT IN 则不推荐。

## 扩展

- 如果要查"至少下过两单的客户"，用 `GROUP BY ... HAVING COUNT(*) > 1`
- 如果要查"每个客户的下单数（包括 0）"，用 LEFT JOIN + COUNT：
  ```sql
  SELECT c.Name, COUNT(o.Id) AS order_count
  FROM Customers c
  LEFT JOIN Orders o ON c.Id = o.CustomerId
  GROUP BY c.Id, c.Name;
  ```
  **注意**：COUNT(o.Id) 而非 COUNT(*)，因为 COUNT(*) 会把 NULL 行也计为 1，COUNT(列名) 不计数 NULL。
