// ============================================================
// TypeScript 基础语法 02：数组基础
// 运行：npx tsx 02-arrays-basics.ts
// ============================================================

// ---------- 1. 数组的创建 ----------
// 语法一：类型[] —— 最常用写法
let nums: number[] = [1, 2, 3, 4, 5];
// 语法二：Array<类型> —— 泛型写法，与上面等价
let strs: Array<string> = ["a", "b", "c"];
// 联合类型数组：数组元素可以是多种类型之一
let mixed: (string | number)[] = [1, "a", 2, "b"];
// 空数组需要显式标注类型，否则推断为 never[]
let empty: number[] = [];

// ---------- 2. 访问与长度 ----------
let first = nums[0]; // 通过索引访问，索引从 0 开始
let last = nums[nums.length - 1]; // length 属性返回数组长度
let count = nums.length; // 数组元素个数

// ---------- 3. 二维数组（数组的数组） ----------
// number[][] 表示「元素是 number[] 的数组」。
let matrix: number[][] = [
  [1, 2, 3],
  [4, 5, 6],
  [7, 8, 9],
];
let center = matrix[1][1]; // 访问第 2 行第 2 列 = 5

// ---------- 4. 元组（固定长度、固定类型的数组） ----------
// 元组每个位置类型不同、长度固定。
let tuple: [string, number] = ["iPhone", 9999];
let productName = tuple[0]; // string
let productPrice = tuple[1]; // number

// 元组解构：按位置一次性取出并保留各自类型。
let [pn, pp] = tuple;

// 可选元组元素：该位置可有可无。
let optTuple: [string, number?] = ["ok"];
// 剩余元素：前面固定，后面可放任意多个 number。
let restTuple: [string, ...number[]] = ["scores", 90, 80, 70];

// ---------- 5. 只读数组 ----------
// readonly 让数组变成只读，不能增删改。
const readonlyArr: readonly number[] = [1, 2, 3];
// readonlyArr.push(4); // ❌ 报错：只读数组不能 push

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("数组长度", nums.length, 5);
verify("访问第一个元素", first, 1);
verify("访问最后一个元素", last, 5);
verify("数组元素个数", count, 5);
verify("字符串数组", strs, ["a", "b", "c"]);
verify("联合类型数组", mixed, [1, "a", 2, "b"]);
verify("二维数组取中心", center, 5);
verify("元组第一个元素", productName, "iPhone");
verify("元组第二个元素", productPrice, 9999);
verify("元组解构", [pn, pp], ["iPhone", 9999]);
verify("只读数组可读取", readonlyArr[2], 3);

export {}; // 让本文件成为模块，避免全局变量冲突
