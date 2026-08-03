-- ============================================================
-- 第 29 题：递归查询 - 组织架构
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee CASCADE;
CREATE TABLE Employee (
    id         INT PRIMARY KEY,
    name       VARCHAR,
    manager_id INT
);

INSERT INTO Employee (id, name, manager_id) VALUES
(1, '张CEO',  NULL),
(2, '李VP',   1),
(3, '王总监', 2),
(4, '赵经理', 3),
(5, '孙专员', 4),
(6, '周VP',   1),
(7, '吴经理', 6);

-- 解法：递归 CTE
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id,
           1 AS level,
           name::TEXT AS path
    FROM Employee
    WHERE manager_id IS NULL

    UNION ALL

    SELECT e.id, e.name, e.manager_id,
           ot.level + 1,
           ot.path || ' -> ' || e.name
    FROM Employee e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT id, name, level, path
FROM org_tree
ORDER BY id;
