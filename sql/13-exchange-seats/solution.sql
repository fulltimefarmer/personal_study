-- ============================================================
-- 第 13 题：换座位
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Seat CASCADE;
CREATE TABLE Seat (
    id      INT PRIMARY KEY,
    student VARCHAR
);

INSERT INTO Seat (id, student) VALUES
(1, '张三'),
(2, '李四'),
(3, '王五'),
(4, '赵六'),
(5, '孙七');

-- 解法一：CASE WHEN 计算新座位号（推荐）
SELECT
    id,
    CASE
        WHEN id % 2 = 1 AND id = (SELECT COUNT(*) FROM Seat) THEN student
        WHEN id % 2 = 1 THEN (SELECT student FROM Seat s2 WHERE s2.id = s.id + 1)
        ELSE (SELECT student FROM Seat s2 WHERE s2.id = s.id - 1)
    END AS student
FROM Seat s
ORDER BY id;

-- 解法二：重排 ID + 直接排序
-- SELECT
--     CASE
--         WHEN id % 2 = 1 AND id = (SELECT MAX(id) FROM Seat) THEN id
--         WHEN id % 2 = 1 THEN id + 1
--         ELSE id - 1
--     END AS id,
--     student
-- FROM Seat
-- ORDER BY id;
