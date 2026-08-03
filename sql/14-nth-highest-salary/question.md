
# 第 14 题：第 N 高薪水

## 题目描述

在 `Employee` 表的基础上（同第 10 题），请编写一个**通用的 SQL 函数** `getNthHighestSalary(N INT)`，返回表中第 N 高的薪水。如果不存在第 N 高的薪水，则返回 `NULL`。

| 列名   | 类型    | 说明     |
|--------|---------|----------|
| id     | INT     | 主键     |
| salary | INT     | 工资     |

### 示例

`Employee` 表数据：

| id | salary |
|----|--------|
| 1  | 100    |
| 2  | 200    |
| 3  | 300    |

- `getNthHighestSalary(1)` 返回 `300`（最高）
- `getNthHighestSalary(2)` 返回 `200`（第二高）
- `getNthHighestSalary(3)` 返回 `100`（第三高）
- `getNthHighestSalary(4)` 返回 `NULL`（不存在第四高）

## 考察点

- PostgreSQL 函数定义：`CREATE OR REPLACE FUNCTION`
- `LIMIT 1 OFFSET N - 1` 的通用化
- `DENSE_RANK()` 与参数化的结合
- 函数中的参数使用与返回类型

## 解题思路

### 思路一：LIMIT + OFFSET（最简单）

```sql
CREATE OR REPLACE FUNCTION getNthHighestSalary(N INT) RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT DISTINCT salary
        FROM Employee
        ORDER BY salary DESC
        LIMIT 1 OFFSET N - 1
    );
END;
$$ LANGUAGE plpgsql;
```

`OFFSET N - 1` 跳过前 N-1 行，取第 N 行的 `DISTINCT` 薪水。如果不存在，子查询返回 `NULL`。

### 思路二：DENSE_RANK()（语义更清晰）

```sql
CREATE OR REPLACE FUNCTION getNthHighestSalary(N INT) RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT salary
        FROM (
            SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
            FROM Employee
        ) t
        WHERE rnk = N
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;
```

### 关键点

1. `LIMIT 1 OFFSET N - 1` 中，`OFFSET` 不能直接接受表达式（在某些数据库中），但在 PostgreSQL 中支持动态参数
2. 使用 `DISTINCT` 确保相同薪水只算一个排名
3. 如果 N ≤ 0，`OFFSET -1` 会导致错误，面试中应和面试官讨论这个边界情况

### 扩展

- 如果题目要求不使用函数，只用一个普通查询返回第 N 高，可以用 CTE + 变量
- 在 MySQL 中，`LIMIT` 的 `OFFSET` 不接受子查询，需要使用 `SET @N = ...` 声明变量
