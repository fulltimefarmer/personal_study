
# 第 11 题：删除重复的邮箱

## 题目描述

有一张 `Person` 表：

| 列名  | 类型    | 说明     |
|-------|---------|----------|
| id    | INT     | 主键     |
| email | VARCHAR | 邮箱地址 |

请编写一条 `DELETE` 语句，删除所有重复的邮箱记录，**只保留 `id` 最小**的那一条。

### 示例

**输入：**

| id | email            |
|----|------------------|
| 1  | john@example.com |
| 2  | bob@example.com  |
| 3  | john@example.com |

**输出：**

| id | email            |
|----|------------------|
| 1  | john@example.com |
| 2  | bob@example.com  |

**解释：** `john@example.com` 出现了两次，id=1 最小，保留它，删除 id=3 的记录。

## 考察点

- `DELETE` 结合自连接删除重复数据
- 自连接中的条件比较（保留最小 ID）
- PostgreSQL 中 `USING` 语法简化自连接删除

## 解题思路

### 思路一：自连接删除（多数据库兼容写法）

```sql
DELETE FROM Person
WHERE id NOT IN (
    SELECT min_id
    FROM (
        SELECT MIN(id) AS min_id
        FROM Person
        GROUP BY email
    ) t
);
```

先找出每个邮箱最小的 ID，然后删除 ID 不在这个最小 ID 集合中的记录。

### 思路二：自连接用不等于（PostgreSQL特有）

```sql
DELETE FROM Person p1
USING Person p2
WHERE p1.email = p2.email AND p1.id > p2.id;
```

`p1.id > p2.id` 的意思是：当存在一个更小的 ID 具有相同邮箱时，删除当前行。这样对于每组重复邮箱，只有 id 最小的那条不会被删除（因为没有比它更小的 id）。

### 思路三：窗口函数 ROW_NUMBER()

```sql
DELETE FROM Person
WHERE id IN (
    SELECT id FROM (
        SELECT id,
               ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
        FROM Person
    ) t
    WHERE rn > 1
);
```

按邮箱分组，按 ID 排序编号，删除编号大于 1 的记录。

### 思路二推荐使用

因为它是一次扫描完成删除，逻辑直观。写的时候注意：
- `USING Person p2` 是 PostgreSQL 的语法，相当于 `FROM Person p1 JOIN Person p2`
- 条件 `p1.email = p2.email AND p1.id > p2.id` 精确控制了删除范围
