-- ============================================================
-- 第 26 题：累计销售额（窗口函数）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Orders CASCADE;
CREATE TABLE Orders (
    order_id   INT PRIMARY KEY,
    order_date DATE,
    amount     DECIMAL(12,2)
);

INSERT INTO Orders (order_id, order_date, amount) VALUES
(1, '2024-01-01', 100),
(2, '2024-01-03', 200),
(3, '2024-01-04', 150),
(4, '2024-01-05', 50),
(5, '2024-01-05', 100);

-- 解法：先按天聚合，再窗口累计
SELECT order_date,
       daily_total,
       SUM(daily_total) OVER (ORDER BY order_date) AS cumulative_total
FROM (
    SELECT order_date, SUM(amount) AS daily_total
    FROM Orders
    GROUP BY order_date
) t
ORDER BY order_date;

-- 扩展：近3天移动平均
-- SELECT order_date,
--        daily_total,
--        AVG(daily_total) OVER (ORDER BY order_date
--            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3d
-- FROM (
--     SELECT order_date, SUM(amount) AS daily_total
--     FROM Orders
--     GROUP BY order_date
-- ) t
-- ORDER BY order_date;
