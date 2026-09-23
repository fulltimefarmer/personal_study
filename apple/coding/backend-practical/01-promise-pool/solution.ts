// Promise Pool — 代码空壳（CoderPad 中填充）
// 并发限流：同时最多 limit 个任务在运行，结果按输入顺序返回。

async function mapConcurrent<T, R>(
  items: T[],
  limit: number,
  fn: (item: T, index: number) => Promise<R>
): Promise<R[]> {
  // TODO: 共享游标 + 固定数量 worker，按下标写结果
  return [];
}

// —— 测试（可运行验证）——
const sleep = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

async function run() {
  const items = [1, 2, 3, 4, 5];
  const fn = async (x: number) => {
    await sleep(120 - x * 20); // 后提交的任务更快完成
    return x * 2;
  };

  console.log(JSON.stringify(await mapConcurrent(items, 2, fn))); // [2,4,6,8,10]
  console.log(JSON.stringify(await mapConcurrent([], 2, fn)));     // []
  console.log(JSON.stringify(await mapConcurrent([1, 2], 10, fn))); // [2,4]（limit 超界等价 Promise.all）

  // 失败即 reject
  await mapConcurrent([1, 2, 3], 2, async (x) => {
    if (x === 2) throw new Error("boom");
    return x;
  }).then(
    () => console.log("no-error"),
    e => console.log((e as Error).message) // boom
  );
}

run();
