-- ============================================================
-- 第 4 题：超过 5 名学生的课程
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Courses CASCADE;
CREATE TABLE Courses (
    student VARCHAR,
    class   VARCHAR
);

INSERT INTO Courses (student, class) VALUES
('张三', '数学'),
('李四', '英语'),
('王五', '数学'),
('赵六', '计算机'),
('张三', '英语'),
('孙七', '数学'),
('周八', '数学'),
('张三', '数学'),
('吴九', '数学');

-- 解法：GROUP BY + HAVING + COUNT(DISTINCT)
SELECT class
FROM Courses
GROUP BY class
HAVING COUNT(DISTINCT student) >= 5;
