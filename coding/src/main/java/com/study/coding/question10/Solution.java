package com.study.coding.question10;

import java.util.Objects;
import java.util.concurrent.PriorityBlockingQueue;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/**
 * A lightweight delayed task scheduler backed by a priority queue.
 *
 * <p>A single worker thread polls the queue for tasks whose execution time has
 * arrived. Supports one-shot and repeating tasks, cancellation, and graceful
 * shutdown.
 */
public class Solution {

    // 【技术深度】PriorityBlockingQueue：线程安全优先队列，按执行时间排序
    private final PriorityBlockingQueue<ScheduledTask> taskQueue;
    private final Lock lock;
    private final Condition taskAvailable;
    // 【技术深度】AtomicLong 生成唯一任务 ID，无锁递增，保证 Comparable tie-break 确定性
    private final AtomicLong taskIdGenerator;
    // 【技术深度】volatile 保证 running 标志在多线程间的可见性
    private volatile boolean running;
    private Thread worker;

    public Solution() {
        this.taskQueue = new PriorityBlockingQueue<>();
        this.lock = new ReentrantLock();
        this.taskAvailable = lock.newCondition();
        this.taskIdGenerator = new AtomicLong();
    }

    /**
     * Starts the scheduler worker thread.
     */
    public void start() {
        running = true;
        worker = new Thread(new WorkerLoop(), "task-scheduler");
        // 【生产实践】daemon 线程：JVM 退出时不会阻止进程结束
        worker.setDaemon(true);
        worker.start();
    }

    /**
     * Schedules a one-shot task to run after the specified delay.
     *
     * @param task        the task to execute
     * @param delayMillis delay in milliseconds before execution
     * @return a handle that can be used to cancel the task
     * @throws NullPointerException     if task is null
     * @throws IllegalArgumentException if delayMillis is negative
     */
    public ScheduledTask schedule(Runnable task, long delayMillis) {
        return schedule(task, delayMillis, 0);
    }

    /**
     * Schedules a task. If periodMillis is positive, the task repeats at
     * fixed intervals.
     *
     * @param task         the task to execute
     * @param initialDelay delay before first execution in milliseconds
     * @param periodMillis repeat interval in milliseconds (0 = one-shot)
     * @return a handle that can be used to cancel the task
     */
    public ScheduledTask schedule(Runnable task, long initialDelay, long periodMillis) {
        // 【生产实践】全面参数校验：null 检查 + 边界值校验，fail-fast 原则
        Objects.requireNonNull(task, "task must not be null");
        if (initialDelay < 0) {
            throw new IllegalArgumentException(
                    "initialDelay must be >= 0, got: " + initialDelay);
        }
        if (periodMillis < 0) {
            throw new IllegalArgumentException(
                    "periodMillis must be >= 0, got: " + periodMillis);
        }

        long executeAt = System.currentTimeMillis() + initialDelay;
        ScheduledTask scheduledTask = new ScheduledTask(
                taskIdGenerator.incrementAndGet(), task, executeAt, periodMillis);
        taskQueue.offer(scheduledTask);

        // 【技术深度】Condition.signal() 唤醒等待的 worker 线程，避免轮询空转
        lock.lock();
        try {
            taskAvailable.signal();
        } finally {
            lock.unlock();
        }
        return scheduledTask;
    }

    /**
     * Cancels a scheduled task. No effect if already executed or already cancelled.
     *
     * @param task the task to cancel
     */
    public void cancel(ScheduledTask task) {
        if (task != null) {
            task.cancel();
        }
    }

    /**
     * Returns the number of pending (not yet due and not cancelled) tasks.
     */
    public int pendingTasks() {
        return taskQueue.size();
    }

    /**
     * Shuts down the scheduler. Cancels all pending tasks and interrupts the
     * worker thread. Already-executing tasks are allowed to finish (cooperative).
     */
    // 【生产实践】优雅关闭：volatile 标志 → interrupt → join(timeout) → clear，防止资源泄漏
    public void shutdown() {
        running = false;
        if (worker != null) {
            worker.interrupt();
            try {
                worker.join(3000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        taskQueue.clear();
    }

    // ──────────────────────────────────────────────
    // Worker loop
    // ──────────────────────────────────────────────

    private class WorkerLoop implements Runnable {
        @Override
        public void run() {
            // 【代码质量】while(running) 协作式取消，响应 shutdown 的 volatile 标志
            while (running) {
                try {
                    ScheduledTask task = taskQueue.poll();
                    // 【技术深度】poll 返回 null 时阻塞等待信号，避免 CPU 空转
                    if (task == null) {
                        awaitSignalOrTimeout(500);
                        continue;
                    }

                    long delay = task.executeAtMillis - System.currentTimeMillis();
                    // 【问题求解】任务未到期 → 重新入队 + 短暂休眠，避免反复取出放回
                    if (delay > 0) {
                        taskQueue.offer(task);
                        Thread.sleep(Math.min(delay, 200));
                        continue;
                    }

                    // 【代码质量】执行前检查取消状态：已取消的任务直接跳过
                    if (task.isCancelled()) {
                        continue;
                    }

                    // 【生产实践】异常隔离：单个任务抛异常不影响后续任务执行
                    try {
                        task.runnable.run();
                    } catch (Exception ignored) {
                    }

                    // 【问题求解】重复任务：执行后重新计算到期时间并入队
                    if (task.isRepeat() && !task.isCancelled()) {
                        task.executeAtMillis = System.currentTimeMillis() + task.periodMillis;
                        taskQueue.offer(task);
                    }
                } catch (InterruptedException e) {
                    // 【技术深度】区分 shutdown 中断与虚假中断：shutdown 时 break，否则恢复中断状态
                    if (!running) {
                        break;
                    }
                    Thread.currentThread().interrupt();
                }
            }
        }

        private void awaitSignalOrTimeout(long timeoutMillis) throws InterruptedException {
            lock.lock();
            try {
                taskAvailable.await(timeoutMillis, java.util.concurrent.TimeUnit.MILLISECONDS);
            } finally {
                lock.unlock();
            }
        }
    }

    // ──────────────────────────────────────────────
    // Scheduled task
    // ──────────────────────────────────────────────

    // 【技术深度】volatile 字段保证跨线程可见性，Comparable 用于 PriorityBlockingQueue 排序
    public static class ScheduledTask implements Comparable<ScheduledTask> {
        final long id;
        final Runnable runnable;
        volatile long executeAtMillis;
        volatile boolean cancelled;
        final long periodMillis;

        ScheduledTask(long id, Runnable runnable, long executeAtMillis, long periodMillis) {
            this.id = id;
            this.runnable = runnable;
            this.executeAtMillis = executeAtMillis;
            this.periodMillis = periodMillis;
        }

        boolean isRepeat() {
            return periodMillis > 0;
        }

        void cancel() {
            cancelled = true;
        }

        boolean isCancelled() {
            return cancelled;
        }

        @Override
        public int compareTo(ScheduledTask other) {
            int cmp = Long.compare(this.executeAtMillis, other.executeAtMillis);
            return cmp != 0 ? cmp : Long.compare(this.id, other.id);
        }
    }
}
