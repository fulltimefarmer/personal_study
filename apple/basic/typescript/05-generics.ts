// ============================================================
// TypeScript 基础语法 05：泛型（generics）
// 运行：npx tsx typescript/05-generics.ts
// ============================================================

// ---------- 1. 泛型函数 ----------
// <T> 表示“类型参数”，调用时由实参自动推断（也可显式指定）。
function identity<T>(value: T): T {
  return value;
}
const s = identity<string>("hello"); // 显式指定 T = string
const n = identity(42);              // 自动推断 T = number

// 多个类型参数
function pair<K, V>(key: K, value: V): [K, V] {
  return [key, value];
}
const p = pair("age", 30); // [string, number]

// ---------- 2. 泛型约束（extends） ----------
// 限制 T 必须具有某些属性
interface HasLength { length: number }
function longest<T extends HasLength>(a: T, b: T): T {
  return a.length >= b.length ? a : b;
}
longest("abc", "de");   // string 有 length
longest([1, 2], [3]);   // 数组有 length
// longest(1, 2);        // 报错：number 没有 length

// 用 keyof 约束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
getProperty({ name: "x", age: 1 }, "name"); // OK
// getProperty({ name: "x" }, "age");       // 报错：age 不是键

// ---------- 3. 泛型接口 ----------
interface ApiResponse<T> {
  data: T;
  error: string | null;
}
const userResp: ApiResponse<{ name: string }> = {
  data: { name: "Alice" },
  error: null,
};

// ---------- 4. 泛型类 ----------
class Stack<T> {
  private items: T[] = [];
  push(item: T): void { this.items.push(item); }
  pop(): T | undefined { return this.items.pop(); }
  get size(): number { return this.items.length; }
}
const numStack = new Stack<number>();
numStack.push(1);

// ---------- 5. 泛型默认值 ----------
interface Container<T = string> {
  value: T;
}
const c1: Container = { value: "default" };        // T 默认 string
const c2: Container<number> = { value: 1 };        // 显式 number

// ---------- 6. 泛型 + 箭头函数（.tsx 中注意加逗号 <T,>） ----------
const wrap = <T,>(value: T): T[] => [value]; // 在 .tsx 里写 <T,> 避免与 JSX 冲突

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个泛型函数 first，返回数组第一个元素（或 undefined）。
// function first<T>(arr: T[]): T | undefined { /* 你的代码 */ }

// TODO 2：写一个泛型函数 swap，交换两个元素并返回数组 [T, T]。
// function swap<T>(a: T, b: T): [T, T] { /* 你的代码 */ }

// TODO 3：写一个泛型类 Queue<T>，含 enqueue、dequeue、size。
// class Queue<T> { /* 你的代码 */ }

export {};
