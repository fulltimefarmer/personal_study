# 题目 8：事件总线（观察者模式）

## 题目描述

实现一个**事件总线（EventBus）**，基于**发布-订阅（Pub/Sub）**模式，支持解耦的组件间通信。

要求实现：

- `void register(Object subscriber)` —— 注册一个订阅者。订阅者类中的带有 `@Subscribe` 注解的方法会被自动识别为事件处理器。
- `void unregister(Object subscriber)` —— 注销一个订阅者，移除其所有事件处理器。
- `void post(Object event)` —— 发布一个事件。事件总线索会找到所有能处理该事件的订阅者方法，并使用 `@Subscribe` 中指定的线程策略进行调用。
- 支持**同步执行**（默认）和**异步执行**两种线程策略。
- 根据**事件类型的继承关系**进行匹配：如果订阅者订阅了 `ParentEvent`，则发布 `ChildEvent extends ParentEvent` 时也应触发对应处理器。

## 示例

```java
// 定义事件
class OrderCreatedEvent {
    private final long orderId;
    // ...
}

// 订阅者
class OrderListener {
    @Subscribe
    public void onOrderCreated(OrderCreatedEvent event) {
        System.out.println("处理订单: " + event.getOrderId());
    }
}

// 使用
EventBus bus = new EventBus();
bus.register(new OrderListener());
bus.post(new OrderCreatedEvent(12345));
```

## 解题思路

### 1. 架构概览

```
                         ┌─────────────────┐
                         │    EventBus      │
                         │                  │
    post(event) ────────►│  ┌─────────────┐ │
                         │  │ 注册中心      │ │
                         │  │ ┌───────────┐│ │
                         │  │ │EventType  ││ │
                         │  │ │  └─ Sub1  ││ │
                         │  │ │  └─ Sub2  ││ │
                         │  │ └───────────┘│ │
                         │  └─────────────┘ │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ 处理器1   │ │ 处理器2   │ │ 处理器3   │
              │ (同步)    │ │ (异步)    │ │ (同步)    │
              └──────────┘ └──────────┘ └──────────┘
```

### 2. 核心数据结构

```
ConcurrentHashMap<Class<?>, CopyOnWriteArraySet<SubscriberMethod>>
       ↑ 事件类型                  ↑ 订阅者方法列表
```

- **Key**：事件类型（Class 对象）。
- **Value**：订阅该事件类型的所有方法的集合。
- `CopyOnWriteArraySet` 保证注销时的线程安全（写少读多场景）。

### 3. 注册流程

```
register(subscriber)
    │
    ▼
1. 遍历 subscriber 的所有方法（包括父类）
2. 筛选带有 @Subscribe 注解且只有一个参数的方法
3. 提取参数类型（事件类型）作为 key
4. 将 (subscriber, method) 存入 subscribers 注册表
5. 同时缓存事件类型到其所有父类型和接口的映射（用于继承匹配）
```

### 4. @Subscribe 注解设计

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Subscribe {
    ThreadMode threadMode() default ThreadMode.POSTING;
}

public enum ThreadMode {
    POSTING,  // 在发布线程同步执行
    ASYNC     // 在独立线程池异步执行
}
```

### 5. 事件匹配（类型继承）

```
当 post(ChildEvent) 时，需要找到所有能处理以下类型的方法：
  - ChildEvent 自身
  - ChildEvent 的父类 (ParentEvent, Object)
  - ChildEvent 实现的接口

实现方式：
  注册时，对于每个方法，将其事件类型的所有父类型都展开，
  每个父类型都关联到该方法。

  例如：@Subscribe void handle(ChildEvent e)
  注册表存储：{ChildEvent → [method], ParentEvent → [method], Object → [method]}
```

### 6. 异步执行策略

```java
private final ExecutorService asyncExecutor;

// post 方法中
for (SubscriberMethod sm : matchedMethods) {
    if (sm.threadMode == ThreadMode.ASYNC) {
        asyncExecutor.submit(() -> invokeSafely(sm, event));
    } else {
        invokeSafely(sm, event);
    }
}
```

### 7. 异常隔离

单个订阅者的异常不应影响其他订阅者：

```java
private void invokeSafely(SubscriberMethod sm, Object event) {
    try {
        sm.method.invoke(sm.subscriber, event);
    } catch (Exception e) {
        // 记录日志，不向上抛
    }
}
```

### 8. 复杂度分析

- **注册**：O(M * H)，M 为 @Subscribe 方法数，H 为类型层次深度。
- **注销**：O(M)（需要从所有事件类型中移除）。
- **发布**：O(S)，S 为匹配的订阅者方法数。
- **空间复杂度**：O(T * S)，T 为事件类型数，S 为订阅者方法数。

## 考察维度

- **设计模式**：观察者/发布-订阅模式的深入理解。
- **反射机制**：注解处理、Method 调用、类型层次遍历。
- **并发编程**：CopyOnWrite 集合、异步执行、线程安全。
- **生产工程实践**：异常隔离、事件类型继承、线程策略可配置。
