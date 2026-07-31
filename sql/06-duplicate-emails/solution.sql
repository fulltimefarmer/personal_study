-- ============================================
-- 重复的邮箱 (Duplicate Emails)
-- ============================================

-- 解法一：GROUP BY + HAVING（最经典）
-- 思路：
--   1. 按 Email 分组（GROUP BY Email）
--   2. 统计每组行数（COUNT(Id) 或 COUNT(*)）
--   3. 用 HAVING 过滤出行数 > 1 的组（即重复的邮箱）
-- SQL 执行顺序：
--   FROM → WHERE → GROUP BY → 聚合 → HAVING → SELECT → ORDER BY
-- 注意：WHERE 不能使用聚合函数，必须用 HAVING
SELECT Email
FROM Person
GROUP BY Email
HAVING COUNT(Id) > 1;

-- 解法二：自连接（不推荐，仅作思维练习）
-- 思路：
--   Person 表自连接，条件为 Email 相同但 Id 不同
--   由于是多对多关联，会重复出现同一邮箱，需要 DISTINCT 去重
-- 缺点：JOIN 后数据膨胀，性能差
SELECT DISTINCT p1.Email
FROM Person p1
JOIN Person p2 ON p1.Email = p2.Email AND p1.Id != p2.Id;

-- 解法三：窗口函数 COUNT() OVER (PARTITION BY)（MySQL 8.0+）
-- 思路：
--   用 COUNT(*) OVER (PARTITION BY Email) 计算每个邮箱的出现次数
--   子查询外层 WHERE cnt > 1 筛选，DISTINCT 去重
SELECT DISTINCT Email
FROM (
  SELECT Email, COUNT(*) OVER (PARTITION BY Email) AS cnt
  FROM Person
) t
WHERE cnt > 1;

-- ============================================
-- 扩展：返回邮箱及出现次数
-- ============================================
SELECT Email, COUNT(*) AS occurrence_count
FROM Person
GROUP BY Email
HAVING COUNT(*) > 1;

-- ============================================
-- 扩展：返回所有重复邮箱对应的完整记录
-- ============================================
SELECT *
FROM Person
WHERE Email IN (
  SELECT Email FROM Person GROUP BY Email HAVING COUNT(*) > 1
)
ORDER BY Email, Id;

-- ============================================
-- 建表与测试数据
-- ============================================
/*
CREATE TABLE Person (
  Id INT PRIMARY KEY,
  Email VARCHAR(255)
);

INSERT INTO Person VALUES
  (1, 'a@b.com'),
  (2, 'c@d.com'),
  (3, 'a@b.com');
*/
