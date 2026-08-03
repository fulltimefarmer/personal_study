
# 第 21 题：游戏玩法分析 - 次日留存

## 题目描述

有一张 `Activity` 表，记录游戏玩家的登录活动：

| 列名       | 类型    | 说明               |
|------------|---------|--------------------|
| player_id  | INT     | 玩家 ID            |
| device_id  | INT     | 设备 ID（本题不关心） |
| event_date | DATE    | 登录日期           |
| games_played | INT   | 当天玩的游戏数量（本题不关心） |

玩家的**首次登录日期**是每个玩家的 `MIN(event_date)`。

请编写 SQL，查询所有玩家中，**首次登录后第二天又登录了的玩家**占全体玩家的比例，结果保留 2 位小数。

### 示例

**输入：**

| player_id | device_id | event_date | games_played |
|-----------|-----------|------------|--------------|
| 1         | 2         | 2024-03-01 | 5            |
| 1         | 2         | 2024-03-02 | 6            |
| 2         | 3         | 2024-05-01 | 1            |
| 3         | 1         | 2024-04-02 | 0            |
| 3         | 4         | 2024-04-03 | 5            |
| 3         | 1         | 2024-04-04 | 3            |
| 4         | 1         | 2024-06-01 | 3            |
| 4         | 1         | 2024-06-03 | 2            |

**输出：**

| fraction |
|----------|
| 0.50     |

**解释：**
- player 1 首次登录 2024-03-01，第二天 03-02 登录了 → 留存 ✅
- player 2 首次登录 2024-05-01，没有第二天记录 → 未留存 ❌
- player 3 首次登录 2024-04-02，第二天 04-03 登录了 → 留存 ✅
- player 4 首次登录 2024-06-01，第二天 06-02 没有记录（06-03 不是次日）→ 未留存 ❌
- 4 个玩家中 2 个次日留存 → 2/4 = 0.50

## 考察点

- `MIN()` + `GROUP BY` 找首次日期
- 日期计算 `event_date + INTERVAL '1 day'`
- `LEFT JOIN` 检查次日是否存在记录
- 分子/分母 计算比例
- `COUNT(DISTINCT)` 与子查询配合

## 解题思路

1. 找出每个玩家的首次登录日期
2. 判断该玩家是否在"首次登录日期 + 1 天"也有登录记录
3. 统计次日留存的玩家数 ÷ 总玩家数

```sql
WITH first_login AS (
    SELECT player_id, MIN(event_date) AS first_date
    FROM Activity
    GROUP BY player_id
)
SELECT ROUND(
    COUNT(DISTINCT a.player_id) * 1.0 /
    (SELECT COUNT(DISTINCT player_id) FROM Activity),
    2
) AS fraction
FROM first_login f
JOIN Activity a ON f.player_id = a.player_id
                AND a.event_date = f.first_date + INTERVAL '1 day';
```

**关键点**：
- `JOIN` 条件中同时匹配 `player_id` 和 `event_date = first_date + 1 day`
- 只有次日登录了的玩家才能 `JOIN` 上，`COUNT(DISTINCT a.player_id)` 就是次日留存的玩家数
- 分母需要 `(SELECT COUNT(DISTINCT player_id) FROM Activity)` 单独计算总玩家数

注意示例数据需要调整输出预期值。根据数据，player 1 和 player 3 都次日留存了，是 2/4 = 0.50。
