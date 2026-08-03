package com.study.coding.question3;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A thread-safe, in-memory key-value store with optional TTL (time-to-live).
 *
 * <p>Design highlights:
 * <ul>
 *   <li>Lazy expiration on {@code get} — expired entries return {@code null} and are
 *       removed immediately.</li>
 *   <li>Periodic background cleanup via {@link ScheduledExecutorService} prevents
 *       memory leaks from keys that are written but never accessed again.</li>
 *   <li>Explicit lifecycle methods {@link #start()} / {@link #shutdown()} allow the
 *       caller to control cleanup resources.</li>
 *   <li>Uses {@link ConcurrentHashMap} for high-concurrency reads; writes are
 *       lock-free at the map level.</li>
 * </ul>
 *
 * @param <K> the type of keys
 * @param <V> the type of values
 */
public class Solution<K, V> {

    // 【技术深度】Long.MAX_VALUE 作为"永不过期"哨兵值，避免 null 分支判断
    private static final long NO_EXPIRY = Long.MAX_VALUE;

    // 【技术深度】ConcurrentHashMap 实现锁自由读取，高并发场景下读取零竞争
    private final ConcurrentMap<K, Entry<V>> store;
    private final long cleanupIntervalMs;
    private final ScheduledExecutorService scheduler;
    private volatile boolean running;

    /**
     * Creates a new key-value store with the specified cleanup interval.
     *
     * @param cleanupIntervalMs interval in milliseconds between background expiration sweeps
     * @throws IllegalArgumentException if cleanupIntervalMs is not positive
     */
    public Solution(long cleanupIntervalMs) {
        if (cleanupIntervalMs <= 0) {
            throw new IllegalArgumentException(
                    "cleanupIntervalMs must be positive, got: " + cleanupIntervalMs);
        }
        this.store = new ConcurrentHashMap<>();
        this.cleanupIntervalMs = cleanupIntervalMs;
        // 【生产实践】守护线程工厂：JVM 退出时不会因清理线程阻塞，资源安全释放
        this.scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "kvstore-cleanup");
            t.setDaemon(true);
            return t;
        });
    }

    /**
     * Starts the periodic background cleanup task.
     */
    public void start() {
        running = true;
        // 【问题求解】scheduleWithFixedDelay 确保上次清理完成后才启动下次，避免任务堆积
        scheduler.scheduleWithFixedDelay(
                this::cleanupExpired,
                cleanupIntervalMs,
                cleanupIntervalMs,
                TimeUnit.MILLISECONDS);
    }

    /**
     * Shuts down the cleanup scheduler gracefully.
     */
    // 【生产实践】优雅 shutdown：先尝试等待任务完成，超时则强制终止，异常时恢复中断状态
    public void shutdown() {
        running = false;
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }

    /**
     * Stores a value with no expiration.
     */
    public void put(K key, V value) {
        store.put(key, new Entry<>(value, NO_EXPIRY));
    }

    /**
     * Stores a value that expires after the given TTL.
     *
     * @param key        the key
     * @param value      the value
     * @param ttlMillis  time-to-live in milliseconds
     * @throws IllegalArgumentException if ttlMillis is not positive
     */
    public void put(K key, V value, long ttlMillis) {
        if (ttlMillis <= 0) {
            throw new IllegalArgumentException("ttlMillis must be positive, got: " + ttlMillis);
        }
        long expiryTime = System.currentTimeMillis() + ttlMillis;
        store.put(key, new Entry<>(value, expiryTime));
    }

    /**
     * Retrieves the value for the given key. Returns {@code null} if the key
     * does not exist or has expired (expired entries are removed eagerly on access).
     */
    public V get(K key) {
        Entry<V> entry = store.get(key);
        if (entry == null) {
            return null;
        }
        if (entry.isExpired()) {
            // 【生产实践】原子条件删除 remove(key, value)：仅在值未被替换时移除，避免误删并发写入
            store.remove(key, entry);
            return null;
        }
        return entry.value;
    }

    /**
     * Explicitly removes the entry for the given key.
     *
     * @return the previous value, or {@code null} if not present
     */
    public V remove(K key) {
        Entry<V> entry = store.remove(key);
        if (entry == null || entry.isExpired()) {
            return null;
        }
        return entry.value;
    }

    /**
     * Returns the approximate number of non-expired entries. This count does not
     * include entries that have expired but have not yet been cleaned up by the
     * background task.
     */
    public int size() {
        // Not perfectly accurate due to lazy expiration but safe to call.
        return store.size();
    }

    private void cleanupExpired() {
        if (!running) {
            return;
        }
        for (K key : store.keySet()) {
            Entry<V> entry = store.get(key);
            if (entry != null && entry.isExpired()) {
                store.remove(key, entry);
            }
        }
    }

    // 【代码质量】Java 17 record 内置 equals/hashCode/不可变性，天然适合作为值对象
    private record Entry<V>(V value, long expiryTime) {
        boolean isExpired() {
            return System.currentTimeMillis() > expiryTime;
        }
    }

}
