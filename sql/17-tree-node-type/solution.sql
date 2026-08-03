-- ============================================================
-- 第 17 题：树节点类型判断
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Tree CASCADE;
CREATE TABLE Tree (
    id   INT,
    p_id INT
);

INSERT INTO Tree (id, p_id) VALUES
(1, NULL),
(2, 1),
(3, 1),
(4, 2),
(5, 2);

-- 解法一：CASE WHEN + 子查询（推荐）
SELECT id,
       CASE
           WHEN p_id IS NULL THEN 'Root'
           WHEN id IN (SELECT DISTINCT p_id FROM Tree WHERE p_id IS NOT NULL) THEN 'Inner'
           ELSE 'Leaf'
       END AS "Type"
FROM Tree;

-- 解法二：LEFT JOIN 方式
-- SELECT t1.id,
--        CASE
--            WHEN t1.p_id IS NULL THEN 'Root'
--            WHEN t2.id IS NOT NULL THEN 'Inner'
--            ELSE 'Leaf'
--        END AS "Type"
-- FROM Tree t1
-- LEFT JOIN (SELECT DISTINCT p_id AS id FROM Tree WHERE p_id IS NOT NULL) t2
--     ON t1.id = t2.id;
