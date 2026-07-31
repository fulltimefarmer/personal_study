-- ============================================
-- 连续出现的数字 (Consecutive Numbers)
-- ============================================

-- 解法一：窗口函数 LAG()（MySQL 8.0+ / PostgreSQL, 推荐）
-- 思路：
--   LAG(Num, 1) 取前一行的 Num，LAG(Num, 2) 取前两行的 Num
--   如果 Num = prev1 = prev2，说明连续三行相同
-- 数据推演：
--   Id=1: Num=1, prev1=NULL, prev2=NULL  → 不满足
--   Id=2: Num=1, prev1=1,    prev2=NULL  → 不满足
--   Id=3: Num=1, prev1=1,    prev2=1     → 满足！Num=1 连续出现 3 次
SELECT DISTINCT Num AS ConsecutiveNums
FROM (
  SELECT Num,
         LAG(Num, 1) OVER (ORDER BY Id) AS prev1,
         LAG(Num, 2) OVER (ORDER BY Id) AS prev2
  FROM Logs
) t
WHERE Num = prev1 AND Num = prev2;

-- 解法二：使用 LEAD()（向前看，而非向后看）
-- 思路：
--   与 LAG 相反：LEAD(Num,1) 取下个值，LEAD(Num,2) 取下下个值
--   如果 Num = next1 = next2，说明连续三行相同
-- 结果与 LAG 等价，方向不同而已
SELECT DISTINCT Num AS ConsecutiveNums
FROM (
  SELECT Num,
         LEAD(Num, 1) OVER (ORDER BY Id) AS next1,
         LEAD(Num, 2) OVER (ORDER BY Id) AS next2
  FROM Logs
) t
WHERE Num = next1 AND Num = next2;

-- 解法三：自连接（兼容所有数据库版本）
-- 思路：
--   三表自连接
--   l1.Id = l2.Id - 1 保证 l2 是 l1 的下一行
--   l2.Id = l3.Id - 1 保证 l3 是 l2 的下一行
--   l1.Num = l2.Num = l3.Num 保证三个值相同
-- 缺点：三表 JOIN 数据量膨胀，大表时性能差
SELECT DISTINCT l1.Num AS ConsecutiveNums
FROM Logs l1
JOIN Logs l2 ON l1.Id = l2.Id - 1 AND l1.Num = l2.Num
JOIN Logs l3 ON l2.Id = l3.Id - 1 AND l2.Num = l3.Num;

-- 解法四：MySQL 用户变量法（兼容 MySQL 5.x）
-- 思路：
--   @prev 记录上一条 Num，@cnt 记录连续计数
--   遍历时逐行比较：同值 cnt+1，不同值 cnt 重置为 1
--   最后筛选 cnt >= 3 的记录
-- 注意：
--   - 变量赋值和比较在同一 SELECT 中，顺序很重要
--   - MySQL 8.0+ 中用户变量在 ORDER BY 子查询中行为不确定，建议用窗口函数
SELECT DISTINCT Num AS ConsecutiveNums
FROM (
  SELECT Num,
         @cnt := IF(@prev = Num, @cnt + 1, 1) AS cnt,
         @prev := Num
  FROM Logs, (SELECT @cnt := 0, @prev := NULL) AS init
  ORDER BY Id
) t
WHERE cnt >= 3;

-- ============================================
-- 通用解法：连续序列分组法（Gaps and Islands）
-- 思路：
--   1. 用 ROW_NUMBER() 按 Num 分区，按 Id 排序
--   2. 计算 Id - ROW_NUMBER()，连续值相同的行会得到相同的差值
--   3. 按 Num 和差值分组，COUNT >= 3 即为连续出现 3 次
-- 原理：
--   如果是连续序列 [Id=1,2,3]，ROW_NUMBER = [1,2,3]，差值为 [0,0,0]
--   如果中间断开了 [Id=1,2,4]，ROW_NUMBER = [1,2,3]，差值为 [0,0,1]
--   差值相同的行构成一个"连续的岛"
-- ============================================
SELECT DISTINCT Num AS ConsecutiveNums
FROM (
  SELECT Num,
         Id - ROW_NUMBER() OVER (PARTITION BY Num ORDER BY Id) AS grp
  FROM Logs
) t
GROUP BY Num, grp
HAVING COUNT(*) >= 3;

-- ============================================
-- 建表与测试数据
-- ============================================
/*
CREATE TABLE Logs (
  Id INT PRIMARY KEY,
  Num INT
);

INSERT INTO Logs VALUES
  (1, 1),
  (2, 1),
  (3, 1),
  (4, 2),
  (5, 1),
  (6, 2),
  (7, 2);
*/
