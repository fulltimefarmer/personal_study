package com.study.coding.question1;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private Solution<Integer, Integer> cache;

    // 【代码质量】@BeforeEach 保证每个测试方法获得独立缓存实例，消除测试间状态耦合
    @BeforeEach
    void setUp() {
        cache = new Solution<>(3);
    }

    // 【代码质量】should 命名约定：清晰表达被测试行为与预期结果
    @Test
    void shouldReturnNegativeOneWhenKeyNotFound() {
        assertNull(cache.get(1));
    }

    @Test
    void shouldPutAndGetSuccessfully() {
        cache.put(1, 10);
        assertEquals(10, cache.get(1));
    }

    @Test
    void shouldUpdateExistingKey() {
        cache.put(1, 10);
        cache.put(1, 20);
        assertEquals(20, cache.get(1));
    }

    // 【问题求解】全面覆盖逐出后各元素状态，多断言验证 LRU 语义的完整性
    @Test
    void shouldEvictLeastRecentlyUsedWhenCapacityExceeded() {
        cache.put(1, 1);
        cache.put(2, 2);
        cache.put(3, 3);
        cache.put(4, 4);

        assertNull(cache.get(1));
        assertEquals(2, cache.get(2));
        assertEquals(3, cache.get(3));
        assertEquals(4, cache.get(4));
    }

    @Test
    void shouldPromoteRecentlyAccessedKey() {
        cache.put(1, 1);
        cache.put(2, 2);
        cache.put(3, 3);

        cache.get(1);      // 访问 1，使其变为最近使用
        cache.put(4, 4);   // 应逐出 2

        assertEquals(1, cache.get(1));
        assertNull(cache.get(2));
        assertEquals(3, cache.get(3));
        assertEquals(4, cache.get(4));
    }

    @Test
    void shouldHandleSingleElementCache() {
        Solution<Integer, Integer> smallCache = new Solution<>(1);
        smallCache.put(1, 100);
        assertEquals(100, smallCache.get(1));

        smallCache.put(2, 200);
        assertNull(smallCache.get(1));
        assertEquals(200, smallCache.get(2));
    }

    @Test
    void shouldReturnCorrectSize() {
        assertEquals(0, cache.size());
        cache.put(1, 1);
        assertEquals(1, cache.size());
        cache.put(2, 2);
        cache.put(3, 3);
        assertEquals(3, cache.size());
        cache.put(4, 4);
        assertEquals(3, cache.size());
    }

    @Test
    void shouldClearAllEntries() {
        cache.put(1, 1);
        cache.put(2, 2);
        cache.clear();
        assertEquals(0, cache.size());
        assertNull(cache.get(1));
        assertNull(cache.get(2));
    }

    // 【生产实践】空值输入防御测试：验证 get/put 的 requireNonNull 快速失败路径
    @Test
    void shouldRejectNullKey() {
        assertThrows(NullPointerException.class, () -> cache.get(null));
        assertThrows(NullPointerException.class, () -> cache.put(null, 1));
    }

    // 【问题求解】边界值测试：覆盖零值与负值容量，验证构造器参数校验的完备性
    @Test
    void shouldRejectNonPositiveCapacity() {
        assertThrows(IllegalArgumentException.class, () -> new Solution<>(0));
        assertThrows(IllegalArgumentException.class, () -> new Solution<>(-1));
    }
}
