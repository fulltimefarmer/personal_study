
# 第 16 题：部门最高工资的员工

## 题目描述

有两张表 `Employee` 和 `Department`：

**Employee 表：**

| 列名         | 类型    | 说明           |
|--------------|---------|----------------|
| id           | INT     | 主键           |
| name         | VARCHAR | 员工姓名       |
| salary       | INT     | 工资           |
| departmentId | INT     | 所属部门 ID    |

**Department 表：**

| 列名 | 类型    | 说明     |
|------|---------|----------|
| id   | INT     | 主键     |
| name | VARCHAR | 部门名称 |

请编写 SQL，查询每个部门中**工资最高的员工**。返回部门名称、员工姓名和工资。

**注意**：如果某个部门有多个员工并列最高工资，需要全部返回。

### 示例

**Employee 输入：**

| id | name | salary | departmentId |
|----|------|--------|-------------|
| 1  | 张三 | 70000  | 1           |
| 2  | 李四 | 90000  | 1           |
| 3  | 王五 | 80000  | 2           |
| 4  | 赵六 | 60000  | 2           |
| 5  | 孙七 | 90000  | 1           |
| 6  | 周八 | 70000  | 3           |

**Department 输入：**

| id | name   |
|----|--------|
| 1  | 技术部 |
| 2  | 销售部 |
| 3  | 行政部 |

**输出：**

| Department | Employee | Salary |
|------------|----------|--------|
| 技术部     | 李四     | 90000  |
| 技术部     | 孙七     | 90000  |
| 销售部     | 王五     | 80000  |
| 行政部     | 周八     | 70000  |

**解释：** 技术部最高工资 90000，有李四和孙七两人并列；销售部最高 80000，只有王五；行政部最高 70000，只有周八。

## 考察点

- 多表 `JOIN`
- 分组内最大值：`MAX() OVER()` 窗口函数 或 子查询
- `RANK()` / `DENSE_RANK()` 的 `PARTITION BY`

## 解题思路

### 思路一：DENSE_RANK() 窗口函数（推荐）

```sql
SELECT d.name AS "Department",
       e.name AS "Employee",
       e.salary AS "Salary"
FROM (
    SELECT name, salary, departmentId,
           DENSE_RANK() OVER (PARTITION BY departmentId ORDER BY salary DESC) AS rnk
    FROM Employee
) e
JOIN Department d ON e.departmentId = d.id
WHERE e.rnk = 1;
```

在 `Employee` 表内，按 `departmentId` 分区，按 `salary` 降序排名。每个部门的最高工资排第 1 名。`DENSE_RANK()` 确保并列最高都被保留。

### 思路二：关联子查询

```sql
SELECT d.name AS "Department",
       e.name AS "Employee",
       e.salary AS "Salary"
FROM Employee e
JOIN Department d ON e.departmentId = d.id
WHERE e.salary = (
    SELECT MAX(salary) FROM Employee e2 WHERE e2.departmentId = e.departmentId
);
```

### 思路三：IN 子查询

```sql
SELECT d.name AS "Department",
       e.name AS "Employee",
       e.salary AS "Salary"
FROM Employee e
JOIN Department d ON e.departmentId = d.id
WHERE (e.departmentId, e.salary) IN (
    SELECT departmentId, MAX(salary) FROM Employee GROUP BY departmentId
);
```

利用 PostgreSQL 的行构造器 `(col1, col2) IN (...)` ，将部门 ID 和最高工资组合进行匹配。

### 如何选择？

| 方式           | 并列最高 | 代码简洁度 | 推荐度 |
|---------------|---------|-----------|--------|
| DENSE_RANK()  | 自动保留 | ⭐⭐⭐    | ⭐⭐⭐  |
| 关联子查询     | 自动保留 | ⭐⭐      | ⭐⭐    |
| IN 子查询       | 自动保留 | ⭐⭐⭐    | ⭐⭐⭐  |
