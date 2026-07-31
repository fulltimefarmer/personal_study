# 题目：面向对象的四大特性

## 问题
请阐述面向对象编程（OOP）的四大特性：封装、继承、多态、抽象，并说明各自的用途。

## 考点
- 面向对象基本概念
- 各大特性的设计意图与应用场景
- 对代码可维护性、可扩展性的理解

## 解答

### 1. 封装（Encapsulation）

**定义**：将数据（属性）和操作数据的方法绑定在一起，隐藏内部实现细节，仅暴露必要的访问接口。

**核心手段**：
- 使用 `private` / `protected` 修饰字段，禁止外部直接访问
- 通过 `public` 的 getter/setter 方法控制访问逻辑
- 内部状态变化对外部透明，外部只关心「做什么」而非「怎么做」

**用途**：
- **数据保护**：防止外部代码随意修改内部状态，可在 setter 中加入校验逻辑
- **降低耦合**：修改内部实现时不影响调用方
- **提高可维护性**：职责清晰，便于定位问题

```java
// Java 示例
public class BankAccount {
    private double balance;  // 隐藏内部状态

    public double getBalance() {
        return balance;
    }

    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("金额必须大于0");
        balance += amount;
    }

    public void withdraw(double amount) {
        if (amount > balance) throw new IllegalArgumentException("余额不足");
        balance -= amount;
    }
}
```

```typescript
// TypeScript 示例
class BankAccount {
    private _balance: number = 0;

    get balance(): number {
        return this._balance;
    }

    deposit(amount: number): void {
        if (amount <= 0) throw new Error("金额必须大于0");
        this._balance += amount;
    }

    withdraw(amount: number): void {
        if (amount > this._balance) throw new Error("余额不足");
        this._balance -= amount;
    }
}
```

### 2. 继承（Inheritance）

**定义**：子类继承父类的属性和方法，实现代码复用和「is-a」关系的表达。

**用途**：
- **代码复用**：公共逻辑提取到父类，减少重复代码
- **层次分类**：建立类与类之间的层次结构，表达真实世界的分类关系
- **扩展性**：子类可以重写父类方法，实现差异化行为

**注意事项**：
- 继承破坏封装（子类依赖父类实现细节）
- 单继承（Java） vs 多继承（C++），Java/TS 通过接口实现多继承的替代
- 继承层次不宜过深，一般不超过 3 层

```java
// Java 示例
class Animal {
    protected String name;

    public Animal(String name) { this.name = name; }

    public void eat() {
        System.out.println(name + " is eating");
    }
}

class Dog extends Animal {
    public Dog(String name) { super(name); }

    @Override
    public void eat() {
        System.out.println(name + " is eating dog food");
    }

    public void bark() {
        System.out.println(name + " says woof!");
    }
}
```

```typescript
// TypeScript 示例
class Animal {
    constructor(protected name: string) {}

    eat(): void {
        console.log(`${this.name} is eating`);
    }
}

class Dog extends Animal {
    eat(): void {
        console.log(`${this.name} is eating dog food`);
    }

    bark(): void {
        console.log(`${this.name} says woof!`);
    }
}
```

### 3. 多态（Polymorphism）

**定义**：同一操作作用于不同对象，可以产生不同的行为。即"一个接口，多种实现"。

**两种形式**：
- **编译时多态（静态多态）**：方法重载（Overloading）—— 通过参数列表区分同名方法
- **运行时多态（动态多态）**：方法重写（Overriding）—— 父类引用指向子类对象，运行时动态绑定

**用途**：
- **消除冗长的 if-else / switch**：用设计模式（策略模式等）替代条件分支
- **开闭原则的基石**：对扩展开放，对修改关闭
- **代码灵活性**：编程针对抽象（接口/父类），而非具体实现

```java
// Java 示例
interface Shape {
    double area();
}

class Circle implements Shape {
    private double radius;
    public Circle(double r) { radius = r; }
    public double area() { return Math.PI * radius * radius; }
}

class Rectangle implements Shape {
    private double width, height;
    public Rectangle(double w, double h) { width = w; height = h; }
    public double area() { return width * height; }
}

public class Main {
    public static void printArea(Shape s) {  // 多态：接收 Shape 类型
        System.out.println("面积: " + s.area());
    }
}
```

```typescript
// TypeScript 示例
interface Shape {
    area(): number;
}

class Circle implements Shape {
    constructor(private radius: number) {}
    area(): number { return Math.PI * this.radius ** 2; }
}

class Rectangle implements Shape {
    constructor(private width: number, private height: number) {}
    area(): number { return this.width * this.height; }
}

function printArea(s: Shape): void {
    console.log(`面积: ${s.area()}`);
}
```

### 4. 抽象（Abstraction）

**定义**：提取一类事物的共同特征和行为，忽略非本质的细节，形成更高层次的概念模型。

**手段**：
- **抽象类**：包含抽象方法和具体方法，不能实例化
- **接口**：定义行为契约，不包含实现（Java 8+ 允许 default 方法）

**用途**：
- **简化复杂系统**：使用者只需关注高层接口，不必了解内部实现
- **解耦**：上层模块依赖抽象而非具体实现（依赖倒置原则）
- **统一标准**：定义统一的协议/契约，不同实现可互相替换

```java
// Java 示例
abstract class DatabaseConnector {
    abstract void connect(String url);
    abstract void disconnect();

    // 模板方法：定义算法骨架，具体步骤由子类实现
    public final void executeQuery(String sql) {
        connect("default-url");
        // 执行查询逻辑...
        disconnect();
    }
}

class MySQLConnector extends DatabaseConnector {
    void connect(String url) { /* MySQL 连接逻辑 */ }
    void disconnect() { /* MySQL 断开逻辑 */ }
}
```

```typescript
// TypeScript 示例
abstract class DatabaseConnector {
    abstract connect(url: string): void;
    abstract disconnect(): void;

    executeQuery(sql: string): void {
        this.connect("default-url");
        // 执行查询逻辑...
        this.disconnect();
    }
}

class MySQLConnector extends DatabaseConnector {
    connect(url: string): void { /* MySQL 连接逻辑 */ }
    disconnect(): void { /* MySQL 断开逻辑 */ }
}
```

## 总结
封装隐藏细节，继承复用代码，多态实现灵活，抽象简化系统 —— 四者互相配合，共同构建高内聚、低耦合的面向对象系统。
