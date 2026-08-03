package com.study.coding.question3;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private Solution<String, String> kv;

    // 【生产实践】@BeforeEach/@AfterEach 管理资源生命周期，确保每个测试隔离且资源不泄漏
    @BeforeEach
    void setUp() {
        kv = new Solution<>(1000);
        kv.start();
    }

    @AfterEach
    void tearDown() {
        kv.shutdown();
    }

    @Test
    void shouldPutAndGetPermanentKey() {
        kv.put("name", "Alice");
        assertEquals("Alice", kv.get("name"));
    }

    @Test
    void shouldReturnNullForNonExistentKey() {
        assertNull(kv.get("missing"));
    }

    // 【问题求解】TTL 过期测试：验证key在TTL内存在、过期后自动清除
    @Test
    void shouldExpireKeyAfterTTL() throws InterruptedException {
        kv.put("temp", "expire-soon", 500);
        assertEquals("expire-soon", kv.get("temp"));
        Thread.sleep(600);
        assertNull(kv.get("temp"));
    }

    @Test
    void shouldNotExpirePermanentKey() throws InterruptedException {
        kv.put("permanent", "forever");
        Thread.sleep(600);
        assertEquals("forever", kv.get("permanent"));
    }

    @Test
    void shouldRemoveKeySuccessfully() {
        kv.put("foo", "bar");
        assertEquals("bar", kv.remove("foo"));
        assertNull(kv.get("foo"));
    }

    @Test
    void shouldReturnNullWhenRemovingNonExistentKey() {
        assertNull(kv.remove("does-not-exist"));
    }

    @Test
    void shouldOverwriteExistingKey() {
        kv.put("key", "old");
        kv.put("key", "new");
        assertEquals("new", kv.get("key"));
    }

    // 【生产实践】独立 store 实例 + 更短清理间隔，验证后台清理线程的正确性
    @Test
    void shouldCleanUpExpiredEntriesViaBackgroundTask() throws InterruptedException {
        Solution<String, String> store = new Solution<>(300);
        store.start();
        store.put("ghost", "data", 200);
        assertEquals("data", store.get("ghost"));

        Thread.sleep(600);
        assertEquals(0, store.size());

        store.shutdown();
    }

    // 【技术深度】边界值覆盖：0 和负数 TTL，确保参数校验无遗漏
    @Test
    void shouldRejectNonPositiveTTL() {
        assertThrows(IllegalArgumentException.class, () -> kv.put("x", "y", 0));
        assertThrows(IllegalArgumentException.class, () -> kv.put("x", "y", -1));
    }

    // 【生产实践】构造函数参数校验：拒绝无效的清理间隔，防止创建无意义实例
    @Test
    void shouldRejectNonPositiveCleanupInterval() {
        assertThrows(IllegalArgumentException.class, () -> new Solution<>(0));
        assertThrows(IllegalArgumentException.class, () -> new Solution<>(-100));
    }
}
