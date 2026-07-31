# 题目：死锁

## 问题
请说明死锁（Deadlock）的定义、四个必要条件、预防死锁的方法，以及如何通过银行家算法（Banker's Algorithm）避免死锁。结合 Java 代码示例展示死锁的产生和避免。

## 考点
- 死锁的四个必要条件（Coffman 条件）
- 死锁预防（打破四个条件）vs 死锁避免（银行家算法）
- 死锁检测与恢复
- 实际开发中常见的死锁场景和排查方法

## 解答

### 一、死锁的定义

多个进程/线程因相互等待对方占有的资源而无法继续执行，形成一种"僵持"状态，若无外力干涉，这些进程/线程将永远等待下去。

**生活中的例子**：两个人在吃饭，桌上只有一双筷子（每人一支筷子和一把刀）。每个人都需要一双完整的筷子才能吃饭，谁也不愿放下手中的那一支。结果大家都无法吃饭——这就是死锁。

---

### 二、死锁的四个必要条件（Coffman 条件）

四个条件**必须同时满足**才会发生死锁：

| 编号 | 条件 | 说明 |
|------|------|------|
| 1 | **互斥（Mutual Exclusion）** | 资源一次只能被一个进程/线程使用 |
| 2 | **持有并等待（Hold and Wait）** | 进程持有至少一个资源，同时等待获取其他资源 |
| 3 | **不可剥夺（No Preemption）** | 已获得的资源不能被强行剥夺，只能主动释放 |
| 4 | **循环等待（Circular Wait）** | 存在进程等待链 P1→P2→...→Pn→P1，形成环路 |

**必要条件意味着**：只要打破其中任何一个条件，就可以预防死锁。

---

### 三、死锁预防（Deadlock Prevention）

通过**破坏四个必要条件中的至少一个**来预防：

| 打破条件 | 方法 | 代价 |
|---------|------|------|
| 互斥 | 使用无锁数据结构（如 `AtomicInteger`），或虚拟化资源（SPOOLing） | 并非所有资源都能无锁共享 |
| 持有并等待 | **一次性申请所有资源**（All-or-Nothing） | 资源利用率低，可能饥饿 |
| 不可剥夺 | 允许剥夺（如优先级高的进程可抢占资源） | 大部分资源不便于剥夺 |
| 循环等待 | **按序申请资源**（给资源编号，必须按编号递增申请） | 资源编号可能不自然，难以在复杂系统中实施 |

---

### 四、死锁避免：银行家算法（Banker's Algorithm）

**核心思想**：在分配资源之前，先"试探性"地判断分配后系统是否仍处于安全状态。只有安全时才分配。

**数据结构**：
- `Available[j]`：资源 j 的可用数量
- `Max[i][j]`：进程 i 对资源 j 的最大需求
- `Allocation[i][j]`：进程 i 当前已分配的资源 j
- `Need[i][j]`：进程 i 对资源 j 的剩余需求 = `Max - Allocation`

**安全状态判断**（安全性算法）：
1. 假设 Work = Available，Finish[i] = false
2. 找一个满足 `!Finish[i] && Need[i] <= Work` 的进程 i
3. 如果找到，模拟该进程运行完成：`Work += Allocation[i]`，`Finish[i] = true`
4. 重复步骤 2-3
5. 如果所有进程 Finish 都变为 true，则系统处于安全状态

```java
// 银行家算法简化实现
public class BankersAlgorithm {
    private int[] available;               // 可用资源
    private int[][] max;                   // 最大需求
    private int[][] allocation;            // 已分配
    private int[][] need;                  // 还需
    private int processCount, resourceCount;

    public BankersAlgorithm(int[] available, int[][] max, int[][] allocation) {
        this.available = available.clone();
        this.max = max;
        this.allocation = allocation;
        this.processCount = max.length;
        this.resourceCount = available.length;
        this.need = new int[processCount][resourceCount];
        for (int i = 0; i < processCount; i++)
            for (int j = 0; j < resourceCount; j++)
                need[i][j] = max[i][j] - allocation[i][j];
    }

    // 判断当前状态是否安全
    public boolean isSafe() {
        int[] work = available.clone();
        boolean[] finish = new boolean[processCount];

        for (int count = 0; count < processCount; count++) {
            boolean found = false;
            for (int i = 0; i < processCount; i++) {
                if (!finish[i] && canAllocate(need[i], work)) {
                    // 模拟进程 i 执行完并释放资源
                    for (int j = 0; j < resourceCount; j++)
                        work[j] += allocation[i][j];
                    finish[i] = true;
                    found = true;
                    break;
                }
            }
            if (!found) return false; // 没有找到可完成的进程
        }
        return true;
    }

    // 判断能否分配资源给进程
    public boolean requestResources(int processId, int[] request) {
        for (int i = 0; i < resourceCount; i++) {
            if (request[i] > need[processId][i]) return false;  // 超需求
            if (request[i] > available[i]) return false;         // 资源不足
        }

        // 试探性分配
        for (int i = 0; i < resourceCount; i++) {
            available[i] -= request[i];
            allocation[processId][i] += request[i];
            need[processId][i] -= request[i];
        }

        if (!isSafe()) {
            // 不安全，回滚
            for (int i = 0; i < resourceCount; i++) {
                available[i] += request[i];
                allocation[processId][i] -= request[i];
                need[processId][i] += request[i];
            }
            return false;
        }
        return true;
    }

    private boolean canAllocate(int[] need, int[] work) {
        for (int i = 0; i < resourceCount; i++)
            if (need[i] > work[i]) return false;
        return true;
    }
}
```

---



### 五、Java 死锁示例与排查

```java
// 死锁示例
public class DeadlockDemo {
    private static final Object LOCK_A = new Object();
    private static final Object LOCK_B = new Object();

    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (LOCK_A) {
                System.out.println("Thread-1 获取了 LockA");
                try { Thread.sleep(100); } catch (Exception e) {}
                synchronized (LOCK_B) {  // 等待 LockB
                    System.out.println("Thread-1 获取了 LockB");
                }
            }
        }).start();

        new Thread(() -> {
            synchronized (LOCK_B) {
                System.out.println("Thread-2 获取了 LockB");
                try { Thread.sleep(100); } catch (Exception e) {}
                synchronized (LOCK_A) {  // 等待 LockA
                    System.out.println("Thread-2 获取了 LockA");
                }
            }
        }).start();
    }
}
```

**排查死锁**：

```bash
# 1. 查找 Java 进程 PID
jps -l

# 2. 打印线程堆栈和死锁信息
jstack <PID>
# 输出会包含: "Found one Java-level deadlock:"

# 3. 查看线程状态
jstack -l <PID> | grep -A 5 "deadlock"
```

**避免死锁的最佳实践**：
1. **固定加锁顺序**：所有线程按相同顺序获取锁（如先 A 后 B）
2. **使用超时锁**：`tryLock(timeout)` 代替无限期的 `synchronized`
3. **减少锁的粒度**：用读写锁、分段锁（如 `ConcurrentHashMap`）
4. **避免嵌套锁**：在执行带锁代码时不要再获取其他锁
5. **使用更高级的并发工具**：`java.util.concurrent` 包

```java
// ✅ 避免死锁：按固定顺序加锁
public class SafeTransfer {
    private static final Object tieLock = new Object();

    public void transfer(Object from, Object to, int amount) {
        int fromHash = System.identityHashCode(from);
        int toHash = System.identityHashCode(to);

        if (fromHash < toHash) {
            synchronized (from) {
                synchronized (to) {
                    doTransfer(from, to, amount);
                }
            }
        } else if (fromHash > toHash) {
            synchronized (to) {
                synchronized (from) {
                    doTransfer(from, to, amount);
                }
            }
        } else {
            // 哈希碰撞时使用"加时赛锁"
            synchronized (tieLock) {
                synchronized (from) {
                    synchronized (to) {
                        doTransfer(from, to, amount);
                    }
                }
            }
        }
    }

    private void doTransfer(Object from, Object to, int amount) {
        // 转账逻辑
    }
}
```

### 六、死锁检测与恢复

**检测**：通过资源分配图（Resource Allocation Graph，RAG）检测是否存在环。如果图中无环，则无死锁；如果有环，可能死锁（对于多实例资源）或必定死锁（对于单实例资源）。

**恢复**：
| 方法 | 说明 |
|------|------|
| 终止进程 | 终止所有死锁进程（最简单）或逐个终止直到死锁解除 |
| 资源剥夺 | 从某些进程抢走资源分配给其他进程 |
| 回滚 | 保存检查点（checkpoint），死锁时回滚到安全点 |

## 总结
死锁是并发编程中的经典问题，四个必要条件缺一不可：互斥、持有并等待、不可剥夺、循环等待。预防就是打破其中之一；避免则是用银行家算法做安全状态判断。实际开发中最常用的避免手段是**统一加锁顺序**和**使用超时锁**。
