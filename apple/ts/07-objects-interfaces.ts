// ============================================================
// TypeScript 基础语法 07：对象、interface、type
// 运行：npx tsx 07-objects-interfaces.ts
// ============================================================

// ---------- 1. 对象字面量（直接标注属性类型） ----------
const user: { name: string; age: number } = { name: "Alice", age: 25 };

// ---------- 2. interface：定义对象的「形状」（可扩展、可继承） ----------
interface Product {
  id: number;
  name: string;
  price: number;
  inStock?: boolean; // 可选属性：可有可无
  readonly category: string; // 只读属性：赋值后不能修改
}

const iPhone: Product = {
  id: 1,
  name: "iPhone 16",
  price: 6999,
  category: "手机",
};
// iPhone.category = "电脑"; // ❌ 报错：只读属性不能改

// 接口继承：extends 继承父接口的所有属性
interface ElectronicProduct extends Product {
  warrantyYears: number;
}
const mac: ElectronicProduct = {
  id: 2,
  name: "MacBook",
  price: 12999,
  category: "电脑",
  warrantyYears: 2,
};

// 接口可以同名合并（声明合并）
interface Config { host: string }
interface Config { port: number }
const config: Config = { host: "localhost", port: 8080 };

// ---------- 3. type：类型别名（更灵活，可描述任意类型） ----------
type ID = string | number; // 联合类型别名
type Point = { x: number; y: number }; // 对象类型别名
const p: Point = { x: 1, y: 2 };

// ---------- 4. 索引签名：允许任意字符串键 ----------
interface Dictionary {
  [key: string]: number; // 任意字符串键，值必须是 number
}
const scores: Dictionary = { 语文: 90, 数学: 95 };

// ---------- 5. 函数签名：接口也能描述函数 ----------
interface GreetFn {
  (name: string): string;
}
const hello: GreetFn = (name) => "Hello " + name;

// ---------- 6. 可选属性读取（用 ?. 可选链） ----------
// 用一个返回 Product | undefined 的函数，模拟「可能找不到」的情况。
function findProduct(id: number): Product | undefined {
  return undefined; // 假设没找到，返回 undefined
}
const nameOrEmpty = findProduct(1)?.name; // 若为 undefined 则返回 undefined，不报错

// ---------- 7. 对象的操作：读取、修改、删除、遍历 ----------
// 注意：delete 只能删除「可选属性」，所以 height 标注为可选。
const box: { width: number; height?: number } = { width: 10, height: 20 };
box.width = 30; // 修改属性
delete box.height; // 删除属性
const keys = Object.keys(box); // 获取所有键
const values = Object.values(box); // 获取所有值
const entries = Object.entries(box); // 获取键值对数组

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("对象字面量 name", user.name, "Alice");
verify("对象字面量 age", user.age, 25);
verify("interface 对象 name", iPhone.name, "iPhone 16");
verify("interface 只读属性", iPhone.category, "手机");
verify("接口继承 warrantyYears", mac.warrantyYears, 2);
verify("接口声明合并", config, { host: "localhost", port: 8080 });
verify("type 别名对象", p, { x: 1, y: 2 });
verify("索引签名取值", scores["语文"], 90);
verify("接口函数签名", hello("World"), "Hello World");
verify("可选链读取 undefined", nameOrEmpty, undefined);
verify("修改对象属性", box.width, 30);
verify("Object.keys", keys, ["width"]);
verify("Object.values", values, [30]);
verify("Object.entries", entries, [["width", 30]]);

export {}; // 让本文件成为模块，避免全局变量冲突
