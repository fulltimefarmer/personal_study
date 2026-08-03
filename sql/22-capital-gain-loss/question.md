
# 第 22 题：股票的资本损益

## 题目描述

有一张 `Stocks` 表，记录股票交易：

| 列名        | 类型    | 说明               |
|-------------|---------|-------------------|
| stock_name  | VARCHAR | 股票名称           |
| operation   | VARCHAR | 操作：`'Buy'` 或 `'Sell'` |
| operation_day | INT   | 操作日期（第几天） |
| price       | INT     | 每股价格           |

注意：同一种股票，总是**先买入再卖出**，且买卖操作在时间上交叉出现。请编写 SQL，计算每只股票的**总资本损益**（`capital_gain_loss`），即：**所有卖出金额之和 - 所有买入金额之和**。

### 示例

**输入：**

| stock_name | operation | operation_day | price |
|------------|-----------|---------------|-------|
| 茅台       | Buy       | 1             | 1000  |
| 腾讯       | Buy       | 2             | 500   |
| 茅台       | Sell      | 5             | 1500  |
| 腾讯       | Sell      | 10            | 600   |
| 茅台       | Buy       | 8             | 1200  |
| 腾讯       | Buy       | 12            | 550   |
| 茅台       | Sell      | 15            | 1400  |

**输出：**

| stock_name | capital_gain_loss |
|------------|-------------------|
| 茅台       | 700               |
| 腾讯       | -450              |

**解释：**
- 茅台：卖出总额 = 1500 + 1400 = 2900，买入总额 = 1000 + 1200 = 2200，损益 = 2900 - 2200 = 700
- 腾讯：卖出总额 = 600，买入总额 = 500 + 550 = 1050，损益 = 600 - 1050 = -450（亏损）

## 考察点

- `CASE WHEN` 在 `SUM()` 中的条件聚合
- `GROUP BY` 股票名称
- 差值的计算

## 解题思路

将卖出金额累加为正，买入金额累加为负（或者分开汇总再相减）。

```sql
SELECT stock_name,
       SUM(CASE WHEN operation = 'Sell' THEN price ELSE -price END) AS capital_gain_loss
FROM Stocks
GROUP BY stock_name
ORDER BY stock_name;
```

思路：`Sell` 时金额为正（收入），`Buy` 时金额为负（支出）。对所有行的金额求和，就得到了总损益。

另一种写法（更直观）：

```sql
SELECT stock_name,
       SUM(CASE WHEN operation = 'Sell' THEN price ELSE 0 END)
       - SUM(CASE WHEN operation = 'Buy' THEN price ELSE 0 END) AS capital_gain_loss
FROM Stocks
GROUP BY stock_name;
```

分别汇总卖出总金额和买入总金额，然后相减。

### 要点

- `SUM(CASE WHEN ... THEN ... ELSE ... END)` 是 SQL 中做条件求和的模式
- 所有聚合都是在 `GROUP BY` 分组内进行的
