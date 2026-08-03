-- ============================================================
-- 第 22 题：股票的资本损益
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Stocks CASCADE;
CREATE TABLE Stocks (
    stock_name    VARCHAR,
    operation     VARCHAR,
    operation_day INT,
    price         INT
);

INSERT INTO Stocks (stock_name, operation, operation_day, price) VALUES
('茅台', 'Buy',  1,  1000),
('腾讯', 'Buy',  2,  500),
('茅台', 'Sell', 5,  1500),
('腾讯', 'Sell', 10, 600),
('茅台', 'Buy',  8,  1200),
('腾讯', 'Buy',  12, 550),
('茅台', 'Sell', 15, 1400);

-- 解法一：Sell 为正，Buy 为负，求和（推荐）
SELECT stock_name,
       SUM(CASE WHEN operation = 'Sell' THEN price ELSE -price END) AS capital_gain_loss
FROM Stocks
GROUP BY stock_name
ORDER BY stock_name;

-- 解法二：分别汇总再相减（更直观）
-- SELECT stock_name,
--        SUM(CASE WHEN operation = 'Sell' THEN price ELSE 0 END)
--        - SUM(CASE WHEN operation = 'Buy' THEN price ELSE 0 END) AS capital_gain_loss
-- FROM Stocks
-- GROUP BY stock_name;
