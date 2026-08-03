-- ============================================================
-- 第 6 题：上升的温度
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Weather CASCADE;
CREATE TABLE Weather (
    id          INT PRIMARY KEY,
    recordDate  DATE,
    temperature INT
);

INSERT INTO Weather (id, recordDate, temperature) VALUES
(1, '2024-01-01', 10),
(2, '2024-01-02', 25),
(3, '2024-01-03', 20),
(4, '2024-01-04', 30),
(5, '2024-01-06', 28);

-- 解法一：自连接（推荐）
SELECT w1.id
FROM Weather w1
JOIN Weather w2 ON w1.recordDate = w2.recordDate + INTERVAL '1 day'
WHERE w1.temperature > w2.temperature;

-- 解法二：窗口函数 LAG()
-- WITH t AS (
--     SELECT id, recordDate, temperature,
--            LAG(temperature) OVER (ORDER BY recordDate) AS prev_temp,
--            LAG(recordDate) OVER (ORDER BY recordDate) AS prev_date
--     FROM Weather
-- )
-- SELECT id
-- FROM t
-- WHERE temperature > prev_temp
--   AND recordDate - prev_date = 1;
