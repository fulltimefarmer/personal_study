-- ============================================
-- 从不订购的客户 (Customers Who Never Order)
-- ============================================

-- 解法一：LEFT JOIN + IS NULL（推荐，最直观）
-- 思路：
--   1. Customers 左连接 Orders（保留所有客户）
--   2. 没有订单的客户，Orders 表的所有列都是 NULL
--   3. WHERE o.CustomerId IS NULL 筛选出这些客户
-- LEFT JOIN 原理：
--   左表全保留，右表无匹配时填充 NULL
-- IS NULL 判断：
--   o.CustomerId 是 JOIN 键，无匹配时为 NULL，是最可靠的判断列
SELECT c.Name AS Customers
FROM Customers c
LEFT JOIN Orders o ON c.Id = o.CustomerId
WHERE o.CustomerId IS NULL;

-- 解法二：NOT EXISTS（性能通常更好，有短路优化）
-- 思路：
--   NOT EXISTS 检查子查询是否为空
--   如果 Customers.c.Id 在 Orders 中找不到匹配，NOT EXISTS 返回 TRUE
-- 短路机制：
--   EXISTS 只要找到第一条匹配就停止扫描，不需要扫描全部
-- 优点：
--   - 不受 NULL 值影响（EXISTS 只关心是否有行返回）
--   - 优化器常将其转换为 ANTI JOIN 执行计划
SELECT c.Name AS Customers
FROM Customers c
WHERE NOT EXISTS (
  SELECT 1
  FROM Orders o
  WHERE o.CustomerId = c.Id
);

-- 解法三：NOT IN（简单但有 NULL 陷阱）
-- 思路：
--   Customers.Id 不在所有已下过单的 CustomerId 中
-- NULL 陷阱：
--   NOT IN (1, 2, NULL) 永远返回空！
--   因为 1 NOT IN (2, NULL) → 1!=2 AND 1!=NULL → TRUE AND UNKNOWN → UNKNOWN
--   SQL 三值逻辑中 WHERE 只接受 TRUE，UNKNOWN 被丢弃
-- 解决方法：
--   子查询中加 WHERE CustomerId IS NOT NULL 过滤掉 NULL
-- 不推荐：即使加了 IS NOT NULL，优化器优化 NOT IN 不如 NOT EXISTS 好
SELECT c.Name AS Customers
FROM Customers c
WHERE c.Id NOT IN (
  SELECT CustomerId
  FROM Orders
  WHERE CustomerId IS NOT NULL
);

-- 解法四：使用 CTE 提取已有订单的客户 ID（MySQL 8.0+ / PostgreSQL）
-- 思路：
--   先查出所有下过单的客户 ID 集合
--   主查询排除这些 ID
-- 优点：逻辑清晰，CTE 可被优化器物化
/*
WITH ordered_customers AS (
  SELECT DISTINCT CustomerId FROM Orders
)
SELECT c.Name AS Customers
FROM Customers c
LEFT JOIN ordered_customers oc ON c.Id = oc.CustomerId
WHERE oc.CustomerId IS NULL;
*/

-- ============================================
-- 扩展：每个客户的下单数（含 0 单）
-- 注意：COUNT(o.Id) 只计数非 NULL，即只计数实际订单
--       如果用 COUNT(*)，0 单客户也会显示 1
-- ============================================
SELECT c.Name AS Customer,
       COUNT(o.Id) AS order_count
FROM Customers c
LEFT JOIN Orders o ON c.Id = o.CustomerId
GROUP BY c.Id, c.Name
ORDER BY order_count;

-- ============================================
-- 建表与测试数据
-- ============================================
/*
CREATE TABLE Customers (
  Id INT PRIMARY KEY,
  Name VARCHAR(50)
);

CREATE TABLE Orders (
  Id INT PRIMARY KEY,
  CustomerId INT
);

INSERT INTO Customers VALUES
  (1, 'Joe'),
  (2, 'Henry'),
  (3, 'Sam'),
  (4, 'Max');

INSERT INTO Orders VALUES
  (1, 3),
  (2, 1);
*/
