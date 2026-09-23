# 第 3 题：用两个栈实现队列（Implement Queue using Stacks）

## 题目描述

请你仅使用两个栈实现一个先进先出（FIFO）的队列。

实现 `MyQueue` 类：

| 方法 | 说明 |
|------|------|
| `push(x)` | 将元素 `x` 移到队列末尾 |
| `pop()` | 移除并返回队列头部元素 |
| `peek()` | 返回队列头部元素 |
| `empty()` | 队列为空返回 `true`，否则返回 `false` |

你只能使用栈的标准操作：`push to top`、`peek/pop from top`、`size`、`is empty`。

### 示例

```text
q = MyQueue()
q.push(1)
q.push(2)
q.peek()   -> 1
q.pop()    -> 1
q.empty()  -> False
```

## 考察点

- 栈的 LIFO 与队列的 FIFO 之间的转化
- 摊还分析（amortized analysis）：每次元素只会从入栈被搬到出栈一次

## 解题思路

用两个栈 `in_stack`（入队）和 `out_stack`（出队）：

1. `push(x)`：直接压入 `in_stack`。
2. `pop()/peek()`：当 `out_stack` 为空时，把 `in_stack` 全部弹出并依次压入 `out_stack`，此时 `out_stack` 栈顶即队头；否则直接操作 `out_stack`。
3. `empty()`：两个栈都为空即为空。

关键点：**只有 `out_stack` 为空时才做转移**，保证顺序不被打乱。虽然单次 `pop` 可能 O(n)，但每个元素最多被搬一次，均摊后每次操作 O(1)。

### 复杂度

| 操作 | 均摊时间复杂度 | 空间复杂度 |
|------|--------------|-----------|
| push / pop / peek / empty | O(1) | O(n) |
