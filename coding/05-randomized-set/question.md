# 第 5 题：O(1) 时间插入、删除和获取随机元素（RandomizedSet）

## 题目描述

实现 `RandomizedSet` 类，要求所有操作平均时间复杂度为 O(1)：

| 方法 | 说明 |
|------|------|
| `insert(val)` | 向集合中插入 `val`。若 `val` 已存在返回 `false`，否则插入并返回 `true` |
| `remove(val)` | 从集合中移除 `val`。若存在返回 `true`，否则返回 `false` |
| `getRandom()` | 随机返回集合中的一个元素。每个元素被返回的概率应相同 |

### 示例

```text
rs = RandomizedSet()
rs.insert(1)     -> True
rs.remove(2)     -> False
rs.insert(2)     -> True
rs.getRandom()   -> 1 或 2（等概率）
rs.remove(1)     -> True
rs.insert(2)     -> False
rs.getRandom()   -> 2
```

## 考察点

- 动态数组 O(1) 随机访问 + 哈希表 O(1) 查找的组合
- 删除时用"末尾元素替换"技巧避免数组中间删除的 O(n) 开销

## 解题思路

难点在于：随机获取需要数组（O(1) 按下标访问），而 O(1) 插入/删除需要哈希表。

1. 用动态数组 `nums` 存元素，哈希表 `pos` 存 `val -> 下标`。
2. `insert`：存在则返回 `False`；否则 `pos[val] = len(nums)` 后 `nums.append(val)`。
3. `remove`：不存在返回 `False`；否则取 `idx = pos[val]`，把数组最后一个元素搬到 `idx` 位置（覆盖被删元素），更新其 `pos`，再 `pop` 掉末尾。这样删除是 O(1)。
4. `getRandom`：`random.choice(nums)` 或 `nums[random.randrange(len(nums))]`。

### 复杂度

| 操作 | 平均时间复杂度 | 空间复杂度 |
|------|--------------|-----------|
| insert / remove / getRandom | O(1) | O(n) |
