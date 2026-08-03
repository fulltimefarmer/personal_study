-- ============================================================
-- 第 8 题：从不订购的客户
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Orders CASCADE;
DROP TABLE IF EXISTS Customers CASCADE;
CREATE TABLE Customers (
    id   INT PRIMARY KEY,
    name VARCHAR
);
CREATE TABLE Orders (
    id         INT PRIMARY KEY,
    customerId INT,
    FOREIGN KEY (customerId) REFERENCES Customers(id)
);

INSERT INTO Customers (id, name) VALUES
(1, '张三'),
(2, '李四'),
(3, '王五'),
(4, '赵六');

INSERT INTO Orders (id, customerId) VALUES
(1, 3),
(2, 1);

-- 解法一：LEFT JOIN + IS NULL（推荐）
SELECT c.name AS "Customers"
FROM Customers c
LEFT JOIN Orders o ON c.id = o.customerId
WHERE o.id IS NULL;

-- 解法二：NOT IN
-- SELECT name AS "Customers"
-- FROM Customers
-- WHERE id NOT IN (SELECT customerId FROM Orders);

-- 解法三：NOT EXISTS
-- SELECT name AS "Customers"
-- FROM Customers c
-- WHERE NOT EXISTS (
--     SELECT 1 FROM Orders o WHERE o.customerId = c.id
-- );
