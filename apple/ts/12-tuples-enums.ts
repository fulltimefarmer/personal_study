// ============================================================
// TypeScript 基础语法 12：元组 与 枚举
// 运行：npx tsx 12-tuples-enums.ts
// ============================================================

// ---------- 1. 元组（Tuple）：固定长度、固定类型的数组 ----------
let point: [number, number] = [10, 20]; // 两个 number
let user: [string, number] = ["Alice", 25]; // 类型可不同

// 元组常用场景：函数返回多个不同类型的值
function getUser(): [string, number, boolean] {
  return ["Bob", 30, true];
}
const [name, age, active] = getUser(); // 解构拿到各自类型

// 命名元组（给每个位置起名字，增强可读性，仅文档作用）
type HttpResult = [status: number, message: string];
const res: HttpResult = [200, "OK"];

// 可选元组元素
let opt: [string, number?] = ["ok"];
let opt2: [string, number?] = ["ok", 1];

// 剩余元素元组
let rest: [string, ...number[]] = ["nums", 1, 2, 3];

// ---------- 2. 枚举（Enum）：一组有名字的常量 ----------
// 数字枚举：默认从 0 开始自增。
enum Direction {
  Up, // 0
  Down, // 1
  Left, // 2
  Right, // 3
}
// 手动指定起始值
enum StatusCode {
  OK = 200,
  NotFound = 404,
  ServerError = 500,
}

// 字符串枚举：必须给每个成员赋值字符串
enum Color {
  Red = "red",
  Green = "green",
  Blue = "blue",
}

// 访问方式：通过 枚举名.成员 拿到值，也能反向拿名字（数字枚举）。
let myColor: Color = Color.Red;

// ---------- 3. const 枚举（现代推荐写法，编译时内联，无运行时开销） ----------
// 更推荐用「const 对象 + 联合类型」代替 enum，树摇友好。
const Fruit = {
  Apple: "apple",
  Banana: "banana",
  Orange: "orange",
} as const; // as const 让值变成字面量类型
type FruitType = (typeof Fruit)[keyof typeof Fruit]; // 取出所有值的联合类型
const favorite: FruitType = "banana";

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("元组第一个元素", point[0], 10);
verify("元组第二个元素", point[1], 20);
verify("元组解构 name", name, "Bob");
verify("元组解构 age", age, 30);
verify("元组解构 active", active, true);
verify("命名元组 status", res[0], 200);
verify("命名元组 message", res[1], "OK");
verify("可选元组(缺省)", opt, ["ok"]);
verify("可选元组(完整)", opt2, ["ok", 1]);
verify("剩余元素元组", rest, ["nums", 1, 2, 3]);

verify("数字枚举默认值 Up", Direction.Up, 0);
verify("数字枚举 Right", Direction.Right, 3);
verify("数字枚举指定值", StatusCode.NotFound, 404);
verify("字符串枚举", myColor, "red");
verify("反向映射(数字枚举)", Direction[Direction.Up], "Up");

verify("const 对象写法", Fruit.Apple, "apple");
verify("const 对象联合类型", favorite, "banana");

export {}; // 让本文件成为模块，避免全局变量冲突
