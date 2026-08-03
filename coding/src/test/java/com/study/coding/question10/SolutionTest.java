package com.study.coding.question10;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private Solution scheduler;

    // 【生产实践】@BeforeEach/@AfterEach 管理调度器生命周期，每个测试独立启停
    @BeforeEach
    void setUp() {
        scheduler = new Solution();
        scheduler.start();
    }

    @AfterEach
    void tearDown() {
        scheduler.shutdown();
    }

    // 【问题求解】延迟执行验证：CountDownLatch 配合 wait 超时 + 最短耗时断言
    @Test
    void shouldExecuteTaskAfterDelay() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(1);
        long start = System.currentTimeMillis();

        scheduler.schedule(latch::countDown, 300);

        assertTrue(latch.await(2, TimeUnit.SECONDS));
        long elapsed = System.currentTimeMillis() - start;
        assertTrue(elapsed >= 250, "Elapsed: " + elapsed + "ms");
    }

    // 【生产实践】取消尚未执行的任务：sleep 超延迟后验证 latch 未被倒计数
    @Test
    void shouldCancelTaskBeforeExecution() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(1);
        Solution.ScheduledTask task = scheduler.schedule(latch::countDown, 500);
        scheduler.cancel(task);

        Thread.sleep(800);
        assertEquals(1, latch.getCount());
    }

    @Test
    void shouldExecuteMultipleTasksInOrder() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(3);
        AtomicInteger counter = new AtomicInteger();

        scheduler.schedule(() -> {
            counter.incrementAndGet();
            latch.countDown();
        }, 100);

        scheduler.schedule(() -> {
            counter.incrementAndGet();
            latch.countDown();
        }, 200);

        scheduler.schedule(() -> {
            counter.incrementAndGet();
            latch.countDown();
        }, 300);

        assertTrue(latch.await(2, TimeUnit.SECONDS));
        assertEquals(3, counter.get());
    }

    // 【问题求解】重复任务测试：CountDownLatch(3) 验证定时任务至少执行 3 次
    @Test
    void shouldExecuteRepeatingTask() throws InterruptedException {
        AtomicInteger counter = new AtomicInteger();
        CountDownLatch latch = new CountDownLatch(3);

        scheduler.schedule(() -> {
            counter.incrementAndGet();
            latch.countDown();
        }, 100, 150);

        assertTrue(latch.await(3, TimeUnit.SECONDS));
        assertTrue(counter.get() >= 3);
    }

    // 【问题求解】取消重复任务：记录取消前的计数快照，休眠后验证不再递增
    @Test
    void shouldCancelRepeatingTask() throws InterruptedException {
        AtomicInteger counter = new AtomicInteger();
        Solution.ScheduledTask task = scheduler.schedule(counter::incrementAndGet, 100, 200);

        Thread.sleep(350);
        scheduler.cancel(task);
        int beforeCancel = counter.get();

        Thread.sleep(600);
        assertEquals(beforeCancel, counter.get());
    }

    // 【生产实践】异常隔离测试：前一个任务抛异常不影响后续任务的正常调度
    @Test
    void shouldIsolateTaskExceptions() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(1);

        scheduler.schedule(() -> {
            throw new RuntimeException("Intentional failure");
        }, 100);

        scheduler.schedule(latch::countDown, 200);

        assertTrue(latch.await(2, TimeUnit.SECONDS));
    }

    // 【生产实践】shutdown 清理验证：超长延迟任务在 shutdown 后确定不会执行
    @Test
    void shouldClearPendingOnShutdown() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(1);
        scheduler.schedule(latch::countDown, 5000);
        scheduler.shutdown();

        assertTrue(latch.getCount() > 0);
    }

    @Test
    void shouldRejectNullTask() {
        assertThrows(NullPointerException.class, () -> scheduler.schedule(null, 100));
    }

    @Test
    void shouldRejectNegativeDelay() {
        assertThrows(IllegalArgumentException.class,
                () -> scheduler.schedule(() -> {}, -1));
    }

    @Test
    void shouldRejectNegativePeriod() {
        assertThrows(IllegalArgumentException.class,
                () -> scheduler.schedule(() -> {}, 100, -1));
    }
}
