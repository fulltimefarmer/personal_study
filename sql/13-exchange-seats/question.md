
# 第 13 题：换座位

## 题目描述

有一张 `Seat` 表，记录学生的座位信息：

| 列名     | 类型    | 说明         |
|----------|---------|--------------|
| id       | INT     | 主键，座位号（连续递增） |
| student  | VARCHAR | 学生姓名     |

请编写 SQL 查询，交换相邻学生的座位号：每两个连续的学生交换座位。如果学生总数为奇数，最后一个学生的座位号不变。

### 示例

**输入：**

| id | student |
|----|---------|
| 1  | 张三    |
| 2  | 李四    |
| 3  | 王五    |
| 4  | 赵六    |
| 5  | 孙七    |

**输出：**

| id | student |
|----|---------|
| 1  | 李四    |
| 2  | 张三    |
| 3  | 赵六    |
| 4  | 王五    |
| 5  | 孙七    |

**解释：** 张三和李四交换（1↔2），王五和赵六交换（3↔4），孙七是最后一个（奇数），保持不变。

## 考察点

- `CASE WHEN` 条件判断
- 奇数/偶数判断（`id % 2` 或 `MOD(id, 2)`）
- 子查询获取总行数
- `LEAD()` / `LAG()` 窗口函数的替代解法

## 解题思路

### 思路一：CASE WHEN（推荐）

对于每个 `id`：
- 如果是奇数且不是最后一个 → 取下一行的学生（id + 1）
- 如果是偶数 → 取上一行的学生（id - 1）
- 如果是奇数且是最后一个 → 保持不变

```sql
SELECT
    id,
    CASE
        WHEN id % 2 = 1 AND id = (SELECT COUNT(*) FROM Seat) THEN student
        WHEN id % 2 = 1 THEN (SELECT student FROM Seat s2 WHERE s2.id = s.id + 1)
        ELSE (SELECT student FROM Seat s2 WHERE s2.id = s.id - 1)
    END AS student
FROM Seat s
ORDER BY id;
```

### 思路二：CASE WHEN + 子查询计算新 ID（更简洁）

```sql
SELECT
    CASE
        WHEN id % 2 = 1 AND id = (SELECT MAX(id) FROM Seat) THEN id
        WHEN id % 2 = 1 THEN id + 1
        ELSE id - 1
    END AS id,
    student
FROM Seat
ORDER BY id;
```

直接重新计算出新的 ID，然后按新 ID 排序。奇数（非最后）变为 id+1，偶数变为 id-1，奇数且最后一个保持不变。

### 思路三：窗口函数 COALESCE + LEAD/LAG

```sql
SELECT id,
       COALESCE(
           CASE WHEN id % 2 = 1 THEN LEAD(student) OVER (ORDER BY id) END,
           student
       ) AS student
FROM Seat;
```

`LEAD()` 取下一行，如果是偶数行则取原值；最后一行 `LEAD()` 返回 NULL，用 `COALESCE` 兜底保留原值。

这个解法只处理了 `student` 列的交换，`id` 列保持原样，输出含义是"原来的座位号上现在坐的是谁"，语义更清晰。
