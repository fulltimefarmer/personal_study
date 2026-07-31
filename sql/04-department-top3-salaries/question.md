# 部门前三薪水 (Department Top Three Salaries)

## 题目描述

Employee 表：

| Id | Name  | Salary | DepartmentId |
|----|-------|--------|--------------|
| 1  | Joe   | 85000  | 1            |
| 2  | Henry | 80000  | 2            |
| 3  | Sam   | 60000  | 2            |
| 4  | Max   | 90000  | 1            |
| 5  | Janet | 69000  | 1            |
| 6  | Randy | 85000  | 1            |
| 7  | Will  | 70000  | 1            |

Department 表：

| Id | Name     |
|----|----------|
| 1  | IT       |
| 2  | Sales    |

编写一个 SQL 查询，找出每个部门薪水前三名的员工。如果多人并列，全部返回。

**期望输出：**

| Department | Employee | Salary |
|------------|----------|--------|
| IT         | Max      | 90000  |
| IT         | Joe      | 85000  |
| IT         | Randy    | 85000  |
| IT         | Will     | 70000  |
| Sales      | Henry    | 80000  |
| Sales      | Sam      | 60000  |

说明：
- IT 部门：Max (90000) 第1，Joe+Randy (85000) 并列第2，Will (70000) 第3。由于并列，实际返回了 4 个人，但薪水的去重排名只有 3 个。
- Sales 部门只有两人，全部返回。

## 考察点

- 窗口函数 DENSE_RANK() + PARTITION BY（核心考点）
- RANK() vs DENSE_RANK() 在分组内排名的区别
- 多列 JOIN
- 子查询筛选

## 解题思路详解

### 为什么必须用 DENSE_RANK 而不是 RANK 或 ROW_NUMBER？

假设 IT 部门薪水为 [90000, 85000, 85000, 70000, 69000]：

| Salary | ROW_NUMBER | RANK | DENSE_RANK | 期望 |
|--------|-----------|------|------------|------|
| 90000  | 1         | 1    | 1          | ✓    |
| 85000  | 2         | 2    | 2          | ✓    |
| 85000  | 3         | 2    | 2          | ✓    |
| 70000  | 4         | 4    | 3          | ✓    |
| 69000  | 5         | 5    | 4          | ✗    |

- **ROW_NUMBER**：每个人分配不同序号，85000 的两人一个 2 一个 3，导致 Will (70000) 排第 4，被错误排除（正确应该保留）。
- **RANK**：相同值同排名但跳号，90000→1, 85000→2, 70000→4，Will 排名 4 > 3 被错误排除（正确应该保留，因为去重后他是第 3 个不同的薪水）。
- **DENSE_RANK**：90000→1, 85000→2, 70000→3，刚好前三，且并列的都能保留。

**结论：必须用 DENSE_RANK 才能实现"去重后前三名"的语义。**

### 核心 SQL 结构

```sql
SELECT Department, Employee, Salary
FROM (
  SELECT d.Name AS Department, e.Name AS Employee, e.Salary,
         DENSE_RANK() OVER (PARTITION BY e.DepartmentId ORDER BY e.Salary DESC) AS rnk
  FROM Employee e
  JOIN Department d ON e.DepartmentId = d.Id
) t
WHERE rnk <= 3;
```

`PARTITION BY DepartmentId` 按部门分区，每个部门内独立排名。`WHERE rnk <= 3` 保留前三。

## 执行计划分析

1. Employee 和 Department 执行 JOIN（Nested Loop 或 Hash Join）
2. 对 JOIN 结果按 DepartmentId 分区，按 Salary DESC 排序
3. 计算 DENSE_RANK
4. 用 WHERE rnk <= 3 过滤

主要开销在于排序。如果 Employee 表很大，可考虑在 `(DepartmentId, Salary DESC)` 上建索引加速排序。

## 扩展

- 如何查询"每个部门薪水前 10%"？——用 PERCENT_RANK() 或 NTILE(10) 窗口函数。
- 如果没有窗口函数（MySQL 5.7），如何实现？——用自连接 + 计数法（性能差但可行）：
  ```sql
  SELECT d.Name AS Department, e1.Name AS Employee, e1.Salary
  FROM Employee e1
  JOIN Department d ON e1.DepartmentId = d.Id
  WHERE 3 > (
    SELECT COUNT(DISTINCT e2.Salary)
    FROM Employee e2
    WHERE e2.DepartmentId = e1.DepartmentId AND e2.Salary > e1.Salary
  );
  ```
  含义：对于 e1 的每条记录，统计同部门中比它高的去重薪水数，如果 < 3，说明它是前三。
