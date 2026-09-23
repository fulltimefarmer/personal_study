// ============================================================
// TypeScript 基础语法 04：数组高阶函数（不修改原数组）
// 运行：npx tsx 04-array-higher-order.ts
// ============================================================

// 高阶函数：把「函数」当作参数传入，对数组做批量处理。
const numbers = [1, 2, 3, 4, 5];

// ---------- 1. map：把每个元素映射成新值，返回新数组 ----------
// 回调函数参数：元素、索引、原数组。
const doubled = numbers.map((n) => n * 2);
const withIndex = numbers.map((n, i) => `${i}:${n}`);

// ---------- 2. filter：筛选满足条件的元素，返回新数组 ----------
const evens = numbers.filter((n) => n % 2 === 0);

// ---------- 3. reduce：把数组「累积」成一个值 ----------
// 语法：reduce((累加器, 当前元素) => 新累加器, 初始值)
const sum = numbers.reduce((acc, cur) => acc + cur, 0);
// 不传初始值时，用第一个元素作为初始值
const max = numbers.reduce((acc, cur) => (cur > acc ? cur : acc));

// ---------- 4. find：返回第一个满足条件的元素（找不到返回 undefined） ----------
const found = numbers.find((n) => n > 3);

// ---------- 5. findIndex：返回第一个满足条件的索引（找不到返回 -1） ----------
const foundIdx = numbers.findIndex((n) => n > 3);

// ---------- 6. some：是否存在「至少一个」满足条件的元素 ----------
const hasEven = numbers.some((n) => n % 2 === 0);

// ---------- 7. every：是否「所有」元素都满足条件 ----------
const allPositive = numbers.every((n) => n > 0);

// ---------- 8. sort：排序（可传比较函数自定义规则） ----------
const sorted = [3, 1, 2].sort((x, y) => x - y); // 升序

// ---------- 9. reverse：反转 ----------
const reversed = [...numbers].reverse(); // 用展开运算符复制一份再反转，避免改原数组

// ---------- 10. forEach：遍历（仅执行副作用，不返回新数组） ----------
let total = 0;
numbers.forEach((n) => {
  total += n;
});

// ---------- 11. flat / flatMap：展平数组 ----------
const nested = [[1, 2], [3, 4]];
const flat = nested.flat(); // 展平一层 -> [1,2,3,4]
// flatMap = map 之后立刻展平一层
const flatMapped = [1, 2, 3].flatMap((n) => [n, n * 10]);

// ---------- 12. 链式调用：把多个高阶函数串起来 ----------
const result = numbers
  .filter((n) => n % 2 === 1) // 先取奇数 [1,3,5]
  .map((n) => n * n) // 再平方 [1,9,25]
  .reduce((acc, n) => acc + n, 0); // 最后求和 = 35

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("map 翻倍", doubled, [2, 4, 6, 8, 10]);
verify("map 带索引", withIndex, ["0:1", "1:2", "2:3", "3:4", "4:5"]);
verify("filter 筛选偶数", evens, [2, 4]);
verify("reduce 求和", sum, 15);
verify("reduce 求最大值", max, 5);
verify("find 找第一个大于3", found, 4);
verify("findIndex 索引", foundIdx, 3);
verify("some 存在偶数", hasEven, true);
verify("every 全部为正", allPositive, true);
verify("sort 升序", sorted, [1, 2, 3]);
verify("reverse 反转", reversed, [5, 4, 3, 2, 1]);
verify("forEach 累加", total, 15);
verify("flat 展平", flat, [1, 2, 3, 4]);
verify("flatMap 映射并展平", flatMapped, [1, 10, 2, 20, 3, 30]);
verify("链式调用结果", result, 35);

export {}; // 让本文件成为模块，避免全局变量冲突
