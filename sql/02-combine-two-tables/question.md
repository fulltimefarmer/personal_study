
# 第 2 题：组合两个表

## 题目描述

有两张表 `Person` 和 `Address`：

**Person 表：**

| 列名      | 类型    | 说明     |
|-----------|---------|----------|
| PersonId  | INT     | 主键，人员ID |
| FirstName | VARCHAR | 名       |
| LastName  | VARCHAR | 姓       |

**Address 表：**

| 列名      | 类型    | 说明       |
|-----------|---------|------------|
| AddressId | INT     | 主键，地址ID |
| PersonId  | INT     | 外键，关联Person |
| City      | VARCHAR | 城市       |
| State     | VARCHAR | 省份/州    |

请编写 SQL，查询每个人的姓名和地址信息：`FirstName`、`LastName`、`City`、`State`。**无论这个人是否有地址信息**，都需要提供姓名。如果某个人的地址不存在，则 `City` 和 `State` 显示为 `NULL`。

### 示例

**Person 表输入：**

| PersonId | FirstName | LastName |
|----------|-----------|----------|
| 1        | 张        | 三       |
| 2        | 李        | 四       |

**Address 表输入：**

| AddressId | PersonId | City   | State     |
|-----------|----------|--------|-----------|
| 1         | 1        | 北京   | 北京市    |

**输出：**

| FirstName | LastName | City | State |
|-----------|----------|------|-------|
| 张        | 三       | 北京 | 北京市 |
| 李        | 四       | NULL | NULL  |

## 考察点

- `LEFT JOIN` 与 `INNER JOIN` 的区别
- 保留左表（主表）所有记录的场景
- 缺失匹配时自动填充 `NULL`

## 解题思路

这是一个典型的左连接场景：

1. `Person` 是主表，我们关心**所有人**的信息
2. `Address` 是补充信息，有就带上，没有就留 `NULL`
3. 使用 `LEFT JOIN` 以 `Person` 为左表，`Address` 为右表，关联条件是 `Person.PersonId = Address.PersonId`

如果使用 `INNER JOIN`，则只会返回有地址的人（即 join 成功的人），李四就不会出现在结果中，这是错误的。

### 扩展

- 如果题目改为"只查询有地址的人"，直接用 `INNER JOIN` 即可
- 如果想变成"只查询没有地址的人"，用 `LEFT JOIN ... WHERE Address.PersonId IS NULL`
