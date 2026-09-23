// ============================================================
// TypeScript 基础语法 09：类型收窄（Narrowing）
// 运行：npx tsx 09-type-narrowing.ts
// ============================================================

// 收窄：让 TS 在某个分支里把「宽类型」缩小成「更具体的类型」。

// ---------- 1. typeof：判断基础类型 ----------
function format(v: string | number): string {
  if (typeof v === "string") {
    return v.trim(); // 这里 v 被收窄成 string
  }
  return v.toFixed(2); // 这里 v 被收窄成 number
}

// ---------- 2. instanceof：判断是否为某个类的实例 ----------
class Animal { walk() { return "走"; } }
class Fish { swim() { return "游"; } }

function move(creature: Animal | Fish): string {
  if (creature instanceof Animal) {
    return creature.walk();
  }
  return creature.swim();
}

// ---------- 3. in：判断对象是否包含某个属性 ----------
interface Bird { fly: () => string }
interface Dog { bark: () => string }

function speak(x: Bird | Dog): string {
  if ("fly" in x) {
    return x.fly();
  }
  return x.bark();
}

// ---------- 4. 字面量/可辨识联合收窄（switch） ----------
type Result = { status: "ok"; data: string } | { status: "fail"; error: string };
function handle(r: Result): string {
  switch (r.status) {
    case "ok": return r.data; // 收窄到 ok 分支
    case "fail": return r.error; // 收窄到 fail 分支
  }
}

// ---------- 5. 自定义类型守卫（is 关键字） ----------
function isString(v: unknown): v is string {
  return typeof v === "string";
}
function process(v: unknown): string {
  if (isString(v)) {
    return v.toUpperCase(); // 守卫后 v 是 string
  }
  return "不是字符串";
}

// ---------- 6. 类型断言 as：手动告诉 TS「我确定它是什么类型」 ----------
const maybe: unknown = "hello";
const asString = maybe as string; // 断言成 string
const length = asString.length;

// ---------- 7. 非空断言 !：告诉 TS「这个值一定不是 null/undefined」 ----------
let maybeName: string | undefined = "Jack";
const certainName = maybeName!; // 断言非空

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("typeof 收窄 string", format("  hi  "), "hi");
verify("typeof 收窄 number", format(3.14159), "3.14");
verify("instanceof 收窄 Animal", move(new Animal()), "走");
verify("instanceof 收窄 Fish", move(new Fish()), "游");
verify("in 收窄 Bird", speak({ fly: () => "飞" }), "飞");
verify("in 收窄 Dog", speak({ bark: () => "汪" }), "汪");
verify("switch 收窄 ok", handle({ status: "ok", data: "成功" }), "成功");
verify("switch 收窄 fail", handle({ status: "fail", error: "失败" }), "失败");
verify("自定义类型守卫", process("hello"), "HELLO");
verify("自定义类型守卫(非字符串)", process(123), "不是字符串");
verify("类型断言 as", length, 5);
verify("非空断言 !", certainName, "Jack");

export {}; // 让本文件成为模块，避免全局变量冲突
