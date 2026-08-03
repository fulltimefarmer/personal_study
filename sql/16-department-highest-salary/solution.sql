-- ============================================================
-- 第 16 题：部门最高工资的员工
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee CASCADE;
DROP TABLE IF EXISTS Department CASCADE;

CREATE TABLE Department (
    id   INT PRIMARY KEY,
    name VARCHAR
);

CREATE TABLE Employee (
    id           INT PRIMARY KEY,
    name         VARCHAR,
    salary       INT,
    departmentId INT,
    FOREIGN KEY (departmentId) REFERENCES Department(id)
);

INSERT INTO Department (id, name) VALUES
(1, '技术部'),
(2, '销售部'),
(3, '行政部');

INSERT INTO Employee (id, name, salary, departmentId) VALUES
(1, '张三', 70000, 1),
(2, '李四', 90000, 1),
(3, '王五', 80000, 2),
(4, '赵六', 60000, 2),
(5, '孙七', 90000, 1),
(6, '周八', 70000, 3);

-- 解法一：DENSE_RANK() 窗口函数（推荐）
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

-- 解法二：IN 子查询
-- SELECT d.name AS "Department",
--        e.name AS "Employee",
--        e.salary AS "Salary"
-- FROM Employee e
-- JOIN Department d ON e.departmentId = d.id
-- WHERE (e.departmentId, e.salary) IN (
--     SELECT departmentId, MAX(salary) FROM Employee GROUP BY departmentId
-- );
