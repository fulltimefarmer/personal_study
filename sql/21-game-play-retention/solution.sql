-- ============================================================
-- 第 21 题：游戏玩法分析 - 次日留存
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Activity CASCADE;
CREATE TABLE Activity (
    player_id    INT,
    device_id    INT,
    event_date   DATE,
    games_played INT
);

INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES
(1, 2, '2024-03-01', 5),
(1, 2, '2024-03-02', 6),
(2, 3, '2024-05-01', 1),
(3, 1, '2024-04-02', 0),
(3, 4, '2024-04-03', 5),
(3, 1, '2024-04-04', 3),
(4, 1, '2024-06-01', 3),
(4, 1, '2024-06-03', 2);

-- 解法
WITH first_login AS (
    SELECT player_id, MIN(event_date) AS first_date
    FROM Activity
    GROUP BY player_id
)
SELECT ROUND(
    COUNT(DISTINCT a.player_id) * 1.0 /
    (SELECT COUNT(DISTINCT player_id) FROM Activity),
    2
) AS fraction
FROM first_login f
JOIN Activity a ON f.player_id = a.player_id
                AND a.event_date = f.first_date + INTERVAL '1 day';
