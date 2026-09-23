// ============================================================
// TypeScript 基础语法 10：模块导入导出 / enum vs as const / 类型断言 / 非空断言
// 运行：npx tsx typescript/10-modules-enum-decorators.ts
// ============================================================

// ---------- 1. 模块导入导出（ESM） ----------
// 导出：export / export default
// 导入：import { x } from './x'；import def from './x'
// 类型也可以导入：import type { Foo } from './x'
export const API_BASE = "https://api.example.com";
export interface ApiConfig { baseUrl: string; timeout: number }
export default function init(cfg: ApiConfig): void {
  console.log("init", cfg);
}

// 导入示例（取消注释后，需存在对应模块）：
// import init, { API_BASE, type ApiConfig } from "./some-module";

// 命名空间导入 / 重命名
// import * as utils from "./utils";
// import { foo as bar } from "./utils";

// ---------- 2. enum 与 as const 对象 ----------
// enum：生成运行时代码，数字枚举有反向映射
enum Direction {
  Up,      // 0
  Down,    // 1
  Left,    // 2
  Right,   // 3
}
console.log(Direction.Up);          // 0
console.log(Direction[0]);          // "Up"（反向映射）

// 字符串枚举
enum Color {
  Red = "red",
  Green = "green",
}

// 现代实践：用 as const 对象代替 enum（更可预测、可 tree-shake）
const Status = {
  ACTIVE: "active",
  INACTIVE: "inactive",
} as const;
type StatusType = (typeof Status)[keyof typeof Status];

// ---------- 3. 类型断言（as）与尖括号语法 ----------
const someValue: unknown = "hello";
const length = (someValue as string).length; // as 断言
// const length2 = (<string>someValue).length; // 尖括号语法（TSX 中不能用）

// 双重断言（危险，尽量不用）：unknown -> 任意类型
const risky = someValue as unknown as number;

// ---------- 4. 非空断言（!） ----------
// 告诉 TS“这个值一定不是 null/undefined”，运行时仍可能出错
function getName(): string | null { return "Alice"; }
const name: string = getName()!; // 断言非空
// 可选属性/链式调用中的非空断言
interface Config { user?: { id?: number } }
function getId(c: Config): number {
  return c.user!.id!; // 断言 user 和 id 都存在
}

// 更安全：用可选链 ?. 和空值合并 ??
function getIdSafe(c: Config): number {
  return c.user?.id ?? -1; // 空则返回 -1
}

// ---------- 5. 可选链（?.）与空值合并（??） ----------
const user = { address: { city: "Shanghai" } as { city: string } | undefined };
const city = user.address?.city; // 若 address 为 undefined 则结果是 undefined
const cityOrUnknown = user.address?.city ?? "Unknown"; // 兜底

// ?? 与 || 的区别：?? 只在 null/undefined 时兜底，|| 在 falsy 时兜底
const zero = 0;
const a = zero ?? 1; // 0（?? 不把 0 当空）
const b = zero || 1; // 1（|| 把 0 当 falsy）

// ---------- 6. 装饰器（实验性特性，NestJS/Angular 大量使用） ----------
// 类装饰器、方法装饰器等，配合 reflect-metadata 注入元数据
function Log(target: any, key: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`[Log] 调用 ${key}(${args.join(", ")})`);
    return original.apply(this, args);
  };
}
class Calculator {
  @Log
  add(a: number, b: number): number { return a + b; }
}
// new Calculator().add(1, 2); // 会打印日志

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：用 as const 定义一个角色对象，并导出其值类型联合。
// const Role = /* 你的代码 */;
// type RoleType = /* 你的代码 */;

// TODO 2：写一个函数，参数可能是 string | null，用 ?. 或 ?? 安全返回长度。
// function safeLength(s: string | null): number { /* 你的代码 */ }

export { init };
