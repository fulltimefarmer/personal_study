// ============================================================
// TypeScript 基础语法 06：函数
// 运行：npx tsx 06-functions.ts
// ============================================================

// ---------- 1. 函数声明（给参数和返回值都标注类型） ----------
function add(a: number, b: number): number {
  return a + b;
}

// 无返回值时标注 void
function greet(name: string): void {
  console.log("你好，" + name);
}

// ---------- 2. 函数表达式 ----------
const multiply = function (a: number, b: number): number {
  return a * b;
};

// ---------- 3. 箭头函数（最常用） ----------
// 语法：(参数) => 返回值。只有一个参数可省略括号；函数体只有一行可省略大括号和 return。
const square = (x: number): number => x * x;
const sayHi = (name: string) => "Hi, " + name; // 返回类型可自动推断

// ---------- 4. 可选参数（用 ? 标注，调用时可不传） ----------
function fullName(first: string, last?: string): string {
  return last ? first + " " + last : first;
}

// ---------- 5. 默认参数（不传时使用默认值） ----------
function power(base: number, exp: number = 2): number {
  return base ** exp;
}

// ---------- 6. 剩余参数（... 把多个参数收集成一个数组） ----------
function sumAll(...nums: number[]): number {
  return nums.reduce((acc, n) => acc + n, 0);
}

// ---------- 7. 函数重载（同名函数多套签名） ----------
// 声明多套签名，最后实现一份通用逻辑。
function combine(a: number, b: number): number;
function combine(a: string, b: string): string;
function combine(a: unknown, b: unknown): unknown {
  if (typeof a === "number" && typeof b === "number") return a + b;
  if (typeof a === "string" && typeof b === "string") return a + b;
  return "";
}

// ---------- 8. 回调函数（把函数作为参数传入） ----------
function operate(a: number, b: number, fn: (x: number, y: number) => number): number {
  return fn(a, b);
}

// ---------- 9. 函数类型别名（用 type 描述函数签名） ----------
type MathFn = (a: number, b: number) => number;
const divide: MathFn = (a, b) => a / b;

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("函数声明 add", add(1, 2), 3);
verify("函数表达式 multiply", multiply(3, 4), 12);
verify("箭头函数 square", square(5), 25);
verify("箭头函数 sayHi", sayHi("Tom"), "Hi, Tom");
verify("可选参数(不传)", fullName("张三"), "张三");
verify("可选参数(传入)", fullName("张", "三"), "张 三");
verify("默认参数(不传)", power(3), 9);
verify("默认参数(传入)", power(2, 3), 8);
verify("剩余参数求和", sumAll(1, 2, 3, 4, 5), 15);
verify("函数重载(数字)", combine(1, 2), 3);
verify("函数重载(字符串)", combine("a", "b"), "ab");
verify("回调函数", operate(10, 2, (a, b) => a - b), 8);
verify("函数类型别名", divide(10, 2), 5);

export {}; // 让本文件成为模块，避免全局变量冲突
