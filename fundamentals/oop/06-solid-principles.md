# 题目：SOLID 五大原则

## 问题
请详细阐述面向对象设计的 SOLID 五大原则：单一职责原则（SRP）、开闭原则（OCP）、里氏替换原则（LSP）、接口隔离原则（ISP）、依赖反转原则（DIP）。说明每个原则的核心思想、违反该原则的后果、以及如何遵循该原则。

## 考点
- SOLID 五大原则的核心定义
- 识别违反原则的代码"坏味道"
- 各原则之间的关系与实际应用
- 设计模式如何体现这些原则

## 解答

### 一、SOLID 总览

| 缩写 | 原则 | 核心思想 |
|------|------|---------|
| S | 单一职责原则 (SRP) | 一个类应该只有一个引起它变化的原因 |
| O | 开闭原则 (OCP) | 对扩展开放，对修改关闭 |
| L | 里氏替换原则 (LSP) | 子类对象应该可以替换父类对象而不影响程序正确性 |
| I | 接口隔离原则 (ISP) | 不应强迫客户端依赖它不使用的方法 |
| D | 依赖反转原则 (DIP) | 高层模块不应依赖低层模块，二者都应依赖抽象 |

---

### 二、单一职责原则（SRP）

**定义**：一个类（或模块、方法）应该有且只有一个引起它变化的原因，即只负责一项职责。

**违反后果**：
- 一个职责的变化可能影响其他职责
- 类变得臃肿难以维护
- 代码耦合度高，复用困难

```java
// ❌ 违反 SRP：一个类干了三件事
class Employee {
    void calculatePay() { /* 计算工资 */ }
    void save() { /* 持久化到数据库 */ }
    void generateReport() { /* 生成报表 */ }
}

// ✅ 遵循 SRP：拆分为三个专用类
class PayCalculator {
    void calculatePay(Employee e) { /* 只做工资计算 */ }
}
class EmployeeRepository {
    void save(Employee e) { /* 只做数据持久化 */ }
}
class ReportGenerator {
    void generateReport(Employee e) { /* 只做报表生成 */ }
}
```

```typescript
// ❌ 违反 SRP
class User {
    constructor(public name: string, public email: string) {}
    validate(): boolean { /* 验证 */ }
    save(): void { /* 存库 */ }
    sendEmail(): void { /* 发邮件 */ }
}

// ✅ 遵循 SRP
class User {
    constructor(public name: string, public email: string) {}
}
class UserValidator {
    validate(user: User): boolean { /* 验证 */ return true; }
}
class UserRepository {
    save(user: User): void { /* 存库 */ }
}
class EmailService {
    sendWelcomeEmail(user: User): void { /* 发邮件 */ }
}
```

---

### 三、开闭原则（OCP）

**定义**：软件实体（类、模块、函数等）应该对扩展开放，对修改关闭。即不修改原有代码的情况下增加新功能。

**实现方式**：通过抽象（接口/抽象类）和多态，利用策略模式、装饰器模式、工厂模式等。

```java
// ❌ 违反 OCP：增加新形状需要修改 AreaCalculator
class AreaCalculator {
    double area(Object shape) {
        if (shape instanceof Circle c) {
            return Math.PI * c.radius * c.radius;
        } else if (shape instanceof Rectangle r) {
            return r.width * r.height;
        }
        return 0;
    }
}

// ✅ 遵循 OCP：通过接口扩展
interface Shape {
    double area();
}
class Circle implements Shape {
    double radius;
    public double area() { return Math.PI * radius * radius; }
}
class Rectangle implements Shape {
    double width, height;
    public double area() { return width * height; }
}
class Triangle implements Shape {  // 新增三角形，无需修改现有代码
    double base, height;
    public double area() { return 0.5 * base * height; }
}
```

```typescript
// ✅ TypeScript 遵循 OCP
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

function totalArea(shapes: Shape[]): number {
    return shapes.reduce((sum, s) => sum + s.area(), 0);
}
```

---

### 四、里氏替换原则（LSP）

**定义**：如果 S 是 T 的子类型，那么程序中 T 类型的对象可以用 S 类型的对象替换，而不会改变程序的正确性。

**核心要求**：
1. 子类不能重写父类的非抽象方法并抛出更宽泛的异常
2. 子类的前置条件（入参验证）不能比父类更严格
3. 子类的后置条件（返回值/副作用）不能比父类更弱
4. 子类的不变式（Invariant）必须保持父类的约束

```java
// ❌ 违反 LSP：正方形不是长方形的合理子类
class Rectangle {
    protected int width, height;

    public void setWidth(int w) { width = w; }
    public void setHeight(int h) { height = h; }
    public int area() { return width * height; }
}

class Square extends Rectangle {
    @Override
    public void setWidth(int w) {
        super.setWidth(w);
        super.setHeight(w);  // 破坏父类的预期行为！
    }

    @Override
    public void setHeight(int h) {
        super.setWidth(h);
        super.setHeight(h);
    }
}

// 测试会失败：正方形替换长方形后行为不一致
void test(Rectangle r) {
    r.setWidth(5);
    r.setHeight(10);
    assert r.area() == 50;  // Square 的 area = 100，测试失败
}
```

**经典反例**：鸵鸟（不会飞）继承自鸟（会飞），`bird.fly()` 对鸵鸟来说抛异常是违反 LSP 的。

**解决方案**：
- 重新设计继承关系（如不将 Square 继承 Rectangle）
- 将 `fly()` 拆分为独立接口，只有能飞的鸟才实现

---

### 五、接口隔离原则（ISP）

**定义**：客户端不应该被迫依赖它不使用的方法。接口应该小而专一，而不是大而全。

**核心思想**：
- "胖接口"应该拆分为多个独立的小接口
- 每个接口只包含一组高内聚的方法
- 类似于 SRP 在接口层面的体现

```java
// ❌ 违反 ISP：胖接口
interface Worker {
    void work();
    void eat();
    void sleep();
}

// 机器人不需要 eat() 和 sleep()，但被迫实现
class Robot implements Worker {
    public void work() { /* 正常工作 */ }
    public void eat() { /* 不需要，但必须实现 */ }
    public void sleep() { /* 不需要，但必须实现 */ }
}

// ✅ 遵循 ISP：接口隔离
interface Workable {
    void work();
}

interface Eatable {
    void eat();
}

interface Sleepable {
    void sleep();
}

class Human implements Workable, Eatable, Sleepable {
    public void work() { /* 工作 */ }
    public void eat() { /* 吃饭 */ }
    public void sleep() { /* 睡觉 */ }
}

class Robot implements Workable {
    public void work() { /* 只工作 */ }
}
```

```typescript
// ✅ TypeScript 遵循 ISP
interface Readable {
    read(): string;
}

interface Writable {
    write(data: string): void;
}

interface Deletable {
    delete(): void;
}

// 只读文件只实现 Readable
class ReadOnlyFile implements Readable {
    read(): string { return "file content"; }
}

// 可读写文件实现多个小接口
class FileSystem implements Readable, Writable, Deletable {
    read(): string { return "data"; }
    write(data: string): void { /* write */ }
    delete(): void { /* delete */ }
}
```

---

### 六、依赖反转原则（DIP）

**定义**：
1. 高层模块不应依赖低层模块，二者都应依赖抽象
2. 抽象不应依赖细节，细节应依赖抽象

**核心思想**：倒转传统"高层依赖低层"的依赖方向，让稳定的抽象层成为桥梁。

**实现方式**：依赖注入（DI）、控制反转（IoC）

```java
// ❌ 违反 DIP：高层直接依赖低层具体实现
class MySQLDatabase {
    void save(String data) { /* MySQL 保存 */ }
}

class UserService {
    private MySQLDatabase db = new MySQLDatabase();  // 紧耦合！

    void saveUser(String user) {
        db.save(user);
    }
}

// ✅ 遵循 DIP：依赖抽象
interface Database {
    void save(String data);
}

class MySQLDatabase implements Database {
    public void save(String data) { /* MySQL 实现 */ }
}

class MongoDB implements Database {
    public void save(String data) { /* MongoDB 实现 */ }
}

class UserService {
    private Database db;  // 依赖接口，而非具体类

    public UserService(Database db) {  // 依赖注入
        this.db = db;
    }

    void saveUser(String user) {
        db.save(user);
    }
}
```

```typescript
// ✅ TypeScript 遵循 DIP
interface Database {
    save(data: string): void;
}

class MySQLDatabase implements Database {
    save(data: string): void { /* MySQL 实现 */ }
}

class UserService {
    constructor(private db: Database) {}  // 依赖注入

    saveUser(user: string): void {
        this.db.save(user);
    }
}

// 使用
const service = new UserService(new MySQLDatabase());
```

### 七、SOLID 原则之间的关系

| 原则对 | 关系 |
|--------|------|
| SRP ↔ ISP | SRP 是类的单一职责，ISP 是接口的单一职责——同一思想不同层面 |
| OCP ↔ DIP | DIP 是实现 OCP 的重要手段（通过依赖抽象来支持扩展） |
| LSP ↔ OCP | LSP 是 OCP 的前提——只有子类可替换，扩展才有意义 |
| LSP ↔ ISP | 违反 ISP 的"胖接口"容易导致子类违反 LSP（被迫实现不需要的方法） |

### 八、反模式警示

- **SRP**："上帝类"（God Class）—— 一个类干了所有事
- **OCP**：到处 `if/else instanceof` —— 每次加新类型都要改分支
- **LSP**：子类方法抛 `UnsupportedOperationException` —— 子类不符合父类契约
- **ISP**：接口中大量方法被空实现 —— 胖接口
- **DIP**：`new` 操作符到处使用 —— 紧耦合

## 总结
SOLID 是面向对象设计的五个核心原则：SRP 让类职责清晰，OCP 让系统可扩展，LSP 保证继承体系的正确性，ISP 让接口精细，DIP 让依赖可替换。它们共同指导我们写出高内聚、低耦合、易维护的代码。
