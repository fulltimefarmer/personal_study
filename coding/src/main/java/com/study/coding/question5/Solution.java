package com.study.coding.question5;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A sliding-window rate limiter using the sliding-log approach.
 *
 * <p>Each client maintains a {@link ConcurrentLinkedDeque} of request timestamps.
 * On each {@link #isAllowed(String)} call, stale timestamps (outside the current
 * window) are evicted. If the number of remaining timestamps is below the threshold,
 * the request is allowed and its timestamp is recorded.
 *
 * <p>Design decisions:
 * <ul>
 *   <li>Sliding-log gives precise rate limiting (unlike fixed-window which suffers
 *       from burst-at-boundary issues).</li>
 *   <li>Per-client locking via {@code synchronized} on the deque instance keeps
 *       contention low — different clients never block each other.</li>
 *   <li>A background cleanup task removes clients that have had no traffic within
 *       the window period, preventing memory leaks.</li>
 *   <li>{@link #getStats(String)} exposes observability data for monitoring.</li>
 * </ul>
 */
public class Solution {

    private final int maxRequests;
    private final long windowMillis;
    private final long cleanupIntervalMillis;
    // 【技术深度】使用 ConcurrentHashMap，支持无锁迭代和高并发读
    private final ConcurrentMap<String, ConcurrentLinkedDeque<Long>> clientTimestamps;
    private final ConcurrentMap<String, AtomicLong> deniedCounts;
    private final ScheduledExecutorService cleanupScheduler;
    private volatile boolean running;

    /**
     * Creates a sliding-window rate limiter.
     *
     * @param maxRequests     max allowed requests per window
     * @param windowSeconds   duration of the sliding window in seconds
     * @param cleanupIntervalSeconds interval between stale-client cleanups
     * @throws IllegalArgumentException if any parameter is not positive
     */
    // 【生产实践】构造函数参数快速失败验证，避免无效对象创建
    public Solution(int maxRequests, long windowSeconds, long cleanupIntervalSeconds) {
        if (maxRequests <= 0) {
            throw new IllegalArgumentException("maxRequests must be positive, got: " + maxRequests);
        }
        if (windowSeconds <= 0) {
            throw new IllegalArgumentException(
                    "windowSeconds must be positive, got: " + windowSeconds);
        }
        if (cleanupIntervalSeconds <= 0) {
            throw new IllegalArgumentException(
                    "cleanupIntervalSeconds must be positive, got: " + cleanupIntervalSeconds);
        }
        this.maxRequests = maxRequests;
        this.windowMillis = TimeUnit.SECONDS.toMillis(windowSeconds);
        this.cleanupIntervalMillis = TimeUnit.SECONDS.toMillis(cleanupIntervalSeconds);
        this.clientTimestamps = new ConcurrentHashMap<>();
        this.deniedCounts = new ConcurrentHashMap<>();
        this.cleanupScheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "ratelimiter-cleanup");
            t.setDaemon(true);
            return t;
        });
    }

    /**
     * Convenience constructor that defaults cleanup interval to windowSeconds * 2.
     */
    // 【代码质量】构造器链式调用，消除重复代码
    public Solution(int maxRequests, long windowSeconds) {
        this(maxRequests, windowSeconds, windowSeconds * 2);
    }

    /**
     * Starts the background cleanup task.
     */
    // 【生产实践】显式生命周期管理，确保资源正确释放
    public void start() {
        running = true;
        cleanupScheduler.scheduleWithFixedDelay(
                this::cleanupStaleClients,
                cleanupIntervalMillis,
                cleanupIntervalMillis,
                TimeUnit.MILLISECONDS);
    }

    /**
     * Shuts down the cleanup scheduler.
     */
    public void shutdown() {
        running = false;
        cleanupScheduler.shutdown();
        try {
            if (!cleanupScheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                cleanupScheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            cleanupScheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }

    /**
     * Determines whether a request from the given client should be allowed.
     *
     * @param clientId the client identifier
     * @return {@code true} if the request is within the rate limit
     * @throws NullPointerException if clientId is null
     */
    public boolean isAllowed(String clientId) {
        if (clientId == null) {
            throw new NullPointerException("clientId must not be null");
        }

        // 【技术深度】computeIfAbsent 实现线程安全惰性初始化
        ConcurrentLinkedDeque<Long> deque = clientTimestamps.computeIfAbsent(
                clientId, k -> new ConcurrentLinkedDeque<>());

        long now = System.currentTimeMillis();
        long cutoff = now - windowMillis;

        // 【技术深度】细粒度锁：按客户端 Deque 同步，不同客户端互不阻塞
        synchronized (deque) {
            // 【问题求解】滑动窗口逻辑：先驱逐过期时间戳再判断限流
            while (!deque.isEmpty() && deque.peekFirst() < cutoff) {
                deque.pollFirst();
            }

            if (deque.size() < maxRequests) {
                deque.offerLast(now);
                return true;
            }

            // 【技术深度】AtomicLong 非阻塞计数，无锁递增被拒请求数
            deniedCounts.computeIfAbsent(clientId, k -> new AtomicLong()).incrementAndGet();
            return false;
        }
    }

    /**
     * Returns statistics for the given client.
     */
    public ClientStats getStats(String clientId) {
        ConcurrentLinkedDeque<Long> deque = clientTimestamps.get(clientId);
        AtomicLong denied = deniedCounts.get(clientId);
        return new ClientStats(
                deque != null ? deque.size() : 0,
                denied != null ? denied.get() : 0);
    }

    // 【生产实践】后台清理过期客户端，防止内存泄漏
    private void cleanupStaleClients() {
        if (!running) {
            return;
        }
        long cutoff = System.currentTimeMillis() - windowMillis;
        for (Map.Entry<String, ConcurrentLinkedDeque<Long>> entry : clientTimestamps.entrySet()) {
            ConcurrentLinkedDeque<Long> deque = entry.getValue();
            synchronized (deque) {
                while (!deque.isEmpty() && deque.peekFirst() < cutoff) {
                    deque.pollFirst();
                }
                if (deque.isEmpty()) {
                    clientTimestamps.remove(entry.getKey());
                    deniedCounts.remove(entry.getKey());
                }
            }
        }
    }

    /**
     * Immutable stats object for monitoring.
     */
    // 【技术深度】使用 Java record 实现不可变统计对象
    public record ClientStats(int currentWindowCount, long totalDenied) {
        @Override
        public String toString() {
            return "ClientStats{windowCount=" + currentWindowCount +
                    ", totalDenied=" + totalDenied + '}';
        }
    }

}
