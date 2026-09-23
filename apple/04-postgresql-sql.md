# PostgreSQL / SQL 深度问答 · Deep Q&A

> 说明：每题含中文题干、英文题干、中文答案、英文答案。
> Note: Each question has Chinese prompt, English prompt, Chinese answer, English answer.

---

## PG-1. PostgreSQL 的索引类型有哪些？各自适用场景？什么是覆盖索引？
**EN:** PostgreSQL index types and their use cases? What is a covering index?

**中文答案：**
- **B-tree**（默认）：等值、范围、排序、`LIKE '前缀%'`——绝大多数场景。
- **Hash**：仅等值，通常不如 B-tree 通用。
- **GIN**：一值对多 key，数组(`@>`)、JSONB、全文搜索。
- **GiST**：通用框架，全文、几何、范围类型。
- **BRIN**：大表且物理顺序与键相关，占用极小。
- **覆盖索引**：`INCLUDE (col)` 把额外列存进索引，查询走 index-only scan 免回表，例如 `CREATE INDEX idx ON orders(user_id) INCLUDE (total)`。

**English answer:**
- **B-tree** (default): equality, range, ordering, `LIKE 'prefix%'` — most cases.
- **Hash**: equality only; usually less versatile.
- **GIN**: one value → many keys: arrays (`@>`), JSONB, full-text.
- **GiST**: general framework for full-text, geometric, range types.
- **BRIN**: very large tables where physical order correlates with the key; tiny.
- **Covering index**: `INCLUDE (col)` stores extra columns so queries use an index-only scan without a heap fetch — e.g. `CREATE INDEX idx ON orders(user_id) INCLUDE (total)`.

---

## PG-2. 事务隔离级别有哪些？各解决什么问题？什么是 MVCC？
**EN:** Transaction isolation levels? What does each solve? What is MVCC?

**中文答案：**
隔离级别（低→高）：**Read Uncommitted**（PG 视同 Read Committed）、**Read Committed**（默认，避免脏读）、**Repeatable Read**（同一事务重复读一致，避免不可重复读，PG 还避免幻读）、**Serializable**（完全串行，防幻读/写偏斜，用 SSI 检测冲突）。
- 三类问题：脏读、不可重复读、幻读。
- **MVCC（多版本并发控制）**：每次写生成新版本，读者读事务开始时的快照，读写互不阻塞；旧版本由 VACUUM 回收。PG 并发模型的核心。

**English answer:**
Isolation levels (low→high): **Read Uncommitted** (treated as Read Committed in PG), **Read Committed** (default; avoids dirty reads), **Repeatable Read** (consistent repeated reads; avoids non-repeatable reads, and in PG also phantom reads), **Serializable** (fully serial; avoids phantoms/write skew via SSI).
- Three anomalies: dirty reads, non-repeatable reads, phantom reads.
- **MVCC (Multi-Version Concurrency Control)**: each write creates a new version; readers see a snapshot from transaction start, so readers and writers don't block each other; old versions are reclaimed by VACUUM. The core of PG's concurrency model.

---

## PG-3. 如何优化一条慢查询？`EXPLAIN`/`EXPLAIN ANALYZE` 怎么看？
**EN:** How to optimize a slow query? How to read `EXPLAIN`/`EXPLAIN ANALYZE`?

**中文答案：**
步骤：① `EXPLAIN ANALYZE` 看真实计划与耗时分布；② 关注 `Seq Scan`（全表扫描）、`Sort`、`Hash Join` 成本、**估算行数 vs 实际行数**偏差（偏差大说明统计信息过期，可 `ANALYZE`）；③ 加合适索引（等值/范围/排序/覆盖）；④ 重写查询（避免 `SELECT *`、函数包住索引列导致无法走索引、隐式类型转换、`OR` 改 `UNION`）；⑤ 表设计（分区、规范化/反规范化）；⑥ 调 `work_mem`、`random_page_cost` 等；⑦ 缓存热点数据。
`EXPLAIN ANALYZE` 实际执行并给出每步真实耗时与行数，用于对比估算 vs 实际。

**English answer:**
Steps: ① `EXPLAIN ANALYZE` for the real plan and time distribution; ② watch `Seq Scan`, `Sort`, `Hash Join` cost, and the **estimated vs actual rows** gap (a big gap means stale stats — run `ANALYZE`); ③ add appropriate indexes (equality/range/order/covering); ④ rewrite the query (avoid `SELECT *`, functions wrapping indexed columns, implicit casts, `OR`→`UNION`); ⑤ table design (partitioning, normalize/denormalize); ⑥ tune `work_mem`, `random_page_cost`; ⑦ cache hot data.
`EXPLAIN ANALYZE` actually executes and reports real per-step timing and row counts — compare estimated vs actual.

---

## PG-4. 各 JOIN 的区别，以及电商「订单 vs 客户」的典型用法。
**EN:** JOIN differences, and typical e-commerce "orders vs customers" usage.

**中文答案：**
- `INNER JOIN`：只返回匹配行。
- `LEFT JOIN`：保留左表全部行，右表无匹配填 `NULL`。
- `RIGHT JOIN`：保留右表全部行。
- `FULL OUTER JOIN`：保留两表全部行。
- `CROSS JOIN`：笛卡尔积。
电商例子：`orders LEFT JOIN customers` 保留「无客户信息」的订单（如匿名/历史订单）；`orders INNER JOIN customers` 只统计有客户档案的订单。

```sql
SELECT o.id, c.name
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id;  -- 保留无客户信息的订单
```

**English answer:**
- `INNER JOIN`: only matching rows.
- `LEFT JOIN`: all left rows; `NULL` where right has no match.
- `RIGHT JOIN`: all right rows.
- `FULL OUTER JOIN`: all rows from both.
- `CROSS JOIN`: Cartesian product.
E-commerce: `orders LEFT JOIN customers` keeps orders without customer info (anonymous/legacy); `orders INNER JOIN customers` counts only orders with a customer profile.

```sql
SELECT o.id, c.name
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id;  -- keeps orders with no customer info
```

---

## PG-5. 连接池是什么？在 Node/NestJS 里如何配置？Prisma 为什么要配 pgbouncer？
**EN:** What is a connection pool? Config in Node/NestJS? Why pgbouncer with Prisma?

**中文答案：**
连接池复用已建立的 DB 连接，避免每请求都做 TCP 握手 + 认证。配置 `min`/`max`、空闲超时、获取超时。池太小会排队，太大浪费资源甚至耗尽 PG 连接上限。
- TypeORM：`TypeOrmModule.forRoot({ ..., pool: { max: 10, min: 2 } })`。
- Prisma：默认连接池较小；serverless/多实例场景连接数会超 PG 上限，故生产常配 **pgbouncer**（连接复用代理，`connection_limit`），把「应用连接」池化为少数「数据库连接」。

**English answer:**
A connection pool reuses established DB connections, avoiding a TCP handshake + auth per request. Configure `min`/`max`, idle timeout, acquire timeout. Too small → queueing; too large → wasted resources or exhausting PG's connection limit.
- TypeORM: `TypeOrmModule.forRoot({ ..., pool: { max: 10, min: 2 } })`.
- Prisma: has a smaller default pool; in serverless/multi-instance scenarios connection counts exceed PG's limit, so production pairs it with **pgbouncer** (a connection-multiplexing proxy, `connection_limit`) that pools many app connections into few DB connections.

---

## PG-6. 索引为何加速查询，为何不能给每列都建索引？
**EN:** Why do indexes speed up queries, and why not index every column?

**中文答案：**
索引是有序结构（B-tree），让 DB 用 O(log n) 定位行而非 O(n) 全表扫描。不能每列都建：① 写操作需同步维护索引，拖慢 INSERT/UPDATE/DELETE；② 占用磁盘与内存缓存；③ 优化器选择变多可能选错计划；④ 低区分度列（如性别、状态）收益低。应基于**查询模式**（where/join/order by）与读写比选择性建索引。

**English answer:**
An index is an ordered structure (B-tree) letting the DB find rows in O(log n) instead of an O(n) scan. Don't index every column: ① writes must maintain indexes, slowing INSERT/UPDATE/DELETE; ② disk and memory (cache) overhead; ③ more optimizer choices can lead to bad plans; ④ low-cardinality columns (gender, status) yield little benefit. Build indexes based on **query patterns** (where/join/order-by) and read/write ratio.

---

## PG-7. 规范化(normalization) vs 反规范化(denormalization)，电商如何权衡？
**EN:** Normalization vs denormalization — trade-offs in e-commerce?

**中文答案：**
- **规范化**：消除冗余、保证一致性（避免更新异常），如把「订单」与「客户」拆表；写友好。
- **反规范化**：有意冗余、牺牲一致性换读取性能，如订单表里冗余存 `customer_name`/`product_snapshot`（下单时的快照，避免 JOIN 与历史价格追溯问题）。
- 电商实践：订单/支付偏规范化保证一致；**订单明细存商品快照**（价格、名称）反规范化——因为历史订单必须记录「下单那一刻」的价格，不能随商品表更新而变。

**English answer:**
- **Normalization**: removes redundancy, guarantees consistency (no update anomalies), e.g. split orders/customers; write-friendly.
- **Denormalization**: intentional redundancy, trading consistency for read performance, e.g. storing `customer_name`/`product_snapshot` on the order row.
- E-commerce practice: orders/payments stay normalized for consistency; **order items store a product snapshot** (price, name) denormalized — historical orders must record the price "at purchase time," immune to later product changes.

---

## PG-8. 窗口函数(window functions)是什么？`ROW_NUMBER`/`RANK`/`LAG` 的典型用法。
**EN:** What are window functions? Typical uses of `ROW_NUMBER`/`RANK`/`LAG`.

**中文答案：**
窗口函数在「不折叠行」的情况下，对与当前行相关的一组行做计算（`OVER (PARTITION BY ... ORDER BY ...)`）。与聚合不同，它保留每行并附带计算值。
- `ROW_NUMBER()`：分区内顺序编号（去重保留一条）。
- `RANK()`/`DENSE_RANK()`：排名（有/无并列跳号）。
- `LAG()/LEAD()`：取前/后一行（计算环比增长）。

```sql
SELECT order_id, total,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn
FROM orders;                          -- 每个客户最近的订单排第 1
SELECT month, total,
       LAG(total) OVER (ORDER BY month) AS prev_total
FROM monthly_sales;                   -- 环比
```

**English answer:**
Window functions compute over a set of rows related to the current row without collapsing rows (`OVER (PARTITION BY ... ORDER BY ...)`). Unlike aggregates, they keep each row and attach computed values.
- `ROW_NUMBER()`: sequential numbering within a partition (dedupe keep one).
- `RANK()`/`DENSE_RANK()`: ranking (with/without gaps for ties).
- `LAG()/LEAD()`: previous/next row (period-over-period growth).

```sql
SELECT order_id, total,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn
FROM orders;                          -- each customer's latest order is #1
SELECT month, total,
       LAG(total) OVER (ORDER BY month) AS prev_total
FROM monthly_sales;                   -- month-over-month
```

---

## PG-9. CTE 与子查询的区别？递归 CTE 的用途？
**EN:** CTE vs subquery? Use cases for recursive CTEs?

**中文答案：**
- **CTE**（`WITH`）：命名临时结果集，可读性更好、可复用（同一 CTE 多处引用）、可递归；通常不物化（`MATERIALIZED` 可强制）。**子查询**：内联、一次性。
- **递归 CTE**：处理树/层级数据（组织架构、商品分类、评论回复），`WITH RECURSIVE` + 初始项 + `UNION ALL` 递归项。

```sql
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 1 AS depth
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, t.depth + 1
  FROM categories c
  JOIN category_tree t ON c.parent_id = t.id
)
SELECT * FROM category_tree;          -- 展开整棵分类树
```

**English answer:**
- **CTE** (`WITH`): named temporary result set — more readable, reusable (referenced multiple times), recursive-capable; usually not materialized (`MATERIALIZED` forces it). **Subquery**: inline, one-shot.
- **Recursive CTE**: handles tree/hierarchy data (org charts, product categories, comment replies) via `WITH RECURSIVE` + a base term + `UNION ALL` recursive term.

```sql
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 1 AS depth
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, t.depth + 1
  FROM categories c
  JOIN category_tree t ON c.parent_id = t.id
)
SELECT * FROM category_tree;          -- expand the whole category tree
```

---

## PG-10. 什么是死锁(deadlock)？如何避免？锁的类型有哪些？
**EN:** What is a deadlock? How to avoid it? Lock types?

**中文答案：**
死锁 = 两个事务互相等待对方持有的锁，谁也动不了（PG 会检测并自动回滚其中一个）。避免：**按固定顺序访问资源**（锁顺序一致）、事务尽量短、批量更新排序、合适隔离级别。
- 锁类型：行级锁 `FOR UPDATE`/`FOR SHARE`、表级锁（`ACCESS EXCLUSIVE` 由 DDL 触发）、advisory lock（应用级互斥）。

```sql
-- 固定顺序：先锁客户再锁订单，避免交叉等待
UPDATE customers SET ... WHERE id = 1;
UPDATE orders SET ... WHERE customer_id = 1;
```

**English answer:**
A deadlock is two transactions each waiting for a lock the other holds (PG detects it and auto-aborts one). Avoid by: **accessing resources in a consistent order**, keeping transactions short, sorting batch updates, choosing a suitable isolation level.
- Lock types: row-level `FOR UPDATE`/`FOR SHARE`, table-level (`ACCESS EXCLUSIVE` from DDL), advisory locks (app-level mutex).

```sql
-- consistent order: lock customers then orders, avoiding cross-wait
UPDATE customers SET ... WHERE id = 1;
UPDATE orders SET ... WHERE customer_id = 1;
```

---

## PG-11. VACUUM 与 autovacuum 的作用？为什么 MVCC 需要它？
**EN:** What do VACUUM/autovacuum do? Why does MVCC need them?

**中文答案：**
MVCC 下更新/删除会留下**死元组(dead tuples)**，占用空间并使索引膨胀。**VACUUM** 标记死元组为可复用；`VACUUM FULL` 物理压缩（会锁表）。**autovacuum** 后台自动执行，防止表/索引无限膨胀、并**更新统计信息**（影响执行计划质量）。若关闭，会引发「表膨胀」导致查询变慢、甚至事务 ID 回卷(xid wraparound)问题。监控：`pg_stat_user_tables.n_dead_tup`。

**English answer:**
Under MVCC, updates/deletes leave **dead tuples** that consume space and bloat indexes. **VACUUM** marks dead tuples reusable; `VACUUM FULL` physically compacts (locks the table). **autovacuum** runs in the background automatically, preventing unbounded table/index bloat and **refreshing statistics** (which affect plan quality). Without it you get "table bloat" (slower queries) and eventually transaction-ID wraparound issues. Monitor via `pg_stat_user_tables.n_dead_tup`.

---

## PG-12. PostgreSQL 的 JSONB 与普通 JSON 的区别？何时用 JSONB？
**EN:** JSONB vs JSON in PostgreSQL? When to use JSONB?

**中文答案：**
- `json`：存储原始文本，保留空格/键顺序/重复键，查询需每次解析，慢。
- `jsonb`：二进制格式，去重键、排序键、**可建 GIN 索引**、支持 `@>`/`->`/`->>`/`?` 等运算符，查询快。代价：写入略慢、不保留原始格式。
- 场景：半结构化数据（商品扩展属性、事件 payload、配置），且需要按 JSON 内字段查询/索引时用 `jsonb`。若只是存原样再读出，用 `json`。

```sql
CREATE INDEX ON products USING GIN (attributes jsonb_path_ops);
SELECT * FROM products WHERE attributes @> '{"color": "black"}';
```

**English answer:**
- `json`: stores raw text, preserves whitespace/key order/duplicate keys, re-parses each query, slow.
- `jsonb`: binary format, dedupes & sorts keys, **GIN-indexable**, supports `@>`/`->`/`->>`/`?` operators, fast queries. Cost: slightly slower writes, doesn't preserve original formatting.
- Use `jsonb` for semi-structured data (product extension attributes, event payloads, config) when you need to query/index inside the JSON. Use `json` if you only store-and-retrieve verbatim.

```sql
CREATE INDEX ON products USING GIN (attributes jsonb_path_ops);
SELECT * FROM products WHERE attributes @> '{"color": "black"}';
```

---

## PG-13. 表分区(partitioning)与分片(sharding)的区别？什么时候分区？
**EN:** Partitioning vs sharding? When to partition?

**中文答案：**
- **分区**：单库内把大表按键（范围/列表/哈希）拆成多个物理子表，逻辑上仍是同一张表——提升查询剪枝(partition pruning)、便于归档/删除旧数据、VACUUM 局部化。仍是单机。
- **分片**：把数据分布到**多个数据库/节点**，横向扩容写入与存储，通常应用层或中间件（如 Citus）路由。
- 分区时机：单表上亿行、查询总是带分区键（如按日期/地区）、需定期清理历史数据。

```sql
CREATE TABLE orders_2026 PARTITION OF orders FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

**English answer:**
- **Partitioning**: splits one big table into physical sub-tables by key (range/list/hash) within a single DB, logically still one table — enables partition pruning, easier archiving/deletion, localized VACUUM. Still single-node.
- **Sharding**: distributes data across **multiple databases/nodes** to scale writes & storage horizontally, usually routed at the app layer or via middleware (Citus).
- When to partition: hundreds of millions of rows, queries always filter by the partition key (date/region), frequent purging of historical data.

```sql
CREATE TABLE orders_2026 PARTITION OF orders FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

---

## PG-14. 主从复制(replication)与高可用如何做？流复制是什么？
**EN:** How to do replication and high availability? What is streaming replication?

**中文答案：**
- **流复制(streaming replication)**：主库把 WAL（预写日志）实时流式传给备库，备库重放保持同步——用于读扩展（备库只读）、容灾。同步/异步可选（`synchronous_commit`）。
- **高可用**：主库故障时把备库**提升(failover/promote)** 为新主；配合工具（Patroni + etcd、repmgr、阿里云 RDS 高可用版）自动切换。
- 读扩展注意：备库有复制延迟，需容忍短暂不一致；关键读（如「我的订单」）走主库，非关键读（商品列表）走备库。

**English answer:**
- **Streaming replication**: the primary streams WAL (write-ahead log) to standby(s) in real time, which replay it to stay in sync — used for read scaling (read-only standby) and DR. Sync/async selectable (`synchronous_commit`).
- **High availability**: on primary failure, **promote** a standby to primary (failover); tools (Patroni + etcd, repmgr, Aliyun RDS HA edition) automate it.
- Read scaling caveat: standbys have replication lag; tolerate brief inconsistency — critical reads (e.g. "my orders") hit the primary, non-critical reads (product lists) hit standbys.
