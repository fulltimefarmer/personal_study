-- ============================================
-- 删除重复的邮箱 (Delete Duplicate Emails)
-- ============================================

-- 解法一：自连接删除（推荐，最简洁）
-- 思路：
--   Person 表自连接 (p1 JOIN p2)，条件 Email 相同
--   WHERE p1.Id > p2.Id 删除 Id 不是最小的那一行
-- 原理推演（以 Id=1,2,3 数据为例）：
--   保留：p1.Id=1, p2.Id=1 → 1>1 FALSE
--   保留：p1.Id=1, p2.Id=3 → 1>3 FALSE
--   删除：p1.Id=3, p2.Id=1 → 3>1 TRUE  ← 删除 Id=3
--   保留：p1.Id=3, p2.Id=3 → 3>3 FALSE
--   保留：p1.Id=2, p2.Id=2 → 2>2 FALSE（唯一邮箱）
DELETE p1
FROM Person p1
JOIN Person p2 ON p1.Email = p2.Email
WHERE p1.Id > p2.Id;

-- 解法二：子查询 + NOT IN（MySQL 需要套层子查询）
-- 思路：
--   1. 子查询找出每个邮箱的最小 Id（保留的）
--   2. 外层 WHERE Id NOT IN 这些最小 Id（删除的）
-- 注意：MySQL 不允许 DELETE 和子查询引用同一张表
--   解决办法：套一层临时表 (SELECT * FROM (...)) AS tmp 物化子查询结果
DELETE FROM Person
WHERE Id NOT IN (
  SELECT * FROM (
    SELECT MIN(Id)
    FROM Person
    GROUP BY Email
  ) AS tmp
);

-- 解法三：窗口函数 ROW_NUMBER() + 子查询删除（MySQL 8.0+ / PostgreSQL）
-- 思路：
--   1. ROW_NUMBER() 按 Email 分区，按 Id 升序编号
--   2. rn = 1 的是每组最小 Id（保留），rn > 1 的是要删除的
--   3. 删除子查询中 rn > 1 的 Id
-- 为什么用 ROW_NUMBER 而不是 DENSE_RANK？
--   Id 是唯一主键，不会存在相同 Id，ROW_NUMBER 足矣
--   同邮箱的每个 Id 都不同，ROW_NUMBER 恰好给每行分配 1,2,3...
DELETE FROM Person
WHERE Id IN (
  SELECT Id FROM (
    SELECT Id,
           ROW_NUMBER() OVER (PARTITION BY Email ORDER BY Id) AS rn
    FROM Person
  ) t
  WHERE rn > 1
);

-- 解法四：CTE + DELETE（PostgreSQL / MySQL 8.0+，最清晰的现代写法）
-- 注意：MySQL 8.0 支持 CTE，但 DELETE 中使用 CTE 语法可能有限制
--       以下写法在 PostgreSQL 中直接可用
/*
WITH duplicates AS (
  SELECT Id,
         ROW_NUMBER() OVER (PARTITION BY Email ORDER BY Id) AS rn
  FROM Person
)
DELETE FROM Person
WHERE Id IN (SELECT Id FROM duplicates WHERE rn > 1);
*/

-- ============================================
-- 扩展：删除所有重复记录（不留最小 Id，全部删除）
-- ============================================
/*
DELETE p1
FROM Person p1
JOIN Person p2 ON p1.Email = p2.Email AND p1.Id != p2.Id;
*/

-- ============================================
-- 扩展：查询哪些行会被删除（预览不执行）
-- ============================================
/*
SELECT p1.*
FROM Person p1
JOIN Person p2 ON p1.Email = p2.Email
WHERE p1.Id > p2.Id;
*/

-- ============================================
-- 建表与测试数据
-- ============================================
/*
CREATE TABLE Person (
  Id INT PRIMARY KEY,
  Email VARCHAR(255)
);

INSERT INTO Person VALUES
  (1, 'john@example.com'),
  (2, 'bob@example.com'),
  (3, 'john@example.com');
*/
