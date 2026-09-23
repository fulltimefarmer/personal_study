// ============================================================
// TypeScript 基础语法 01：基础类型 与 类型推断
// 运行：npx tsx 01-basic-types.ts
// ============================================================

// ---------- 1. 基本类型注解 ----------
// 语法：let 变量名: 类型 = 值。冒号后面的「类型」就是类型注解。
let name: string = "Apple Store"; // 字符串：用单引号或双引号包裹
let age: number = 30;             // 数字：整数、浮点数、负数统称 number
let price: number = 99.9;         // 浮点数也是 number
let isPro: boolean = true;        // 布尔：只有 true / false
let nothing: null = null;         // null：表示「空值」
let undef: undefined = undefined; // undefined：表示「未定义」
let big: bigint = 100n;           // 大整数：字面量末尾加 n，可表示超大整数
let sym: symbol = Symbol("id");   // 符号：永远唯一的标识值

// ---------- 2. 类型推断 ----------
// 不写类型注解时，TS 会根据初始值自动推断类型。
let inferredString = "hello"; // 自动推断为 string
// inferredString = 123;      // ❌ 报错：number 不能赋给 string

let inferredNumber = 42; // 自动推断为 number

// ---------- 3. any / unknown / never / void ----------
// any：关闭类型检查，任何值都能赋值，任何方法都能调用（危险，尽量少用）。
let anything: any = 123;
anything = "now a string"; // 合法
// anything.随便调用.任何方法(); // 合法（但运行时可能崩溃，因此不真正执行）

// unknown：类型安全的「任意值」。用之前必须先「收窄」类型。
let unknownVal: unknown = 42;
// unknownVal.toFixed(2); // ❌ 报错：unknown 不能直接调用方法
if (typeof unknownVal === "number") {
  unknownVal.toFixed(2); // ✅ 收窄成 number 后可以调用
}

// void：函数没有返回值。
function log(msg: string): void {
  console.log(msg);
}

// never：函数永远不会正常返回（抛异常或死循环），或表示不可能出现的值。
function fail(msg: string): never {
  throw new Error(msg);
}

// ============================================================
// 验证方法：运行后对比「期望值」和「实际值」。
// ============================================================

// 内置的简易断言函数：用 JSON 序列化比较两个值是否相等。
function verify(label: string, actual: unknown, expected: unknown): void {
  // bigint 无法被 JSON.stringify 序列化，先转成字符串再比较。
  const a = typeof actual === "bigint" ? `${actual}n` : actual;
  const e = typeof expected === "bigint" ? `${expected}n` : expected;
  const pass = JSON.stringify(a) === JSON.stringify(e);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(e)} 实际=${JSON.stringify(a)}`
  );
}

verify("name 是字符串", name, "Apple Store");
verify("age 是数字", age, 30);
verify("price 是数字", price, 99.9);
verify("isPro 是布尔", isPro, true);
verify("big 是大整数", big, 100n);
verify("类型推断 string", inferredString, "hello");
verify("类型推断 number", inferredNumber, 42);
verify("unknown 收窄后取整", typeof unknownVal, "number");

export {}; // 让本文件成为模块，避免全局变量冲突
