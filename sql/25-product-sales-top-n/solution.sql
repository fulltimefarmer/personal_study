-- ============================================================
-- 第 25 题：产品销售分析 - 分组 TopN
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Sales CASCADE;
DROP TABLE IF EXISTS Product CASCADE;

CREATE TABLE Product (
    product_id   INT PRIMARY KEY,
    product_name VARCHAR,
    category     VARCHAR
);

CREATE TABLE Sales (
    sale_id    INT PRIMARY KEY,
    product_id INT,
    sale_date  DATE,
    quantity   INT,
    revenue    DECIMAL(12,2),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

INSERT INTO Product (product_id, product_name, category) VALUES
(1, '手机A', '电子产品'),
(2, '手机B', '电子产品'),
(3, 'T恤',   '服装'),
(4, '裤子',   '服装'),
(5, '手机C', '电子产品');

INSERT INTO Sales (sale_id, product_id, sale_date, quantity, revenue) VALUES
(1, 1, '2024-01-01', 10, 50000),
(2, 1, '2024-01-02', 5,  25000),
(3, 2, '2024-01-03', 8,  40000),
(4, 3, '2024-01-01', 20, 2000),
(5, 4, '2024-01-02', 15, 3000),
(6, 5, '2024-01-03', 3,  18000),
(7, 2, '2024-01-04', 15, 75000);

-- 解法一：RANK() 窗口函数（推荐）
WITH product_revenue AS (
    SELECT p.product_name, p.category,
           COALESCE(SUM(s.revenue), 0) AS total_revenue
    FROM Product p
    LEFT JOIN Sales s ON p.product_id = s.product_id
    GROUP BY p.product_id, p.product_name, p.category
),
ranked AS (
    SELECT category, product_name, total_revenue,
           RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rnk
    FROM product_revenue
)
SELECT category, product_name, total_revenue
FROM ranked
WHERE rnk = 1
ORDER BY category;
