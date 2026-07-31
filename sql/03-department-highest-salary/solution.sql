-- ============================================
-- 部门最高薪水 (Department Highest Salary)
-- ============================================

-- 解法一：多列 IN 子查询（推荐，兼容性好）
-- 思路：
--   1. 子查询按 DepartmentId 分组，用 MAX(Salary) 获取每个部门的最高薪
--   2. 外层用多列 IN 语法 (DepartmentId, Salary) 匹配子查询结果
--   3. JOIN Department 获取部门名称
-- 注意：
--   - 多列 IN 是 SQL 标准语法，MySQL/PostgreSQL 均支持
--   - 如果有多个员工并列最高薪，都会返回
SELECT d.Name AS Department, e.Name AS Employee, e.Salary
FROM Employee e
JOIN Department d ON e.DepartmentId = d.Id
WHERE (e.DepartmentId, e.Salary) IN (
  SELECT DepartmentId, MAX(Salary)
  FROM Employee
  GROUP BY DepartmentId
);

-- 解法二：窗口函数 RANK() / DENSE_RANK()（MySQL 8.0+ / PostgreSQL）
-- 思路：
--   RANK() 按部门分区 (PARTITION BY)，按薪水降序排名
--   外层 WHERE rnk = 1 取每个部门的第一名
-- 原理：
--   PARTITION BY DepartmentId 将数据按部门切成独立窗口
--   每个窗口内独立排序，排名从 1 开始
SELECT Department, Employee, Salary
FROM (
  SELECT d.Name AS Department, e.Name AS Employee, e.Salary,
         RANK() OVER (PARTITION BY e.DepartmentId ORDER BY e.Salary DESC) AS rnk
  FROM Employee e
  JOIN Department d ON e.DepartmentId = d.Id
) t
WHERE rnk = 1;

-- 解法三：关联子查询（简单但不推荐，性能差）
-- 思路：
--   外层遍历 Employee 每一行
--   子查询返回该员工所在部门的最高薪
--   如果该员工薪水等于部门最高薪，则保留
-- 缺点：对 Employee 每行都执行一次子查询，时间复杂度 O(n²)
SELECT d.Name AS Department, e.Name AS Employee, e.Salary
FROM Employee e
JOIN Department d ON e.DepartmentId = d.Id
WHERE e.Salary = (
  SELECT MAX(Salary) FROM Employee WHERE DepartmentId = e.DepartmentId
);

-- ============================================
-- 建表与测试数据
-- ============================================
/*
CREATE TABLE Employee (
  Id INT PRIMARY KEY,
  Name VARCHAR(50),
  Salary INT,
  DepartmentId INT
);

CREATE TABLE Department (
  Id INT PRIMARY KEY,
  Name VARCHAR(50)
);

INSERT INTO Employee VALUES
  (1, 'Joe',   70000, 1),
  (2, 'Jim',   90000, 1),
  (3, 'Henry', 80000, 2),
  (4, 'Sam',   60000, 2),
  (5, 'Max',   90000, 1);

INSERT INTO Department VALUES
  (1, 'IT'),
  (2, 'Sales');
*/
