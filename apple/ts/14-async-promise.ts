// ============================================================
// TypeScript 基础语法 14：异步（Promise / async / await）
// 运行：npx tsx 14-async-promise.ts
// ============================================================

// ---------- 1. Promise：表示一个「将来才会完成」的操作 ----------
// 状态：pending（进行中）-> fulfilled（成功）/ rejected（失败）。
function fetchData(id: number): Promise<string> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (id > 0) {
        resolve(`数据-${id}`); // 成功：调用 resolve 并传递结果
      } else {
        reject(new Error("id 必须大于 0")); // 失败：调用 reject 并传递错误
      }
    }, 10);
  });
}

// ---------- 2. .then / .catch / .finally 链式调用 ----------
// .then 处理成功，.catch 处理失败，.finally 无论成败都执行。
function demoThen(): void {
  fetchData(1)
    .then((data) => console.log("then 成功:", data))
    .catch((err) => console.log("catch 失败:", (err as Error).message))
    .finally(() => console.log("finally 完成"));
}

// ---------- 3. async / await：用同步写法写异步代码 ----------
// async 函数一定返回 Promise；await 等待 Promise 完成并拿到结果。
async function loadAll(): Promise<string> {
  const a = await fetchData(1); // 等待第一个完成
  const b = await fetchData(2); // 再等第二个
  return a + " + " + b; // 组合结果
}

// ---------- 4. 并行执行：Promise.all / Promise.race ----------
async function loadParallel(): Promise<string[]> {
  // Promise.all：全部成功才返回，任何一个失败则整体失败。
  return Promise.all([fetchData(1), fetchData(2), fetchData(3)]);
}

// ---------- 5. 错误处理：try / catch / finally ----------
async function safeLoad(id: number): Promise<string> {
  try {
    return await fetchData(id);
  } catch (err) {
    return "捕获到错误: " + (err as Error).message;
  } finally {
    // 无论成功失败都执行（如清理资源）
  }
}

// ---------- 6. 异步数组处理（等待全部 Promise） ----------
async function processAll(): Promise<string[]> {
  const ids = [1, 2, 3];
  const promises = ids.map((id) => fetchData(id)); // 先得到 Promise 数组
  return Promise.all(promises); // 一次性等待全部
}

// ============================================================
// 验证方法（异步验证需要 await，所以包在 async 主函数里）
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

async function main(): Promise<void> {
  verify("await 单个结果", await fetchData(1), "数据-1");

  verify("async 顺序执行", await loadAll(), "数据-1 + 数据-2");

  verify("Promise.all 并行", await loadParallel(), ["数据-1", "数据-2", "数据-3"]);

  verify("try/catch 捕获成功", await safeLoad(5), "数据-5");
  verify("try/catch 捕获失败", await safeLoad(-1), "捕获到错误: id 必须大于 0");

  verify("map + Promise.all", await processAll(), ["数据-1", "数据-2", "数据-3"]);

  // .then 风格演示（同步打印，不参与 verify）
  demoThen();
}

// 执行主函数
main();

export {}; // 让本文件成为模块，避免全局变量冲突
