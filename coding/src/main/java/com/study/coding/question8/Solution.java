package com.study.coding.question8;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArraySet;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * A lightweight, thread-safe event bus supporting synchronous and asynchronous
 * event delivery with type-hierarchy-aware event matching.
 *
 * <p>Usage:
 * <pre>{@code
 * EventBus bus = new EventBus();
 * bus.register(new MyListener());
 * bus.post(new MyEvent());
 * bus.shutdown();
 * }</pre>
 */
public class Solution {

    // 【生产实践】ConcurrentHashMap 确保订阅者注册表的线程安全
    private final Map<Class<?>, Set<SubscriberMethod>> subscribers;
    // 【技术深度】ExecutorService 异步分发——解耦事件投递与处理
    private final ExecutorService asyncExecutor;
    private volatile boolean shutdown;

    /**
     * Creates an event bus with a fixed-size async thread pool.
     */
    public Solution(int asyncThreads) {
        this.subscribers = new ConcurrentHashMap<>();
        // 【生产实践】守护线程工厂——避免异步线程池阻止 JVM 退出
        this.asyncExecutor = Executors.newFixedThreadPool(asyncThreads, r -> {
            Thread t = new Thread(r, "eventbus-async");
            t.setDaemon(true);
            return t;
        });
    }

    /**
     * Creates an event bus with default async pool size.
     */
    // 【代码质量】构造器链式委托，availableProcessors 作为合理的默认线程数
    public Solution() {
        this(Runtime.getRuntime().availableProcessors());
    }

    /**
     * Registers an object as a subscriber. All methods annotated with
     * {@link Subscribe} are discovered and registered.
     *
     * @param subscriber the subscriber object
     */
    // 【技术深度】反射发现 @Subscribe 注解方法，merge 进线程安全注册表
    public void register(Object subscriber) {
        Objects.requireNonNull(subscriber, "subscriber must not be null");

        Map<Class<?>, Set<SubscriberMethod>> discovered = findAllSubscriberMethods(subscriber);
        for (Map.Entry<Class<?>, Set<SubscriberMethod>> entry : discovered.entrySet()) {
            // 【生产实践】CopyOnWriteArraySet 读写分离——注册低频、分发高频场景下的最优选择
            subscribers.computeIfAbsent(entry.getKey(), k -> new CopyOnWriteArraySet<>())
                    .addAll(entry.getValue());
        }
    }

    /**
     * Unregisters a subscriber, removing all its event handlers.
     *
     * @param subscriber the subscriber to remove
     */
    // 【代码质量】removeIf 批量清理订阅者所有事件绑定——一次遍历完成注销
    public void unregister(Object subscriber) {
        Objects.requireNonNull(subscriber, "subscriber must not be null");
        for (Set<SubscriberMethod> methods : subscribers.values()) {
            methods.removeIf(sm -> sm.subscriber == subscriber);
        }
    }

    /**
     * Posts an event to all matching subscribers. Handlers annotated with
     * {@link ThreadMode#ASYNC} are executed on a background thread.
     *
     * @param event the event to post
     */
    // 【问题求解】post 入口完整校验：null 检查、shutdown 检查、按 ThreadMode 分发
    public void post(Object event) {
        Objects.requireNonNull(event, "event must not be null");
        if (shutdown) {
            throw new IllegalStateException("EventBus has been shut down");
        }

        List<SubscriberMethod> matched = findAllMatchingSubscribers(event.getClass());
        for (SubscriberMethod sm : matched) {
            // 【技术深度】ASYNC 模式提交到线程池——主线程不阻塞，提升吞吐
            if (sm.threadMode == ThreadMode.ASYNC) {
                asyncExecutor.submit(() -> invokeSafely(sm, event));
            } else {
                invokeSafely(sm, event);
            }
        }
    }

    /**
     * Shuts down the event bus gracefully.
     */
    public void shutdown() {
        shutdown = true;
        asyncExecutor.shutdown();
        try {
            if (!asyncExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                asyncExecutor.shutdownNow();
            }
        } catch (InterruptedException e) {
            asyncExecutor.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }

    // 【技术深度】类型层次遍历——沿父类和接口链查找匹配订阅者，实现继承感知
    private List<SubscriberMethod> findAllMatchingSubscribers(Class<?> eventType) {
        List<SubscriberMethod> result = new ArrayList<>();
        Class<?> current = eventType;
        while (current != null) {
            Set<SubscriberMethod> methods = subscribers.get(current);
            if (methods != null) {
                result.addAll(methods);
            }
            for (Class<?> iface : current.getInterfaces()) {
                Set<SubscriberMethod> ifaceMethods = subscribers.get(iface);
                if (ifaceMethods != null) {
                    result.addAll(ifaceMethods);
                }
            }
            current = current.getSuperclass();
        }
        return result;
    }

    // 【技术深度】反射扫描订阅者方法——沿类层次遍历 declaredMethods，发现所有订阅标注
    private Map<Class<?>, Set<SubscriberMethod>> findAllSubscriberMethods(Object subscriber) {
        Map<Class<?>, Set<SubscriberMethod>> result = new ConcurrentHashMap<>();
        Class<?> clazz = subscriber.getClass();
        while (clazz != null) {
            for (Method method : clazz.getDeclaredMethods()) {
                Subscribe annotation = method.getAnnotation(Subscribe.class);
                if (annotation == null || method.getParameterCount() != 1) {
                    continue;
                }
                // 【生产实践】setAccessible 允许调用 private 订阅方法——提升封装性
                method.setAccessible(true);
                SubscriberMethod sm = new SubscriberMethod(subscriber, method, annotation.threadMode());
                registerForAllAssignableTypes(method.getParameterTypes()[0], sm, result);
            }
            clazz = clazz.getSuperclass();
        }
        return result;
    }

    private void registerForAllAssignableTypes(Class<?> eventType, SubscriberMethod sm,
                                                Map<Class<?>, Set<SubscriberMethod>> result) {
        Class<?> current = eventType;
        while (current != null && current != Object.class) {
            addToResult(current, sm, result);
            for (Class<?> iface : current.getInterfaces()) {
                addToResult(iface, sm, result);
            }
            current = current.getSuperclass();
        }
    }

    private void addToResult(Class<?> type, SubscriberMethod sm,
                             Map<Class<?>, Set<SubscriberMethod>> result) {
        result.computeIfAbsent(type, k -> new CopyOnWriteArraySet<>()).add(sm);
    }

    // 【生产实践】异常隔离——单个订阅者失败不影响其他订阅者接收事件
    private void invokeSafely(SubscriberMethod sm, Object event) {
        try {
            sm.method.invoke(sm.subscriber, event);
        } catch (Exception ignored) {
        }
    }

    // ──────────────────────────────────────────────
    // Supporting types
    // ──────────────────────────────────────────────

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    public @interface Subscribe {
        ThreadMode threadMode() default ThreadMode.POSTING;
    }

    public enum ThreadMode {
        POSTING,
        ASYNC
    }

    // 【代码质量】自定义 equals/hashCode——identityHashCode 区分订阅者实例，避免冲突
    private static class SubscriberMethod {
        final Object subscriber;
        final Method method;
        final ThreadMode threadMode;

        SubscriberMethod(Object subscriber, Method method, ThreadMode threadMode) {
            this.subscriber = subscriber;
            this.method = method;
            this.threadMode = threadMode;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            // 【技术深度】pattern matching instanceof (Java 16+)——简洁的类型检查与变量绑定
            if (!(o instanceof SubscriberMethod that)) return false;
            return subscriber == that.subscriber && method.equals(that.method);
        }

        @Override
        public int hashCode() {
            return Objects.hash(System.identityHashCode(subscriber), method);
        }
    }
}
