# 题目：不可变对象

## 问题
什么是不可变对象（Immutable Object）？Java 中的 `String` 为什么设计为不可变？如何设计一个不可变类？结合实际场景说明不可变对象的优缺点。

## 考点
- 不可变对象的定义与意义
- Java String 的不可变性原理（常量池、安全性、哈希缓存）
- 不可变类的设计规则
- 不可变对象与线程安全的关系
- 防御性拷贝（Defensive Copy）

## 解答

### 一、不可变对象的定义

**不可变对象**：对象创建后，其内部状态（所有字段的值）在整个生命周期中不可改变。

**常见不可变类**：
- Java：`String`、`Integer`、`BigDecimal`、`LocalDate`
- 集合：`Collections.unmodifiableList()`
- 函数式编程中的值对象

---

### 二、Java `String` 为什么不可变

**1. 字符串常量池（String Pool）**

字符串是使用最频繁的类型，JVM 设计了字符串常量池来节省内存。如果 `String` 可变，一个引用修改了字符串内容，所有指向该常量的引用都会受到影响。

```java
String s1 = "hello";
String s2 = "hello";  // 复用常量池中的同一个对象

// 如果 String 可变：
// 修改 s1 时 s2 也会被修改，这是灾难性的
```

**2. 哈希码缓存**

`String` 作为 `HashMap` 的 key 非常常见。因为不可变，哈希码可以在第一次计算后缓存，后续直接返回，大幅提升性能。

```java
// String 源码（简化）
public final class String {
    private int hash; // 缓存哈希码，默认为 0

    public int hashCode() {
        int h = hash;
        if (h == 0 && value.length > 0) {
            // 只计算一次
            h = /* 计算哈希值 */;
            hash = h;
        }
        return h;
    }
}
```

**3. 安全性**

如果 `String` 可变，以下场景会出现严重安全漏洞：
- 类加载器加载类名被篡改
- 数据库 URL / 用户名 / 密码被修改
- 网络连接参数在验证后被恶意修改
- 反射访问控制失效

**4. 线程安全**

不可变对象天然线程安全，无需同步即可在多线程间安全共享。这比使用锁或 `synchronized` 高效得多。

**5. `String` 的"修改"其实是创建新对象**

```java
String s = "Hello";
s = s + " World";  // 不是修改原对象，而是创建了新的 String 对象
// 原来的 "Hello" 对象仍然存在于常量池中
```

---

### 三、如何设计不可变类

**五条规则**：

1. **声明类为 `final`** —— 防止子类化修改行为
2. **所有字段为 `private final`** —— 确保字段不被外部修改，且在构造后不会重新赋值
3. **不提供 setter 方法** —— 只暴露 getter，不暴露修改入口
4. **如果字段是引用类型** —— 在构造方法和 getter 中做防御性拷贝（Defensive Copy），防止外部持有引用后修改
5. **所有修改方法返回新对象** —— 如 `String.concat()`、`BigDecimal.add()` 返回新实例

```java
// ====== 不可变类示例 ======
public final class ImmutablePerson {
    private final String name;
    private final int age;
    private final Date birthday;        // 可变对象！
    private final List<String> hobbies; // 可变集合！

    public ImmutablePerson(String name, int age, Date birthday, List<String> hobbies) {
        this.name = name;
        this.age = age;
        // 防御性拷贝：即使调用方持有原引用并修改，也不影响本对象
        this.birthday = new Date(birthday.getTime());
        this.hobbies = new ArrayList<>(hobbies);
    }

    public String getName() { return name; }

    public int getAge() { return age; }

    public Date getBirthday() {
        // 返回拷贝而非原对象
        return new Date(birthday.getTime());
    }

    public List<String> getHobbies() {
        // 返回不可修改的视图或拷贝
        return Collections.unmodifiableList(new ArrayList<>(hobbies));
    }

    // "修改"方法返回新对象
    public ImmutablePerson withName(String newName) {
        return new ImmutablePerson(newName, this.age, this.birthday, this.hobbies);
    }

    public ImmutablePerson withAge(int newAge) {
        return new ImmutablePerson(this.name, newAge, this.birthday, this.hobbies);
    }
}
```

**现代替代方案**：Java 14+ 的 `record` 类型自动生成不可变的数据载体：

```java
// Record 自动生成：
//   private final 字段
//   全参构造器
//   各字段的 getter（方法名同字段名）
//   equals() / hashCode() / toString()
public record Person(String name, int age) {}

// 注意：Record 对引用类型字段不会自动做防御性拷贝
public record Person(String name, List<String> hobbies) {
    // 需要手动写紧凑构造器做防御性拷贝
    public Person {
        hobbies = List.copyOf(hobbies);  // 不可变副本
    }
}
```

```typescript
// ====== TypeScript 不可变类 ======
class ImmutablePerson {
    constructor(
        public readonly name: string,
        public readonly age: number,
        public readonly hobbies: readonly string[]  // readonly 数组
    ) {}

    // "修改"方法返回新对象
    withName(newName: string): ImmutablePerson {
        return new ImmutablePerson(newName, this.age, this.hobbies);
    }

    withAge(newAge: number): ImmutablePerson {
        return new ImmutablePerson(this.name, newAge, this.hobbies);
    }
}

// 更推荐：直接用普通对象 + `as const` + `Readonly` 类型
const person = {
    name: "张三",
    age: 30,
    hobbies: ["读书", "游泳"]
} as const;

// 或者使用 Readonly 工具类型
interface ReadonlyPerson {
    readonly name: string;
    readonly age: number;
    readonly hobbies: readonly string[];
}

// Immmer.js / Immutable.js 在复杂场景下是更好的选择
```

---

### 四、不可变对象的优缺点

**优点**：

| 优点 | 说明 |
|------|------|
| 线程安全 | 无状态变更，多线程共享无需同步 |
| 简单性 | 创建后可放心传递，不用追踪状态变化 |
| 失败原性 | 不会出现"一半修改"的不一致状态 |
| 适用作 Map 的 key | 哈希码不变，不会因状态变化导致定位丢失 |
| 缓存友好 | 可放心缓存复用 |

**缺点**：

| 缺点 | 说明 |
|------|------|
| 内存开销 | 每次"修改"都创建新对象，频繁修改时 GC 压力大 |
| 性能问题 | 适合读多写少的场景，高频写场景不适用 |

**折中方案**：
- 对频繁修改的字符串，`StringBuilder` / `StringBuffer` 提供可变缓冲
- `String.intern()` 复用常量池对象
- 适当场合使用可变对象 + 锁机制

---

### 五、不可变对象的应用场景

| 场景 | 说明 |
|------|------|
| 值对象（Value Object） | 如 `Money`、`PhoneNumber`、`Address` |
| 配置对象 | 系统配置在运行时不应改变 |
| 缓存 key | HashMap / HashSet 的 key |
| 函数式编程 | 数据不可变是函数式编程的基础 |
| 事件/消息 | 事件对象创建后不应被后续逻辑修改 |
| 多线程共享数据 | 无需加锁的数据共享 |

## 总结
不可变对象创建后状态不变，天然线程安全、可缓存复用、适合做 Map key。设计不可变类的五条核心规则是：final class、private final 字段、无 setter、防御性拷贝、修改返回新对象。Java 的 `String` 设计为不可变正是因为常量池、哈希缓存和安全性的综合考量。
