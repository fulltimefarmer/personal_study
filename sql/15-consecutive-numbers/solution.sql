-- ============================================================
-- 第 15 题：连续出现的数字
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Logs CASCADE;
CREATE TABLE Logs (
    id  INT PRIMARY KEY,
    num VARCHAR
);

INSERT INTO Logs (id, num) VALUES
(1, '1'),
(2, '1'),
(3, '1'),
(4, '2'),
(5, '1'),
(6, '2'),
(7, '2');

-- 解法一：LAG() 窗口函数（推荐）
SELECT DISTINCT num AS "ConsecutiveNums"
FROM (
    SELECT num,
           LAG(num, 1) OVER (ORDER BY id) AS prev1,
           LAG(num, 2) OVER (ORDER BY id) AS prev2
    FROM Logs
) t
WHERE num = prev1 AND num = prev2;

-- 解法二：自连接
-- SELECT DISTINCT l1.num AS "ConsecutiveNums"
-- FROM Logs l1
-- JOIN Logs l2 ON l1.id = l2.id - 1 AND l1.num = l2.num
-- JOIN Logs l3 ON l2.id = l3.id - 1 AND l2.num = l3.num;
