// ============================================================
// TypeScript 基础语法 10：泛型（Generics）
// 运行：npx tsx 10-generics.ts
// ============================================================

// 泛型：让函数/接口/类可以「接受类型参数」，从而复用逻辑而不丢失类型信息。

// ---------- 1. 泛型函数 ----------
// 语法：函数名<类型参数>(参数: 类型参数)。<T> 是类型占位符。
function identity<T>(value: T): T {
  return value; // 传入什么类型就返回什么类型
}
const s = identity<string>("hello"); // 显式指定 T = string
const n = identity(42); // 自动推断 T = number

// 多个类型参数
function pair<T, U>(a: T, b: U): [T, U] {
  return [a, b];
}

// ---------- 2. 泛型约束 extends：限制 T 必须具备某些属性 ----------
interface HasLength { length: number }
function longest<T extends HasLength>(a: T, b: T): T {
  return a.length >= b.length ? a : b;
}
// longest(1, 2); // ❌ 报错：number 没有 length

// ---------- 3. 泛型数组操作 ----------
function firstElement<T>(arr: T[]): T | undefined {
  return arr[0];
}
function reverseArray<T>(arr: T[]): T[] {
  return [...arr].reverse();
}

// ---------- 4. 泛型接口 ----------
interface Box<T> {
  value: T;
}
const stringBox: Box<string> = { value: "内容" };
const numberBox: Box<number> = { value: 100 };

// ---------- 5. 泛型类 ----------
class Stack<T> {
  private items: T[] = [];
  push(item: T): void {
    this.items.push(item);
  }
  pop(): T | undefined {
    return this.items.pop();
  }
  size(): number {
    return this.items.length;
  }
}

// ---------- 6. 泛型默认值 ----------
interface Config<T = string> {
  data: T;
}
const defaultConfig: Config = { data: "默认是 string" };

// ---------- 7. keyof 与泛型结合：安全地访问对象属性 ----------
function getProp<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
const fruit = { name: "苹果", price: 5, inStock: true };

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("泛型函数显式指定", s, "hello");
verify("泛型函数自动推断", n, 42);
verify("多类型参数", pair("a", 1), ["a", 1]);
verify("泛型约束 longest", longest("ab", "abc"), "abc");
verify("泛型数组 firstElement", firstElement([1, 2, 3]), 1);
verify("泛型数组 reverseArray", reverseArray([1, 2, 3]), [3, 2, 1]);
verify("泛型接口 stringBox", stringBox.value, "内容");
verify("泛型接口 numberBox", numberBox.value, 100);

const stack = new Stack<number>();
stack.push(1);
stack.push(2);
stack.push(3);
verify("泛型类 size", stack.size(), 3);
verify("泛型类 pop", stack.pop(), 3);
verify("泛型类 pop 后 size", stack.size(), 2);

verify("泛型默认值", defaultConfig.data, "默认是 string");
verify("keyof 安全取属性", getProp(fruit, "name"), "苹果");
verify("keyof 取数字属性", getProp(fruit, "price"), 5);

export {}; // 让本文件成为模块，避免全局变量冲突
