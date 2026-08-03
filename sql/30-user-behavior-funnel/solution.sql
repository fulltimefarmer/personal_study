-- ============================================================
-- 第 30 题：用户行为漏斗分析
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS UserBehavior CASCADE;
CREATE TABLE UserBehavior (
    user_id   INT,
    page      VARCHAR,
    timestamp TIMESTAMP
);

INSERT INTO UserBehavior (user_id, page, timestamp) VALUES
(1, 'home',    '2024-01-01 08:00:00'),
(1, 'search',  '2024-01-01 08:05:00'),
(1, 'product', '2024-01-01 08:10:00'),
(1, 'cart',    '2024-01-01 08:15:00'),
(1, 'pay',     '2024-01-01 08:20:00'),
(2, 'home',    '2024-01-01 09:00:00'),
(2, 'search',  '2024-01-01 09:05:00'),
(3, 'home',    '2024-01-01 10:00:00'),
(3, 'search',  '2024-01-01 10:05:00'),
(3, 'product', '2024-01-01 10:10:00'),
(3, 'cart',    '2024-01-01 10:15:00'),
(4, 'home',    '2024-01-01 11:00:00');

-- 解法
WITH page_users AS (
    SELECT user_id,
           MAX(CASE WHEN page = 'home' THEN 1 ELSE 0 END) AS has_home,
           MAX(CASE WHEN page = 'search' THEN 1 ELSE 0 END) AS has_search,
           MAX(CASE WHEN page = 'product' THEN 1 ELSE 0 END) AS has_product,
           MAX(CASE WHEN page = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN page = 'pay' THEN 1 ELSE 0 END) AS has_pay
    FROM UserBehavior
    GROUP BY user_id
),
funnel AS (
    SELECT
        COUNT(*) FILTER (WHERE has_home = 1) AS home_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1) AS search_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1 AND has_product = 1) AS product_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1 AND has_product = 1 AND has_cart = 1) AS cart_count,
        COUNT(*) FILTER (WHERE has_home = 1 AND has_search = 1 AND has_product = 1 AND has_cart = 1 AND has_pay = 1) AS pay_count
    FROM page_users
)
SELECT UNNEST(ARRAY['home', 'search', 'product', 'cart', 'pay']) AS step,
       UNNEST(ARRAY[home_count, search_count, product_count, cart_count, pay_count]) AS user_count,
       UNNEST(ARRAY[
           100.00,
           ROUND(search_count * 100.0 / home_count, 2),
           ROUND(product_count * 100.0 / search_count, 2),
           ROUND(cart_count * 100.0 / product_count, 2),
           ROUND(pay_count * 100.0 / cart_count, 2)
       ]) AS conversion_rate
FROM funnel;
