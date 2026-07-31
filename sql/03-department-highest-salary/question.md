# 部门最高薪水 (Department Highest Salary)

## 题目描述

Employee 表包含所有员工信息，每个员工有其对应的 Id、Salary 和 DepartmentId。

| Id | Name  | Salary | DepartmentId |
|----|-------|--------|--------------|
| 1  | Joe   | 70000  | 1            |
| 2  | Jim   | 90000  | 1            |
| 3  | Henry | 80000  | 2            |
| 4  | Sam   | 60000  | 2            |
| 5  | Max   | 90000  | 1            |

Department 表包含公司所有部门信息：

| Id | Name     |
|----|----------|
| 1  | IT       |
| 2  | Sales    |

编写一个 SQL 查询，找出每个部门中薪水最高的员工。返回 Department、Employee、Salary 三列。

**期望输出：**

| Department | Employee | Salary |
|------------|----------|--------|
| IT         | Jim      | 90000  |
| IT         | Max      | 90000  |
| Sales      | Henry    | 80000  |

注意：IT 部门有两个人都拿了最高薪 90000，需要都返回。

## 考察点

- INNER JOIN 连接多表
- 子查询配合 IN 进行多列匹配
- 窗口函数 RANK() / DENSE_RANK() 在分组中的应用（PARTITION BY）
- 多列 IN 子查询的语法（MySQL/PostgreSQL 均支持）

## 解题思路详解

### 解法一：子查询 + 多列 IN

```sql
SELECT d.Name AS Department, e.Name AS Employee, e.Salary
FROM Employee e
JOIN Department d ON e.DepartmentId = d.Id
WHERE (e.DepartmentId, e.Salary) IN (
  SELECT DepartmentId, MAX(Salary) FROM Employee GROUP BY DepartmentId
);
```

**关键点：多列 IN 子查询**

`WHERE (e.DepartmentId, e.Salary) IN (...)` 是 SQL 标准语法，MySQL 和 PostgreSQL 都支持。它同时匹配部门的 ID 和部门最高薪水的组合。

如果没有多列 IN，可以这样拆解：
```sql
WHERE e.Salary = (SELECT MAX(Salary) FROM Employee WHERE DepartmentId = e.DepartmentId)
```
这种方式是**关联子查询**，对于 Employee 的每一行都会执行一次子查询，性能较差。

### 解法二：窗口函数 RANK() OVER (PARTITION BY)

```sql
SELECT Department, Employee, Salary
FROM (
  SELECT d.Name AS Department, e.Name AS Employee, e.Salary,
         RANK() OVER (PARTITION BY e.DepartmentId ORDER BY e.Salary DESC) AS rnk
  FROM Employee e
  JOIN Department d ON e.DepartmentId = d.Id
) t
WHERE rnk = 1;
```

**PARTITION BY 原理**：
- `PARTITION BY DepartmentId` 把数据按部门分组
- 在每个分组内独立执行 `ORDER BY Salary DESC`
- 每个分组的第一名都会被保留

**RANK() vs DENSE_RANK() 在本题的选择**：
- 如果部门最高薪只有一个人，两者结果相同
- 如果多人并列最高（如 IT 部门的 Jim 和 Max 都是 90000），两者都能返回多行
- RANK() 和 DENSE_RANK() 在 rnk = 1 时结果一致，因为第一名不存在跳号问题

### JOIN vs LEFT JOIN

本题使用 INNER JOIN 即可，因为 Employee 表中的 DepartmentId 都对应有效的部门。如果某些员工没有部门（DepartmentId = NULL），用 LEFT JOIN 可以保留这些记录，但这与题目要求不符。

## 执行计划与性能

| 解法 | 扫描次数 | 排序开销 | 适用场景 |
|------|---------|---------|---------|
| 多列 IN | 2 次（一次 Group By，一次主查询） | 无额外排序 | 小到中型表 |
| 窗口函数 | 1 次扫描 + 窗口排序 | PARTITION BY + ORDER BY | 大型表，MySQL 8.0+ |
| 关联子查询 | N+1 次扫描 | 无 | 不推荐，性能最差 |

## 扩展

- 如何查询每个部门的薪水第二高的员工？——将 rnk = 1 改为 rnk = 2 即可（用 DENSE_RANK）
- 如果部门可能没有任何员工（空部门），如何展示？——需要用 LEFT JOIN 从 Department 开始
- 如果最高薪水为 NULL 怎么办？——需额外处理，通常加 `WHERE Salary IS NOT NULL`
