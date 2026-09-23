// Promise.all — 代码空壳（CoderPad 中填充）
// 实现与原生 Promise.all 等价的行为（结果有序、fail-fast、包装普通值、空数组）。

function promiseAll<T>(promises: Array<T | PromiseLike<T>>): Promise<T[]> {
  // TODO: new Promise + 按下标写结果 + completed 计数 + fail-fast
  promises.forEach(p => Promise.resolve(p).catch(() => {}));
  return Promise.resolve([]);
}

// —— 测试（可运行验证）——
async function run() {
  console.log(JSON.stringify(await promiseAll([Promise.resolve(1), Promise.resolve(2)]))); // [1,2]
  console.log(JSON.stringify(await promiseAll([1, Promise.resolve(2), 3])));               // [1,2,3]
  console.log(JSON.stringify(await promiseAll([])));                                       // []

  // 结果按输入顺序（慢的先完成也不影响顺序）
  const slow = new Promise<number>(r => setTimeout(() => r(99), 50));
  const fast = Promise.resolve(1);
  console.log(JSON.stringify(await promiseAll([slow, fast]))); // [99,1]

  // fail-fast：第二个稍后 reject，应立即 reject 且不等待第三个
  const msg = await promiseAll([
    Promise.resolve(1),
    new Promise((_, reject) => setTimeout(() => reject(new Error("boom")), 10)),
    new Promise<number>(r => setTimeout(() => r(3), 1000)),
  ]).then(
    () => "no-error",
    e => (e as Error).message
  );
  console.log(msg); // boom
}

run();
