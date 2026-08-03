-- ============================================================
-- 第 5 题：变更性别
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Salary CASCADE;
CREATE TABLE Salary (
    id     INT PRIMARY KEY,
    name   VARCHAR,
    sex    CHAR(1),
    salary INT
);

INSERT INTO Salary (id, name, sex, salary) VALUES
(1, '张三', 'm', 8000),
(2, '李四', 'f', 12000),
(3, '王五', 'm', 9000),
(4, '赵六', 'f', 15000);

-- 查看更新前数据
SELECT '更新前：' AS info;
SELECT * FROM Salary;

-- 解法：CASE WHEN 在 SET 中
UPDATE Salary
SET sex = CASE WHEN sex = 'm' THEN 'f' ELSE 'm' END;

-- 查看更新后数据
SELECT '更新后：' AS info;
SELECT * FROM Salary;
