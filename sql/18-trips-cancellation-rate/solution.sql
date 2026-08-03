-- ============================================================
-- 第 18 题：行程和用户（取消率）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Trips CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
    users_id INT PRIMARY KEY,
    banned   VARCHAR,
    role     VARCHAR
);

CREATE TABLE Trips (
    id         INT PRIMARY KEY,
    client_id  INT,
    driver_id  INT,
    city_id    INT,
    status     VARCHAR,
    request_at DATE,
    FOREIGN KEY (client_id) REFERENCES Users(users_id),
    FOREIGN KEY (driver_id) REFERENCES Users(users_id)
);

INSERT INTO Users (users_id, banned, role) VALUES
(1,  'No', 'client'),
(2,  'Yes', 'client'),
(3,  'No', 'client'),
(4,  'No', 'client'),
(10, 'No', 'driver'),
(11, 'No', 'driver'),
(12, 'No', 'driver'),
(13, 'No', 'driver');

INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES
(1, 1, 10, 1, 'completed',            '2013-10-01'),
(2, 2, 11, 1, 'cancelled_by_driver', '2013-10-01'),
(3, 3, 12, 1, 'completed',            '2013-10-01'),
(4, 4, 13, 1, 'cancelled_by_client', '2013-10-01'),
(5, 1, 10, 1, 'completed',            '2013-10-02'),
(6, 2, 11, 1, 'completed',            '2013-10-02'),
(7, 3, 12, 1, 'completed',            '2013-10-02'),
(8, 1, 12, 1, 'completed',            '2013-10-03'),
(9, 3, 10, 1, 'cancelled_by_driver', '2013-10-03');

-- 解法
SELECT t.request_at AS "Day",
       ROUND(
           SUM(CASE WHEN t.status LIKE 'cancelled%' THEN 1 ELSE 0 END) * 1.0
           / COUNT(*),
           2
       ) AS "Cancellation Rate"
FROM Trips t
JOIN Users u_client ON t.client_id = u_client.users_id
JOIN Users u_driver ON t.driver_id = u_driver.users_id
WHERE u_client.banned = 'No'
  AND u_driver.banned = 'No'
  AND t.request_at BETWEEN '2013-10-01' AND '2013-10-03'
GROUP BY t.request_at
ORDER BY t.request_at;
