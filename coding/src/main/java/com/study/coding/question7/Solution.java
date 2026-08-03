package com.study.coding.question7;

import java.io.Closeable;
import java.io.IOException;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.BlockingDeque;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Predicate;

/**
 * A generic thread-safe connection pool supporting borrow/release semantics,
 * health checking, and graceful shutdown.
 *
 * @param <T> the connection type, must implement {@link Closeable}
 */
// 【技术深度】T extends Closeable —— 有界类型参数确保可关闭性，编译期安全
public class Solution<T extends Closeable> {

    private final int maxConnections;
    private final long maxIdleTimeMillis;
    private final ConnectionFactory<T> factory;
    private final Predicate<T> healthCheck;

    private final BlockingDeque<TimedConnection<T>> idleQueue;
    // 【代码质量】activeSet 追踪借出连接，idleQueue 维护可用连接——关注点分离
    private final Set<T> activeSet;
    private final Lock lock;
    private final Condition notEmpty;
    private volatile boolean shutdown;

    /**
     * Creates a connection pool.
     *
     * @param maxConnections  maximum number of concurrent connections
     * @param maxIdleTimeMillis maximum idle time before a connection is evicted
     * @param factory          factory to create new connections
     * @param healthCheck      predicate to test connection validity (e.g. conn::isValid)
     */
    public Solution(int maxConnections, long maxIdleTimeMillis,
                    ConnectionFactory<T> factory, Predicate<T> healthCheck) {
        // 【生产实践】构造器全面校验所有参数，失败快速（fail-fast）
        if (maxConnections <= 0) {
            throw new IllegalArgumentException(
                    "maxConnections must be positive, got: " + maxConnections);
        }
        if (maxIdleTimeMillis <= 0) {
            throw new IllegalArgumentException(
                    "maxIdleTimeMillis must be positive, got: " + maxIdleTimeMillis);
        }
        Objects.requireNonNull(factory, "factory must not be null");
        Objects.requireNonNull(healthCheck, "healthCheck must not be null");

        this.maxConnections = maxConnections;
        this.maxIdleTimeMillis = maxIdleTimeMillis;
        this.factory = factory;
        this.healthCheck = healthCheck;
        this.idleQueue = new LinkedBlockingDeque<>();
        this.activeSet = new HashSet<>();
        this.lock = new ReentrantLock();
        this.notEmpty = lock.newCondition();
    }

    /**
     * Convenience constructor that defaults idle timeout to 30 minutes
     * and health check to always-true.
     */
    // 【代码质量】构造器链式委托，提供合理默认值，减少调用方决策负担
    public Solution(int maxConnections, ConnectionFactory<T> factory) {
        this(maxConnections, TimeUnit.MINUTES.toMillis(30),
                factory, conn -> true);
    }

    /**
     * Borrows a connection from the pool. Blocks if none available and pool is full.
     *
     * @return a valid connection
     * @throws IllegalStateException if the pool has been shut down
     * @throws RuntimeException      if interrupted while waiting
     */
    public T borrow() {
        lock.lock();
        try {
            // 【问题求解】借出循环：先尝试空闲连接 → 未达上限则新建 → 否则阻塞等待
            while (!shutdown) {
                T conn = tryBorrowIdle();
                if (conn != null) {
                    return conn;
                }
                if (totalCount() < maxConnections) {
                    conn = factory.create();
                    activeSet.add(conn);
                    return conn;
                }
                awaitUninterruptibly(notEmpty);
            }
            throw new IllegalStateException("Pool has been shut down");
        } finally {
            lock.unlock();
        }
    }

    /**
     * Returns a connection to the pool. Does nothing if the connection is null.
     *
     * @param conn the connection to release
     */
    // 【问题求解】释放路径三元分流：shutdown 路径、健康检查路径、正常归还路径全部分离
    public void release(T conn) {
        if (conn == null) {
            return;
        }
        lock.lock();
        try {
            activeSet.remove(conn);
            if (shutdown) {
                closeQuietly(conn);
            } else if (!healthCheck.test(conn)) {
                closeQuietly(conn);
            } else {
                idleQueue.offerLast(new TimedConnection<>(conn, System.currentTimeMillis()));
                notEmpty.signal();
            }
        } finally {
            lock.unlock();
        }
    }

    /**
     * Shuts down the pool: closes idle connections immediately and prevents
     * further borrowing. Currently borrowed connections are not closed.
     */
    // 【生产实践】优雅关闭：先关闭空闲连接，再唤醒所有等待线程——避免死锁
    public void shutdown() {
        lock.lock();
        try {
            shutdown = true;
            notEmpty.signalAll();
            for (TimedConnection<T> tc : idleQueue) {
                closeQuietly(tc.connection);
            }
            idleQueue.clear();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Evicts idle connections that have exceeded the maximum idle time.
     * Should be called periodically (e.g., by a ScheduledExecutorService).
     */
    // 【技术深度】LIFO 淘汰——从双端队列头部移除，优先回收最久未使用的空闲连接
    public void evictIdleConnections() {
        lock.lock();
        try {
            TimedConnection<T> tc;
            while ((tc = idleQueue.peekFirst()) != null) {
                if (System.currentTimeMillis() - tc.createTime > maxIdleTimeMillis) {
                    idleQueue.pollFirst();
                    closeQuietly(tc.connection);
                } else {
                    break;
                }
            }
        } finally {
            lock.unlock();
        }
    }

    /**
     * Returns the current pool statistics.
     */
    public PoolStats stats() {
        lock.lock();
        try {
            return new PoolStats(idleQueue.size(), activeSet.size(), maxConnections, shutdown);
        } finally {
            lock.unlock();
        }
    }

    // 【代码质量】借用前进行健康验证——防止将已失效连接返回给调用方
    private T tryBorrowIdle() {
        TimedConnection<T> tc;
        while ((tc = idleQueue.pollFirst()) != null) {
            if (healthCheck.test(tc.connection)) {
                activeSet.add(tc.connection);
                return tc.connection;
            }
            closeQuietly(tc.connection);
        }
        return null;
    }

    private int totalCount() {
        return idleQueue.size() + activeSet.size();
    }

    // 【技术深度】awaitUninterruptibly 保留中断状态——遵循线程中断规范
    private void awaitUninterruptibly(Condition condition) {
        boolean interrupted = false;
        try {
            condition.await();
        } catch (InterruptedException e) {
            interrupted = true;
        }
        if (interrupted) {
            Thread.currentThread().interrupt();
        }
    }

    // 【生产实践】资源清理永不抛异常——避免丢失主线异常或被忽略
    private void closeQuietly(Closeable c) {
        try {
            c.close();
        } catch (IOException ignored) {
        }
    }

    // ──────────────────────────────────────────────
    // Supporting types
    // ──────────────────────────────────────────────

    // 【代码质量】@FunctionalInterface ConnectionFactory —— 清晰的 SPI 契约，支持 lambda
    @FunctionalInterface
    public interface ConnectionFactory<T> {
        T create();
    }

    // 【技术深度】private record TimedConnection —— 不可变数据载体，Java 17 特性
    private record TimedConnection<T>(T connection, long createTime) {}

    // 【代码质量】public record PoolStats —— 不可变统计快照，Java 17 特性
    public record PoolStats(int idleCount, int activeCount, int maxConnections, boolean isShutdown) {
        @Override
        public String toString() {
            return "PoolStats{idle=" + idleCount + ", active=" + activeCount
                    + ", max=" + maxConnections + ", shutdown=" + isShutdown + '}';
        }
    }
}
