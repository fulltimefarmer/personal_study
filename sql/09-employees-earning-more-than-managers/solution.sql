-- ============================================================
-- 第 9 题：超过经理收入的员工
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee CASCADE;
CREATE TABLE Employee (
    id        INT PRIMARY KEY,
    name      VARCHAR,
    salary    INT,
    managerId INT
);

INSERT INTO Employee (id, name, salary, managerId) VALUES
(1, '张总', 80000, NULL),
(2, '小王', 60000, 1),
(3, '小李', 75000, 1),
(4, '小赵', 85000, 1),
(5, '小孙', 50000, 3);

-- 解法：自连接（Self Join）
SELECT e1.name AS "Employee"
FROM Employee e1
JOIN Employee e2 ON e1.managerId = e2.id
WHERE e1.salary > e2.salary;
