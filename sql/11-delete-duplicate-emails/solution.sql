-- ============================================================
-- 第 11 题：删除重复的邮箱
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Person CASCADE;
CREATE TABLE Person (
    id    INT PRIMARY KEY,
    email VARCHAR
);

INSERT INTO Person (id, email) VALUES
(1, 'john@example.com'),
(2, 'bob@example.com'),
(3, 'john@example.com');

-- 查看删除前数据
SELECT '删除前：' AS info;
SELECT * FROM Person ORDER BY id;

-- 解法一：自连接使用 USING（PostgreSQL推荐）
DELETE FROM Person p1
USING Person p2
WHERE p1.email = p2.email AND p1.id > p2.id;

-- 解法二：子查询
-- DELETE FROM Person
-- WHERE id NOT IN (
--     SELECT min_id FROM (
--         SELECT MIN(id) AS min_id
--         FROM Person
--         GROUP BY email
--     ) t
-- );

-- 解法三：窗口函数
-- DELETE FROM Person
-- WHERE id IN (
--     SELECT id FROM (
--         SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
--         FROM Person
--     ) t WHERE rn > 1
-- );

-- 查看删除后数据
SELECT '删除后：' AS info;
SELECT * FROM Person ORDER BY id;
