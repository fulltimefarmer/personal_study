-- ============================================================
-- 第 3 题：有趣的电影
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Cinema CASCADE;
CREATE TABLE Cinema (
    id          INT PRIMARY KEY,
    movie       VARCHAR,
    description VARCHAR,
    rating      FLOAT
);

INSERT INTO Cinema (id, movie, description, rating) VALUES
(1, '战狼',     'great',     9.0),
(2, '科幻片A',  'boring',    7.5),
(3, '流浪地球', 'wonderful', 8.9),
(4, '动画片B',  'boring',    6.0),
(5, '哪吒',     'amazing',   9.5);

-- 解法：不等于 + 取模判奇 + 降序排序
SELECT id, movie, description, rating
FROM Cinema
WHERE description <> 'boring'
  AND id % 2 = 1
ORDER BY rating DESC;
