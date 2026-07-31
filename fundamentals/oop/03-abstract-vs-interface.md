# 题目：抽象类与接口的区别

## 问题
请详细说明抽象类（Abstract Class）和接口（Interface）的区别，结合 Java 和 TypeScript 中的具体差异进行阐述。什么时候应该使用抽象类？什么时候应该使用接口？

## 考点
- 抽象类与接口的设计意图
- Java 8+ 接口的 default 方法对差异的影响
- TypeScript 中抽象类与接口的差异
- "is-a" 与 "can-do" 的设计哲学

## 解答

### 一、核心区别对照表（Java）

| 对比维度 | 抽象类 (Abstract Class) | 接口 (Interface) |
|---------|------------------------|-------------------|
| 关键字 | `abstract class` | `interface` |
| 实例化 | 不能实例化 | 不能实例化 |
| 构造方法 | 有构造方法（供子类调用） | 没有构造方法（Java 8+ 也没有） |
| 方法实现 | 可以有抽象方法和具体方法 | Java 8+ 可有 `default`/`static` 方法；Java 9+ 可有 `private` 方法 |
| 字段 | 可以有实例变量（任意修饰符） | 只能有常量（`public static final`），不能有实例变量 |
| 访问修饰符 | 方法可以用任意访问修饰符 | 方法默认 `public`（Java 9+ 支持 `private`） |
| 继承/实现 | 单继承（一个类只能继承一个抽象类） | 多实现（一个类可以实现多个接口） |
| 设计意图 | "is-a" 关系，代码复用，模板方法 | "can-do" 契约，行为抽象 |
| 版本兼容 | 添加新方法可能破坏子类 | Java 8+ 的 default 方法可以安全添加 |

### 二、TypeScript 中的具体差异

TypeScript 的抽象类和接口与 Java 有关键差异：

| 特性 | TS 抽象类 | TS 接口 |
|------|----------|--------|
| 编译产物 | 编译为 JS 类（有运行时实体） | 编译时擦除（无运行时开销） |
| 属性实现 | 可以声明抽象属性 | 只能声明属性签名 |
| 合并声明 | 不支持 | 支持（同名接口自动合并） |
| 映射类型 | 不能用于映射类型 | 广泛用于类型体操 |

```java
// ============ Java 示例 ============

// 抽象类：模板方法模式
abstract class ReportGenerator {
    // 具体方法（子类共用）
    public void generate() {
        String data = fetchData();   // 子类实现数据获取
        String formatted = format(data); // 子类实现格式化
        export(formatted);           // 父类统一导出逻辑
    }

    protected abstract String fetchData();
    protected abstract String format(String data);

    private void export(String content) {
        System.out.println("导出报告: " + content);
    }
}

class PDFReportGenerator extends ReportGenerator {
    protected String fetchData() { return "PDF 数据"; }
    protected String format(String data) { return "[PDF] " + data; }
}

// 接口：多能力组合
interface Flyable {
    void fly();
    default void takeOff() {  // Java 8+ default 方法
        System.out.println("起飞准备...");
    }
}

interface Swimmable {
    void swim();
}

// 一个类实现多个接口
class Duck implements Flyable, Swimmable {
    public void fly() { System.out.println("鸭子飞行"); }
    public void swim() { System.out.println("鸭子游泳"); }
}

// 同时继承抽象类和实现接口
class PDFReport extends ReportGenerator implements Flyable {
    protected String fetchData() { return "数据"; }
    protected String format(String d) { return d; }
    public void fly() { System.out.println("PDF 报告飞走了"); }
}
```

```typescript
// ============ TypeScript 示例 ============

// 抽象类
abstract class ReportGenerator {
    generate(): void {
        const data = this.fetchData();
        const formatted = this.format(data);
        this.export(formatted);
    }

    protected abstract fetchData(): string;
    protected abstract format(data: string): string;

    private export(content: string): void {
        console.log(`导出报告: ${content}`);
    }
}

class PDFReportGenerator extends ReportGenerator {
    protected fetchData(): string { return "PDF 数据"; }
    protected format(data: string): string { return `[PDF] ${data}`; }
}

// 接口
interface Flyable {
    fly(): void;
    takeOff?(): void;  // 可选方法
}

interface Swimmable {
    swim(): void;
}

class Duck implements Flyable, Swimmable {
    fly(): void { console.log("鸭子飞行"); }
    swim(): void { console.log("鸭子游泳"); }
}
```

### 三、使用场景选择指南

**优先使用接口**：
- 定义跨多个不相关类的行为契约（如 `Comparable`、`Serializable`）
- 希望支持多重继承语义
- 设计 API 时希望保留灵活扩展能力
- TypeScript 中做类型体操（泛型约束、映射类型等）

**优先使用抽象类**：
- 多个相关类之间有大量共用代码需要复用
- 需要定义非 `public static final` 的成员变量
- 模板方法模式（定义算法骨架，子类填充细节）
- 希望控制子类的构造过程（通过构造方法）
- 需要受保护的方法（`protected`），不希望对外暴露

**总结口诀**：
- **接口**：强调"能做什么"（行为能力），跨继承层次
- **抽象类**：强调"是什么"（本质归属），在继承体系内

### 四、常见面试追问

**Q: Java 8 的 default 方法让接口和抽象类几乎没区别了？**
A: 不完全是。接口依然不能有实例字段和构造方法，不能维护对象状态。default 方法无法被子类直接访问内部的 `private` 状态（Java 9+ 接口可有 private 方法，但仍无实例字段）。接口的设计哲学仍是行为契约，抽象类是代码复用。

**Q: 什么时候同时使用抽象类和接口？**
A: 抽象类提供默认实现骨架，接口定义行为契约。例如 Java 集合框架中：`AbstractList`（抽象类，提供公共实现）+ `List`（接口，定义契约）。

## 总结
抽象类用于"是什么"的继承树中的代码复用，接口用于"能做什么"的跨继承层次行为契约。Java 8+ 和 TypeScript 都模糊了二者的边界，但核心设计哲学不变：优先用接口定义契约，必要时用抽象类共享实现。
