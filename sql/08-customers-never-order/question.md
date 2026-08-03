
# 第 8 题：从不订购的客户

## 题目描述

有两张表 `Customers` 和 `Orders`：

**Customers 表：**

| 列名 | 类型    | 说明   |
|------|---------|--------|
| id   | INT     | 主键   |
| name | VARCHAR | 客户名 |

**Orders 表：**

| 列名       | 类型 | 说明       |
|------------|------|------------|
| id         | INT  | 主键       |
| customerId | INT  | 外键，客户 ID |

请编写 SQL，找出**从未下过订单**的客户姓名。

### 示例

**Customers 输入：**

| id | name |
|----|------|
| 1  | 张三 |
| 2  | 李四 |
| 3  | 王五 |
| 4  | 赵六 |

**Orders 输入：**

| id | customerId |
|----|------------|
| 1  | 3          |
| 2  | 1          |

**输出：**

| Customers |
|-----------|
| 李四      |
| 赵六      |

**解释：** 张三（id=1）和王五（id=3）下过订单，李四（id=2）和赵六（id=4）从未下单。

## 考察点

- `LEFT JOIN ... WHERE ... IS NULL` 模式查找"不存在于右表"的记录
- `NOT IN` 子查询
- `NOT EXISTS` 子查询

## 解题思路

### 思路一：LEFT JOIN + IS NULL（推荐）

```sql
SELECT c.name AS "Customers"
FROM Customers c
LEFT JOIN Orders o ON c.id = o.customerId
WHERE o.id IS NULL;
```

左连接后，没有订单的客户在 `Orders` 表的列全部为 `NULL`，用 `WHERE o.id IS NULL` 过滤出来即可。

### 思路二：NOT IN 子查询

```sql
SELECT name AS "Customers"
FROM Customers
WHERE id NOT IN (
    SELECT DISTINCT customerId FROM Orders
);
```

### 思路三：NOT EXISTS 子查询

```sql
SELECT name AS "Customers"
FROM Customers c
WHERE NOT EXISTS (
    SELECT 1 FROM Orders o WHERE o.customerId = c.id
);
```

### 三种方式对比

| 方式       | 性能（有索引时） | NULL安全性      | 推荐度     |
|-----------|-----------------|----------------|-----------|
| LEFT JOIN + IS NULL | 较好 | 安全 | ⭐⭐⭐   |
| NOT IN    | 一般 | 子查询有NULL时不安全 | ⭐⭐ |
| NOT EXISTS | 好 | 安全 | ⭐⭐⭐  |

`NOT IN` 需要特别小心：如果子查询结果中有 `NULL`，整个条件会返回空！因此推荐使用 `LEFT JOIN ... IS NULL` 或 `NOT EXISTS`。
