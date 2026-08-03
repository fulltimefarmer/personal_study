-- ============================================================
-- 全部 30 题 solution 验证脚本
-- 表名已重命名（表名+题号后缀）
-- 第 5、11 题（UPDATE/DELETE）自动在外层事务中回滚
-- ============================================================

-- ============================================================
-- 第 1 题：big-countries
-- ============================================================
-- 解法：用 OR 连接两个条件
SELECT name, population, area
FROM World01
WHERE area >= 3000000
   OR population >= 25000000;


-- ============================================================
-- 第 2 题：combine-two-tables
-- ============================================================
-- 解法：LEFT JOIN（推荐）
SELECT p.FirstName, p.LastName, a.City, a.State
FROM Person02 p
LEFT JOIN Address02 a ON p.PersonId = a.PersonId;

-- 扩展：只查询有地址的人（INNER JOIN）
-- SELECT p.FirstName, p.LastName, a.City, a.State
-- FROM Person02 p
-- INNER JOIN Address02 a ON p.PersonId = a.PersonId;

-- 扩展：只查询没有地址的人
-- SELECT p.FirstName, p.LastName
-- FROM Person02 p
-- LEFT JOIN Address02 a ON p.PersonId = a.PersonId
-- WHERE a.AddressId IS NULL;


-- ============================================================
-- 第 3 题：not-boring-movies
-- ============================================================
-- 解法：不等于 + 取模判奇 + 降序排序
SELECT id, movie, description, rating
FROM Cinema03
WHERE description <> 'boring'
  AND id % 2 = 1
ORDER BY rating DESC;


-- ============================================================
-- 第 4 题：classes-more-than-5
-- ============================================================
-- 解法：GROUP BY + HAVING + COUNT(DISTINCT)
SELECT class
FROM Courses04
GROUP BY class
HAVING COUNT(DISTINCT student) >= 5;


-- ============================================================
-- 第 5 题：swap-sex
-- ============================================================
-- (在事务中运行，执行后回滚)
BEGIN;
-- 解法：CASE WHEN 在 SET 中
UPDATE Salary05
SET sex = CASE WHEN sex = 'm' THEN 'f' ELSE 'm' END;

-- 查看更新后数据
SELECT '更新后：' AS info;
SELECT * FROM Salary05;
ROLLBACK;


-- ============================================================
-- 第 6 题：rising-temperature
-- ============================================================
-- 解法一：自连接（推荐）
SELECT w1.id
FROM Weather06 w1
JOIN Weather06 w2 ON w1.recordDate = w2.recordDate + INTERVAL '1 day'
WHERE w1.temperature > w2.temperature;

-- 解法二：窗口函数 LAG()
-- WITH t AS (
--     SELECT id, recordDate, temperature,
--            LAG(temperature) OVER (ORDER BY recordDate) AS prev_temp,
--            LAG(recordDate) OVER (ORDER BY recordDate) AS prev_date
--     FROM Weather06
-- )
-- SELECT id
-- FROM t
-- WHERE temperature > prev_temp
--   AND recordDate - prev_date = 1;


-- ============================================================
-- 第 7 题：duplicate-emails
-- ============================================================
-- 解法：GROUP BY + HAVING COUNT(*) > 1
SELECT email AS "Email"
FROM Person07
GROUP BY email
HAVING COUNT(*) > 1;

-- 扩展：查找重复邮箱的具体所有行
-- SELECT * FROM Person07
-- WHERE email IN (
--     SELECT email FROM Person07 GROUP BY email HAVING COUNT(*) > 1
-- );


-- ============================================================
-- 第 8 题：customers-never-order
-- ============================================================
-- 解法一：LEFT JOIN + IS NULL（推荐）
SELECT c.name AS "Customers08"
FROM Customers08 c
LEFT JOIN Orders08 o ON c.id = o.customerId
WHERE o.id IS NULL;

-- 解法二：NOT IN
-- SELECT name AS "Customers08"
-- FROM Customers08
-- WHERE id NOT IN (SELECT customerId FROM Orders08);

-- 解法三：NOT EXISTS
-- SELECT name AS "Customers08"
-- FROM Customers08 c
-- WHERE NOT EXISTS (
--     SELECT 1 FROM Orders08 o WHERE o.customerId = c.id
-- );


-- ============================================================
-- 第 9 题：employees-earning-more-than-managers
-- ============================================================
-- 解法：自连接（Self Join）
SELECT e1.name AS "Employee09"
FROM Employee09 e1
JOIN Employee09 e2 ON e1.managerId = e2.id
WHERE e1.salary > e2.salary;


-- ============================================================
-- 第 10 题：second-highest-salary
-- ============================================================
-- 解法一：DISTINCT + LIMIT + OFFSET（推荐）
SELECT (
    SELECT DISTINCT salary
    FROM Employee10
    ORDER BY salary DESC
    LIMIT 1 OFFSET 1
) AS "SecondHighestSalary";

-- 解法二：MAX + 子查询
-- SELECT MAX(salary) AS "SecondHighestSalary"
-- FROM Employee10
-- WHERE salary < (SELECT MAX(salary) FROM Employee10);

-- 解法三：DENSE_RANK()
-- SELECT (
--     SELECT salary
--     FROM (
--         SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
--         FROM Employee10
--     ) t
--     WHERE rnk = 2
--     LIMIT 1
-- ) AS "SecondHighestSalary";

-- 测试空结果返回 NULL 的场景（可选运行）
-- DELETE FROM Employee10;
-- INSERT INTO Employee10 (id, salary) VALUES (1, 100);
-- SELECT (
--     SELECT DISTINCT salary
--     FROM Employee10
--     ORDER BY salary DESC
--     LIMIT 1 OFFSET 1
-- ) AS "SecondHighestSalary";


-- ============================================================
-- 第 11 题：delete-duplicate-emails
-- ============================================================
-- (在事务中运行，执行后回滚)
BEGIN;
-- 解法一：自连接使用 USING（PostgreSQL推荐）
DELETE FROM Person11 p1
USING Person11 p2
WHERE p1.email = p2.email AND p1.id > p2.id;

-- 解法二：子查询
-- DELETE FROM Person11
-- WHERE id NOT IN (
--     SELECT min_id FROM (
--         SELECT MIN(id) AS min_id
--         FROM Person11
--         GROUP BY email
--     ) t
-- );

-- 解法三：窗口函数
-- DELETE FROM Person11
-- WHERE id IN (
--     SELECT id FROM (
--         SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
--         FROM Person11
--     ) t WHERE rn > 1
-- );

-- 查看删除后数据
SELECT '删除后：' AS info;
SELECT * FROM Person11 ORDER BY id;
ROLLBACK;


-- ============================================================
-- 第 12 题：rank-scores
-- ============================================================
-- 解法一：DENSE_RANK() 窗口函数（推荐）
SELECT score,
       DENSE_RANK() OVER (ORDER BY score DESC) AS rank
FROM Scores12
ORDER BY score DESC;

-- 解法二：子查询（不用窗口函数）
-- SELECT s1.score,
--        (SELECT COUNT(DISTINCT s2.score)
--         FROM Scores12 s2
--         WHERE s2.score >= s1.score) AS rank
-- FROM Scores12 s1
-- ORDER BY s1.score DESC;


-- ============================================================
-- 第 13 题：exchange-seats
-- ============================================================
-- 解法一：CASE WHEN 计算新座位号（推荐）
SELECT
    id,
    CASE
        WHEN id % 2 = 1 AND id = (SELECT COUNT(*) FROM Seat13) THEN student
        WHEN id % 2 = 1 THEN (SELECT student FROM Seat13 s2 WHERE s2.id = s.id + 1)
        ELSE (SELECT student FROM Seat13 s2 WHERE s2.id = s.id - 1)
    END AS student
FROM Seat13 s
ORDER BY id;

-- 解法二：重排 ID + 直接排序
-- SELECT
--     CASE
--         WHEN id % 2 = 1 AND id = (SELECT MAX(id) FROM Seat13) THEN id
--         WHEN id % 2 = 1 THEN id + 1
--         ELSE id - 1
--     END AS id,
--     student
-- FROM Seat13
-- ORDER BY id;


-- ============================================================
-- 第 14 题：nth-highest-salary
-- ============================================================
-- 解法一：LIMIT + OFFSET（推荐）
CREATE OR REPLACE FUNCTION getNthHighestSalary(N INT) RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT DISTINCT salary
        FROM Employee14
        ORDER BY salary DESC
        LIMIT 1 OFFSET N - 1
    );
END;
$$ LANGUAGE plpgsql;

-- 测试
SELECT getNthHighestSalary(1) AS first_highest;
SELECT getNthHighestSalary(2) AS second_highest;
SELECT getNthHighestSalary(3) AS third_highest;
SELECT getNthHighestSalary(4) AS fourth_highest;

-- 解法二：DENSE_RANK()
-- CREATE OR REPLACE FUNCTION getNthHighestSalary(N INT) RETURNS INT AS $$
-- BEGIN
--     RETURN (
--         SELECT salary
--         FROM (
--             SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
--             FROM Employee14
--         ) t
--         WHERE rnk = N
--         LIMIT 1
--     );
-- END;
-- $$ LANGUAGE plpgsql;


-- ============================================================
-- 第 15 题：consecutive-numbers
-- ============================================================
-- 解法一：LAG() 窗口函数（推荐）
SELECT DISTINCT num AS "ConsecutiveNums"
FROM (
    SELECT num,
           LAG(num, 1) OVER (ORDER BY id) AS prev1,
           LAG(num, 2) OVER (ORDER BY id) AS prev2
    FROM Logs15
) t
WHERE num = prev1 AND num = prev2;

-- 解法二：自连接
-- SELECT DISTINCT l1.num AS "ConsecutiveNums"
-- FROM Logs15 l1
-- JOIN Logs15 l2 ON l1.id = l2.id - 1 AND l1.num = l2.num
-- JOIN Logs15 l3 ON l2.id = l3.id - 1 AND l2.num = l3.num;


-- ============================================================
-- 第 16 题：department-highest-salary
-- ============================================================
-- 解法一：DENSE_RANK() 窗口函数（推荐）
SELECT d.name AS "Department16",
       e.name AS "Employee16",
       e.salary AS "Salary"
FROM (
    SELECT name, salary, departmentId,
           DENSE_RANK() OVER (PARTITION BY departmentId ORDER BY salary DESC) AS rnk
    FROM Employee16
) e
JOIN Department16 d ON e.departmentId = d.id
WHERE e.rnk = 1;

-- 解法二：IN 子查询
-- SELECT d.name AS "Department16",
--        e.name AS "Employee16",
--        e.salary AS "Salary"
-- FROM Employee16 e
-- JOIN Department16 d ON e.departmentId = d.id
-- WHERE (e.departmentId, e.salary) IN (
--     SELECT departmentId, MAX(salary) FROM Employee16 GROUP BY departmentId
-- );


-- ============================================================
-- 第 17 题：tree-node-type
-- ============================================================
-- 解法一：CASE WHEN + 子查询（推荐）
SELECT id,
       CASE
           WHEN p_id IS NULL THEN 'Root'
           WHEN id IN (SELECT DISTINCT p_id FROM Tree17 WHERE p_id IS NOT NULL) THEN 'Inner'
           ELSE 'Leaf'
       END AS "Type"
FROM Tree17;

-- 解法二：LEFT JOIN 方式
-- SELECT t1.id,
--        CASE
--            WHEN t1.p_id IS NULL THEN 'Root'
--            WHEN t2.id IS NOT NULL THEN 'Inner'
--            ELSE 'Leaf'
--        END AS "Type"
-- FROM Tree17 t1
-- LEFT JOIN (SELECT DISTINCT p_id AS id FROM Tree17 WHERE p_id IS NOT NULL) t2
--     ON t1.id = t2.id;


-- ============================================================
-- 第 18 题：trips-cancellation-rate
-- ============================================================
-- 解法
SELECT t.request_at AS "Day",
       ROUND(
           SUM(CASE WHEN t.status LIKE 'cancelled%' THEN 1 ELSE 0 END) * 1.0
           / COUNT(*),
           2
       ) AS "Cancellation Rate"
FROM Trips18 t
JOIN Users18 u_client ON t.client_id = u_client.users_id
JOIN Users18 u_driver ON t.driver_id = u_driver.users_id
WHERE u_client.banned = 'No'
  AND u_driver.banned = 'No'
  AND t.request_at BETWEEN '2013-10-01' AND '2013-10-03'
GROUP BY t.request_at
ORDER BY t.request_at;


-- ============================================================
-- 第 19 题：monthly-transactions
-- ============================================================
-- 解法
SELECT TO_CHAR(trans_date, 'YYYY-MM') AS month,
       country,
       COUNT(*) AS trans_count,
       SUM(CASE WHEN state = 'approved' THEN 1 ELSE 0 END) AS approved_count,
       SUM(amount) AS trans_total_amount,
       SUM(CASE WHEN state = 'approved' THEN amount ELSE 0 END) AS approved_total_amount
FROM Transactions19
GROUP BY TO_CHAR(trans_date, 'YYYY-MM'), country
ORDER BY month, country;


-- ============================================================
-- 第 20 题：stadium-high-traffic
-- ============================================================
-- 解法：GAP/ISLAND——行号差值分组
WITH filtered AS (
    SELECT id, visit_date, people
    FROM Stadium20
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


-- ============================================================
-- 第 21 题：game-play-retention
-- ============================================================
-- 解法
WITH first_login AS (
    SELECT player_id, MIN(event_date) AS first_date
    FROM Activity21
    GROUP BY player_id
)
SELECT ROUND(
    COUNT(DISTINCT a.player_id) * 1.0 /
    (SELECT COUNT(DISTINCT player_id) FROM Activity21),
    2
) AS fraction
FROM first_login f
JOIN Activity21 a ON f.player_id = a.player_id
                AND a.event_date = f.first_date + INTERVAL '1 day';


-- ============================================================
-- 第 22 题：capital-gain-loss
-- ============================================================
-- 解法一：Sell 为正，Buy 为负，求和（推荐）
SELECT stock_name,
       SUM(CASE WHEN operation = 'Sell' THEN price ELSE -price END) AS capital_gain_loss
FROM Stocks22
GROUP BY stock_name
ORDER BY stock_name;

-- 解法二：分别汇总再相减（更直观）
-- SELECT stock_name,
--        SUM(CASE WHEN operation = 'Sell' THEN price ELSE 0 END)
--        - SUM(CASE WHEN operation = 'Buy' THEN price ELSE 0 END) AS capital_gain_loss
-- FROM Stocks22
-- GROUP BY stock_name;


-- ============================================================
-- 第 23 题：immediate-food-delivery
-- ============================================================
-- 解法
WITH first_orders AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS rn
    FROM Delivery23
)
SELECT ROUND(
    SUM(CASE WHEN order_date = customer_pref_delivery_date THEN 1 ELSE 0 END) * 100.0
    / COUNT(*),
    2
) AS immediate_percentage
FROM first_orders
WHERE rn = 1;


-- ============================================================
-- 第 24 题：friend-request-acceptance
-- ============================================================
-- 解法一：PostgreSQL 行构造器（推荐）
SELECT ROUND(
    COALESCE(
        (SELECT COUNT(DISTINCT (requester_id, accepter_id)) FROM RequestAccepted24) * 1.0
        / NULLIF(
            (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest24), 0
        ),
        0
    ),
    2
) AS accept_rate;

-- 解法二：CASE WHEN 处理分母为 0
-- SELECT ROUND(
--     CASE
--         WHEN (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest24) = 0 THEN 0
--         ELSE (SELECT COUNT(DISTINCT (requester_id, accepter_id)) FROM RequestAccepted24) * 1.0
--              / (SELECT COUNT(DISTINCT (sender_id, send_to_id)) FROM FriendRequest24)
--     END,
--     2
-- ) AS accept_rate;


-- ============================================================
-- 第 25 题：product-sales-top-n
-- ============================================================
-- 解法一：RANK() 窗口函数（推荐）
WITH product_revenue AS (
    SELECT p.product_name, p.category,
           COALESCE(SUM(s.revenue), 0) AS total_revenue
    FROM Product25 p
    LEFT JOIN Sales25 s ON p.product_id = s.product_id
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


-- ============================================================
-- 第 26 题：cumulative-sales
-- ============================================================
-- 解法：先按天聚合，再窗口累计
SELECT order_date,
       daily_total,
       SUM(daily_total) OVER (ORDER BY order_date) AS cumulative_total
FROM (
    SELECT order_date, SUM(amount) AS daily_total
    FROM Orders26
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
--     FROM Orders26
--     GROUP BY order_date
-- ) t
-- ORDER BY order_date;


-- ============================================================
-- 第 27 题：avg-salary-dept-vs-company
-- ============================================================
-- 解法
SELECT id, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank,
       ROUND(AVG(salary) OVER (PARTITION BY department), 2) AS dept_avg,
       ROUND(AVG(salary) OVER (), 2) AS company_avg,
       CASE
           WHEN salary > AVG(salary) OVER (PARTITION BY department) THEN '高于'
           WHEN salary < AVG(salary) OVER (PARTITION BY department) THEN '低于'
           ELSE '等于'
       END AS vs_dept,
       CASE
           WHEN salary > AVG(salary) OVER () THEN '高于'
           WHEN salary < AVG(salary) OVER () THEN '低于'
           ELSE '等于'
       END AS vs_company
FROM Employee27
ORDER BY department, dept_rank;


-- ============================================================
-- 第 28 题：consecutive-login-days
-- ============================================================
-- 解法：GAP/ISLAND - 日期与行号差值分组
WITH distinct_days AS (
    SELECT DISTINCT user_id, login_date
    FROM Login28
),
numbered AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM distinct_days
),
grouped AS (
    SELECT user_id,
           login_date - rn * INTERVAL '1 day' AS grp
    FROM numbered
)
SELECT user_id, MAX(consecutive_days) AS max_consecutive_days
FROM (
    SELECT user_id, grp, COUNT(*) AS consecutive_days
    FROM grouped
    GROUP BY user_id, grp
) t
GROUP BY user_id
ORDER BY user_id;


-- ============================================================
-- 第 29 题：recursive-org-tree
-- ============================================================
-- 解法：递归 CTE
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id,
           1 AS level,
           name::TEXT AS path
    FROM Employee29
    WHERE manager_id IS NULL

    UNION ALL

    SELECT e.id, e.name, e.manager_id,
           ot.level + 1,
           ot.path || ' -> ' || e.name
    FROM Employee29 e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT id, name, level, path
FROM org_tree
ORDER BY id;


-- ============================================================
-- 第 30 题：user-behavior-funnel
-- ============================================================
-- 解法
WITH page_users AS (
    SELECT user_id,
           MAX(CASE WHEN page = 'home' THEN 1 ELSE 0 END) AS has_home,
           MAX(CASE WHEN page = 'search' THEN 1 ELSE 0 END) AS has_search,
           MAX(CASE WHEN page = 'product' THEN 1 ELSE 0 END) AS has_product,
           MAX(CASE WHEN page = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN page = 'pay' THEN 1 ELSE 0 END) AS has_pay
    FROM UserBehavior30
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

-- 全部测试完成
