
# 第 17 题：树节点类型判断

## 题目描述

有一张 `Tree` 表，表示树形结构中的节点：

| 列名 | 类型    | 说明         |
|------|---------|--------------|
| id   | INT     | 节点 ID      |
| p_id | INT     | 父节点 ID（如果是根节点则为 NULL） |

树中的每个节点可能属于以下三种类型之一：
- **Root（根节点）**：没有父节点（`p_id IS NULL`）
- **Inner（内部节点）**：既是某个节点的子节点，又是某些节点的父节点
- **Leaf（叶子节点）**：有父节点，但没有子节点

请编写 SQL 查询，输出每个节点的 ID 及其类型。

### 示例

**输入：**

| id | p_id |
|----|------|
| 1  | NULL |
| 2  | 1    |
| 3  | 1    |
| 4  | 2    |
| 5  | 2    |

**输出：**

| id | Type  |
|----|-------|
| 1  | Root  |
| 2  | Inner |
| 3  | Leaf  |
| 4  | Leaf  |
| 5  | Leaf  |

**树形结构图示：**
```
       1 (Root)
      / \
     2   3 (Leaf)
    / \
   4   5 (Leaf)
```

## 考察点

- `CASE WHEN` 多条件判断
- 用 `IN` / `EXISTS` 子查询判断"是否存在子节点"
- `NULL` 条件处理（`IS NULL` 而非 `= NULL`）

## 解题思路

### 思路一：CASE WHEN + 子查询（推荐）

```sql
SELECT id,
       CASE
           WHEN p_id IS NULL THEN 'Root'
           WHEN id IN (SELECT DISTINCT p_id FROM Tree WHERE p_id IS NOT NULL) THEN 'Inner'
           ELSE 'Leaf'
       END AS "Type"
FROM Tree;
```

判断逻辑：
1. `p_id IS NULL` → `Root`（没有父节点）
2. `id` 存在于 `p_id` 列中 → `Inner`（它的 ID 被人当作父节点引用了）
3. 其余 → `Leaf`

### 思路二：LEFT JOIN + CASE WHEN

```sql
SELECT t1.id,
       CASE
           WHEN t1.p_id IS NULL THEN 'Root'
           WHEN t2.id IS NOT NULL THEN 'Inner'
           ELSE 'Leaf'
       END AS "Type"
FROM Tree t1
LEFT JOIN (SELECT DISTINCT p_id AS id FROM Tree WHERE p_id IS NOT NULL) t2
    ON t1.id = t2.id;
```

思路相同，只是用 `LEFT JOIN` 代替 `IN` 子查询来判断是否为父节点。

### 注意

- `p_id IS NULL` 必须用 `IS NULL`，不能用 `= NULL`（`NULL` 不等于任何值包括自身）
- 子查询中需要 `DISTINCT` 去重，避免 `IN` 子查询有多余的扫描
