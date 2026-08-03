-- ============================================================
-- 第 2 题：组合两个表
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Address CASCADE;
DROP TABLE IF EXISTS Person CASCADE;
CREATE TABLE Person (
    PersonId  INT PRIMARY KEY,
    FirstName VARCHAR,
    LastName  VARCHAR
);
CREATE TABLE Address (
    AddressId INT PRIMARY KEY,
    PersonId  INT,
    City      VARCHAR,
    State     VARCHAR,
    FOREIGN KEY (PersonId) REFERENCES Person(PersonId)
);

INSERT INTO Person (PersonId, FirstName, LastName) VALUES
(1, '张', '三'),
(2, '李', '四');

INSERT INTO Address (AddressId, PersonId, City, State) VALUES
(1, 1, '北京', '北京市');

-- 解法：LEFT JOIN（推荐）
SELECT p.FirstName, p.LastName, a.City, a.State
FROM Person p
LEFT JOIN Address a ON p.PersonId = a.PersonId;

-- 扩展：只查询有地址的人（INNER JOIN）
-- SELECT p.FirstName, p.LastName, a.City, a.State
-- FROM Person p
-- INNER JOIN Address a ON p.PersonId = a.PersonId;

-- 扩展：只查询没有地址的人
-- SELECT p.FirstName, p.LastName
-- FROM Person p
-- LEFT JOIN Address a ON p.PersonId = a.PersonId
-- WHERE a.AddressId IS NULL;
