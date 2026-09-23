# Best Time to Buy and Sell Stock — 考点分析与解题思路

## 考点分析

1. **单次交易 = 最大差值**：要在某天买入、未来某天卖出，等价于求 `max(prices[j] - prices[i])` 且 `i < j`。
2. **前缀最小值（贪心）**：从左到右扫描，维护「到当前为止的最低买入价」`minPrice`。每一天的潜在利润 = `prices[i] - minPrice`，用它与全局 `maxProfit` 比较。
3. **本质是 DP**：状态 `dp[i]` = 前 i 天最大利润，`dp[i] = max(dp[i-1], prices[i] - minPrice)`，可空间优化为 O(1)。
4. **边界**：价格单调下降时利润为 0（`maxProfit` 初始 0，不会为负）。

## 解题思路

- 初始化 `minPrice = Infinity`、`maxProfit = 0`。
- 遍历 `prices`：
  - 若 `prices[i] < minPrice`，更新 `minPrice`；
  - 否则用 `prices[i] - minPrice` 更新 `maxProfit`。
- 返回 `maxProfit`。

## 复杂度

- 时间：O(n)，一次遍历。
- 空间：O(1)。

## 参考代码

```ts
function maxProfit(prices: number[]): number {
  let minPrice = Infinity;
  let maxProfit = 0;
  for (const price of prices) {
    if (price < minPrice) {
      minPrice = price;
    } else {
      maxProfit = Math.max(maxProfit, price - minPrice);
    }
  }
  return maxProfit;
}
```

## 追问 / Follow-ups

1. **可多次交易**（LeetCode 122）？→ 累加所有「上坡」段：`sum(max(prices[i]-prices[i-1], 0))`。
2. **最多两次交易**（LeetCode 123）？→ 状态机 DP（持 5 个状态）或双向各算一次最大利润再合并。
3. **最多 k 次交易**（LeetCode 188）/ **含冷冻期**（LeetCode 309）/ **含手续费**（LeetCode 714）？→ 通用状态机：`hold` 与 `notHold` 两个状态滚动更新。
4. 能否返回具体的买入/卖出日？→ 在更新 `minPrice` 时记录其下标，更新 `maxProfit` 时记录卖出下标。
