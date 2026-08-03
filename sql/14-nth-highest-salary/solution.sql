-- ============================================================
-- 第 14 题：第 N 高薪水
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee CASCADE;
DROP FUNCTION IF EXISTS getNthHighestSalary(INT);

CREATE TABLE Employee (
    id     INT PRIMARY KEY,
    salary INT
);

INSERT INTO Employee (id, salary) VALUES
(1, 100),
(2, 200),
(3, 300);

-- 解法一：LIMIT + OFFSET（推荐）
CREATE OR REPLACE FUNCTION getNthHighestSalary(N INT) RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT DISTINCT salary
        FROM Employee
        ORDER BY salary DESC
        LIMIT 1 OFFSET N - 1
    );
END;
$$ LANGUAGE plpgsql;

-- 测试
SELECT getNthHighestSalary(1) AS first_highest;
SELECT getNthHighestSalary(2) AS second_highest;
SELECT getNthHighestSalary(3) AS third_highest;
SELECT getNthHighestSalary(4) AS fourth_highest;

-- 解法二：DENSE_RANK()
-- CREATE OR REPLACE FUNCTION getNthHighestSalary(N INT) RETURNS INT AS $$
-- BEGIN
--     RETURN (
--         SELECT salary
--         FROM (
--             SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
--             FROM Employee
--         ) t
--         WHERE rnk = N
--         LIMIT 1
--     );
-- END;
-- $$ LANGUAGE plpgsql;
