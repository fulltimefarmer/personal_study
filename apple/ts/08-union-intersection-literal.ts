// ============================================================
// TypeScript 基础语法 08：联合类型、交叉类型、字面量类型
// 运行：npx tsx 08-union-intersection-literal.ts
// ============================================================

// ---------- 1. 联合类型：一个值可以是「几种类型之一」 ----------
// 语法：类型A | 类型B
type Status = "success" | "error" | "loading"; // 字符串字面量联合
let id: string | number; // id 可以是字符串或数字
id = 123;
id = "abc";

// 用联合类型时，只能访问「共有」的成员。
function printId(v: string | number): string {
  if (typeof v === "string") {
    return v.toUpperCase(); // 收窄后可用 string 方法
  }
  return v.toFixed(2); // 收窄后可用 number 方法
}

// ---------- 2. 字面量类型：值本身就是一个类型 ----------
let direction: "up" | "down" | "left" | "right";
direction = "up";
// direction = "sideways"; // ❌ 报错：不在字面量集合内

let answer: true; // 只能是 true
answer = true;

// ---------- 3. 交叉类型：把多个类型「合并」成一个 ----------
// 语法：类型A & 类型B，必须同时满足所有属性。
interface HasName { name: string }
interface HasAge { age: number }
type Person = HasName & HasAge;
const person: Person = { name: "Bob", age: 30 }; // 两个属性都要有

// ---------- 4. 联合 + 交叉结合使用 ----------
type Admin = { role: "admin"; permissions: string[] };
type Guest = { role: "guest"; session: string };
type AppUser = Admin | Guest; // 联合：二选一

function describeUser(u: AppUser): string {
  if (u.role === "admin") {
    return u.permissions.join(","); // 收窄成 Admin
  }
  return u.session; // 收窄成 Guest
}

// ---------- 5. 可辨识联合（discriminated union） ----------
// 用共同的「字面量」字段（role）区分不同分支。
interface Circle { kind: "circle"; radius: number }
interface Square { kind: "square"; side: number }
type Shape = Circle | Square;

function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;
    case "square": return s.side ** 2;
  }
}

// ---------- 6. 模板字面量类型（字面量类型的进阶用法） ----------
type Size = "small" | "large";
type SizeId = `${Size}-${number}`; // 如 "small-1"、"large-100"
const s1: SizeId = "small-42";

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("联合类型存数字", id, "abc");
verify("联合类型收窄 string", printId("abc"), "ABC");
verify("联合类型收窄 number", printId(1.234), "1.23");
verify("字面量类型", direction, "up");
verify("字面量类型 true", answer, true);
verify("交叉类型合并", person, { name: "Bob", age: 30 });
verify("可辨识联合 admin", describeUser({ role: "admin", permissions: ["read", "write"] }), "read,write");
verify("可辨识联合 guest", describeUser({ role: "guest", session: "s123" }), "s123");
verify("圆的面积", Math.round(area({ kind: "circle", radius: 2 })), Math.round(Math.PI * 4));
verify("正方形面积", area({ kind: "square", side: 4 }), 16);
verify("模板字面量类型", s1, "small-42");

export {}; // 让本文件成为模块，避免全局变量冲突
