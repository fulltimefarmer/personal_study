# 题目 7：线程安全连接池

## 题目描述

实现一个**通用线程安全连接池**，模拟数据库连接池的核心功能。

要求实现：

- `ConnectionPool(int maxConnections, ConnectionFactory factory)` —— 构造方法，指定最大连接数和连接工厂。
- `Connection borrow()` —— 从池中获取一个可用连接。如果池中没有空闲连接且未达到上限，则**创建新连接**；如果已达到上限且无空闲连接，则**阻塞等待**，直到有连接归还。
- `void release(Connection conn)` —— 将连接归还到池中，唤醒等待的线程。
- `void shutdown()` —— 关闭连接池，关闭所有空闲连接，唤醒等待线程，拒绝后续操作。
- 支持**连接健康检查**：borrow 时验证连接有效性，无效则丢弃并重试。
- 支持**最大空闲时间**：空闲超时的连接自动关闭并从池中移除。

## 示例

```java
ConnectionPool<DatabaseConn> pool = new ConnectionPool<>(
    5,
    () -> new DatabaseConn("jdbc:mysql://localhost:3306/db")
);

DatabaseConn conn = pool.borrow(); // 获取连接
// ... 使用连接 ...
pool.release(conn);                // 归还连接
pool.shutdown();                   // 关闭连接池
```

## 解题思路

### 1. 连接池状态模型

```
                     ┌──────────────┐
                     │   已创建 0/N  │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             │             ▼
     ┌────────────┐        │    ┌──────────────┐
     │  空闲队列   │◄───────┘    │  已借出集合    │
     │ (idleQueue) │   release   │ (activeSet)   │
     └─────┬──────┘              └──────┬───────┘
           │ borrow                     │
           ▼                            │
     ┌──────────────────────────────────┘
     │  总数 = idleQueue.size() + activeSet.size() <= maxConnections
```

### 2. 核心设计

```
┌──────────────────────────────────────────────────────┐
│                  ConnectionPool<T>                    │
│                                                       │
│  BlockingDeque<T> idleQueue    ← 空闲连接队列         │
│  Set<T>           activeSet    ← 已借出的连接         │
│  int              maxConnections ← 连接上限           │
│  ConnectionFactory<T> factory  ← 连接工厂             │
│  long             maxIdleTimeMs ← 最大空闲时间        │
│  ReentrantLock    lock         ← 全局锁               │
│  Condition        notEmpty     ← borrow 等待条件      │
│  volatile boolean shutdown     ← 关闭标记             │
└──────────────────────────────────────────────────────┘
```

### 3. borrow 执行流程

```
 borrow() 被调用
     │
     ▼
 ┌───────────┐
 │ 获取锁      │
 └─────┬─────┘
       ▼
 ┌─────────────────────────┐
 │ idleQueue 非空？          │──Yes──► 取出连接 → 健康检查 → 返回
 └───────────┬─────────────┘
             │ No
             ▼
 ┌─────────────────────────┐
 │ 总数 < maxConnections？  │──Yes──► 创建新连接 → 返回
 └───────────┬─────────────┘
             │ No
             ▼
 ┌─────────────────────────┐
 │ await() 等待（阻塞）      │ ← 等待 release() 或 shutdown() 唤醒
 └───────────┬─────────────┘
             ▼
        重新检查条件 (while 循环)
```

### 4. 健康检查机制

```java
private T borrowInternal() {
    while (!idleQueue.isEmpty()) {
        T conn = idleQueue.pollFirst();
        if (isConnectionValid(conn)) {
            activeSet.add(conn);
            return conn;
        }
        // 连接无效，销毁并继续取下一个
        closeConnection(conn);
    }
    return null; // 无可用空闲连接
}
```

关键考量：
- 健康检查可以是一个 `Predicate<T>`，由调用方注入（如 `Connection::isValid`）。
- 健康检查可能开销较大（如 `SELECT 1`），可设置检查间隔避免每次 borrow 都检查。

### 5. 空闲超时淘汰

使用一个后台线程定期扫描空闲队列，关闭超过 `maxIdleTimeMs` 的连接：

```
cleanupIdleTask() {
    获取 lock
    遍历 idleQueue：
        if (conn.borrowTime + maxIdleTimeMs < now)：
            从队列中移除
            关闭连接
}
```

### 6. 优雅关闭

```
shutdown() 流程：
1. shutdown = true
2. notEmpty.signalAll() → 唤醒所有 borrow 等待者
3. 遍历 idleQueue → 关闭所有空闲连接
4. 不主动关闭 activeSet 中的连接 → 让调用方归还后自行关闭
```

### 7. 复杂度分析

- **时间复杂度**：`borrow` / `release` 均为 O(1)。
- **空间复杂度**：O(N)，N 为最大连接数。

## 考察维度

- **资源管理**：连接生命周期、健康检查、空闲回收、优雅关闭。
- **并发控制**：精确的 wait/notify 机制、线程安全的双集合管理。
- **生产工程实践**：工厂模式（依赖注入）、可配置参数、监控点（活跃/空闲计数）。
- **代码质量**：泛型设计、清晰的 Javadoc、接口抽象。
