// ============================================================
// TypeScript 基础语法 01：基本类型 / 数组 / 元组 / any·unknown·never·void
// 运行：npx tsx typescript/01-basic-types.ts
// 说明：每一行都用中文注解解释语法，末尾有「练习」区块。
// ============================================================

// ---------- 1. 基本类型注解 ----------
// 语法：let 变量名: 类型 = 值。冒号后是类型注解。
let name: string = "Apple Store Online"; // 字符串
let age: number = 30;                     // 数字（整数、浮点都叫 number）
let isPro: boolean = true;                // 布尔
let nothing: null = null;                 // null
let undef: undefined = undefined;         // undefined
let big: bigint = 100n;                   // 大整数，字面量末尾加 n
let sym: symbol = Symbol("id");           // 符号，唯一值

// 类型推断：不加注解时 TS 会自动推断类型。
let inferred = "hello"; // 推断为 string
// inferred = 123;      // 报错：不能把 number 赋给 string

// ---------- 2. 数组 ----------
let nums: number[] = [1, 2, 3];           // 数字数组
let strs: Array<string> = ["a", "b"];     // 泛型写法，等价
let mixed: (string | number)[] = [1, "a"]; // 联合类型的数组

// ---------- 3. 元组（固定长度、固定类型的数组） ----------
// 每个位置类型不同、长度固定。
let tuple: [string, number] = ["iPhone", 9999];
// tuple[0] 是 string，tuple[1] 是 number
let [productName, price] = tuple; // 解构也保留类型
console.log(productName, price);

// 可选元组元素 与 剩余元素
let optionalTuple: [string, number?] = ["ok"];
let restTuple: [string, ...number[]] = ["scores", 1, 2, 3];

// ---------- 4. any / unknown / never / void ----------
// any：关闭类型检查（危险，尽量少用）
let anything: any = 123;
anything = "now a string";     // 合法
anything.foo.bar();            // 不会报错（运行时可能崩）

// unknown：类型安全的“任意值”，用之前必须收窄
let unknownVal: unknown = 42;
// unknownVal.toFixed();       // 报错：unknown 不能直接调用方法
if (typeof unknownVal === "number") {
  unknownVal.toFixed(2);       // 收窄后合法
}

// void：函数没有返回值
function log(msg: string): void {
  console.log(msg);
}

// never：函数永远不会返回（抛错 / 死循环），或不可能存在的值
function fail(msg: string): never {
  throw new Error(msg);
}
function infiniteLoop(): never {
  while (true) {}
}

// 穷尽性检查：never 用于“不可能的分支”
type Color = "red" | "green" | "blue";
function describe(c: Color): string {
  switch (c) {
    case "red": return "红色";
    case "green": return "绿色";
    case "blue": return "蓝色";
    default: {
      const exhaust: never = c; // 若漏了某个 case，这里会编译报错
      return exhaust;
    }
  }
}

// ============================================================
// 练习：补全下面的 TODO，让代码通过类型检查并正确运行。
// ============================================================

// TODO 1：声明一个数字数组，包含 5 个元素，并打印其长度。
// let myNumbers: number[] = /* 你的代码 */;
let myNumbers: number[] = [1, 2, 3, 4, 5];
console.log(myNumbers.length); // 期望输出 5

// TODO 2：声明一个元组，第一个是 string，第二个是 boolean。
// let myTuple: /* 你的代码 */ = ["done", true];

// TODO 3：写一个函数，参数是 unknown，若它是 string 就返回其大写形式，否则返回 "not a string"。
function upperIfString(value: unknown): string {
  // 你的代码：用 typeof 收窄
  if (typeof value === "string") {
    return value.toUpperCase();
  }
  return "";
}

// TODO 4：写一个返回类型为 never 的函数。
// function crash(): never { /* 你的代码 */ }

// 运行结果（取消注释验证）：
// console.log(upperIfString("hello")); // 期望 HELLO
// console.log(upperIfString(123));     // 期望 not a string

export {}; // 让本文件成为模块，避免全局变量冲突
