# 第 0 题：玩家积分榜（Leaderboard）

## 题目描述

设计一个玩家积分榜，支持以下 3 个方法：

| 方法 | 说明 |
|------|------|
| `addScore(playerId, score)` | 将玩家 `playerId` 加入积分榜并累加 `score` 分。如果玩家已存在，则在其现有分数上累加 `score` |
| `reset(playerId)` | 从积分榜移除玩家 `playerId`（该玩家之后若再 `addScore`，视作重新加入） |
| `topK(k)` | 返回积分榜中分数最高的前 `k` 个玩家的**总分** |

假设每个玩家的 `playerId` 唯一，且 `topK` 的参数 `k` 一定不超过当前积分榜中的玩家数量。

### 示例

```text
addScore(1, 73)   # 积分榜: {1: 73}
addScore(2, 56)   # 积分榜: {1: 73, 2: 56}
addScore(3, 39)   # 积分榜: {1: 73, 2: 56, 3: 39}
addScore(4, 51)   # 积分榜: {1: 73, 2: 56, 3: 39, 4: 51}
addScore(5, 4)    # 积分榜: {1: 73, 2: 56, 3: 39, 4: 51, 5: 4}
topK(1)  -> 73
reset(1)          # 移除玩家 1
reset(2)          # 移除玩家 2
addScore(2, 51)   # 玩家 2 重新加入
topK(3)  -> 141   # 51 + 51 + 39 = 141
```

## 考察点

- 哈希表的增删改查
- 对"取前 k 个"这类 Top-K 问题的复杂度敏感度
- 排序 vs 堆的取舍

## 解题思路

核心数据结构是一张哈希表 `scores`，`key` 为玩家 ID，`value` 为当前分数：

1. **addScore**：`scores[playerId] = scores.get(playerId, 0) + score`，O(1)
2. **reset**：`scores.pop(playerId, None)`，O(1)
3. **topK**：对所有分数排序取前 k 个求和。朴素实现 O(n log n)；若用大小为 k 的最小堆，可优化到 O(n log k)

本题 `addScore` 和 `reset` 调用远多于 `topK`（排行榜场景），因此把复杂度集中放在 `topK` 是可接受的。

### 复杂度

| 方法 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| addScore | O(1) | O(1) |
| reset | O(1) | O(1) |
| topK（排序） | O(n log n) | O(n) |
| topK（堆） | O(n log k) | O(k) |
