# 题目 2：线程安全的有界阻塞队列

## 题目描述

实现一个**线程安全的有界阻塞队列**，支持多生产者和多消费者场景。

要求实现以下功能：

- **构造方法**：指定队列的固定容量 `capacity`。
- `void enqueue(T item)` —— 将元素加入队列，如果队列已满则**阻塞等待**，直到有空间可用。
- `T dequeue()` —— 从队列头部取出一个元素，如果队列为空则**阻塞等待**，直到有元素可用。
- `void shutdown()` —— **优雅关闭**队列，唤醒所有等待线程，防止后续操作。
- 支持**带超时**的 `enqueue`/`dequeue` 变体（可选扩展）。
- 在 `shutdown` 后，`enqueue` 应抛出异常，`dequeue` 应消费完剩余元素后抛出异常。

## 示例

```
BoundedBlockingQueue<Integer> queue = new BoundedBlockingQueue<>(3);

// 生产者线程调用 queue.enqueue(item)
// 消费者线程调用 queue.dequeue()

线程 A: enqueue(1) → 成功 (队列: [1])
线程 B: enqueue(2) → 成功 (队列: [1, 2])
线程 C: enqueue(3) → 成功 (队列: [1, 2, 3], 已满)
线程 D: enqueue(4) → 阻塞等待...
线程 E: dequeue()  → 返回 1, 唤醒线程 D, 4 成功入队
```

## 解题思路

### 1. 方案对比与选择

| 方案 | 优点 | 缺点 |
|------|------|------|
| `synchronized` + `wait/notifyAll` | 简单直观，JDK 内置 | 信号精度低，唤醒所有线程 |
| `ReentrantLock` + 两个 `Condition` | 精准唤醒，性能更好 | 需要手动管理锁释放 |
| 直接使用 `ArrayBlockingQueue` | 无需自己实现 | 面试题不允许直接用 |

**推荐方案**：`ReentrantLock` + 双 `Condition`（`notFull` 和 `notEmpty`），实现精准的线程协作。

### 2. 核心设计

```
┌──────────────────────────────────────────────┐
│              BoundedBlockingQueue              │
│                                                │
│   lock (ReentrantLock)                         │
│   ├── notFull  (Condition)  ── 生产者等待      │
│   └── notEmpty (Condition)  ── 消费者等待      │
│                                                │
│   queue (LinkedList) ── 实际存储               │
│   capacity            ── 最大容量              │
│   shutdown (volatile) ── 关闭标记              │
└──────────────────────────────────────────────┘
```

### 3. 关键线程安全措施

| 措施 | 原因 |
|------|------|
| `while` 而非 `if` 判断条件 | **防止虚假唤醒**（spurious wakeup）：被唤醒后需重新检查条件是否满足 |
| `lock.lockInterruptibly()` | 支持线程中断，优雅停止 |
| `volatile shutdown` | 确保关闭标记在多线程间的内存可见性 |
| `signal()` 而非 `signalAll()` | 双 Condition 设计下只需唤醒一个生产者/消费者，减少上下文切换 |
| `try-finally` 释放锁 | 确保异常时锁一定被释放 |

### 4. 优雅关闭设计

```
shutdown() 执行流程：
1. 设置 shutdown = true
2. 调用 notFull.signalAll()   —— 唤醒所有阻塞的生产者
3. 调用 notEmpty.signalAll()  —— 唤醒所有阻塞的消费者
4. 被唤醒的线程在 while 循环中检测到 shutdown=true：
   - enqueue → 抛出 IllegalStateException
   - dequeue → 若队列还有数据则正常消费，空后抛出 IllegalStateException
```

### 5. 注意事项

- **禁止 null 元素**：与 Java 标准 Queue 接口一致，防止空指针陷阱。
- **带超时的操作**：使用 `awaitNanos(nanos)` 并正确处理返回值（剩余等待时间）。
- **不可变性**：`capacity` 一经构造不可变，避免并发修改的复杂性。

### 6. 复杂度分析

- **时间复杂度**：`enqueue`/`dequeue` 均为 O(1)（LinkedList 头尾操作）。
- **空间复杂度**：O(n)，n 为队列容量。

## 考察维度

- **并发编程能力**：正确使用锁和条件变量，避免死锁、虚假唤醒。
- **生产工程实践**：优雅关闭、异常处理、参数校验。
- **代码质量**：清晰的 API、生命周期管理、完善的 Javadoc。
- **技术深度**：生产者-消费者模式、内存可见性（`volatile`）、线程协调机制。
