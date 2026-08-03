-- ============================================================
-- 第 20 题：体育馆人流量（连续多天）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Stadium CASCADE;
CREATE TABLE Stadium (
    id         INT PRIMARY KEY,
    visit_date DATE,
    people     INT
);

INSERT INTO Stadium (id, visit_date, people) VALUES
(1, '2024-01-01', 10),
(2, '2024-01-02', 109),
(3, '2024-01-03', 150),
(4, '2024-01-04', 99),
(5, '2024-01-05', 145),
(6, '2024-01-06', 1455),
(7, '2024-01-07', 199),
(8, '2024-01-08', 188);

-- 解法：GAP/ISLAND——行号差值分组
WITH filtered AS (
    SELECT id, visit_date, people
    FROM Stadium
    WHERE people >= 100
),
grouped AS (
    SELECT id, visit_date, people,
           id - ROW_NUMBER() OVER (ORDER BY id) AS grp
    FROM filtered
),
long_groups AS (
    SELECT grp
    FROM grouped
    GROUP BY grp
    HAVING COUNT(*) >= 3
)
SELECT g.id, g.visit_date, g.people
FROM grouped g
JOIN long_groups l ON g.grp = l.grp
ORDER BY g.id;
