-- ============================================================
-- 第 12 题：分数排名
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Scores CASCADE;
CREATE TABLE Scores (
    id    INT PRIMARY KEY,
    score DECIMAL(5,2)
);

INSERT INTO Scores (id, score) VALUES
(1, 95.0),
(2, 85.0),
(3, 85.0),
(4, 76.0),
(5, 60.0);

-- 解法一：DENSE_RANK() 窗口函数（推荐）
SELECT score,
       DENSE_RANK() OVER (ORDER BY score DESC) AS rank
FROM Scores
ORDER BY score DESC;

-- 解法二：子查询（不用窗口函数）
-- SELECT s1.score,
--        (SELECT COUNT(DISTINCT s2.score)
--         FROM Scores s2
--         WHERE s2.score >= s1.score) AS rank
-- FROM Scores s1
-- ORDER BY s1.score DESC;
