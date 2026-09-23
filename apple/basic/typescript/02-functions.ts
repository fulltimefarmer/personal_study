// ============================================================
// TypeScript 基础语法 02：函数类型 / 可选·默认·剩余参数 / 函数重载
// 运行：npx tsx typescript/02-functions.ts
// ============================================================

// ---------- 1. 参数与返回值类型注解 ----------
function add(a: number, b: number): number {
  return a + b;
}
// 返回值可省略（TS 自动推断），但显式写更清晰

// ---------- 2. 可选参数 ----------
// 用 ? 表示可选，可选参数必须在必选参数之后
function greet(name: string, title?: string): string {
  return title ? `${title} ${name}` : name;
}
console.log(greet("Tom"));          // Tom
console.log(greet("Tom", "Dr."));   // Dr. Tom

// ---------- 3. 默认参数 ----------
// 有默认值的参数可视为可选
function createUser(name: string, vip: boolean = false): string {
  return vip ? `${name} (VIP)` : name;
}

// ---------- 4. 剩余参数 ----------
// ...rest 收集剩余参数为数组
function sum(...nums: number[]): number {
  return nums.reduce((acc, n) => acc + n, 0);
}
console.log(sum(1, 2, 3, 4)); // 10

// ---------- 5. 箭头函数 ----------
const multiply = (a: number, b: number): number => a * b;
const double = (a: number) => a * 2; // 单个参数可省略括号

// ---------- 6. 函数类型表达式 ----------
// 用「(参数类型) => 返回类型」描述一个函数类型
type BinaryOp = (a: number, b: number) => number;
const divide: BinaryOp = (a, b) => a / b;

// 函数作为参数（回调）
function applyOp(x: number, y: number, op: BinaryOp): number {
  return op(x, y);
}
console.log(applyOp(10, 5, divide)); // 2

// ---------- 7. 函数重载（overload） ----------
// 同一函数名，多种参数/返回组合。先写“重载签名”，再写“实现签名”。
function format(value: string): string;          // 重载签名 1
function format(value: number): string;          // 重载签名 2
function format(value: string | number): string { // 实现签名（不对外）
  if (typeof value === "string") return `"${value}"`;
  return value.toFixed(2);
}
console.log(format("hi"));  // "hi"
console.log(format(3.14159)); // 3.14

// ---------- 8. this 参数 ----------
// 在函数第一个参数显式声明 this 类型（仅用于类型检查，不影响调用）
interface Card { name: string; price: number }
function getLabel(this: Card): string {
  return `${this.name} - $${this.price}`;
}
const card: Card = { name: "iPhone", price: 999 };
// getLabel.call(card) // 这样调用才正确绑定 this

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个函数，接收可变数量的字符串，用 "-" 连接返回。
// function joinStrings(...parts: string[]): string { /* 你的代码 */ }

// TODO 2：定义一个函数类型 Greet = (name: string, greeting?: string) => string，
//        并实现它：有 greeting 时返回 "greeting, name"，否则返回 name。
type Greet = (name: string, greeting?: string) => string;
// const myGreet: Greet = /* 你的代码 */

// TODO 3：为重载补全：支持 (a: number, b: number) 和 (s: string) 两种调用。
// function calc(a: number, b: number): number;
// function calc(s: string): string;
// function calc(a: number | string, b?: number): number | string { /* 你的代码 */ }

export {};
