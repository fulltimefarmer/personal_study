# Best Time to Buy and Sell Stock · 买卖股票的最佳时机

- **LeetCode:** 121
- **难度 Difficulty:** Easy
- **标签 Topics:** 数组 / 动态规划 / 贪心 / Array / Dynamic Programming / Greedy
- **苹果频率:** 高频（Apple Top 100 #2，单次交易经典题）

## 题干（中文）

给定一个数组 `prices`，它的第 `i` 个元素 `prices[i]` 表示一支给定股票第 `i` 天的价格。

你只能选择**某一天**买入这只股票，并选择在**未来的某一个不同的日子**卖出该股票。设计一个算法来计算你所能获取的**最大利润**。

返回你可以从这笔交易中获取的最大利润。如果你不能获取任何利润，返回 `0`。

## Problem Statement (English)

You are given an array `prices` where `prices[i]` is the price of a given stock on the `i`-th day.

You want to maximize your profit by choosing a **single day** to buy one stock and choosing a **different day in the future** to sell that stock.

Return the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.

## 示例 / Examples

```
输入 / Input:  prices = [7,1,5,3,6,4]
输出 / Output: 5
// 在第 2 天（价格 1）买入，第 5 天（价格 6）卖出，利润 6-1=5。

输入 / Input:  prices = [7,6,4,3,1]
输出 / Output: 0
// 价格持续下跌，不交易，返回 0。
```

## 约束 / Constraints

- `1 <= prices.length <= 10^5`
- `0 <= prices[i] <= 10^4`
