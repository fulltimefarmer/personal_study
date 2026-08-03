
# 第 7 题：查找重复的邮箱

## 题目描述

有一张 `Person` 表，包含邮箱地址信息：

| 列名  | 类型    | 说明     |
|-------|---------|----------|
| id    | INT     | 主键     |
| email | VARCHAR | 邮箱地址 |

请编写 SQL 查询，找出所有重复出现的邮箱地址。

### 示例

**输入：**

| id | email            |
|----|------------------|
| 1  | a@example.com    |
| 2  | c@example.com    |
| 3  | a@example.com    |
| 4  | b@example.com    |

**输出：**

| Email            |
|------------------|
| a@example.com    |

**解释：** `a@example.com` 出现了两次，是重复的邮箱。

## 考察点

- `GROUP BY` + `HAVING COUNT(*) > 1` 查找重复值
- 与"删除重复邮箱"一题的关联

## 解题思路

这是查找重复值的经典模式：

1. 按 `email` 分组
2. 计算每组中的行数 `COUNT(*)`
3. 用 `HAVING` 筛选出行数大于 1 的组
4. `SELECT email` 返回重复的邮箱

```sql
SELECT email AS "Email"
FROM Person
GROUP BY email
HAVING COUNT(*) > 1;
```

这个模式在面试中极其常见，扩展一下可以用于查找按多个列的组合重复（`GROUP BY col1, col2 HAVING COUNT(*) > 1`）。

### 扩展

- 如果想找重复的**所有记录**（而不只是邮箱），可以用子查询或窗口函数：
  ```sql
  SELECT * FROM Person
  WHERE email IN (
      SELECT email FROM Person GROUP BY email HAVING COUNT(*) > 1
  );
  ```
