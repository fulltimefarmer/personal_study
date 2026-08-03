package com.study.coding.question5;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private Solution limiter;

    // 【生产实践】资源生命周期管理：测试前后启停限流器
    @BeforeEach
    void setUp() {
        limiter = new Solution(3, 2);
        limiter.start();
    }

    @AfterEach
    void tearDown() {
        limiter.shutdown();
    }

    @Test
    void shouldAllowRequestsWithinLimit() {
        assertTrue(limiter.isAllowed("client-A"));
        assertTrue(limiter.isAllowed("client-A"));
        assertTrue(limiter.isAllowed("client-A"));
    }

    @Test
    void shouldDenyRequestsWhenLimitExceeded() {
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        assertFalse(limiter.isAllowed("client-A"));
    }

    // 【问题求解】真实时序测试：等待窗口滑动后验证限流恢复
    @Test
    void shouldAllowAgainAfterWindowSlides() throws InterruptedException {
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        assertFalse(limiter.isAllowed("client-A"));

        Thread.sleep(2_100);
        assertTrue(limiter.isAllowed("client-A"));
    }

    // 【问题求解】客户端隔离测试：验证独立限流互不影响
    @Test
    void shouldIsolateClientsFromEachOther() {
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        assertFalse(limiter.isAllowed("client-A"));

        assertTrue(limiter.isAllowed("client-B"));
        assertTrue(limiter.isAllowed("client-B"));
    }

    @Test
    void shouldTrackStatsCorrectly() {
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A");
        limiter.isAllowed("client-A"); // denied

        Solution.ClientStats stats = limiter.getStats("client-A");
        assertEquals(3, stats.currentWindowCount());
        assertEquals(1, stats.totalDenied());
    }

    @Test
    void shouldReturnZeroStatsForUnknownClient() {
        Solution.ClientStats stats = limiter.getStats("unknown");
        assertEquals(0, stats.currentWindowCount());
        assertEquals(0, stats.totalDenied());
    }

    @Test
    void shouldRejectNullClientId() {
        assertThrows(NullPointerException.class, () -> limiter.isAllowed(null));
    }

    // 【代码质量】参数校验：覆盖全部三个构造器重载
    @Test
    void shouldRejectNonPositiveParameters() {
        assertThrows(IllegalArgumentException.class, () -> new Solution(0, 2));
        assertThrows(IllegalArgumentException.class, () -> new Solution(3, 0));
        assertThrows(IllegalArgumentException.class, () -> new Solution(3, 2, 0));
    }
}
