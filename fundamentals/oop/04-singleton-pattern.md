# 题目：单例模式

## 问题
请详细说明单例模式（Singleton Pattern）的几种实现方式：懒汉式、饿汉式、双重校验锁（DCL）、枚举实现。分析各实现的原理、优缺点和线程安全性，并给出 Java 和 TypeScript 代码示例。

## 考点
- 单例模式的核心思想
- 线程安全机制（synchronized、volatile、类加载机制）
- 反射和序列化对单例的破坏与防御
- 不同语言中实现单例的惯用方式

## 解答

### 一、单例模式定义与用途

**定义**：确保一个类只有一个实例，并提供一个全局访问点。

**用途**：
- 全局配置管理
- 数据库连接池
- 日志记录器
- 线程池
- Spring 中的 Bean 默认作用域

**核心要点**：
1. 构造方法私有化
2. 提供静态获取实例的方法
3. 确保多线程环境下只创建一个实例

---

### 二、实现方式对比

| 实现方式 | 线程安全 | 懒加载 | 防反射 | 防序列化 | 推荐度 |
|---------|---------|--------|--------|---------|--------|
| 饿汉式 | ✅ | ❌ | ❌ | ❌ | ⭐⭐ |
| 懒汉式（同步方法） | ✅ | ✅ | ❌ | ❌ | ⭐⭐ |
| DCL | ✅ | ✅ | ❌ | ❌ | ⭐⭐⭐⭐ |
| 静态内部类 | ✅ | ✅ | ❌ | ❌ | ⭐⭐⭐⭐⭐ |
| 枚举 | ✅ | ❌ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |

---

### 三、各实现详解

#### 1. 饿汉式（Eager Initialization）

**原理**：类加载时就创建实例，利用类加载机制保证线程安全。

**优点**：简单，线程安全（JVM 保证类加载过程是线程安全的）  
**缺点**：非懒加载，如果实例创建开销大且不一定会被使用，会浪费资源

```java
public class EagerSingleton {
    // 类加载时创建
    private static final EagerSingleton INSTANCE = new EagerSingleton();

    private EagerSingleton() {}

    public static EagerSingleton getInstance() {
        return INSTANCE;
    }
}
```

```typescript
// TypeScript 饿汉式
class EagerSingleton {
    private static readonly INSTANCE = new EagerSingleton();

    private constructor() {}

    static getInstance(): EagerSingleton {
        return this.INSTANCE;
    }
}
```

#### 2. 懒汉式 — 同步方法（Synchronized Method）

**原理**：第一次调用时才创建，使用 `synchronized` 保证线程安全。

**优点**：懒加载  
**缺点**：每次调用都加锁，并发性能差

```java
public class LazySingleton {
    private static LazySingleton instance;

    private LazySingleton() {}

    public static synchronized LazySingleton getInstance() {
        if (instance == null) {
            instance = new LazySingleton();
        }
        return instance;
    }
}
```

#### 3. 双重校验锁（Double-Checked Locking, DCL）⭐

**原理**：两次检查 `instance == null`，只在第一次创建时加锁。使用 `volatile` 防止指令重排。

**为什么需要 `volatile`**：
`instance = new Singleton()` 在 JVM 中不是原子操作，分为三步：
1. 分配内存空间
2. 初始化对象
3. 将引用指向分配的内存

JVM 可能将步骤 2 和 3 重排，使得其他线程可能拿到一个未完全初始化的对象。`volatile` 禁止指令重排。

**优点**：懒加载 + 高性能并发  
**缺点**：代码复杂，JDK 5 之前 `volatile` 语义不完善

```java
public class DCLSingleton {
    // volatile 禁止指令重排
    private static volatile DCLSingleton instance;

    private DCLSingleton() {}

    public static DCLSingleton getInstance() {
        if (instance == null) {               // 第一次检查（无锁，性能高）
            synchronized (DCLSingleton.class) {
                if (instance == null) {       // 第二次检查（有锁，确保只创建一次）
                    instance = new DCLSingleton();
                }
            }
        }
        return instance;
    }
}
```

```typescript
// TypeScript：JS 是单线程语言，无需考虑线程安全问题
// 但在 Node.js 多线程(worker_threads)中需要注意
class DCLSingleton {
    private static instance: DCLSingleton;

    private constructor() {}

    static getInstance(): DCLSingleton {
        if (!DCLSingleton.instance) {
            DCLSingleton.instance = new DCLSingleton();
        }
        return DCLSingleton.instance;
    }
}
```

#### 4. 静态内部类（Static Inner Class）⭐⭐

**原理**：利用类加载机制——外部类加载时内部类不会被加载，第一次调用 `getInstance()` 时才加载内部类并创建实例。

**优点**：线程安全（JVM 保证）、懒加载、无锁、代码简洁  
**这是 Java 中最推荐的传统单例写法**

```java
public class InnerClassSingleton {
    private InnerClassSingleton() {}

    // 静态内部类在首次被引用时才加载
    private static class Holder {
        private static final InnerClassSingleton INSTANCE = new InnerClassSingleton();
    }

    public static InnerClassSingleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

#### 5. 枚举实现（Enum）⭐⭐

**原理**：Java 枚举在 JVM 层面保证只有一个实例，且天然防反射攻击和序列化破坏。

**这是《Effective Java》作者 Josh Bloch 推荐的方式**

```java
public enum EnumSingleton {
    INSTANCE;

    // 可以添加方法和字段
    private String config;

    public void doSomething() {
        System.out.println("执行单例操作");
    }

    public void setConfig(String config) {
        this.config = config;
    }

    public String getConfig() {
        return config;
    }
}

// 使用
EnumSingleton.INSTANCE.doSomething();
```

```typescript
// TypeScript 枚举版
enum EnumSingleton {
    INSTANCE = "INSTANCE"
}

class SingletonService {
    private static instance: SingletonService;

    private constructor() {}

    getInstance(): SingletonService {
        if (!SingletonService.instance) {
            SingletonService.instance = new SingletonService();
        }
        return SingletonService.instance;
    }
}
```

### 四、破坏单例的方式与防御

**1. 反射攻击**：
```java
// 通过反射强行创建新实例
Constructor<DCLSingleton> c = DCLSingleton.class.getDeclaredConstructor();
c.setAccessible(true);
DCLSingleton newInstance = c.newInstance();  // 破坏了单例!
```

**防御**：在构造方法中判断实例是否已存在，如果存在则抛异常（但无法防御反射修改 `instance` 字段）。枚举天然免疫反射攻击（`newInstance()` 会抛异常）。

**2. 序列化破坏**：
反序列化时会创建新对象，破坏单例。

**防御**：添加 `readResolve()` 方法返回已有实例：
```java
private Object readResolve() {
    return getInstance();
}
```
枚举同样天然免疫。

### 五、Spring 中的单例

Spring 容器管理的 Bean 默认是单例的（Singleton Scope），但与传统的单例模式不同：
- Spring 的单例是**容器级别的单例**（同一个 `ApplicationContext` 中唯一）
- 使用 ConcurrentHashMap 管理，通过 Bean 名称区分
- 可以通过 `@Scope("prototype")` 改为多例

## 总结
饿汉式最简单但非懒加载，DCL 兼顾性能和懒加载但代码复杂，静态内部类是最推荐的传统写法，枚举实现是防反射/防序列化的终极方案。选择时优先考虑枚举，其次是静态内部类，最后是 DCL。
