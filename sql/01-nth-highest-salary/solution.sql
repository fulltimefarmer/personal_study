-- ============================================
-- 第 N 高薪水 (Nth Highest Salary)
-- ============================================

-- 解法一：DISTINCT + LIMIT + OFFSET（MySQL 推荐）
-- 思路：
--   1. DISTINCT 去重，确保相同薪水不占多个排名位置
--   2. ORDER BY Salary DESC 降序排列
--   3. LIMIT 1 OFFSET M 跳过前 M 个，取第 N 个（M = N - 1）
--   4. 最外层 IFNULL 处理 OFFSET 越界时返回空结果集的情况
-- 注意：
--   - OFFSET 子句不能直接写表达式 OFFSET N-1，MySQL 5.x 中需要用变量
--   - IFNULL(expr, NULL) 等价于 IFNULL(expr, NULL)，可简化为子查询直接返回
--     （子查询返回空集时本身就是 NULL）
CREATE FUNCTION getNthHighestSalary(N INT) RETURNS INT
BEGIN
  DECLARE M INT;
  SET M = N - 1;
  RETURN (
    SELECT IFNULL(
      (SELECT DISTINCT Salary
       FROM Employee
       ORDER BY Salary DESC
       LIMIT 1 OFFSET M),
      NULL
    )
  );
END;

-- 解法二：窗口函数 DENSE_RANK()（MySQL 8.0+ / PostgreSQL 通用）
-- 思路：
--   1. 用 DENSE_RANK() OVER (ORDER BY Salary DESC) 按薪水降序排名
--   2. 相同薪水同排名，排名不跳号
--   3. 外层 WHERE rnk = N 筛选第 N 高
-- 原理：
--   - RANK():       300(1), 300(1), 200(3), 100(4)  -- 排名会跳号
--   - DENSE_RANK(): 300(1), 300(1), 200(2), 100(3)  -- 排名不跳号（本题选用）
--   - ROW_NUMBER(): 300(1), 300(2), 200(3), 100(4)  -- 严格递增
CREATE FUNCTION getNthHighestSalary(N INT) RETURNS INT
BEGIN
  RETURN (
    SELECT DISTINCT Salary
    FROM (
      SELECT Salary, DENSE_RANK() OVER (ORDER BY Salary DESC) AS rnk
      FROM Employee
    ) t
    WHERE t.rnk = N
  );
END;

-- ============================================
-- 延伸：不使用函数的纯查询写法（适合直接在查询窗口测试）
-- ============================================

-- 查询第 3 高薪水（不用函数，直接替换 N 的值）
SET @N = 3;
SET @M = @N - 1;
SELECT IFNULL(
  (SELECT DISTINCT Salary
   FROM Employee
   ORDER BY Salary DESC
   LIMIT 1 OFFSET @M),
  NULL
) AS NthHighestSalary;
