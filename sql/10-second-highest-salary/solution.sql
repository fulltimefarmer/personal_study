-- ============================================================
-- 第 10 题：第二高薪水
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee CASCADE;
CREATE TABLE Employee (
    id     INT PRIMARY KEY,
    salary INT
);

INSERT INTO Employee (id, salary) VALUES
(1, 100),
(2, 200),
(3, 300);

-- 解法一：DISTINCT + LIMIT + OFFSET（推荐）
SELECT (
    SELECT DISTINCT salary
    FROM Employee
    ORDER BY salary DESC
    LIMIT 1 OFFSET 1
) AS "SecondHighestSalary";

-- 解法二：MAX + 子查询
-- SELECT MAX(salary) AS "SecondHighestSalary"
-- FROM Employee
-- WHERE salary < (SELECT MAX(salary) FROM Employee);

-- 解法三：DENSE_RANK()
-- SELECT (
--     SELECT salary
--     FROM (
--         SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
--         FROM Employee
--     ) t
--     WHERE rnk = 2
--     LIMIT 1
-- ) AS "SecondHighestSalary";

-- 测试空结果返回 NULL 的场景（可选运行）
-- DELETE FROM Employee;
-- INSERT INTO Employee (id, salary) VALUES (1, 100);
-- SELECT (
--     SELECT DISTINCT salary
--     FROM Employee
--     ORDER BY salary DESC
--     LIMIT 1 OFFSET 1
-- ) AS "SecondHighestSalary";
