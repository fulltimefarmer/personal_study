# 第 N 高薪水 (Nth Highest Salary)

## 题目描述

Employee 表：

| Id | Salary |
|----|--------|
| 1  | 100    |
| 2  | 200    |
| 3  | 300    |

编写一个 SQL 查询，获取 Employee 表中第 N 高的薪水（Salary）。如果不存在第 N 高的薪水，查询应返回 null。

**示例 1：**

输入：
```
Employee 表:
+----+--------+
| Id | Salary |
+----+--------+
| 1  | 100    |
| 2  | 200    |
| 3  | 300    |
+----+--------+
n = 2
```

输出：
```
+------------------------+
| getNthHighestSalary(2) |
+------------------------+
| 200                    |
+------------------------+
```

**示例 2：**

n = 4 时，表中只有 3 条记录，不存在第 4 高薪水：

输出：
```
+------------------------+
| getNthHighestSalary(4) |
+------------------------+
| NULL                   |
+------------------------+
```

## 考察点

- 子查询 / LIMIT OFFSET / 窗口函数 DENSE_RANK
- NULL 值处理（IFNULL / COALESCE）
- 函数式写法（CREATE FUNCTION）
- 变量声明与使用（DECLARE, SET）

## 解题思路详解

### 1. 为什么需要 DISTINCT？

假设 Employee 表中有两条薪水为 300 的记录：
| Id | Salary |
|----|--------|
| 1  | 100    |
| 2  | 300    |
| 3  | 300    |

如果不加 DISTINCT，按 Salary 降序排列取第 2 条会得到 300（因为两条 300 都参与排序），但第二高薪水实际应该是 100。DISTINCT 确保相同薪水只占一个排名位置。

### 2. LIMIT + OFFSET 原理

```sql
SELECT DISTINCT Salary FROM Employee ORDER BY Salary DESC LIMIT 1 OFFSET 2;
```

- `ORDER BY Salary DESC`：从高到低排序
- `LIMIT 1`：只取 1 条记录
- `OFFSET N-1`：跳过前 N-1 条，第 N 条即为第 N 高薪水

当 OFFSET 超出记录数时，查询返回空结果集（不是 NULL），因此外层需要 IFNULL/COALESCE 包装。

### 3. 窗口函数方案：DENSE_RANK() vs RANK() vs ROW_NUMBER()

设有薪水值 [300, 300, 200, 100]：

| Salary | ROW_NUMBER() | RANK() | DENSE_RANK() |
|--------|-------------|--------|--------------|
| 300    | 1           | 1      | 1            |
| 300    | 2           | 1      | 1            |
| 200    | 3           | 3      | 2            |
| 100    | 4           | 4      | 3            |

- **ROW_NUMBER()**：严格递增编号，相同值也分配不同序号（取决于 ORDER BY 及数据库实现）
- **RANK()**：相同值排相同名次，但下一个名次跳过（留空位），即 1,1,3,4
- **DENSE_RANK()**：相同值排相同名次，下一个名次不跳过，即 1,1,2,3

本题要求"第 N 高薪水"，相同薪水应该算同一高度，所以 DENSE_RANK 最合适。

## 执行计划与性能考量

- **LIMIT OFFSET 方案**：
  - 需要全表扫描 + 排序，时间复杂度 O(n log n)
  - 优点：简单直观，MySQL 中对小数据量足够快
  - 缺点：OFFSET 较大时需要扫描并丢弃大量行

- **DENSE_RANK 窗口函数方案**：
  - 同样需要全表扫描 + 排序 + 窗口计算
  - 优点：语义清晰，易于扩展到 Top K 等问题
  - 缺点：在 MySQL 5.7 中不支持窗口函数（MySQL 8.0+ 支持）

- **标量子查询方案**：
  ```sql
  SELECT MAX(Salary) FROM Employee WHERE Salary < (SELECT MAX(Salary) FROM Employee)
  ```
  这种方案只适用于 N=2（第二高），N 为变量时需要递归或循环，不通用。

## 扩展

- 如果允许多个相同薪水并列，如何处理？——使用 DENSE_RANK 即可。
- 如果没有 CREATE FUNCTION 权限怎么办？——可在应用层传参，或使用存储过程。
- 如何返回第 N 高的所有员工信息？——用 DENSE_RANK 子查询 JOIN 回原表。
