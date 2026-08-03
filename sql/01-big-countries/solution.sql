-- ============================================================
-- 第 1 题：大的国家
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS World CASCADE;
CREATE TABLE World (
    name       VARCHAR PRIMARY KEY,
    continent  VARCHAR,
    area       INT,
    population INT,
    gdp        BIGINT
);

INSERT INTO World (name, continent, area, population, gdp) VALUES
('阿富汗',   '亚洲', 652230,  25500100,  20343000000),
('阿尔巴尼亚', '欧洲', 28748,   2831741,   12960000000),
('阿尔及利亚', '非洲', 2381741, 37100000, 188681000000),
('安道尔',   '欧洲', 468,     78115,      3712000000),
('安哥拉',   '非洲', 1246700, 20609294, 100990000000);

-- 解法：用 OR 连接两个条件
SELECT name, population, area
FROM World
WHERE area >= 3000000
   OR population >= 25000000;
