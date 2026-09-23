// ============================================================
// TypeScript 基础语法 04：联合类型 / 交叉类型 / 字面量类型 / as const
// 运行：npx tsx typescript/04-union-intersection-literal.ts
// ============================================================

// ---------- 1. 联合类型（union）：A | B，值可以是 A 或 B ----------
let status: "paid" | "pending" | "cancelled"; // 字面量联合
status = "paid";
// status = "shipped"; // 报错：不在联合中

let id: string | number = 1;
id = "abc"; // 合法

// 联合类型的数组
let arr: (string | number)[] = [1, "two", 3];

// ---------- 2. 交叉类型（intersection）：A & B，同时满足 A 和 B ----------
interface HasId { id: number }
interface HasTime { createdAt: Date }
type Auditable = HasId & HasTime; // 同时有 id 和 createdAt

const record: Auditable = { id: 1, createdAt: new Date() };

// 对象合并
interface A { a: string }
interface B { b: number }
type AB = A & B; // { a: string; b: number }

// ---------- 3. 字面量类型 ----------
// 变量只能取某个具体的字面量值
let direction: "up" | "down" | "left" | "right" = "up";
let size: 1 | 2 | 3 = 2;

// 字符串字面量 vs 数字字面量
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
function request(url: string, method: HttpMethod): void {
  console.log(method, url);
}
request("/api", "GET");

// ---------- 4. as const：把值“冻结”为字面量类型 ----------
// 普通对象会被“拓宽”为宽类型
const obj1 = { theme: "dark", retries: 3 };
// obj1.theme 是 string，obj1.retries 是 number

// as const 保留精确字面量，并设为只读
const obj2 = { theme: "dark", retries: 3 } as const;
// obj2.theme 是 "dark"，obj2.retries 是 3
// obj2.theme = "light"; // 报错：只读

// 数组 as const 变成只读元组
const sizes = ["S", "M", "L"] as const;
// sizes 是 readonly ["S", "M", "L"]
type Size = (typeof sizes)[number]; // "S" | "M" | "L"

// ---------- 5. 用 as const 对象代替 enum（推荐实践） ----------
const OrderStatus = {
  PAID: "paid",
  PENDING: "pending",
  CANCELLED: "cancelled",
} as const;
type OrderStatusType = (typeof OrderStatus)[keyof typeof OrderStatus];
// => "paid" | "pending" | "cancelled"

function setStatus(s: OrderStatusType): void {
  console.log(s);
}
setStatus(OrderStatus.PAID);

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：声明一个变量，类型为 "apple" | "banana" | "orange"，并赋值为 "banana"。
// let fruit: /* 你的代码 */ = "banana";

// TODO 2：定义交叉类型 T = {a:number} & {b:string}，并创建满足它的对象。
// type T = /* 你的代码 */;
// const t: T = /* 你的代码 */;

// TODO 3：用 as const 定义一个颜色对象，并导出它的值类型联合。
// const Theme = /* 你的代码 */;
// type ThemeValue = /* 你的代码 */;

export {};
