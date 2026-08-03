package com.study.coding.question2;

import org.junit.jupiter.api.Test;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

class SolutionTest {

    @Test
    void shouldEnqueueAndDequeueInOrder() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(5);
        queue.enqueue(1);
        queue.enqueue(2);
        queue.enqueue(3);

        assertEquals(1, queue.dequeue());
        assertEquals(2, queue.dequeue());
        assertEquals(3, queue.dequeue());
    }

    // 【问题求解】阻塞行为全链路验证：满队列生产者阻塞 → shutdown 唤醒 → 异常终止
    @Test
    void shouldBlockWhenQueueIsFull() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(2);
        queue.enqueue(1);
        queue.enqueue(2);

        Thread producer = new Thread(() -> {
            try {
                queue.enqueue(3);
                fail("Should have thrown after shutdown");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (IllegalStateException ignored) {
                // expected
            }
        });

        producer.start();
        Thread.sleep(200);
        queue.shutdown();
        producer.join(1000);
    }

    @Test
    void shouldBlockWhenQueueIsEmpty() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(3);

        Thread consumer = new Thread(() -> {
            try {
                int value = queue.dequeue();
                System.out.println("Dequeued: " + value);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (IllegalStateException ignored) {
                // expected
            }
        });

        consumer.start();
        Thread.sleep(200);
        queue.shutdown();
        consumer.join(1000);
    }

    // 【生产实践】多生产者-多消费者并发测试：AtomicInteger 保证计数线程安全，验证生产者消费者协作正确性
    @Test
    void shouldSupportMultipleProducersAndConsumers() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(10);
        AtomicInteger produced = new AtomicInteger();
        AtomicInteger consumed = new AtomicInteger();
        int itemCount = 100;

        Runnable producerTask = () -> {
            try {
                while (true) {
                    int v = produced.incrementAndGet();
                    if (v > itemCount) break;
                    queue.enqueue(v);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        Runnable consumerTask = () -> {
            try {
                while (true) {
                    Integer item;
                    try {
                        item = queue.dequeue();
                    } catch (IllegalStateException e) {
                        break;
                    }
                    if (item != null) {
                        consumed.incrementAndGet();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        Thread p1 = new Thread(producerTask);
        Thread p2 = new Thread(producerTask);
        Thread c1 = new Thread(consumerTask);
        Thread c2 = new Thread(consumerTask);

        p1.start(); p2.start(); c1.start(); c2.start();
        p1.join(); p2.join();

        queue.shutdown();

        c1.join(5000);
        c2.join(5000);

        assertEquals(itemCount, consumed.get());
    }

    // 【问题求解】超时入队测试：满队列下验证超时返回 false 而非无限阻塞，测试超时边界行为
    @Test
    void shouldTimeoutOnEnqueueWhenFull() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(1);
        queue.enqueue(1);

        boolean success = queue.enqueue(2, 200, TimeUnit.MILLISECONDS);
        assertFalse(success);
    }

    @Test
    void shouldReturnNullOnDequeueTimeout() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(3);
        assertNull(queue.dequeue(200, TimeUnit.MILLISECONDS));
    }

    @Test
    void shouldReturnCorrectSize() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(5);
        queue.enqueue(1);
        queue.enqueue(2);
        assertEquals(2, queue.size());
        queue.dequeue();
        assertEquals(1, queue.size());
    }

    @Test
    void shouldThrowOnEnqueueAfterShutdown() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(3);
        queue.shutdown();
        assertThrows(IllegalStateException.class, () -> queue.enqueue(1));
    }

    @Test
    void shouldThrowOnDequeueAfterShutdownWithEmptyQueue() {
        Solution<Integer> queue = new Solution<>(3);
        queue.shutdown();
        assertThrows(IllegalStateException.class, () -> queue.dequeue());
    }

    // 【生产实践】优雅停机测试：shutdown 后可排空剩余元素，队列空后才拒绝操作
    @Test
    void shouldDrainAfterShutdown() throws InterruptedException {
        Solution<Integer> queue = new Solution<>(3);
        queue.enqueue(1);
        queue.enqueue(2);
        queue.shutdown();

        assertEquals(1, queue.dequeue());
        assertEquals(2, queue.dequeue());
        assertThrows(IllegalStateException.class, () -> queue.dequeue());
    }

    @Test
    void shouldRejectNullItem() {
        Solution<Integer> queue = new Solution<>(3);
        assertThrows(NullPointerException.class, () -> queue.enqueue(null));
    }

    @Test
    void shouldRejectNonPositiveCapacity() {
        assertThrows(IllegalArgumentException.class, () -> new Solution<>(0));
        assertThrows(IllegalArgumentException.class, () -> new Solution<>(-5));
    }
}
