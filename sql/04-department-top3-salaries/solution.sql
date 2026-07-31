-- ============================================
-- 部门前三薪水 (Department Top Three Salaries)
-- ============================================

-- 解法一：窗口函数 DENSE_RANK() —— 推荐（MySQL 8.0+ / PostgreSQL）
-- 思路：
--   1. DENSE_RANK() OVER (PARTITION BY DepartmentId ORDER BY Salary DESC) 按部门排名
--   2. 外层 WHERE rnk <= 3 取前三
-- 为什么用 DENSE_RANK 而不是 RANK？
--   - RANK(): 排名跳号，90000(1), 85000(2), 85000(2), 70000(4)
--     70000 的排名是 4 > 3，不会被返回，但去重后他是第 3 个不同的薪水值，应该返回
--   - DENSE_RANK(): 排名不跳号，90000(1), 85000(2), 85000(2), 70000(3)
--     70000 排名 3 <= 3，正确返回
SELECT Department, Employee, Salary
FROM (
  SELECT d.Name AS Department,
         e.Name AS Employee,
         e.Salary,
         DENSE_RANK() OVER (PARTITION BY e.DepartmentId ORDER BY e.Salary DESC) AS rnk
  FROM Employee e
  JOIN Department d ON e.DepartmentId = d.Id
) t
WHERE rnk <= 3
ORDER BY Department, Salary DESC;

-- 解法二：自连接 + COUNT(DISTINCT) —— 兼容旧版 MySQL（5.7 以下）
-- 思路：
--   对每条记录 e1，统计同部门中去重后比 e1.Salary 大的薪水数量 cnt
--   如果 cnt < 3，说明 e1 的薪水是部门中去重后的前三名
-- 原理详解（以 IT 部门为例）：
--   对于 Max (90000)：比 90000 大的 = 0，0 < 3 → 保留
--   对于 Joe (85000)：比 85000 大的 = 1（90000），1 < 3 → 保留
--   对于 Randy(85000)：比 85000 大的 = 1（90000），1 < 3 → 保留
--   对于 Will (70000)：比 70000 大的 = 2（90000, 85000），2 < 3 → 保留
--   对于 Janet(69000)：比 69000 大的 = 3（90000, 85000, 70000），3 < 3 → FALSE，排除
-- 缺点：关联子查询，时间复杂度 O(n²)，大数据量时性能差
SELECT d.Name AS Department, e1.Name AS Employee, e1.Salary
FROM Employee e1
JOIN Department d ON e1.DepartmentId = d.Id
WHERE 3 > (
  SELECT COUNT(DISTINCT e2.Salary)
  FROM Employee e2
  WHERE e2.DepartmentId = e1.DepartmentId
    AND e2.Salary > e1.Salary
)
ORDER BY Department, Salary DESC;

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
  (1, 'Joe',   85000, 1),
  (2, 'Henry', 80000, 2),
  (3, 'Sam',   60000, 2),
  (4, 'Max',   90000, 1),
  (5, 'Janet', 69000, 1),
  (6, 'Randy', 85000, 1),
  (7, 'Will',  70000, 1);

INSERT INTO Department VALUES
  (1, 'IT'),
  (2, 'Sales');
*/
