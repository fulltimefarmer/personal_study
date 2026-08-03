-- ============================================================
-- 第 24 题：好友申请通过率
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS RequestAccepted CASCADE;
DROP TABLE IF EXISTS FriendRequest CASCADE;

CREATE TABLE FriendRequest (
    sender_id    INT,
    send_to_id   INT,
    request_date DATE
);

CREATE TABLE RequestAccepted (
    requester_id INT,
    accepter_id  INT,
    accept_date  DATE
);

INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES
(1, 2, '2024-01-01'),
(1, 3, '2024-01-02'),
(1, 4, '2024-01-03'),
(2, 3, '2024-01-04'),
(1, 2, '2024-01-05'),
(2, 4, '2024-01-06');

INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES
(1, 2, '2024-01-06'),
(1, 3, '2024-01-07'),
(2, 4, '2024-01-07');

-- 解法一：PostgreSQL 行构造器（推荐）
SELECT ROUND(
    COALESCE(
        (SELECT COUNT(DISTINCT (requester_id, accepter_id)) FROM RequestAccepted) * 1.0
        / NULLIF(
            (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest), 0
        ),
        0
    ),
    2
) AS accept_rate;

-- 解法二：CASE WHEN 处理分母为 0
-- SELECT ROUND(
--     CASE
--         WHEN (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest) = 0 THEN 0
--         ELSE (SELECT COUNT(DISTINCT (requester_id, accepter_id)) FROM RequestAccepted) * 1.0
--              / (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest)
--     END,
--     2
-- ) AS accept_rate;
