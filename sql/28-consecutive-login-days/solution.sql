-- ============================================================
-- 第 28 题：连续登录天数（GAP/ISLAND）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Login CASCADE;
CREATE TABLE Login (
    user_id    INT,
    login_date DATE
);

INSERT INTO Login (user_id, login_date) VALUES
(1, '2024-01-01'),
(1, '2024-01-02'),
(1, '2024-01-03'),
(1, '2024-01-05'),
(1, '2024-01-06'),
(2, '2024-01-01'),
(2, '2024-01-02'),
(2, '2024-01-04'),
(3, '2024-01-01'),
(3, '2024-01-01');

-- 解法：GAP/ISLAND - 日期与行号差值分组
WITH distinct_days AS (
    SELECT DISTINCT user_id, login_date
    FROM Login
),
numbered AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM distinct_days
),
grouped AS (
    SELECT user_id,
           login_date - rn * INTERVAL '1 day' AS grp
    FROM numbered
)
SELECT user_id, MAX(consecutive_days) AS max_consecutive_days
FROM (
    SELECT user_id, grp, COUNT(*) AS consecutive_days
    FROM grouped
    GROUP BY user_id, grp
) t
GROUP BY user_id
ORDER BY user_id;
