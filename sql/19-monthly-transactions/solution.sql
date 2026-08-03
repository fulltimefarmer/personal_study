-- ============================================================
-- 第 19 题：每月交易统计
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Transactions CASCADE;
CREATE TABLE Transactions (
    id         INT PRIMARY KEY,
    country    VARCHAR,
    state      VARCHAR,
    amount     INT,
    trans_date DATE
);

INSERT INTO Transactions (id, country, state, amount, trans_date) VALUES
(1, '中国', 'approved', 1000, '2024-01-15'),
(2, '中国', 'declined', 2000, '2024-01-20'),
(3, '中国', 'approved', 3000, '2024-02-10'),
(4, '美国', 'approved', 5000, '2024-01-10'),
(5, '美国', 'declined', 6000, '2024-01-25'),
(6, '美国', 'approved', 2000, '2024-02-05');

-- 解法
SELECT TO_CHAR(trans_date, 'YYYY-MM') AS month,
       country,
       COUNT(*) AS trans_count,
       SUM(CASE WHEN state = 'approved' THEN 1 ELSE 0 END) AS approved_count,
       SUM(amount) AS trans_total_amount,
       SUM(CASE WHEN state = 'approved' THEN amount ELSE 0 END) AS approved_total_amount
FROM Transactions
GROUP BY TO_CHAR(trans_date, 'YYYY-MM'), country
ORDER BY month, country;
