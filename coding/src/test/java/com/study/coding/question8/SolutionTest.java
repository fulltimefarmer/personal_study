package com.study.coding.question8;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    private Solution bus;

    @BeforeEach
    void setUp() {
        bus = new Solution(2);
    }

    @AfterEach
    void tearDown() {
        bus.shutdown();
    }

    // 【问题求解】基本订阅/分发验证——注册后事件正确到达目标方法
    @Test
    void shouldDeliverEventToRegisteredSubscriber() {
        TestSubscriber subscriber = new TestSubscriber();
        bus.register(subscriber);
        bus.post(new StringEvent("hello"));

        assertEquals("hello", subscriber.received);
    }

    @Test
    void shouldNotDeliverToUnregisteredSubscriber() {
        TestSubscriber subscriber = new TestSubscriber();
        bus.register(subscriber);
        bus.unregister(subscriber);
        bus.post(new StringEvent("hello"));

        assertNull(subscriber.received);
    }

    @Test
    void shouldDeliverToMultipleSubscribers() {
        TestSubscriber s1 = new TestSubscriber();
        TestSubscriber s2 = new TestSubscriber();
        bus.register(s1);
        bus.register(s2);
        bus.post(new StringEvent("msg"));

        assertEquals("msg", s1.received);
        assertEquals("msg", s2.received);
    }

    // 【技术深度】继承感知事件匹配——子类事件可被声明父类的订阅者接收
    @Test
    void shouldMatchEventByInheritance() {
        ParentSubscriber subscriber = new ParentSubscriber();
        bus.register(subscriber);
        bus.post(new ChildEvent("child"));

        assertEquals("child", subscriber.received);
    }

    // 【生产实践】异步执行验证——assertNotSame 确保回调在不同线程执行
    @Test
    void shouldExecuteAsyncHandlersOnBackgroundThread() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(1);
        Thread testThread = Thread.currentThread();

        Object asyncSubscriber = new Object() {
            @SuppressWarnings("unused")
            @Solution.Subscribe(threadMode = Solution.ThreadMode.ASYNC)
            void onEvent(IntegerEvent event) {
                assertNotSame(testThread, Thread.currentThread());
                latch.countDown();
            }
        };

        bus.register(asyncSubscriber);
        bus.post(new IntegerEvent(42));

        assertTrue(latch.await(2, TimeUnit.SECONDS));
    }

    // 【生产实践】异常隔离验证——失败订阅者不阻断正常订阅者，健壮性保障
    @Test
    void shouldIsolateExceptions() {
        FailingSubscriber failing = new FailingSubscriber();
        TestSubscriber normal = new TestSubscriber();

        bus.register(failing);
        bus.register(normal);
        bus.post(new StringEvent("data"));

        assertEquals("data", normal.received);
    }

    @Test
    void shouldThrowAfterShutdown() {
        bus.shutdown();
        assertThrows(IllegalStateException.class, () -> bus.post(new StringEvent("x")));
    }

    @Test
    void shouldRejectNullEvent() {
        assertThrows(NullPointerException.class, () -> bus.post(null));
    }

    @Test
    void shouldRejectNullSubscriber() {
        assertThrows(NullPointerException.class, () -> bus.register(null));
    }

    // 【代码质量】测试辅助类均为内部静态类——作用域隔离，减少外部依赖
    // ──────────────────────────────────────────────
    // Test events and subscribers
    // ──────────────────────────────────────────────

    static class StringEvent {
        final String data;
        StringEvent(String data) { this.data = data; }
    }

    static class IntegerEvent {
        final int value;
        IntegerEvent(int value) { this.value = value; }
    }

    static class ParentEvent {
        final String data;
        ParentEvent(String data) { this.data = data; }
    }

    static class ChildEvent extends ParentEvent {
        ChildEvent(String data) { super(data); }
    }

    static class TestSubscriber {
        String received;

        @Solution.Subscribe
        void onStringEvent(StringEvent event) {
            received = event.data;
        }
    }

    static class ParentSubscriber {
        String received;

        @Solution.Subscribe
        void onParentEvent(ParentEvent event) {
            received = event.data;
        }
    }

    static class FailingSubscriber {
        @Solution.Subscribe
        void onStringEvent(StringEvent event) {
            throw new RuntimeException("Intentional failure");
        }
    }
}
