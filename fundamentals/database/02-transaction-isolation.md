# 题目：事务隔离级别与并发问题

## 问题
请详细说明数据库事务的 ACID 特性及四种隔离级别：读未提交（Read Uncommitted）、读已提交（Read Committed）、可重复读（Repeatable Read）、串行化（Serializable），以及它们对应的并发问题：脏读、不可重复读、幻读。结合 MySQL InnoDB 说明默认隔离级别及其实现方式。

## 考点
- ACID 四大特性的含义
- 四种隔离级别的递进
- 脏读/不可重复读/幻读的区别
- MySQL InnoDB 的默认隔离级别
- 实际开发中选择隔离级别的考虑

## 解答

### 一、ACID 四大特性

| 特性 | 说明 | 举例 |
|------|------|------|
| **原子性 (Atomicity)** | 事务是一个不可分割的工作单位，操作要么全部成功要么全部失败 | 转账：A 扣 100 + B 加 100，要么都做要么都不做 |
| **一致性 (Consistency)** | 事务前后数据库都必须处于一致性状态 | 转账前后总金额不变（约束、触发器保护） |
| **隔离性 (Isolation)** | 多个事务并发执行时互不干扰 | 事务 A 看不到事务 B 未提交的中间状态 |
| **持久性 (Durability)** | 事务一旦提交，对数据库的改变是永久的 | 系统崩溃后恢复，已提交的数据不丢失 |

**InnoDB 实现**：
- 原子性：undo log（回滚日志）
- 一致性：undo log + redo log + 约束（业务层面共同保证）
- 隔离性：MVCC + 锁
- 持久性：redo log（重做日志）+ doublewrite buffer

---

### 二、三种并发问题

| 并发问题 | 说明 | 示例 |
|---------|------|------|
| **脏读 (Dirty Read)** | 读到了其他事务未提交的数据 | 事务 B 读到事务 A 未提交的修改；A 回滚了，B 读到的就是脏数据 |
| **不可重复读 (Non-Repeatable Read)** | 同一事务内两次读取同一行数据结果不同 | 事务 A 先读 age=20；事务 B 修改 age=21 并提交；事务 A 再读 age=21 |
| **幻读 (Phantom Read)** | 同一事务内两次范围查询结果的**行数**不同 | 事务 A 查 `age>18` 有 10 行；事务 B 插入一行 age=20 并提交；事务 A 再查有 11 行 |

**区别关键**：
- 脏读 vs 不可重复读：脏读是**未提交**的修改，不可重复读是**已提交**的修改
- 不可重复读 vs 幻读：不可重复读是针对**同一行数据**的修改/删除；幻读是针对**新增的行**（导致范围查询结果变多）

---

### 三、四种隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 实现方式 | 性能 |
|---------|------|----------|------|---------|------|
| **Read Uncommitted** | ✅ 可能 | ✅ 可能 | ✅ 可能 | 无锁读取 | 最高 |
| **Read Committed** | ❌ 解决 | ✅ 可能 | ✅ 可能 | MVCC 快照（每次读生成新 Read View） | 高 |
| **Repeatable Read** | ❌ 解决 | ❌ 解决 | ⚠️ 部分解决 | MVCC 快照（事务开始时生成 Read View）+ 间隙锁 | 中 |
| **Serializable** | ❌ 解决 | ❌ 解决 | ❌ 解决 | 所有 SELECT 隐式转 SELECT ... FOR SHARE | 最低 |

**MySQL InnoDB 默认隔离级别是 Repeatable Read（可重复读）**。

然而 Oracle / PostgreSQL 默认是 Read Committed。

---

### 四、各隔离级别详解

#### Read Uncommitted（读未提交）

直接读取最新数据，不管是否已提交。
```
时间 →
T1: UPDATE age=21 (age 原为 20)  ← 未提交
T2: SELECT age → 读到 21           ← 脏读！
T1: ROLLBACK → age 回到 20
T2: 读到的 21 是脏数据
```

**使用场景**：几乎不推荐，仅在非关键数据、允许误差的统计场景。

#### Read Committed（读已提交）

每次读取都生成一个新的快照，只读已提交版本。

```
时间 →
T1: SELECT age → 20
T2: UPDATE age=21; COMMIT;
T1: SELECT age → 21           ← 不可重复读！同一事务两次读不同
```

**解决了脏读，但存在不可重复读**。

```sql
-- 查看隔离级别
SELECT @@transaction_isolation;

-- 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

#### Repeatable Read（可重复读）

事务开始时生成一个 Read View（快照），整个事务期间所有 SELECT 都基于这个快照。

```
时间 →
T1: START TRANSACTION
T1: SELECT age → 20           ← 建立快照，数据版本为此时
T2: UPDATE age=21; COMMIT;
T1: SELECT age → 20           ← 仍然读快照，不会变
```

**InnoDB 的 Repeatable Read 通过间隙锁（Gap Lock）解决了大部分幻读问题**：
```sql
-- T1
START TRANSACTION;
SELECT * FROM users WHERE age BETWEEN 18 AND 30 FOR UPDATE;
-- InnoDB 会在符合条件的索引间隙加间隙锁，阻止 T2 插入数据

-- T2（被阻塞直到 T1 提交）
INSERT INTO users (name, age) VALUES ('Bob', 25); -- 阻塞！
```

**但并非完全杜绝**：如果 T1 执行的是快照读（不带 `FOR UPDATE`）且在 T2 插入后 T1 做了 UPDATE 操作，仍可能出现幻读现象。

#### Serializable（串行化）

强制所有事务串行执行，完全回避并发问题但性能最低。所有普通 `SELECT` 隐式变为 `SELECT ... FOR SHARE`（读加共享锁）。

---

### 五、MVCC 如何实现隔离（原理概要，详情见 MVCC 专题）

每个数据行有两个隐藏列：
- `DB_TRX_ID`：最后修改该行的事务 ID
- `DB_ROLL_PTR`：指向 undo log 中的旧版本

**Read View** 记录：
- 当前活跃的事务 ID 列表
- 最小活跃事务 ID
- 下一个将要分配的事务 ID

**版本可见性规则**：通过判断行的 `DB_TRX_ID` 是否在 Read View 的可见范围内，决定读当前版本还是通过 `DB_ROLL_PTR` 向上追溯 undo log 中的历史版本。

**RR vs RC 的区别**：
- **Read Committed**：每次 `SELECT` 都生成新的 Read View
- **Repeatable Read**：事务中第一次 `SELECT` 生成 Read View，后续 `SELECT` 复用

---

### 六、实际选择指南

| 场景 | 推荐隔离级别 | 原因 |
|------|------------|------|
| 高并发 Web 应用 | Read Committed | 性能好；应用层通常能容忍不可重复读 |
| 金融/对账 | Repeatable Read (InnoDB 默认) | 需要一致性读 |
| 库存扣减 | Repeatable Read + `FOR UPDATE` | 避免超卖 |
| 报表系统 | Read Uncommitted / Read Committed | 可容忍误差 |
| 严格顺序要求 | Serializable（或应用层保证） | 但通常用乐观锁替代 |

**实际中的最佳实践**：
1. 沿用在用数据库的默认隔离级别，不随意调整
2. 用乐观锁（version 字段）或悲观锁（`SELECT ... FOR UPDATE`）应对特定的并发问题
3. 隔离级别越高性能越低，在应用层通过代码设计减少对最高隔离级别的依赖

---

### 七、扩展知识点

**MySQL InnoDB 为什么默认 RR 而不是 RC？**
- 历史原因：MySQL 5.0 之前，基于 statement 的 binlog 在 RC 下可能产生主备不一致
- RR + 间隙锁可以保证 statement binlog 的一致性
- 现在 row 格式 binlog 下，RC 级别也可以安全使用

**Spring 事务隔离级别映射**：
```java
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void transferMoney() {
    // ...
}
```

| Spring 枚举 | 数据库级别 |
|------------|-----------|
| `DEFAULT` | 使用数据库默认 |
| `READ_UNCOMMITTED` | Read Uncommitted |
| `READ_COMMITTED` | Read Committed |
| `REPEATABLE_READ` | Repeatable Read |
| `SERIALIZABLE` | Serializable |

---

## 总结
隔离级别按从低到高逐渐解决并发问题：Read Uncommitted 最弱（都不解决），Read Committed 解决脏读，Repeatable Read 解决脏读和不可重复读（InnoDB 额外用间隙锁抑制幻读），Serializable 全部解决但性能最低。MVCC 是 InnoDB 实现隔离级别的核心技术，通过 Read View 决定数据的可见性版本。
