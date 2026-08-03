-- ============================================================
-- 第 27 题：平均工资 - 部门 vs 公司
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee CASCADE;
CREATE TABLE Employee (
    id         INT PRIMARY KEY,
    department VARCHAR,
    salary     DECIMAL(10,2)
);

INSERT INTO Employee (id, department, salary) VALUES
(1, '技术部', 15000),
(2, '技术部', 12000),
(3, '技术部', 18000),
(4, '销售部', 10000),
(5, '销售部', 13000),
(6, '行政部', 9000);

-- 解法
SELECT id, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank,
       ROUND(AVG(salary) OVER (PARTITION BY department), 2) AS dept_avg,
       ROUND(AVG(salary) OVER (), 2) AS company_avg,
       CASE
           WHEN salary > AVG(salary) OVER (PARTITION BY department) THEN '高于'
           WHEN salary < AVG(salary) OVER (PARTITION BY department) THEN '低于'
           ELSE '等于'
       END AS vs_dept,
       CASE
           WHEN salary > AVG(salary) OVER () THEN '高于'
           WHEN salary < AVG(salary) OVER () THEN '低于'
           ELSE '等于'
       END AS vs_company
FROM Employee
ORDER BY department, dept_rank;
