package com.study.coding.question7;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.io.Closeable;
import java.io.IOException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private AtomicInteger connectionCounter;
    private Solution<MockConnection> pool;

    // 【生产实践】@BeforeEach 使用 lambda 工厂——简洁、可复现的测试环境搭建
    @BeforeEach
    void setUp() {
        connectionCounter = new AtomicInteger();
        pool = new Solution<>(3, TimeUnit.SECONDS.toMillis(5),
                () -> new MockConnection(connectionCounter.incrementAndGet()),
                MockConnection::isValid);
    }

    // 【生产实践】@AfterEach 确保资源释放——避免测试间状态污染
    @AfterEach
    void tearDown() {
        pool.shutdown();
    }

    // 【问题求解】借还周期验证——断言 idle/active 计数精确匹配预期
    @Test
    void shouldBorrowAndReleaseConnection() {
        MockConnection conn = pool.borrow();
        assertNotNull(conn);
        assertEquals(1, pool.stats().activeCount());

        pool.release(conn);
        assertEquals(0, pool.stats().activeCount());
        assertEquals(1, pool.stats().idleCount());
    }

    // 【代码质量】assertSame 验证连接复用——引用相等性，确保池化行为生效
    @Test
    void shouldReuseConnectionFromPool() {
        MockConnection conn1 = pool.borrow();
        pool.release(conn1);
        MockConnection conn2 = pool.borrow();

        assertSame(conn1, conn2);
    }

    @Test
    void shouldCreateNewConnectionsUpToLimit() {
        MockConnection c1 = pool.borrow();
        MockConnection c2 = pool.borrow();
        MockConnection c3 = pool.borrow();

        assertNotNull(c1);
        assertNotNull(c2);
        assertNotNull(c3);
        assertEquals(3, pool.stats().activeCount());

        assertNotSame(c1, c2);
        assertNotSame(c2, c3);
    }

    // 【技术深度】CountDownLatch 协调多线程——精确控制并发时序，避免 flaky test
    @Test
    void shouldBlockWhenPoolExhausted() throws InterruptedException {
        pool.borrow();
        pool.borrow();
        pool.borrow();

        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch acquired = new CountDownLatch(1);
        Thread borrower = new Thread(() -> {
            started.countDown();
            MockConnection conn = pool.borrow();
            assertNotNull(conn);
            acquired.countDown();
        });

        borrower.start();
        started.await();
        Thread.sleep(200);
        assertEquals(1, acquired.getCount());

        pool.release(new MockConnection(0)); // release to unblock
        acquired.await(2, TimeUnit.SECONDS);
        assertTrue(acquired.getCount() == 0);
    }

    @Test
    void shouldThrowAfterShutdown() {
        pool.shutdown();
        assertThrows(IllegalStateException.class, () -> pool.borrow());
    }

    // 【生产实践】shutdown 后释放连接务必关闭——防止资源泄漏
    @Test
    void shouldCloseConnectionOnReleaseAfterShutdown() {
        MockConnection conn = pool.borrow();
        pool.shutdown();
        pool.release(conn);
        assertTrue(conn.isClosed());
    }

    // 【问题求解】无效连接丢弃测试——验证健康检查与资源释放的联动
    @Test
    void shouldDiscardInvalidConnectionOnRelease() throws InterruptedException {
        MockConnection conn = pool.borrow();
        conn.markInvalid();
        pool.release(conn);

        assertEquals(0, pool.stats().idleCount());
        assertTrue(conn.isClosed());
    }

    @Test
    void shouldEvictIdleConnections() throws InterruptedException {
        MockConnection conn = pool.borrow();
        pool.release(conn);
        assertEquals(1, pool.stats().idleCount());

        Thread.sleep(TimeUnit.SECONDS.toMillis(6));

        pool.evictIdleConnections();
        assertTrue(conn.isClosed());
        assertEquals(0, pool.stats().idleCount());
    }

    @Test
    void shouldRejectNonPositiveMaxConnections() {
        assertThrows(IllegalArgumentException.class,
                () -> new Solution<>(0, 1000, () -> null, c -> true));
    }

    @Test
    void shouldRejectNullFactory() {
        assertThrows(NullPointerException.class,
                () -> new Solution<>(5, 1000, null, c -> true));
    }

    // ──────────────────────────────────────────────
    // Mock connection for testing
    // ──────────────────────────────────────────────

    // 【代码质量】MockConnection —— 最小化测试替身，暴露所有必要状态
    static class MockConnection implements Closeable {
        final int id;
        boolean valid = true;
        boolean closed = false;

        MockConnection(int id) { this.id = id; }

        boolean isValid() { return valid; }
        void markInvalid() { valid = false; }
        boolean isClosed() { return closed; }

        @Override
        public void close() { closed = true; }
    }
}
