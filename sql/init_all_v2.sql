-- ============================================================
-- 初始化脚本：study 数据库全部 30 题（表名加题号后缀）
-- ============================================================

-- -------------------------------------------------------
-- 第 1 题
-- -------------------------------------------------------
-- ============================================================
-- 第 1 题：大的国家
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS World01 CASCADE;
CREATE TABLE World01 (
    name       VARCHAR PRIMARY KEY,
    continent  VARCHAR,
    area       INT,
    population INT,
    gdp        BIGINT
);

INSERT INTO World01 (name, continent, area, population, gdp) VALUES
('阿富汗',   '亚洲', 652230,  25500100,  20343000000),
('阿尔巴尼亚', '欧洲', 28748,   2831741,   12960000000),
('阿尔及利亚', '非洲', 2381741, 37100000, 188681000000),
('安道尔',   '欧洲', 468,     78115,      3712000000),
('安哥拉',   '非洲', 1246700, 20609294, 100990000000);

-- -------------------------------------------------------
-- 第 2 题
-- -------------------------------------------------------
-- ============================================================
-- 第 2 题：组合两个表
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Address02 CASCADE;
DROP TABLE IF EXISTS Person02 CASCADE;
CREATE TABLE Person02 (
    PersonId  INT PRIMARY KEY,
    FirstName VARCHAR,
    LastName  VARCHAR
);
CREATE TABLE Address02 (
    AddressId INT PRIMARY KEY,
    PersonId  INT,
    City      VARCHAR,
    State     VARCHAR,
    FOREIGN KEY (PersonId) REFERENCES Person02(PersonId)
);

INSERT INTO Person02 (PersonId, FirstName, LastName) VALUES
(1, '张', '三'),
(2, '李', '四');

INSERT INTO Address02 (AddressId, PersonId, City, State) VALUES
(1, 1, '北京', '北京市');

-- -------------------------------------------------------
-- 第 3 题
-- -------------------------------------------------------
-- ============================================================
-- 第 3 题：有趣的电影
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Cinema03 CASCADE;
CREATE TABLE Cinema03 (
    id          INT PRIMARY KEY,
    movie       VARCHAR,
    description VARCHAR,
    rating      FLOAT
);

INSERT INTO Cinema03 (id, movie, description, rating) VALUES
(1, '战狼',     'great',     9.0),
(2, '科幻片A',  'boring',    7.5),
(3, '流浪地球', 'wonderful', 8.9),
(4, '动画片B',  'boring',    6.0),
(5, '哪吒',     'amazing',   9.5);

-- -------------------------------------------------------
-- 第 4 题
-- -------------------------------------------------------
-- ============================================================
-- 第 4 题：超过 5 名学生的课程
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Courses04 CASCADE;
CREATE TABLE Courses04 (
    student VARCHAR,
    class   VARCHAR
);

INSERT INTO Courses04 (student, class) VALUES
('张三', '数学'),
('李四', '英语'),
('王五', '数学'),
('赵六', '计算机'),
('张三', '英语'),
('孙七', '数学'),
('周八', '数学'),
('张三', '数学'),
('吴九', '数学');

-- -------------------------------------------------------
-- 第 5 题
-- -------------------------------------------------------
-- ============================================================
-- 第 5 题：变更性别
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Salary05 CASCADE;
CREATE TABLE Salary05 (
    id     INT PRIMARY KEY,
    name   VARCHAR,
    sex    CHAR(1),
    salary INT
);

INSERT INTO Salary05 (id, name, sex, salary) VALUES
(1, '张三', 'm', 8000),
(2, '李四', 'f', 12000),
(3, '王五', 'm', 9000),
(4, '赵六', 'f', 15000);

-- 查看更新前数据
SELECT '更新前：' AS info;
SELECT * FROM Salary05;

-- -------------------------------------------------------
-- 第 6 题
-- -------------------------------------------------------
-- ============================================================
-- 第 6 题：上升的温度
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Weather06 CASCADE;
CREATE TABLE Weather06 (
    id          INT PRIMARY KEY,
    recordDate  DATE,
    temperature INT
);

INSERT INTO Weather06 (id, recordDate, temperature) VALUES
(1, '2024-01-01', 10),
(2, '2024-01-02', 25),
(3, '2024-01-03', 20),
(4, '2024-01-04', 30),
(5, '2024-01-06', 28);

-- -------------------------------------------------------
-- 第 7 题
-- -------------------------------------------------------
-- ============================================================
-- 第 7 题：查找重复的邮箱
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Person07 CASCADE;
CREATE TABLE Person07 (
    id    INT PRIMARY KEY,
    email VARCHAR
);

INSERT INTO Person07 (id, email) VALUES
(1, 'a@example.com'),
(2, 'c@example.com'),
(3, 'a@example.com'),
(4, 'b@example.com');

-- -------------------------------------------------------
-- 第 8 题
-- -------------------------------------------------------
-- ============================================================
-- 第 8 题：从不订购的客户
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Orders08 CASCADE;
DROP TABLE IF EXISTS Customers08 CASCADE;
CREATE TABLE Customers08 (
    id   INT PRIMARY KEY,
    name VARCHAR
);
CREATE TABLE Orders08 (
    id         INT PRIMARY KEY,
    customerId INT,
    FOREIGN KEY (customerId) REFERENCES Customers08(id)
);

INSERT INTO Customers08 (id, name) VALUES
(1, '张三'),
(2, '李四'),
(3, '王五'),
(4, '赵六');

INSERT INTO Orders08 (id, customerId) VALUES
(1, 3),
(2, 1);

-- -------------------------------------------------------
-- 第 9 题
-- -------------------------------------------------------
-- ============================================================
-- 第 9 题：超过经理收入的员工
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee09 CASCADE;
CREATE TABLE Employee09 (
    id        INT PRIMARY KEY,
    name      VARCHAR,
    salary    INT,
    managerId INT
);

INSERT INTO Employee09 (id, name, salary, managerId) VALUES
(1, '张总', 80000, NULL),
(2, '小王', 60000, 1),
(3, '小李', 75000, 1),
(4, '小赵', 85000, 1),
(5, '小孙', 50000, 3);

-- -------------------------------------------------------
-- 第 10 题
-- -------------------------------------------------------
-- ============================================================
-- 第 10 题：第二高薪水
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee10 CASCADE;
CREATE TABLE Employee10 (
    id     INT PRIMARY KEY,
    salary INT
);

INSERT INTO Employee10 (id, salary) VALUES
(1, 100),
(2, 200),
(3, 300);

-- -------------------------------------------------------
-- 第 11 题
-- -------------------------------------------------------
-- ============================================================
-- 第 11 题：删除重复的邮箱
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Person11 CASCADE;
CREATE TABLE Person11 (
    id    INT PRIMARY KEY,
    email VARCHAR
);

INSERT INTO Person11 (id, email) VALUES
(1, 'john@example.com'),
(2, 'bob@example.com'),
(3, 'john@example.com');

-- 查看删除前数据
SELECT '删除前：' AS info;
SELECT * FROM Person11 ORDER BY id;

-- -------------------------------------------------------
-- 第 12 题
-- -------------------------------------------------------
-- ============================================================
-- 第 12 题：分数排名
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Scores12 CASCADE;
CREATE TABLE Scores12 (
    id    INT PRIMARY KEY,
    score DECIMAL(5,2)
);

INSERT INTO Scores12 (id, score) VALUES
(1, 95.0),
(2, 85.0),
(3, 85.0),
(4, 76.0),
(5, 60.0);

-- -------------------------------------------------------
-- 第 13 题
-- -------------------------------------------------------
-- ============================================================
-- 第 13 题：换座位
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Seat13 CASCADE;
CREATE TABLE Seat13 (
    id      INT PRIMARY KEY,
    student VARCHAR
);

INSERT INTO Seat13 (id, student) VALUES
(1, '张三'),
(2, '李四'),
(3, '王五'),
(4, '赵六'),
(5, '孙七');

-- -------------------------------------------------------
-- 第 14 题
-- -------------------------------------------------------
-- ============================================================
-- 第 14 题：第 N 高薪水
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee14 CASCADE;
DROP FUNCTION IF EXISTS getNthHighestSalary(INT);

CREATE TABLE Employee14 (
    id     INT PRIMARY KEY,
    salary INT
);

INSERT INTO Employee14 (id, salary) VALUES
(1, 100),
(2, 200),
(3, 300);

-- -------------------------------------------------------
-- 第 15 题
-- -------------------------------------------------------
-- ============================================================
-- 第 15 题：连续出现的数字
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Logs15 CASCADE;
CREATE TABLE Logs15 (
    id  INT PRIMARY KEY,
    num VARCHAR
);

INSERT INTO Logs15 (id, num) VALUES
(1, '1'),
(2, '1'),
(3, '1'),
(4, '2'),
(5, '1'),
(6, '2'),
(7, '2');

-- -------------------------------------------------------
-- 第 16 题
-- -------------------------------------------------------
-- ============================================================
-- 第 16 题：部门最高工资的员工
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee16 CASCADE;
DROP TABLE IF EXISTS Department16 CASCADE;

CREATE TABLE Department16 (
    id   INT PRIMARY KEY,
    name VARCHAR
);

CREATE TABLE Employee16 (
    id           INT PRIMARY KEY,
    name         VARCHAR,
    salary       INT,
    departmentId INT,
    FOREIGN KEY (departmentId) REFERENCES Department16(id)
);

INSERT INTO Department16 (id, name) VALUES
(1, '技术部'),
(2, '销售部'),
(3, '行政部');

INSERT INTO Employee16 (id, name, salary, departmentId) VALUES
(1, '张三', 70000, 1),
(2, '李四', 90000, 1),
(3, '王五', 80000, 2),
(4, '赵六', 60000, 2),
(5, '孙七', 90000, 1),
(6, '周八', 70000, 3);

-- -------------------------------------------------------
-- 第 17 题
-- -------------------------------------------------------
-- ============================================================
-- 第 17 题：树节点类型判断
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Tree17 CASCADE;
CREATE TABLE Tree17 (
    id   INT,
    p_id INT
);

INSERT INTO Tree17 (id, p_id) VALUES
(1, NULL),
(2, 1),
(3, 1),
(4, 2),
(5, 2);

-- -------------------------------------------------------
-- 第 18 题
-- -------------------------------------------------------
-- ============================================================
-- 第 18 题：行程和用户（取消率）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Trips18 CASCADE;
DROP TABLE IF EXISTS Users18 CASCADE;

CREATE TABLE Users18 (
    users_id INT PRIMARY KEY,
    banned   VARCHAR,
    role     VARCHAR
);

CREATE TABLE Trips18 (
    id         INT PRIMARY KEY,
    client_id  INT,
    driver_id  INT,
    city_id    INT,
    status     VARCHAR,
    request_at DATE,
    FOREIGN KEY (client_id) REFERENCES Users18(users_id),
    FOREIGN KEY (driver_id) REFERENCES Users18(users_id)
);

INSERT INTO Users18 (users_id, banned, role) VALUES
(1,  'No', 'client'),
(2,  'Yes', 'client'),
(3,  'No', 'client'),
(4,  'No', 'client'),
(10, 'No', 'driver'),
(11, 'No', 'driver'),
(12, 'No', 'driver'),
(13, 'No', 'driver');

INSERT INTO Trips18 (id, client_id, driver_id, city_id, status, request_at) VALUES
(1, 1, 10, 1, 'completed',            '2013-10-01'),
(2, 2, 11, 1, 'cancelled_by_driver', '2013-10-01'),
(3, 3, 12, 1, 'completed',            '2013-10-01'),
(4, 4, 13, 1, 'cancelled_by_client', '2013-10-01'),
(5, 1, 10, 1, 'completed',            '2013-10-02'),
(6, 2, 11, 1, 'completed',            '2013-10-02'),
(7, 3, 12, 1, 'completed',            '2013-10-02'),
(8, 1, 12, 1, 'completed',            '2013-10-03'),
(9, 3, 10, 1, 'cancelled_by_driver', '2013-10-03');

-- -------------------------------------------------------
-- 第 19 题
-- -------------------------------------------------------
-- ============================================================
-- 第 19 题：每月交易统计
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Transactions19 CASCADE;
CREATE TABLE Transactions19 (
    id         INT PRIMARY KEY,
    country    VARCHAR,
    state      VARCHAR,
    amount     INT,
    trans_date DATE
);

INSERT INTO Transactions19 (id, country, state, amount, trans_date) VALUES
(1, '中国', 'approved', 1000, '2024-01-15'),
(2, '中国', 'declined', 2000, '2024-01-20'),
(3, '中国', 'approved', 3000, '2024-02-10'),
(4, '美国', 'approved', 5000, '2024-01-10'),
(5, '美国', 'declined', 6000, '2024-01-25'),
(6, '美国', 'approved', 2000, '2024-02-05');

-- -------------------------------------------------------
-- 第 20 题
-- -------------------------------------------------------
-- ============================================================
-- 第 20 题：体育馆人流量（连续多天）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Stadium20 CASCADE;
CREATE TABLE Stadium20 (
    id         INT PRIMARY KEY,
    visit_date DATE,
    people     INT
);

INSERT INTO Stadium20 (id, visit_date, people) VALUES
(1, '2024-01-01', 10),
(2, '2024-01-02', 109),
(3, '2024-01-03', 150),
(4, '2024-01-04', 99),
(5, '2024-01-05', 145),
(6, '2024-01-06', 1455),
(7, '2024-01-07', 199),
(8, '2024-01-08', 188);

-- -------------------------------------------------------
-- 第 21 题
-- -------------------------------------------------------
-- ============================================================
-- 第 21 题：游戏玩法分析 - 次日留存
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Activity21 CASCADE;
CREATE TABLE Activity21 (
    player_id    INT,
    device_id    INT,
    event_date   DATE,
    games_played INT
);

INSERT INTO Activity21 (player_id, device_id, event_date, games_played) VALUES
(1, 2, '2024-03-01', 5),
(1, 2, '2024-03-02', 6),
(2, 3, '2024-05-01', 1),
(3, 1, '2024-04-02', 0),
(3, 4, '2024-04-03', 5),
(3, 1, '2024-04-04', 3),
(4, 1, '2024-06-01', 3),
(4, 1, '2024-06-03', 2);

-- -------------------------------------------------------
-- 第 22 题
-- -------------------------------------------------------
-- ============================================================
-- 第 22 题：股票的资本损益
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Stocks22 CASCADE;
CREATE TABLE Stocks22 (
    stock_name    VARCHAR,
    operation     VARCHAR,
    operation_day INT,
    price         INT
);

INSERT INTO Stocks22 (stock_name, operation, operation_day, price) VALUES
('茅台', 'Buy',  1,  1000),
('腾讯', 'Buy',  2,  500),
('茅台', 'Sell', 5,  1500),
('腾讯', 'Sell', 10, 600),
('茅台', 'Buy',  8,  1200),
('腾讯', 'Buy',  12, 550),
('茅台', 'Sell', 15, 1400);

-- -------------------------------------------------------
-- 第 23 题
-- -------------------------------------------------------
-- ============================================================
-- 第 23 题：即时食物配送比例
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Delivery23 CASCADE;
CREATE TABLE Delivery23 (
    delivery_id                  INT PRIMARY KEY,
    customer_id                  INT,
    order_date                   DATE,
    customer_pref_delivery_date  DATE
);

INSERT INTO Delivery23 (delivery_id, customer_id, order_date, customer_pref_delivery_date) VALUES
(1, 1, '2024-08-01', '2024-08-02'),
(2, 2, '2024-08-02', '2024-08-02'),
(3, 1, '2024-08-11', '2024-08-12'),
(4, 3, '2024-08-24', '2024-08-25'),
(5, 3, '2024-08-26', '2024-08-26'),
(6, 2, '2024-08-28', '2024-08-29');

-- -------------------------------------------------------
-- 第 24 题
-- -------------------------------------------------------
-- ============================================================
-- 第 24 题：好友申请通过率
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS RequestAccepted24 CASCADE;
DROP TABLE IF EXISTS FriendRequest24 CASCADE;

CREATE TABLE FriendRequest24 (
    sender_id    INT,
    send_to_id   INT,
    request_date DATE
);

CREATE TABLE RequestAccepted24 (
    requester_id INT,
    accepter_id  INT,
    accept_date  DATE
);

INSERT INTO FriendRequest24 (sender_id, send_to_id, request_date) VALUES
(1, 2, '2024-01-01'),
(1, 3, '2024-01-02'),
(1, 4, '2024-01-03'),
(2, 3, '2024-01-04'),
(1, 2, '2024-01-05'),
(2, 4, '2024-01-06');

INSERT INTO RequestAccepted24 (requester_id, accepter_id, accept_date) VALUES
(1, 2, '2024-01-06'),
(1, 3, '2024-01-07'),
(2, 4, '2024-01-07');

-- -------------------------------------------------------
-- 第 25 题
-- -------------------------------------------------------
-- ============================================================
-- 第 25 题：产品销售分析 - 分组 TopN
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Sales25 CASCADE;
DROP TABLE IF EXISTS Product25 CASCADE;

CREATE TABLE Product25 (
    product_id   INT PRIMARY KEY,
    product_name VARCHAR,
    category     VARCHAR
);

CREATE TABLE Sales25 (
    sale_id    INT PRIMARY KEY,
    product_id INT,
    sale_date  DATE,
    quantity   INT,
    revenue    DECIMAL(12,2),
    FOREIGN KEY (product_id) REFERENCES Product25(product_id)
);

INSERT INTO Product25 (product_id, product_name, category) VALUES
(1, '手机A', '电子产品'),
(2, '手机B', '电子产品'),
(3, 'T恤',   '服装'),
(4, '裤子',   '服装'),
(5, '手机C', '电子产品');

INSERT INTO Sales25 (sale_id, product_id, sale_date, quantity, revenue) VALUES
(1, 1, '2024-01-01', 10, 50000),
(2, 1, '2024-01-02', 5,  25000),
(3, 2, '2024-01-03', 8,  40000),
(4, 3, '2024-01-01', 20, 2000),
(5, 4, '2024-01-02', 15, 3000),
(6, 5, '2024-01-03', 3,  18000),
(7, 2, '2024-01-04', 15, 75000);

-- -------------------------------------------------------
-- 第 26 题
-- -------------------------------------------------------
-- ============================================================
-- 第 26 题：累计销售额（窗口函数）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Orders26 CASCADE;
CREATE TABLE Orders26 (
    order_id   INT PRIMARY KEY,
    order_date DATE,
    amount     DECIMAL(12,2)
);

INSERT INTO Orders26 (order_id, order_date, amount) VALUES
(1, '2024-01-01', 100),
(2, '2024-01-03', 200),
(3, '2024-01-04', 150),
(4, '2024-01-05', 50),
(5, '2024-01-05', 100);

-- -------------------------------------------------------
-- 第 27 题
-- -------------------------------------------------------
-- ============================================================
-- 第 27 题：平均工资 - 部门 vs 公司
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee27 CASCADE;
CREATE TABLE Employee27 (
    id         INT PRIMARY KEY,
    department VARCHAR,
    salary     DECIMAL(10,2)
);

INSERT INTO Employee27 (id, department, salary) VALUES
(1, '技术部', 15000),
(2, '技术部', 12000),
(3, '技术部', 18000),
(4, '销售部', 10000),
(5, '销售部', 13000),
(6, '行政部', 9000);

-- -------------------------------------------------------
-- 第 28 题
-- -------------------------------------------------------
-- ============================================================
-- 第 28 题：连续登录天数（GAP/ISLAND）
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Login28 CASCADE;
CREATE TABLE Login28 (
    user_id    INT,
    login_date DATE
);

INSERT INTO Login28 (user_id, login_date) VALUES
(1, '2024-01-01'),
(1, '2024-01-02'),
(1, '2024-01-03'),
(1, '2024-01-05'),
(1, '2024-01-06'),
(2, '2024-01-01'),
(2, '2024-01-02'),
(2, '2024-01-04'),
(3, '2024-01-01'),
(3, '2024-01-01');

-- -------------------------------------------------------
-- 第 29 题
-- -------------------------------------------------------
-- ============================================================
-- 第 29 题：递归查询 - 组织架构
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS Employee29 CASCADE;
CREATE TABLE Employee29 (
    id         INT PRIMARY KEY,
    name       VARCHAR,
    manager_id INT
);

INSERT INTO Employee29 (id, name, manager_id) VALUES
(1, '张CEO',  NULL),
(2, '李VP',   1),
(3, '王总监', 2),
(4, '赵经理', 3),
(5, '孙专员', 4),
(6, '周VP',   1),
(7, '吴经理', 6);

-- -------------------------------------------------------
-- 第 30 题
-- -------------------------------------------------------
-- ============================================================
-- 第 30 题：用户行为漏斗分析
-- 数据库：PostgreSQL
-- ============================================================

DROP TABLE IF EXISTS UserBehavior30 CASCADE;
CREATE TABLE UserBehavior30 (
    user_id   INT,
    page      VARCHAR,
    timestamp TIMESTAMP
);

INSERT INTO UserBehavior30 (user_id, page, timestamp) VALUES
(1, 'home',    '2024-01-01 08:00:00'),
(1, 'search',  '2024-01-01 08:05:00'),
(1, 'product', '2024-01-01 08:10:00'),
(1, 'cart',    '2024-01-01 08:15:00'),
(1, 'pay',     '2024-01-01 08:20:00'),
(2, 'home',    '2024-01-01 09:00:00'),
(2, 'search',  '2024-01-01 09:05:00'),
(3, 'home',    '2024-01-01 10:00:00'),
(3, 'search',  '2024-01-01 10:05:00'),
(3, 'product', '2024-01-01 10:10:00'),
(3, 'cart',    '2024-01-01 10:15:00'),
(4, 'home',    '2024-01-01 11:00:00');

-- 初始化完成
