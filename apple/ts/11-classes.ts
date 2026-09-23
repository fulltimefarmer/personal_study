// ============================================================
// TypeScript 基础语法 11：类（Classes）
// 运行：npx tsx 11-classes.ts
// ============================================================

// ---------- 1. 基本类：属性 + 构造器 + 方法 ----------
class Person {
  name: string; // 属性声明（必须显式标注类型）
  age: number;

  constructor(name: string, age: number) {
    this.name = name; // this 指向当前实例
    this.age = age;
  }

  introduce(): string {
    return `我叫${this.name}，今年${this.age}岁`;
  }
}

// ---------- 2. 访问修饰符：public / private / protected / readonly ----------
class Account {
  public username: string; // public 公开（默认就是 public，可省略）
  private password: string; // private 私有：只能在类内部访问
  protected role: string; // protected 受保护：类内部和子类可访问
  readonly id: number; // readonly 只读：只能在声明或构造器里赋值

  constructor(username: string, password: string, role: string, id: number) {
    this.username = username;
    this.password = password;
    this.role = role;
    this.id = id;
  }

  checkPassword(pwd: string): boolean {
    return this.password === pwd; // 私有成员可在类内部访问
  }
}
// const acc = new Account("a", "b", "c", 1);
// acc.password; // ❌ 报错：私有属性不可在外部访问

// ---------- 3. 参数属性（简写）：构造器参数前加修饰符自动成为属性 ----------
class Point {
  // 直接写在构造器参数上，自动声明并赋值，无需单独声明属性。
  constructor(public x: number, public y: number) {}
}

// ---------- 4. 继承 extends + super ----------
class Animal {
  constructor(public name: string) {}
  makeSound(): string {
    return "一些声音";
  }
}
class Cat extends Animal {
  constructor(name: string) {
    super(name); // 必须调用父类构造器
  }
  makeSound(): string {
    return "喵"; // 重写（override）父类方法
  }
}

// ---------- 5. 抽象类 abstract：不能实例化，只能被继承 ----------
abstract class Shape {
  abstract area(): number; // 抽象方法：子类必须实现
  describe(): string {
    return "这是一个形状，面积：" + this.area();
  }
}
class Circle extends Shape {
  constructor(public radius: number) {
    super();
  }
  area(): number {
    return Math.PI * this.radius ** 2;
  }
}

// ---------- 6. getter / setter：像属性一样访问，内部可加逻辑 ----------
class Temperature {
  private _celsius = 0;
  get celsius(): number {
    return this._celsius;
  }
  set celsius(v: number) {
    this._celsius = v;
  }
  get fahrenheit(): number {
    return this._celsius * 9 / 5 + 32;
  }
}

// ---------- 7. 静态成员 static：属于类本身，不靠实例 ----------
class MathUtil {
  static PI = 3.14159; // 静态属性
  static square(n: number): number {
    return n * n;
  }
}

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

const p = new Person("小明", 18);
verify("类的方法 introduce", p.introduce(), "我叫小明，今年18岁");

const acc = new Account("admin", "123456", "root", 1);
verify("私有成员通过方法访问", acc.checkPassword("123456"), true);
verify("readonly 属性", acc.id, 1);

const pt = new Point(3, 4);
verify("参数属性 x", pt.x, 3);
verify("参数属性 y", pt.y, 4);

const cat = new Cat("咪咪");
verify("继承的 name", cat.name, "咪咪");
verify("重写的方法", cat.makeSound(), "喵");

const circle = new Circle(2);
verify("抽象类 describe", circle.describe().startsWith("这是一个形状"), true);
verify("抽象方法实现", Math.round(circle.area()), Math.round(Math.PI * 4));

const t = new Temperature();
t.celsius = 100;
verify("getter 摄氏", t.celsius, 100);
verify("getter 华氏", t.fahrenheit, 212);

verify("静态属性", MathUtil.PI, 3.14159);
verify("静态方法", MathUtil.square(5), 25);

export {}; // 让本文件成为模块，避免全局变量冲突
