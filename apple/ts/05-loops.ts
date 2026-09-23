// ============================================================
// TypeScript 基础语法 05：循环
// 运行：npx tsx 05-loops.ts
// ============================================================

// ---------- 1. for 循环（最常用，已知次数） ----------
// 语法：for (初始化; 条件; 步进) { ... }
let forSum = 0;
for (let i = 0; i <= 10; i++) {
  forSum += i;
}

// 遍历数组
const fruits = ["苹果", "香蕉", "橘子"];
let forOutput = "";
for (let i = 0; i < fruits.length; i++) {
  forOutput += fruits[i];
}

// ---------- 2. while 循环（条件为真就继续） ----------
let whileCount = 0;
while (whileCount < 5) {
  whileCount++;
}

// ---------- 3. do...while 循环（至少执行一次） ----------
let doCount = 0;
do {
  doCount++;
} while (doCount < 5);

// ---------- 4. for...of 循环（遍历数组/可迭代对象的值，最推荐） ----------
let ofSum = 0;
for (const n of [1, 2, 3, 4]) {
  ofSum += n;
}
let fruitList = "";
for (const f of fruits) {
  fruitList += f;
}

// ---------- 5. for...in 循环（遍历对象的键/数组的索引） ----------
// 注意：遍历数组时得到的是索引（字符串），遍历对象得到的是键。
let keys = "";
for (const key in { a: 1, b: 2, c: 3 }) {
  keys += key;
}
let indices = "";
for (const idx in fruits) {
  indices += idx; // 得到 "012"
}

// ---------- 6. break：跳出整个循环 ----------
let breakResult = "";
for (let i = 0; i < 10; i++) {
  if (i === 3) break; // i 到 3 就停止
  breakResult += i; // 得到 "012"
}

// ---------- 7. continue：跳过本次循环，继续下一次 ----------
let continueResult = "";
for (let i = 0; i < 5; i++) {
  if (i === 2) continue; // 跳过 i=2
  continueResult += i; // 得到 "0134"
}

// ---------- 8. 带标签的循环：break/continue 控制外层循环 ----------
let labelResult = "";
outer: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (j === 1) continue outer; // 跳过外层循环本次迭代
    labelResult += `${i}${j} `;
  }
}

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("for 求和 1..10", forSum, 55);
verify("for 遍历数组", forOutput, "苹果香蕉橘子");
verify("while 计数", whileCount, 5);
verify("do...while 计数", doCount, 5);
verify("for...of 求和", ofSum, 10);
verify("for...of 遍历数组", fruitList, "苹果香蕉橘子");
verify("for...in 遍历对象键", keys, "abc");
verify("for...in 遍历数组索引", indices, "012");
verify("break 提前跳出", breakResult, "012");
verify("continue 跳过", continueResult, "0134");
verify("标签循环", labelResult.trim(), "00 10 20");

export {}; // 让本文件成为模块，避免全局变量冲突
