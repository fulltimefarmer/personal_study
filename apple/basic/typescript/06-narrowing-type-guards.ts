// ============================================================
// TypeScript 基础语法 06：类型收窄 / 类型守卫 / 可辨识联合
// 运行：npx tsx typescript/06-narrowing-type-guards.ts
// ============================================================

// ---------- 1. typeof 收窄 ----------
function pad(value: string | number): string {
  if (typeof value === "number") {
    return value.toFixed(2); // 这里 value 是 number
  }
  return value.toUpperCase(); // 这里 value 是 string
}

// ---------- 2. instanceof 收窄 ----------
class Dog { bark() { return "woof"; } }
class Cat { meow() { return "meow"; } }
function makeSound(animal: Dog | Cat): string {
  if (animal instanceof Dog) return animal.bark();
  return animal.meow();
}

// ---------- 3. in 运算符（判断属性是否存在） ----------
interface Fish { swim(): void }
interface Bird { fly(): void }
function move(animal: Fish | Bird): void {
  if ("swim" in animal) animal.swim();
  else animal.fly();
}

// ---------- 4. 真值收窄（truthiness） ----------
function processName(name: string | null | undefined): string {
  if (name) return name.toUpperCase(); // 排除 null/undefined/""
  return "anonymous";
}

// ---------- 5. 相等性收窄 ----------
function example(x: string | number, y: string | boolean): void {
  if (x === y) {
    // 这里 x 和 y 都收窄为 string（唯一共同类型）
    x.toUpperCase();
  }
}

// ---------- 6. 可辨识联合（discriminated union） ----------
// 联合的每个成员都有一个共同的字面量字段（kind/type），switch 后自动收窄。
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":   return Math.PI * shape.radius ** 2;
    case "rect":     return shape.width * shape.height;
    case "triangle": return (shape.base * shape.height) / 2;
    default: {
      const exhaust: never = shape; // 漏了 case 会报错
      return exhaust;
    }
  }
}

// ---------- 7. 自定义类型守卫（type guard） ----------
// 返回值写成「参数 is 类型」，TS 据此在后续代码中收窄。
interface Admin { role: "admin"; permissions: string[] }
interface Member { role: "member" }

function isAdmin(user: Admin | Member): user is Admin {
  return user.role === "admin";
}

function check(user: Admin | Member): void {
  if (isAdmin(user)) {
    user.permissions.length; // 已收窄为 Admin
  }
}

// ---------- 8. 断言收窄（as） ----------
// 手动告诉 TS 某个值更具体的类型（谨慎使用，可能掩盖错误）
const value: unknown = "hello";
const str = value as string; // 断言为 string
const num = value as number; // 断言（运行时并非 number，但 TS 不阻止）

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写函数，参数为 string | number，返回其“长度”（数字为字符串长度）。
// function lengthOf(v: string | number): number { /* 你的代码 */ }

// TODO 2：定义可辨识联合 Payment（cash/credit），switch 处理两种支付。
// type Payment = /* 你的代码 */;
// function handlePayment(p: Payment): string { /* 你的代码 */ }

// TODO 3：写一个类型守卫 isString(x: unknown): x is string。
// function isString(x: unknown): x is string { /* 你的代码 */ }

export {};
