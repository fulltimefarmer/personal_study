// ============================================================
// TypeScript 基础语法 03：数组的增删改查（会修改原数组的方法）
// 运行：npx tsx 03-array-add-remove.ts
// ============================================================

// ---------- 1. 在「末尾」增删 ----------
let nums: number[] = [1, 2, 3];

nums.push(4);   // push：末尾添加一个元素，返回新长度
nums.push(5, 6); // 可一次添加多个
let popped = nums.pop(); // pop：移除末尾元素，返回被移除的元素

// ---------- 2. 在「开头」增删 ----------
nums.unshift(0); // unshift：开头添加元素，返回新长度
let shifted = nums.shift(); // shift：移除开头元素，返回被移除的元素

// ---------- 3. splice：任意位置删除 / 插入 / 替换 ----------
// 语法：splice(起始索引, 删除个数, ...要插入的元素)
let arr = [1, 2, 3, 4, 5];
let removed = arr.splice(1, 2); // 从索引1开始删除2个 -> 删除 [2,3]
let inserted = [10, 20, 30];
inserted.splice(1, 0, 99); // 在索引1插入99（删除0个）-> [10,99,20,30]

// 替换：删除 1 个并插入新元素
let replaceArr = [1, 2, 3];
replaceArr.splice(1, 1, 200); // 把索引1的 2 替换成 200 -> [1,200,3]

// ---------- 4. slice：截取（不修改原数组，返回新数组） ----------
// 语法：slice(起始索引, 结束索引) —— 含头不含尾
let src = [1, 2, 3, 4, 5];
let sliced = src.slice(1, 3); // 取索引 1~2 -> [2,3]
let slicedTail = src.slice(2); // 从索引2到最后 -> [3,4,5]

// ---------- 5. concat：拼接数组（不修改原数组） ----------
let a = [1, 2];
let b = [3, 4];
let merged = a.concat(b); // 返回新数组 [1,2,3,4]
let mergedMore = a.concat(b, [5, 6]); // 可拼接多个

// ---------- 6. 查找 ----------
let list = [10, 20, 30, 20];
let idx = list.indexOf(20); // 返回第一个匹配项的索引，找不到返回 -1
let lastIdx = list.lastIndexOf(20); // 从后往前找
let has = list.includes(30); // 是否包含某元素，返回布尔
let noIdx = list.indexOf(999); // 不存在的元素返回 -1

// ---------- 7. join：把数组转成字符串 ----------
let joined = list.join("-"); // 用指定分隔符连接 -> "10-20-30-20"

// ---------- 8. reverse / sort：排序与反转（会修改原数组） ----------
let rev = [1, 2, 3];
rev.reverse(); // 反转 -> [3,2,1]

let sortNums = [3, 1, 2, 10];
// sort 默认按「字符串」顺序排序，数字 10 会排在 2 前面，需传比较函数。
sortNums.sort((x, y) => x - y); // 升序 -> [1,2,3,10]

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

// 最终 nums 经过 push(4,5,6) -> pop(6) -> unshift(0) -> shift(0) = [1,2,3,4,5]
verify("多次增删后 nums", nums, [1, 2, 3, 4, 5]);
verify("pop 返回被移除元素", popped, 6);
verify("shift 返回被移除元素", shifted, 0);
verify("splice 删除的元素", removed, [2, 3]);
verify("splice 删除后的原数组", arr, [1, 4, 5]);
verify("splice 插入元素", inserted, [10, 99, 20, 30]);
verify("splice 替换元素", replaceArr, [1, 200, 3]);
verify("slice 截取(含头不含尾)", sliced, [2, 3]);
verify("slice 截取到末尾", slicedTail, [3, 4, 5]);
verify("concat 拼接", merged, [1, 2, 3, 4]);
verify("concat 拼接多个", mergedMore, [1, 2, 3, 4, 5, 6]);
verify("indexOf 找到的索引", idx, 1);
verify("lastIndexOf 索引", lastIdx, 3);
verify("includes 包含", has, true);
verify("indexOf 找不到返回 -1", noIdx, -1);
verify("join 转字符串", joined, "10-20-30-20");
verify("reverse 反转", rev, [3, 2, 1]);
verify("sort 数字升序", sortNums, [1, 2, 3, 10]);

export {}; // 让本文件成为模块，避免全局变量冲突
