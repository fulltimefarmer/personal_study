// ============================================================
// TypeScript 基础语法 03：对象类型 / interface / type / 只读·可选属性
// 运行：npx tsx typescript/03-objects-interfaces-types.ts
// ============================================================

// ---------- 1. 对象类型（内联） ----------
let user: { name: string; age: number } = { name: "Alice", age: 25 };

// ---------- 2. interface（接口） ----------
// interface 描述对象的“形状/契约”，可被类实现、可被扩展。
interface Product {
  id: number;
  name: string;
  price: number;
}

const iphone: Product = { id: 1, name: "iPhone", price: 999 };

// 可选属性：属性可能不存在
interface Product {
  description?: string; // 声明合并：同名 interface 会自动合并
}
const ipad: Product = { id: 2, name: "iPad", price: 799 }; // description 可省略

// 只读属性：初始化后不可修改
interface Order {
  readonly orderId: string;
  total: number;
}
const order: Order = { orderId: "A1001", total: 99 };
// order.orderId = "B"; // 报错：只读

// 接口继承
interface DigitalProduct extends Product {
  downloadLink: string;
}

// 接口实现（用于 class）
interface HasName {
  name: string;
  sayHi(): string;
}

// ---------- 3. type（类型别名） ----------
// type 可给任意类型起别名
type Point = { x: number; y: number };
type ID = string | number;

// 类型别名扩展用“交叉类型 &”
type ColoredPoint = Point & { color: string };

// ---------- 4. interface vs type ----------
// 共同点：都能描述对象形状。
// 区别：
//   - interface 可声明合并、可被 class implements/extends；
//   - type 可表达联合/交叉/元组等更复杂的类型。
// 经验：对象/API 契约用 interface；联合、工具类型、别名用 type。

// ---------- 5. 索引签名 ----------
// 描述“任意字符串键”的对象
interface StringMap {
  [key: string]: string;
}
const colors: StringMap = { primary: "blue", danger: "red" };

// ---------- 6. 嵌套对象 ----------
interface Address {
  city: string;
  street: string;
}
interface Customer {
  name: string;
  address: Address;        // 嵌套对象
  tags?: string[];         // 可选 + 数组
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：定义一个 interface Car，包含 brand(string)、model(string)、
//         year(number，只读)、electric(boolean，可选)。
// interface Car { /* 你的代码 */ }

// TODO 2：用 type 定义一个别名 Result = { success: boolean; data?: string }。
// type Result = /* 你的代码 */

// TODO 3：定义一个接口，带索引签名，键为 string，值为 number，
//         并创建一个对象存两个城市的人口。
// interface Population { /* 你的代码 */ }

export {};
