
# 第 29 题：递归查询 - 组织架构

## 题目描述

有一张 Employee 表，描述公司的层级组织架构：

| 列名      | 类型    | 说明                     |
|-----------|---------|--------------------------|
| id        | INT     | 主键，员工 ID             |
| name      | VARCHAR | 员工姓名                 |
| manager_id | INT    | 直属上级 ID（最高层的 manager_id 为 NULL） |

请编写 SQL，查询每位员工的**组织层级路径**（从最顶层到当前员工），以及该员工的管理层级深度（最顶层为第 1 层）。

### 示例

**输入：**

| id | name   | manager_id |
|----|--------|------------|
| 1  | 张CEO  | NULL       |
| 2  | 李VP   | 1          |
| 3  | 王总监 | 2          |
| 4  | 赵经理 | 3          |
| 5  | 孙专员 | 4          |
| 6  | 周VP   | 1          |
| 7  | 吴经理 | 6          |

**输出：**

| id | name   | level | path                          |
|----|--------|-------|-------------------------------|
| 1  | 张CEO  | 1     | 张CEO                          |
| 2  | 李VP   | 2     | 张CEO -> 李VP                  |
| 3  | 王总监 | 3     | 张CEO -> 李VP -> 王总监         |
| 4  | 赵经理 | 4     | 张CEO -> 李VP -> 王总监 -> 赵经理 |
| 5  | 孙专员 | 5     | 张CEO -> 李VP -> 王总监 -> 赵经理 -> 孙专员 |
| 6  | 周VP   | 2     | 张CEO -> 周VP                  |
| 7  | 吴经理 | 3     | 张CEO -> 周VP -> 吴经理         |

## 考察点

- PostgreSQL **递归 CTE**（WITH RECURSIVE）
- 递归查询的初始成员（anchor）和递归成员（recursive member）
- UNION ALL 在递归中的使用
- 字符串拼接构建层级路径

## 解题思路

这是递归 CTE 的经典应用。递归 CTE 由两部分组成：

1. **初始查询（anchor）**：找出起点——最顶层（manager_id IS NULL）
2. **递归查询（recursive）**：从已有的结果中，找出下一层员工

```sql
WITH RECURSIVE org_tree AS (
    -- 初始成员：最顶层员工
    SELECT id, name, manager_id,
           1 AS level,
           name::TEXT AS path
    FROM Employee
    WHERE manager_id IS NULL

    UNION ALL

    -- 递归成员：下一层员工
    SELECT e.id, e.name, e.manager_id,
           ot.level + 1,
           ot.path || ' -> ' || e.name
    FROM Employee e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT id, name, level, path
FROM org_tree
ORDER BY id;
```

### 执行过程

1. 初始查询找出张CEO（level=1, path='张CEO'）
2. 第一次递归：找出所有 manager_id = 1 的员工（李VP、周VP），level=2
3. 第二次递归：找出所有 manager_id = 2 或 6 的员工（王总监、吴经理），level=3
4. 以此类推，直到找不到更多下属

### 关键点

- `WITH RECURSIVE` 是 PostgreSQL 递归 CTE 的标准语法
- 递归必须有终止条件——当 JOIN 不到任何行时自动停止
- `UNION ALL` 不会去重，在递归场景中通常用 `UNION ALL`（性能更好）
- 路径拼接使用 `||` 字符串连接运算符

### 扩展

- 如果需要查找某个员工的所有下属（向下递归），交换递归条件为 `e.id = ot.manager_id`
- 如果需要限制递归深度，可以在递归条件中加 `ot.level < 5`
