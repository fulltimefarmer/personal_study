# 题目 10：延时任务调度器

## 题目描述

实现一个**延时任务调度器**，支持在指定延迟后执行任务，类似简化版的 `ScheduledExecutorService`。

要求实现：

- `ScheduledTask schedule(Runnable task, long delayMillis)` —— 安排一个任务在 `delayMillis` 毫秒后执行，返回 `ScheduledTask` 对象。
- `void cancel(ScheduledTask task)` —— 取消一个已安排但尚未执行的任务。
- 调度器应使用**单一线程**或**少量线程**来执行所有延时任务，而不是为每个任务创建新线程。
- 支持**重复任务**（可选）：以固定间隔重复执行的任务。
- 支持**优雅关闭**：关闭时等待已在执行中的任务完成，取消所有未执行的任务。

## 示例

```java
TaskScheduler scheduler = new TaskScheduler();
scheduler.start();

ScheduledTask task = scheduler.schedule(() -> {
    System.out.println("3 秒后执行");
}, 3_000);

// 不等了，取消
scheduler.cancel(task);

scheduler.shutdown();
```

## 解题思路

### 1. 核心数据结构：优先级阻塞队列

```
                     ┌──────────────────────────┐
                     │  PriorityBlockingQueue    │
                     │  按执行时间排序           │
                     │                          │
                     │  ┌─────────────────────┐ │
                     │  │ Task(id=3, at=T+8s) │ │
                     │  │ Task(id=1, at=T+5s) │ │ ← 最早执行的在前
                     │  │ Task(id=2, at=T+3s) │ │
                     │  └─────────────────────┘ │
                     └────────────┬─────────────┘
                                  │
                   ┌──────────────▼──────────────┐
                   │      Worker Thread          │
                   │                              │
                   │  while (running) {           │
                   │    task = queue.poll(delay); │ ← 阻塞等待最早任务
                   │    if (task != null) {       │
                   │      task.execute();         │
                   │    }                         │
                   │  }                           │
                   └──────────────────────────────┘
```

### 2. 为什么使用 PriorityBlockingQueue？

| 方案 | 优点 | 缺点 |
|------|------|------|
| `ScheduledThreadPoolExecutor` | 开箱即用 | 面试题不能直接用 |
| `PriorityBlockingQueue` | 自动排序、线程安全、可阻塞 | 需要自定义任务包装 |
| `DelayQueue` | 天然支持延时 | 任务只支持一次执行，重复任务需重新入队 |
| 列表 + 轮询 + sleep | 简单 | 精度低，CPU 浪费 |

本实现基于 `PriorityBlockingQueue`，按执行时间戳排序。

### 3. 任务包装

```java
class ScheduledTask implements Comparable<ScheduledTask>, Delayed {
    private final long id;
    private final Runnable runnable;
    private final long executeAtMillis;   // 绝对执行时间
    private volatile boolean cancelled;
    private final boolean repeat;
    private final long periodMillis;      // 重复间隔（> 0 表示重复任务）

    @Override
    public int compareTo(ScheduledTask other) {
        return Long.compare(this.executeAtMillis, other.executeAtMillis);
    }
}
```

### 4. Worker 线程核心循环

```java
void run() {
    while (running) {
        try {
            ScheduledTask task = taskQueue.poll(timeout, TimeUnit.MILLISECONDS);
            if (task == null) continue; // timeout, recheck running

            long delay = task.executeAtMillis - System.currentTimeMillis();
            if (delay > 0) {
                taskQueue.offer(task); // not ready yet, put back
                Thread.sleep(min(delay, 100)); // sleep a bit
                continue;
            }

            if (task.cancelled) continue;

            task.runnable.run();

            if (task.repeat && !task.cancelled) {
                task.executeAtMillis = System.currentTimeMillis() + task.periodMillis;
                taskQueue.offer(task);
            }
        } catch (InterruptedException e) {
            if (!running) break;
        } catch (Exception e) {
            // 记录异常，不中断 worker
        }
    }
}
```

**设计考量**：
- 使用 `poll(timeout)` 而非 `take()`，避免在 shutdown 时永久阻塞。
- 到达但未到期（时间回拨情况）的任务重新入队。
- 异常隔离：单个任务异常不影响调度器运行。

### 5. 另一种实现思路：基于 Thread.sleep 的简单版本

对于面试场景，也可以使用更简单但实用的方式：

```java
class Worker extends Thread {
    public void run() {
        while (running) {
            ScheduledTask task = taskQueue.poll();
            if (task == null) {
                Thread.sleep(100);
                continue;
            }
            long waitMs = task.executeAtMillis - System.currentTimeMillis();
            if (waitMs > 0) {
                taskQueue.offer(task);
                Thread.sleep(Math.min(waitMs, 100));
            } else if (!task.cancelled) {
                task.runnable.run();
            }
        }
    }
}
```

### 6. 优雅关闭

```java
public void shutdown() {
    running = false;
    worker.interrupt();
    worker.join(timeout);
    taskQueue.clear(); // 取消所有未执行任务
}
```

关键：先设置 `running=false`，再 interrupt worker 线程，使其从阻塞中醒来并检查标志。

### 7. 复杂度分析

- **schedule**：O(log N)，N 为队列中待执行任务数（PriorityQueue 插入）。
- **cancel**：O(1)，仅设置标志位（不在队列中搜索）。
- **execute**：O(log N)（从队列中取出）。
- **空间复杂度**：O(N)。

## 考察维度

- **并发编程**：生产者-消费者模式、线程间通信、中断处理。
- **数据结构选择**：优先级队列的应用、比较器设计。
- **生产工程实践**：异常隔离、优雅关闭、线程生命周期管理。
- **技术深度**：延时调度的实现原理、精度与吞吐量的权衡。
