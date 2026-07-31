# 题目：并发同步：互斥锁、信号量、条件变量、CAS

## 问题
请阐述并发编程中的四种核心同步机制：互斥锁（Mutex）、信号量（Semaphore）、条件变量（Condition Variable）和 CAS（Compare-And-Swap）。分析它们的原理、适用场景和相互对比。

## 考点
- 互斥锁的原理与实现（自旋锁 vs 阻塞锁）
- 信号量的 P/V 操作与计数信号量
- 条件变量的"等待-唤醒"机制与虚假唤醒
- CAS 的无锁原理与 ABA 问题
- 各种机制在经典同步问题中的应用

## 解答

### 一、互斥锁（Mutex）

**定义**：确保同一时刻只有一个线程可以访问临界区（Critical Section）。

**原理**：
- `lock()`：尝试获取锁；若已被占用，线程阻塞（或自旋）
- `unlock()`：释放锁，唤醒一个等待的线程

**两种实现风格**：

| 类型 | 自旋锁（Spinlock） | 阻塞锁（Blocking Mutex） |
|------|-------------------|-------------------------|
| 等待方式 | 忙等待（while 循环反复检查） | 让出 CPU，被操作系统挂起 |
| 开销 | 浪费 CPU 周期 | 有上下文切换开销 |
| 适用场景 | 临界区极短（几行代码） | 临界区较长（I/O 操作） |
| 实现 | `std::atomic_flag` 或 `TAS` 指令 | 依赖操作系统提供的 futex |

```java
// Java synchronized 是互斥锁
private final Object lock = new Object();
private int count = 0;

public void increment() {
    synchronized (lock) {  // 获取锁
        count++;
    }  // 释放锁（自动）
}

// Java ReentrantLock
import java.util.concurrent.locks.ReentrantLock;

private final ReentrantLock lock = new ReentrantLock();

public void increment() {
    lock.lock();
    try {
        count++;
    } finally {
        lock.unlock();
    }
}
```

```typescript
// JS 单线程，但在 Node.js 中使用 Mutex 控制异步并发
// 简单互斥锁实现
class Mutex {
    private locked = false;
    private waiting: (() => void)[] = [];

    async acquire(): Promise<void> {
        if (!this.locked) {
            this.locked = true;
            return;
        }
        return new Promise(resolve => {
            this.waiting.push(() => {
                this.locked = true;
                resolve();
            });
        });
    }

    release(): void {
        if (this.waiting.length > 0) {
            const next = this.waiting.shift()!;
            next();
        } else {
            this.locked = false;
        }
    }
}
```

---

### 二、信号量（Semaphore）

**定义**：一个整数计数器，通过 P（减）和 V（加）操作控制对资源的并发访问数量。

**P 操作（Proberen，尝试减少）**：
```
P(S):
    while (S <= 0) ;  // 等待（或阻塞）
    S--;
```

**V 操作（Verhogen，增加）**：
```
V(S):
    S++;
    // 如果有等待的线程，唤醒一个
```

**两种类型**：
| 类型 | 初始值 | 效果 | 用途 |
|------|--------|------|------|
| 二进制信号量 | 1 | 等同于互斥锁 | 互斥访问 |
| 计数信号量 | N (N>1) | 允许 N 个线程同时访问 | 资源池、限流 |

**信号量 vs 互斥锁**：
| 维度 | 互斥锁 | 信号量 |
|------|--------|--------|
| 所有者 | 有所有者概念（谁加锁谁解锁） | 无所有者（V 操作可由其他线程执行） |
| 释放方式 | 只能由持有者释放 | 任何线程都可以 V 操作 |
| 用途 | 互斥 | 互斥、同步顺序、资源计数 |

```java
// Java Semaphore
import java.util.concurrent.Semaphore;

Semaphore semaphore = new Semaphore(3); // 允许 3 个线程并发

semaphore.acquire();  // P 操作，计数 -1
try {
    // 访问资源
} finally {
    semaphore.release(); // V 操作，计数 +1
}
```

```typescript
// TypeScript 信号量（控制并发数）
class Semaphore {
    private counter: number;
    private waiting: (() => void)[] = [];

    constructor(count: number) { this.counter = count; }

    async acquire(): Promise<void> {
        if (this.counter > 0) {
            this.counter--;
            return;
        }
        return new Promise(resolve => {
            this.waiting.push(() => {
                this.counter--;
                resolve();
            });
        });
    }

    release(): void {
        if (this.waiting.length > 0) {
            this.waiting.shift()!();
        } else {
            this.counter++;
        }
    }
}

// 使用：限制同时 3 个并发请求
const limiter = new Semaphore(3);
async function limitedFetch(url: string) {
    await limiter.acquire();
    try {
        return await fetch(url);
    } finally {
        limiter.release();
    }
}
```

---

### 三、条件变量（Condition Variable）

**定义**：允许线程在某个条件不满足时等待（阻塞），直到另一个线程通知条件已满足。

**三个关键操作**：
- `wait()`：释放互斥锁并进入等待状态；被唤醒后重新获取锁
- `signal()` / `notify()`：唤醒一个等待的线程
- `broadcast()` / `notifyAll()`：唤醒所有等待的线程

**核心模式**：
```
线程 A（消费者）：
    lock.acquire()
    while (条件不满足) {
        condition.wait()   // 释放锁，等待唤醒
    }
    // 执行操作
    lock.release()

线程 B（生产者）：
    lock.acquire()
    // 改变条件（如添加元素）
    condition.signal()    // 唤醒等待者
    lock.release()
```

**为什么用 `while` 而不是 `if`**：
- **虚假唤醒（Spurious Wakeup）**：线程可能在没有收到 `signal` 的情况下被唤醒
- 用 `while` 循环在被唤醒后重新检查条件，确保条件确实满足

```java
// Java 生产者-消费者
import java.util.LinkedList;
import java.util.Queue;
import java.util.concurrent.locks.*;

class BoundedQueue<T> {
    private final Queue<T> queue = new LinkedList<>();
    private final int capacity;
    private final Lock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();

    public BoundedQueue(int capacity) { this.capacity = capacity; }

    public void put(T item) throws InterruptedException {
        lock.lock();
        try {
            while (queue.size() == capacity) {
                notFull.await();  // 队列满，等待
            }
            queue.add(item);
            notEmpty.signal();   // 唤醒消费者
        } finally {
            lock.unlock();
        }
    }

    public T take() throws InterruptedException {
        lock.lock();
        try {
            while (queue.isEmpty()) {
                notEmpty.await(); // 队列空，等待
            }
            T item = queue.poll();
            notFull.signal();    // 唤醒生产者
            return item;
        } finally {
            lock.unlock();
        }
    }
}
```

```typescript
// TypeScript 简化版条件变量（基于 Promise）
class AsyncCondition {
    private resolvers: (() => void)[] = [];

    async wait(): Promise<void> {
        return new Promise(resolve => this.resolvers.push(resolve));
    }

    signal(): void {
        const resolve = this.resolvers.shift();
        if (resolve) resolve();
    }

    signalAll(): void {
        while (this.resolvers.length > 0) {
            this.resolvers.shift()!();
        }
    }
}
```

---

### 四、CAS（Compare-And-Swap）

**定义**：比较并交换，一种无锁（Lock-Free）的原子操作。由 CPU 指令（如 x86 的 `CMPXCHG`）直接支持。

**伪代码**：
```c
bool CAS(int *addr, int expected, int newValue) {
    if (*addr == expected) {
        *addr = newValue;
        return true;   // 交换成功
    }
    return false;      // 交换失败
}
```

**关键特性**：整个比较+替换操作是**原子的**（单条 CPU 指令），不会被中断。

**Java 中的 CAS**：
通过 `sun.misc.Unsafe` 类的 `compareAndSwapInt/Object` 方法，或 `java.util.concurrent.atomic` 包。

```java
// Java Atomic 类基于 CAS
import java.util.concurrent.atomic.AtomicInteger;

AtomicInteger counter = new AtomicInteger(0);

// incrementAndGet 内部使用 CAS 循环
counter.incrementAndGet();  // 等价于：
//     do { old = counter.get();
//          new = old + 1;
//     } while (!counter.compareAndSet(old, new));
```

```java
// 手动实现无锁栈（基于 CAS）
import java.util.concurrent.atomic.AtomicReference;

class LockFreeStack<T> {
    static class Node<T> {
        T value;
        Node<T> next;
        Node(T v) { value = v; }
    }

    private AtomicReference<Node<T>> top = new AtomicReference<>(null);

    public void push(T value) {
        Node<T> newNode = new Node<>(value);
        Node<T> oldTop;
        do {
            oldTop = top.get();
            newNode.next = oldTop;
        } while (!top.compareAndSet(oldTop, newNode));
    }

    public T pop() {
        Node<T> oldTop;
        Node<T> newTop;
        do {
            oldTop = top.get();
            if (oldTop == null) return null;
            newTop = oldTop.next;
        } while (!top.compareAndSet(oldTop, newTop));
        return oldTop.value;
    }
}
```

```typescript
// TypeScript 的 Atomics
const buffer = new Int32Array(new SharedArrayBuffer(4));

// 原子操作
Atomics.add(buffer, 0, 1);       // 原子加
Atomics.compareExchange(buffer, 0, expected, newValue); // CAS
```

**ABA 问题**：
1. 线程 A 读取值 X
2. 线程 B 将值从 X 改为 Y，又改回 X
3. 线程 A 执行 CAS，发现值还是 X，认为没有变过（实际已经变了）

**解决方案**：使用版本号（`AtomicStampedReference`）或标记位。

```java
// Java 解决 ABA：AtomicStampedReference
import java.util.concurrent.atomic.AtomicStampedReference;

AtomicStampedReference<Integer> ref = new AtomicStampedReference<>(0, 0);
int[] stamp = new int[1];
Integer oldValue = ref.get(stamp); // 获取值和版本号
ref.compareAndSet(oldValue, 100, stamp[0], stamp[0] + 1); // CAS + 版本号
```

---

### 五、四种机制对比

| 维度 | 互斥锁 | 信号量 | 条件变量 | CAS |
|------|--------|--------|---------|-----|
| 核心用途 | 互斥（串行化） | 资源计数 + 互斥 | 等待特定条件 | 无锁原子操作 |
| 阻塞与否 | 阻塞 | 阻塞（counter=0 时） | 阻塞（条件不满足时） | 非阻塞（忙等待重试） |
| 开销 | 上下文切换 | 上下文切换 | 上下文切换 | 自旋重试开销 |
| 适用并发度 | 低冲突 | 中冲突 | 生产者-消费者 | 高冲突 |
| 复杂度 | 低 | 中 | 中 | 高（需处理 ABA） |
| 典型应用 | 临界区保护 | 连接池限流 | 阻塞队列 | 原子计数器 |

### 六、经典问题应用

**哲学家就餐问题**的多种解决方式：
- 互斥锁 + 条件变量：破坏循环等待条件
- 信号量：限制同时就餐人数 ≤4
- CAS：无锁实现筷子获取

## 总结
互斥锁解决"互斥"，信号量解决"计数+互斥"，条件变量解决"等待条件满足"，CAS 解决"无锁原子操作"。选择时考虑冲突程度：低冲突用锁 + 条件变量，高冲突/简单操作用 CAS，资源访问数量控制用信号量。
