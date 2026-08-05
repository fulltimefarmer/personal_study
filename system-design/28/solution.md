# 设计分布式锁服务 (Design Distributed Lock Service)

## 题目

设计一个高可用的分布式锁服务，为分布式系统中的资源访问提供互斥保证。深度分析 Redis、ZooKeeper、Etcd 三种实现方案的优劣对比。

## 需求澄清

### 功能性需求

1. **互斥 (Mutual Exclusion)**: 同一时刻只有一个客户端能持有锁
2. **自动释放**: 客户端崩溃/网络断开时锁自动释放(防死锁)
3. **可重入 (Reentrant)**: 同一客户端可以多次获取同一把锁
4. **阻塞与非阻塞**: 支持阻塞等待和非阻塞尝试获取
5. **锁续期 (Lease/Watchdog)**: 长时间操作自动延长锁有效期
6. **公平锁 (Fair Lock)**: 按请求顺序获取锁(可选)
7. **读写锁**: 支持共享读锁和排他写锁

### 非功能性需求

- **高可用**: 99.99%，锁服务自身不能成为故障源
- **低延迟**: 获取锁 < 5ms (同机房)
- **防脑裂 (Split-Brain Prevention)**: 网络分区时确保只有一个持有者
- **可观测**: 提供锁持有者、等待队列、锁持有时间等监控

### 容量估算

```
假设:
- 服务数量: 10,000 个微服务实例
- 每秒锁操作: 50,000 次 (获取 + 释放)
- 平均锁持有时间: 100ms
- 并发持有的锁: 50,000 × 0.1s ≈ 5,000 个

存储估算:
- Redis方式: 每把锁 ~200 bytes → 5,000 × 200 ≈ 1 MB
- ZooKeeper方式: 每把锁 ~1KB → 5,000 × 1KB ≈ 5 MB
- 内存占用极小, 主要瓶颈是网络/CPU
```

## API设计

```java
// ============ 分布式锁核心接口 ============

public interface DistributedLock {
    
    /**
     * 尝试获取锁, 非阻塞, 立即返回
     * @return true: 获取成功, false: 锁被他人持有
     */
    boolean tryLock();
    
    /**
     * 尝试获取锁, 超时等待
     * @param timeout 最大等待时间
     * @param unit 时间单位
     * @return true: 获取成功, false: 超时
     */
    boolean tryLock(long timeout, TimeUnit unit) throws InterruptedException;
    
    /**
     * 阻塞获取锁, 直到成功
     */
    void lock() throws InterruptedException;
    
    /**
     * 释放锁
     */
    void unlock();
    
    /**
     * 检查锁是否被当前线程持有 (可重入锁)
     */
    boolean isHeldByCurrentThread();
    
    /**
     * 检查锁是否被任意客户端持有
     */
    boolean isLocked();
    
    /**
     * 获取锁的剩余有效时间 (毫秒)
     */
    long getRemainingLeaseTimeMs();
}

// ============ 工厂接口 ============
public interface DistributedLockFactory {
    
    /**
     * 获取/创建一个命名锁
     * @param lockKey 全局唯一的锁名称
     * @return 分布式锁实例
     */
    DistributedLock getLock(String lockKey);
    
    /**
     * 获取读写锁
     */
    ReadWriteDistributedLock getReadWriteLock(String lockKey);
}

public interface ReadWriteDistributedLock {
    DistributedLock readLock();
    DistributedLock writeLock();
}
```

### 详细 API (服务端/管理接口)

```protobuf
// gRPC 锁服务 API
service DistributedLockService {
    // 获取锁
    rpc Acquire(AcquireRequest) returns (AcquireResponse);
    // 续期锁
    rpc Renew(RenewRequest) returns (RenewResponse);
    // 释放锁
    rpc Release(ReleaseRequest) returns (ReleaseResponse);
    // 获取锁信息
    rpc GetLockInfo(LockInfoRequest) returns (LockInfoResponse);
}

message AcquireRequest {
    string lock_key = 1;
    string client_id = 2;               // 全局唯一的客户端ID
    int64 lease_time_ms = 3;            // 锁持有时长, 0=永久(手动释放)
    int64 wait_timeout_ms = 4;          // 等待超时, 0=不等待
    bool reentrant = 5;                 // 是否可重入
    int32 reentrant_count = 6;          // 重入计数(重入时递增)
}

message AcquireResponse {
    bool success = 1;
    string lock_token = 2;              // 持有锁的凭证, 用于续期/释放
    int64 lease_time_ms = 3;
    int64 acquired_at_ms = 4;
}

message RenewRequest {
    string lock_key = 1;
    string lock_token = 2;
    int64 extend_time_ms = 3;           // 延长时长
}

message ReleaseRequest {
    string lock_key = 1;
    string lock_token = 2;
}
```

## 数据模型

### Redis 实现 (最常用)

```redis
# 单锁实现 (简单但不够健壮)
# 获取锁
SET lock:order:12345 client_001 NX PX 30000
# NX: Not eXists (只在不存在时设置)
# PX 30000: 30秒自动过期

# 释放锁 (需要 Lua 脚本保证原子性)
# 检查 value 是否匹配 (防止释放他人的锁)
EVAL "
  if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
  else
    return 0
  end
" 1 lock:order:12345 client_001

# 可重入锁 (使用 Hash 存储重入计数)
# 获取锁
EVAL "
  if redis.call('EXISTS', KEYS[1]) == 0 then
    redis.call('HINCRBY', KEYS[1], ARGV[1], 1)
    redis.call('PEXPIRE', KEYS[1], ARGV[2])
    return 1
  elseif redis.call('HEXISTS', KEYS[1], ARGV[1]) == 1 then
    redis.call('HINCRBY', KEYS[1], ARGV[1], 1)
    redis.call('PEXPIRE', KEYS[1], ARGV[2])
    return 1
  else
    return 0
  end
" 1 lock:order:12345 client_001 30000

# 释放可重入锁
EVAL "
  if redis.call('HEXISTS', KEYS[1], ARGV[1]) == 0 then
    return 0
  end
  local count = redis.call('HINCRBY', KEYS[1], ARGV[1], -1)
  if count > 0 then
    redis.call('PEXPIRE', KEYS[1], ARGV[2])
    return 1
  else
    redis.call('DEL', KEYS[1])
    return 1
  end
" 1 lock:order:12345 client_001 30000

# Redlock 算法 (多Redis实例)
# 同时对 N 个独立 Redis 实例获取锁
# 在 (N/2 + 1) 个实例获取成功 → 认为获取锁成功
# 获取锁的总耗时 < 锁有效期的 50%
```

### ZooKeeper/Etcd 实现

```
ZooKeeper 锁实现原理 (临时顺序节点):

┌────────────────────────────────────────────────────────────┐
│                  ZooKeeper 锁结构                            │
│                                                            │
│  /locks/order_12345/                                       │
│  ├── _c_0000000001  (client_A, ephemeral_sequential)       │
│  ├── _c_0000000002  (client_B, ephemeral_sequential)       │
│  ├── _c_0000000003  (client_C, ephemeral_sequential)       │
│  └── _c_0000000004  (client_D, ephemeral_sequential)       │
│                                                            │
│  锁获取流程:                                                │
│  1. 在/locks/order_12345/下创建临时顺序节点                  │
│  2. 获取所有子节点, 排序                                    │
│  3. 如果自己的序号最小 → 获取锁成功                          │
│  4. 否则 → 监听前一个节点的删除事件                          │
│  5. 前一个节点删除 → 重新检查 → 自己变最小 → 获取锁          │
│                                                            │
│  释放:                                                      │
│  删除自己的临时节点 → 触发下一个节点的Watch                  │
│                                                            │
│  故障处理:                                                  │
│  客户端崩溃 → Session断开 → 临时节点自动删除                │
│  → 锁自动释放 (防死锁)                                     │
│                                                            │
│  优点:                                                      │
│  - 公平锁保证 (按创建顺序)                                   │
│  - 自动释放 (Ephemeral节点)                                 │
│  - 强一致性 (ZAB协议)                                       │
│                                                            │
│  缺点:                                                      │
│  - 性能不如 Redis (每个锁操作涉及多次ZAB提交)                │
│  - 羊群效应(需Watch前一个节点而非所有节点)                   │
└────────────────────────────────────────────────────────────┘
```

## 高层次架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       分布式锁服务架构                                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      应用服务 (Client)                             │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  DistributedLockClient (SDK)                                │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │  │
│  │  │  │ Lock API │  │ Watchdog │  │ Reentrant Counter        │  │  │
│  │  │  │ (acquire │  │ (自动续期)│  │ (线程本地重入计数)        │  │  │
│  │  │  │ /release)│  │          │  │                          │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────────────────────┘  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  │       Lock Service Router                            │  │  │
│  │  │  │  (根据 lock_key 路由到对应 lock service instance)     │  │  │
│  │  │  └──────────────────────────────────────────────────────┘  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                       │
│                                ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Lock Service Cluster                           │  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │  │
│  │  │  Lock Service   │  │  Lock Service   │  │  Lock Service   │  │  │
│  │  │  Instance 1     │  │  Instance 2     │  │  Instance 3     │  │  │
│  │  │                 │  │                 │  │                 │  │  │
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  │
│  │  │  │Lock       │  │  │  │Lock       │  │  │  │Lock       │  │  │  │
│  │  │  │Manager     │  │  │  │Manager     │  │  │  │Manager     │  │  │  │
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │  │  │
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  │
│  │  │  │Lease      │  │  │  │Lease      │  │  │  │Lease      │  │  │  │
│  │  │  │Tracker    │  │  │  │Tracker    │  │  │  │Tracker    │  │  │  │
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │  │  │
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  │
│  │  │  │Heartbeat  │  │  │  │Heartbeat  │  │  │  │Heartbeat  │  │  │  │
│  │  │  │Receiver   │  │  │  │Receiver   │  │  │  │Receiver   │  │  │  │
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │  │
│  │             │                  │                  │               │  │
│  │             └──────────────────┼──────────────────┘               │  │
│  │                                │                                   │  │
│  │                                ▼                                   │  │
│  │  ┌──────────────────────────────────────────────────────────┐    │  │
│  │  │               Consensus / Storage Layer                  │    │  │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │    │  │
│  │  │  │ Redis      │  │ Etcd/ZK    │  │ MySQL (选主+元数据) │ │    │  │
│  │  │  │ /Sentinel  │  │ Cluster    │  │                    │ │    │  │
│  │  │  └────────────┘  └────────────┘  └────────────────────┘ │    │  │
│  │  └──────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心深入

### 1. 三大实现方案深度对比

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Redis vs ZooKeeper vs Etcd 分布式锁对比                      │
│                                                                         │
│  ┌──────────────┬─────────────────┬─────────────────┬─────────────────┐ │
│  │  维度        │  Redis          │  ZooKeeper       │  Etcd           │ │
│  ├──────────────┼─────────────────┼─────────────────┼─────────────────┤ │
│  │  一致性      │  最终一致        │  强一致(ZAB)     │  强一致(Raft)   │ │
│  │  容错        │  Sentinel/      │  ZK Cluster      │  etcd Cluster   │ │
│  │              │  Cluster        │  (奇数节点)       │  (奇数节点)      │ │
│  │  性能        │  极高 (~10万    │  中等 (~1万      │  中等 (~3万     │ │
│  │  (ops/s)     │   ops/s)        │   ops/s)         │   ops/s)        │ │
│  │  自动释放    │  Key TTL        │  临时节点         │  Lease机制      │ │
│  │  公平锁      │  Redis Queue    │  原生支持         │  原生支持       │ │
│  │              │  (需要额外实现)  │  (顺序节点)       │  (Prefix Watch) │ │
│  │  可重入      │  Lua脚本+Hash   │  不支持(需自己实现)│ 不支持(需自实现)│ │
│  │  客户端复杂度│  低             │  中               │  中             │ │
│  │  运维复杂度  │  低             │  高               │  中             │ │
│  │  适用场景    │  高性能/短期锁  │  强一致/长期锁    │  强一致/长期锁  │ │
│  │  Watchdog    │  需要额外实现   │  天然Session心跳  │  天然Lease心跳  │ │
│  │  脑裂防护    │  Redlock/       │  强(ZAB保证)      │  强(Raft保证)   │ │
│  │              │  Fencing Token  │                  │                 │ │
│  └──────────────┴─────────────────┴─────────────────┴─────────────────┘ │
│                                                                         │
│  选型建议:                                                               │
│  - 性能优先, 可容忍极小概率并发 → Redis (单实例或Redlock)                 │
│  - 安全优先, 已有ZK/Etcd集群 → 直接使用ZK/Etcd                           │
│  - 强一致 + 高性能 → Etcd (Raft比ZAB更工程化)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Redis 分布式锁的陷阱与 Redlock

```
┌────────────────────────────────────────────────────────────────┐
│            Redis 单实例锁的问题与 Redlock 算法                   │
│                                                                │
│  问题1: 主从切换导致锁丢失                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Client A → SET lock:key value NX PX 30000 → Master OK  │  │
│  │  Master 异步复制给 Slave...                               │  │
│  │  Master 宕机! (锁还没复制到Slave)                         │  │
│  │  Slave 提升为 Master                                      │  │
│  │  Client B → SET lock:key value NX PX 30000 → Slave OK   │  │
│  │                                                          │  │
│  │  结果: Client A 和 Client B 同时认为自己持有锁!            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  解决方案: Redlock 算法 (Redis作者提出的分布式锁算法)           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Redlock 原理:                                            │  │
│  │  使用 N 个独立的 Redis 实例 (N=5, 奇数)                    │  │
│  │  每个实例独立部署, 不通过主从复制共享数据                    │  │
│  │                                                          │  │
│  │  获取锁流程:                                              │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ 1. 获取当前时间 T1                                  │  │  │
│  │  │ 2. 依次(不是并发)向 N 个实例获取锁                   │  │  │
│  │  │    - 设置相同的 key, value(随机字符串), TTL         │  │  │
│  │  │    - 每个实例设置超时时间 (远小于锁有效期)            │  │  │
│  │  │ 3. 获取当前时间 T2                                   │  │  │
│  │  │ 4. 计算总耗时 = T2 - T1                             │  │  │
│  │  │ 5. 如果获取成功的实例数 >= N/2+1 (即 >= 3)          │  │  │
│  │  │    AND 总耗时 < 锁的有效期                           │  │  │
│  │  │    → 获取成功                                        │  │  │
│  │  │ 6. 锁实际有效时间 = TTL - 总耗时                     │  │  │
│  │  │ 7. 如果获取失败 → 向所有实例发送释放请求             │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  Redlock 缺点:                                            │  │
│  │  - 运维复杂 (5个独立Redis实例)                            │  │
│  │  - 依赖时钟同步 (如果某个实例时钟跳变导致TTL提前过期)     │  │
│  │  - 争议: Martin Kleppmann 指出 Redlock 仍有理论缺陷      │  │
│  │    (GC pause 可能导致锁失效), 需要 Fencing Token         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 3. Fencing Token (防脑裂的关键)

```
┌────────────────────────────────────────────────────────────────┐
│                    Fencing Token 机制                           │
│                                                                │
│  问题: Lock Service 判断你持有锁, 但你的锁其实已经过期了         │
│                                                                │
│  场景:                                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  1. Client A 持有锁, 租约30秒                             │  │
│  │  2. Client A 发生 Full GC, 暂停60秒                       │  │
│  │  3. 锁自动过期, Client B 获得锁                            │  │
│  │  4. Client A GC结束, 以为自己还持有锁, 继续操作资源        │  │
│  │                                                          │  │
│  │  结果: Client A 和 Client B 同时操作同一资源!              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  解决方案:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Lock Service 每次授予锁时, 返回一个单调递增的 token       │  │
│  │                                                          │  │
│  │  获取锁:                                                  │  │
│  │    Acquire("resource_1") → {success: true, token: 42}     │  │
│  │                                                          │  │
│  │  操作资源时附带 token:                                     │  │
│  │    Storage.Write("resource_1", data, token=42)           │  │
│  │                                                          │  │
│  │  存储层验证 token:                                         │  │
│  │    if token < last_accepted_token:                        │  │
│  │        reject("stale token, lock already re-assigned")    │  │
│  │                                                          │  │
│  │  实现:                                                     │  │
│  │  - token 可以用 ZK 的 zxid / Etcd 的 revision             │  │
│  │  - Redis: 用 INCR 生成全局递增ID                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Fencing Token 伪代码:                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  // Lock Service                                         │  │
│  │  token = redis.incr("lock:token:resource_1")             │  │
│  │  redis.set("lock:resource_1", client_id, "PX", 30000)    │  │
│  │  return {token: token}                                    │  │
│  │                                                          │  │
│  │  // Client                                               │  │
│  │  result = lockService.acquire("resource_1")              │  │
│  │  storage.write("resource_1", data, token=result.token)   │  │
│  │                                                          │  │
│  │  // Storage                                              │  │
│  │  if req.token < last_written_token[resource_1]:           │  │
│  │      return "REJECTED: stale fencing token"              │  │
│  │  last_written_token[resource_1] = req.token               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 4. Watchdog 自动续期机制

```
┌────────────────────────────────────────────────────────────────┐
│                     Watchdog 自动续期                             │
│                                                                │
│  问题: 业务逻辑执行时间可能超过锁的TTL                            │
│  解决: 后台线程自动续期                                          │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Redisson Watchdog 实现原理:                              │  │
│  │                                                          │  │
│  │  lock.lock(30, SECONDS)                                  │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │                                                   │    │  │
│  │  │  主线程                   Watchdog线程            │    │  │
│  │  │  ─────────               ─────────────            │    │  │
│  │  │                         ┌──────────────┐         │    │  │
│  │  │  获取锁 ───────►        │ 启动定时任务  │         │    │  │
│  │  │                         │ 每 30/3=10s   │         │    │  │
│  │  │  执行业务逻辑            │ 调用 RENEW    │         │    │  │
│  │  │  (可能很长)              │ 续期到 30s    │         │    │  │
│  │  │                         │               │         │    │  │
│  │  │                         │  if 续期失败  │         │    │  │
│  │  │                         │   通知主线程  │         │    │  │
│  │  │                         │   锁可能丢失  │         │    │  │
│  │  │  业务完成 ───────►      │ 取消定时任务  │         │    │  │
│  │  │  释放锁                  │               │         │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  续期条件: 检查持有者ID是否匹配                             │  │
│  │  EVAL "                                                  │  │
│  │    if redis.call('GET', KEYS[1]) == ARGV[1] then          │  │
│  │      return redis.call('PEXPIRE', KEYS[1], ARGV[2])      │  │
│  │    else                                                   │  │
│  │      return 0                                             │  │
│  │    end                                                    │  │
│  │  " 1 lock:resource_1 client_id 30000                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5. 可重入锁的实现

```
┌────────────────────────────────────────────────────────────────┐
│                    可重入锁实现                                  │
│                                                                │
│  Redis Hash 方案:                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Key: lock:resource_1                                     │  │
│  │  Field: client_id (持有者ID)                               │  │
│  │  Value: 重入计数                                           │  │
│  │  TTL: 30s                                                 │  │
│  │                                                          │  │
│  │  获取锁 (Lua脚本):                                         │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ local exists = redis.call('EXISTS', KEYS[1])        │ │  │
│  │  │ if exists == 0 then                                 │ │  │
│  │  │   redis.call('HSET', KEYS[1], ARGV[1], 1)           │ │  │
│  │  │   redis.call('PEXPIRE', KEYS[1], ARGV[2])           │ │  │
│  │  │   return 1  -- 成功获取                               │ │  │
│  │  │ end                                                 │ │  │
│  │  │ if redis.call('HEXISTS', KEYS[1], ARGV[1]) == 1 then │ │  │
│  │  │   redis.call('HINCRBY', KEYS[1], ARGV[1], 1)        │ │  │
│  │  │   redis.call('PEXPIRE', KEYS[1], ARGV[2])           │ │  │
│  │  │   return 1  -- 重入成功                               │ │  │
│  │  │ end                                                 │ │  │
│  │  │ return 0  -- 失败，被他人持有                         │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  释放锁 (Lua脚本):                                         │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ if redis.call('HEXISTS', KEYS[1], ARGV[1]) == 0 then │ │  │
│  │  │   return 0  -- 不是持有者                             │ │  │
│  │  │ end                                                 │ │  │
│  │  │ local count = redis.call('HINCRBY', KEYS[1],         │ │  │
│  │  │                          ARGV[1], -1)                │ │  │
│  │  │ if count > 0 then                                   │ │  │
│  │  │   redis.call('PEXPIRE', KEYS[1], ARGV[2])           │ │  │
│  │  │   return 1  -- 未完全释放                             │ │  │
│  │  │ end                                                 │ │  │
│  │  │ redis.call('DEL', KEYS[1])                          │ │  │
│  │  │ return 1  -- 完全释放                                │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 6. ZooKeeper 公平锁实现

```
ZooKeeper 公平锁实现 (伪代码):

```java
public class ZkDistributedLock implements DistributedLock {
    private final CuratorFramework client;
    private final String lockPath;
    private final ThreadLocal<String> currentLockPath = new ThreadLocal<>();
    private final ThreadLocal<Integer> reentrantCount = 
        ThreadLocal.withInitial(() -> 0);
    
    @Override
    public void lock() throws InterruptedException {
        // 可重入检查
        if (currentLockPath.get() != null) {
            reentrantCount.set(reentrantCount.get() + 1);
            return;
        }
        
        // 创建临时顺序节点
        String path = client.create()
            .creatingParentsIfNeeded()
            .withMode(CreateMode.EPHEMERAL_SEQUENTIAL)
            .forPath(lockPath + "/lock-");
        
        currentLockPath.set(path);
        
        while (true) {
            // 获取所有子节点
            List<String> children = client.getChildren()
                .forPath(lockPath);
            Collections.sort(children);
            
            String nodeName = path.substring(
                path.lastIndexOf('/') + 1);
            int index = children.indexOf(nodeName);
            
            if (index == 0) {
                // 自己是最小的 → 获取锁成功
                reentrantCount.set(1);
                return;
            }
            
            // 监听前一个节点
            String prevNode = lockPath + "/" + children.get(index - 1);
            final CountDownLatch latch = new CountDownLatch(1);
            
            Stat stat = client.checkExists()
                .usingWatcher((WatchEvent event) -> {
                    if (event.getType() == EventType.NodeDeleted) {
                        latch.countDown();
                    }
                })
                .forPath(prevNode);
            
            if (stat == null) {
                continue;  // 前一个节点已删除, 重新检查
            }
            
            latch.await();  // 等待前一个节点释放
        }
    }
    
    @Override
    public void unlock() {
        int count = reentrantCount.get();
        if (count > 1) {
            reentrantCount.set(count - 1);
            return;
        }
        
        try {
            client.delete().forPath(currentLockPath.get());
        } catch (Exception e) {
            throw new RuntimeException(e);
        } finally {
            currentLockPath.remove();
            reentrantCount.remove();
        }
    }
}
```

## 扩展性与高可用

### 锁服务的扩展策略

```
┌──────────────────────────────────────────────────────────────┐
│                    扩展性设计                                  │
│                                                              │
│  1. 按锁名分片 (Lock Sharding):                                │
│     ┌──────────────────────────────────────────────────┐    │
│     │  Lock Service Cluster 可以按 lock_key 分片        │    │
│     │  hash(lock_key) % N → 路由到指定的 Lock Service   │    │
│     │  每个 Lock Service 独立管理一部分锁                │    │
│     │  互不影响, 天然水平扩展                            │    │
│     └──────────────────────────────────────────────────┘    │
│                                                              │
│  2. 读写锁优化读性能:                                          │
│     ┌──────────────────────────────────────────────────┐    │
│     │  读锁: 允许多个客户端同时持有                       │    │
│     │  写锁: 排他独占                                    │    │
│     │                                                   │    │
│     │  应用: 配置热更新、缓存刷新等场景                  │    │
│     └──────────────────────────────────────────────────┘    │
│                                                              │
│  3. 降级策略:                                                 │
│     ┌──────────────────────────────────────────────────┐    │
│     │  如果Lock Service完全不可用:                        │    │
│     │  - 降级为本地锁 (单机保护)                          │    │
│     │  - 降级为数据库锁 (SELECT FOR UPDATE)              │    │
│     │  - 或根据业务, 容错跳过                             │    │
│     └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## 总结

| 维度 | Redis | ZooKeeper | Etcd |
|------|-------|-----------|------|
| 一致性 | 最终一致 | 强一致(ZAB) | 强一致(Raft) |
| 性能 | 极高 | 中等 | 中等偏高 |
| 死锁防护 | Key TTL | Ephemeral节点 | Lease |
| 公平锁 | 需自实现 | 原生顺序节点 | Watch方式 |
| 可重入 | Lua实现 | 需自实现 | 需自实现 |
| 运维复杂度 | 低 | 高 | 中 |
| 适用场景 | 高性能短期锁 | 严格正确性 | 严格正确性 |

核心设计要点:
1. **性能 vs 正确性**: Redis 快但不保证100%, ZK/Etcd 慢但正确, 按业务场景选择
2. **Fencing Token 是防脑裂的关键**: 锁服务 + 资源服务协作, 资源服务必须验证 token 单调递增
3. **Watchdog 自动续期**: 避免业务执行超时导致锁意外释放
4. **原子操作是必须的**: Redis 用 Lua 脚本, ZK 用顺序节点 + Watch, 避免竞态条件
5. **时钟不可靠**: 不要依赖系统时钟做锁判断, 使用单调递增的token代替
6. **可重入是常见需求**: 同一个调用链中可能多次获取同一把锁
7. **锁的粒度很重要**: 锁粒度越细, 并发度越高, 但管理成本也增加
