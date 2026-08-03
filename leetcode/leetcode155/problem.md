# LeetCode 155. Min Stack（最小栈）

## 考点
栈、设计

## 题目描述
设计一个支持 `push`，`pop`，`top` 操作，并能在常数时间内检索到最小元素的栈。

实现 `MinStack` 类：
- `MinStack()` 初始化堆栈对象。
- `void push(int val)` 将元素 val 推入堆栈。
- `void pop()` 删除堆栈顶部的元素。
- `int top()` 获取堆栈顶部的元素。
- `int getMin()` 获取堆栈中的最小元素。

你必须实现一个时间复杂度为 `O(1)` 的解决方案。

**示例 1：**
```
输入：
["MinStack","push","push","push","getMin","pop","top","getMin"]
[[],[-2],[0],[-3],[],[],[],[]]
输出：
[null,null,null,null,-3,null,0,-2]
解释：
MinStack minStack = new MinStack();
minStack.push(-2);
minStack.push(0);
minStack.push(-3);
minStack.getMin();  --> 返回 -3.
minStack.pop();
minStack.top();     --> 返回 0.
minStack.getMin();  --> 返回 -2.
```

**提示：**
- `-2^31 <= val <= 2^31 - 1`
- `pop`、`top` 和 `getMin` 操作总是在**非空栈**上调用

## 解题思路
**辅助栈（同步栈）。**

使用两个栈：
- `stack`：存储所有元素
- `minStack`：存储每个元素入栈时的当前最小值

**操作实现：**
- `push(val)`：
  - `stack.push(val)`
  - `minStack.push(min(val, minStack 栈顶))`（如果 `minStack` 空则直接 push val）
- `pop()`：
  - 两个栈同时 pop
- `top()`：
  - 返回 `stack` 栈顶
- `getMin()`：
  - 返回 `minStack` 栈顶

**优化思路：**
也可以只在 `minStack` 中存储最小值的变化点（当 val <= 当前最小值时才压入），但在 pop 时需要判断是否也弹出 `minStack`。使用同步栈方案代码更简洁。

时间复杂度：O(1) —— 所有操作  
空间复杂度：O(n)
