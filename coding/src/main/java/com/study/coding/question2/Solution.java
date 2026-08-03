package com.study.coding.question2;

import java.util.LinkedList;
import java.util.Queue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/**
 * A thread-safe bounded blocking queue for the producer-consumer pattern.
 *
 * <p>Supports multiple producers and consumers. {@code enqueue} blocks when full;
 * {@code dequeue} blocks when empty. Provides graceful shutdown via {@link #shutdown()}
 * and optional timed variants of enqueue/dequeue that return {@code false} on timeout.
 *
 * <p>Design decisions:
 * <ul>
 *   <li>{@link ReentrantLock} with two {@link Condition}s allows precise signaling
 *       (notify producers when space frees, consumers when items arrive) — more
 *       efficient than a single monitor with {@code notifyAll()}.</li>
 *   <li>{@code while} loops around {@code await()} guard against spurious wakeups,
 *       which the JVM is permitted to produce.</li>
 *   <li>Shutdown state uses a {@code volatile} flag for visibility across threads.</li>
 * </ul>
 *
 * @param <T> the type of elements held in this queue
 */
public class Solution<T> {

    private final int capacity;
    private final Queue<T> queue;
    // 【技术深度】ReentrantLock + 双 Condition 实现精准唤醒，避免 notifyAll 惊群效应
    private final Lock lock;
    private final Condition notFull;
    private final Condition notEmpty;
    // 【生产实践】volatile 保证 shutdown 标志在多线程间的可见性
    private volatile boolean shutdown;

    /**
     * Creates a bounded blocking queue.
     *
     * @param capacity maximum number of elements the queue can hold
     * @throws IllegalArgumentException if capacity is not positive
     */
    public Solution(int capacity) {
        // 【生产实践】构造器 fail-fast 校验：拒绝非正容量，避免后续逻辑异常
        if (capacity <= 0) {
            throw new IllegalArgumentException("Capacity must be positive, got: " + capacity);
        }
        this.capacity = capacity;
        this.queue = new LinkedList<>();
        this.lock = new ReentrantLock();
        this.notFull = lock.newCondition();
        this.notEmpty = lock.newCondition();
    }

    /**
     * Inserts the specified element into this queue, waiting if necessary for space
     * to become available.
     *
     * @param item the element to add
     * @throws NullPointerException  if item is null
     * @throws IllegalStateException if the queue has been shut down
     * @throws InterruptedException  if the current thread is interrupted while waiting
     */
    public void enqueue(T item) throws InterruptedException {
        if (item == null) {
            throw new NullPointerException("item must not be null");
        }
        // 【生产实践】lockInterruptibly 响应线程中断，支持优雅取消等待
        lock.lockInterruptibly();
        try {
            // 【技术深度】while 循环而非 if，防御 JVM 虚假唤醒，条件谓词二次确认
            while (queue.size() == capacity && !shutdown) {
                notFull.await();
            }
            // 【代码质量】提取 checkShutdown 消除重复代码，遵循 DRY 原则
            checkShutdown();
            queue.offer(item);
            // 【技术深度】精准 signal 而非 signalAll：仅唤醒一个生产者，减少无效竞争
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Inserts the specified element, waiting up to the specified wait time if
     * necessary for space to become available.
     *
     * @return {@code true} if the element was added; {@code false} on timeout
     */
    public boolean enqueue(T item, long timeout, TimeUnit unit) throws InterruptedException {
        if (item == null) {
            throw new NullPointerException("item must not be null");
        }
        // 【问题求解】追踪剩余 nanos 实现精确超时，虚假唤醒后仍保持准确剩余时间
        long nanos = unit.toNanos(timeout);
        lock.lockInterruptibly();
        try {
            while (queue.size() == capacity && !shutdown) {
                if (nanos <= 0L) {
                    return false;
                }
                nanos = notFull.awaitNanos(nanos);
            }
            checkShutdown();
            queue.offer(item);
            notEmpty.signal();
            return true;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Retrieves and removes the head of this queue, waiting if necessary until
     * an element becomes available.
     *
     * @return the head of this queue
     * @throws IllegalStateException if the queue has been shut down and is empty
     * @throws InterruptedException  if the current thread is interrupted while waiting
     */
    public T dequeue() throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (queue.isEmpty() && !shutdown) {
                notEmpty.await();
            }
            if (queue.isEmpty()) {
                throw new IllegalStateException("Queue has been shut down and is empty");
            }
            T item = queue.poll();
            notFull.signal();
            return item;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Retrieves and removes the head of this queue, waiting up to the specified
     * wait time if necessary for an element to become available.
     *
     * @return the head of this queue, or {@code null} on timeout
     */
    public T dequeue(long timeout, TimeUnit unit) throws InterruptedException {
        long nanos = unit.toNanos(timeout);
        lock.lockInterruptibly();
        try {
            while (queue.isEmpty() && !shutdown) {
                if (nanos <= 0L) {
                    return null;
                }
                nanos = notEmpty.awaitNanos(nanos);
            }
            if (queue.isEmpty()) {
                return null;
            }
            T item = queue.poll();
            notFull.signal();
            return item;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Returns the current number of elements in the queue.
     */
    public int size() {
        lock.lock();
        try {
            return queue.size();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Shuts down the queue, waking up all blocked threads. Subsequent enqueue
     * attempts throw {@link IllegalStateException}; dequeue attempts return
     * remaining items until the queue is empty, then throw.
     */
    public void shutdown() {
        lock.lock();
        try {
        // 【生产实践】signalAll 唤醒所有阻塞线程，确保优雅 shutdown 后无线程永久挂起
            shutdown = true;
            notFull.signalAll();
            notEmpty.signalAll();
        } finally {
            lock.unlock();
        }
    }

    public boolean isShutdown() {
        return shutdown;
    }

    private void checkShutdown() {
        if (shutdown) {
            throw new IllegalStateException("Queue has been shut down");
        }
    }

}
