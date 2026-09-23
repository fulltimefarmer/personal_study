// ============================================================
// TypeScript 基础语法 09：类 / 访问修饰符 / 继承 / 抽象类 / getter·setter
// 运行：npx tsx typescript/09-classes.ts
// ============================================================

// ---------- 1. 基本类与访问修饰符 ----------
// public（默认）、private（仅类内）、protected（类内 + 子类）、readonly
class Animal {
  public name: string;          // 公开
  private secret: string = "x"; // 私有，仅类内可访问
  protected age: number;        // 受保护，类内 + 子类可访问
  readonly id: number;          // 只读，只能初始化一次

  // 构造函数参数加上修饰符 = 自动声明并赋值（参数属性）
  constructor(name: string, age: number, id: number) {
    this.name = name;
    this.age = age;
    this.id = id;
  }

  // 方法
  speak(): string {
    return `${this.name} speaks`;
  }
}

// 参数属性简写：public/private/protected/readonly 直接写在构造参数里
class Dog extends Animal {
  constructor(name: string, age: number, id: number, public breed: string) {
    super(name, age, id); // 必须调用父类构造函数
    // this.breed 已自动声明并赋值
  }

  // 重写方法
  speak(): string {
    return `${this.name} barks`;
  }

  // 访问父类 protected 成员
  describe(): string {
    return `${this.name} is ${this.age} years old`;
  }
}

// ---------- 2. 抽象类（abstract） ----------
// 抽象类不能被实例化，抽象方法必须由子类实现
abstract class Shape {
  abstract area(): number;      // 抽象方法，无实现
  display(): string {
    return `Area: ${this.area()}`;
  }
}
class Circle extends Shape {
  constructor(private radius: number) { super(); }
  area(): number { return Math.PI * this.radius ** 2; }
}

// ---------- 3. implements（实现接口） ----------
interface Comparable {
  compareTo(other: Comparable): number;
}
class Money implements Comparable {
  constructor(public amount: number) {}
  compareTo(other: Money): number {
    return this.amount - other.amount;
  }
}

// ---------- 4. getter / setter ----------
class Temperature {
  private _celsius = 0;
  get celsius(): number { return this._celsius; }
  set celsius(value: number) {
    if (value < -273.15) throw new Error("低于绝对零度");
    this._celsius = value;
  }
  get fahrenheit(): number { return this._celsius * 9 / 5 + 32; }
}

// ---------- 5. static 静态成员 ----------
class MathUtil {
  static PI = 3.14159;
  static square(x: number): number { return x * x; }
}
MathUtil.square(3); // 直接通过类名调用，无需 new

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个类 Rectangle，含 width、height 两个私有字段，
//         并提供 getter area() 计算面积。
// class Rectangle { /* 你的代码 */ }

// TODO 2：写一个抽象类 Vehicle，抽象方法 start(): string，
//         再写一个 Car 类继承并实现它。
// abstract class Vehicle { abstract start(): string; }
// class Car extends Vehicle { /* 你的代码 */ }

export {};
