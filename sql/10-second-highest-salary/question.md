
# 第 10 题：第二高薪水

## 题目描述

有一张 `Employee` 表，包含员工的 ID 和薪水：

| 列名   | 类型    | 说明     |
|--------|---------|----------|
| id     | INT     | 主键     |
| salary | INT     | 工资     |

请编写 SQL 查询，获取表中**第二高的薪水**。如果不存在第二高的薪水（比如表中只有一行，或者所有工资相同），查询应该返回 `NULL`。

### 示例

**示例1：**

输入：

| id | salary |
|----|--------|
| 1  | 100    |
| 2  | 200    |
| 3  | 300    |

输出：

| SecondHighestSalary |
|---------------------|
| 200                 |

**示例2：**

输入：

| id | salary |
|----|--------|
| 1  | 100    |

输出：

| SecondHighestSalary |
|---------------------|
| NULL                |

## 考察点

- `DISTINCT` 去重的必要性（相同工资不能算两个排名）
- `LIMIT` + `OFFSET` 分页取值
- 空结果返回 `NULL` 的处理（外层子查询自动返回 NULL）
- 窗口函数 `DENSE_RANK()`
- `MAX` + 子查询（兼容老数据库）

## 解题思路

### 思路一：DISTINCT + LIMIT + OFFSET（推荐）

```sql
SELECT (
    SELECT DISTINCT salary
    FROM Employee
    ORDER BY salary DESC
    LIMIT 1 OFFSET 1
) AS "SecondHighestSalary";
```

1. `DISTINCT` 去重，确保相同薪水只占一个排名位置
2. 按薪水降序排列，`OFFSET 1` 跳过第一行，`LIMIT 1` 取下一行
3. 外层 `SELECT (...)` 包裹子查询：如果子查询没有返回行，外层自动返回 `NULL`

### 思路二：MAX + 子查询

```sql
SELECT MAX(salary) AS "SecondHighestSalary"
FROM Employee
WHERE salary < (SELECT MAX(salary) FROM Employee);
```

先查出最高工资，再在所有小于最高工资的工资中取最大值。如果不存在（所有工资相同或只有一行），`MAX` 自动返回 `NULL`。

### 思路三：窗口函数 DENSE_RANK()

```sql
SELECT (
    SELECT salary FROM (
        SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
        FROM Employee
    ) t
    WHERE rnk = 2
    LIMIT 1
) AS "SecondHighestSalary";
```

### 关键对比：RANK vs DENSE_RANK vs ROW_NUMBER

| 工资  | ROW_NUMBER | RANK | DENSE_RANK |
|-------|-----------|------|------------|
| 300   | 1         | 1    | 1          |
| 200   | 2         | 2    | 2          |
| 200   | 3         | 2    | 2          |
| 100   | 4         | 4    | 3          |

如果工资 300 的员工有两个，用 `DENSE_RANK()` 第二高是 200；用 `RANK()` 第二高可能不存在（因为两个并列第一，下一个排名是 3）。

本题要求"第二高薪水"（指第二高的薪水**值**，而不是第二行），所以使用 `DISTINCT` 或 `DENSE_RANK` 都是合适的。
