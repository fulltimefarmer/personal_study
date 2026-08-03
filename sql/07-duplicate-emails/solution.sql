-- ============================================================
-- 第 7 题：查找重复的邮箱
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Person CASCADE;
CREATE TABLE Person (
    id    INT PRIMARY KEY,
    email VARCHAR
);

INSERT INTO Person (id, email) VALUES
(1, 'a@example.com'),
(2, 'c@example.com'),
(3, 'a@example.com'),
(4, 'b@example.com');

-- 解法：GROUP BY + HAVING COUNT(*) > 1
SELECT email AS "Email"
FROM Person
GROUP BY email
HAVING COUNT(*) > 1;

-- 扩展：查找重复邮箱的具体所有行
-- SELECT * FROM Person
-- WHERE email IN (
--     SELECT email FROM Person GROUP BY email HAVING COUNT(*) > 1
-- );
