-- ============================================================
-- 第 23 题：即时食物配送比例
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Delivery CASCADE;
CREATE TABLE Delivery (
    delivery_id                  INT PRIMARY KEY,
    customer_id                  INT,
    order_date                   DATE,
    customer_pref_delivery_date  DATE
);

INSERT INTO Delivery (delivery_id, customer_id, order_date, customer_pref_delivery_date) VALUES
(1, 1, '2024-08-01', '2024-08-02'),
(2, 2, '2024-08-02', '2024-08-02'),
(3, 1, '2024-08-11', '2024-08-12'),
(4, 3, '2024-08-24', '2024-08-25'),
(5, 3, '2024-08-26', '2024-08-26'),
(6, 2, '2024-08-28', '2024-08-29');

-- 解法
WITH first_orders AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS rn
    FROM Delivery
)
SELECT ROUND(
    SUM(CASE WHEN order_date = customer_pref_delivery_date THEN 1 ELSE 0 END) * 100.0
    / COUNT(*),
    2
) AS immediate_percentage
FROM first_orders
WHERE rn = 1;
