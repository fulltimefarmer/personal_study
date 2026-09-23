// Throttle — 代码空壳（CoderPad 中填充）
// 实现节流：在任意 wait 毫秒内最多执行一次 fn，保留 this 与参数。

type Procedure = (...args: any[]) => void;

function throttle<F extends Procedure>(fn: F, wait: number) {
  // TODO: 用时间戳/计时器保证固定节奏触发（前置 + 可选尾随）
  return fn;
}

// —— 测试（可运行验证）——
const sleep = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

async function run() {
  const calls: number[] = [];
  const t = throttle((x: number) => calls.push(x), 50);

  t(1);            // 立即执行（leading）
  await sleep(10); t(2);   // 忽略（窗口内）
  await sleep(10); t(3);   // 忽略
  await sleep(10); t(4);   // 忽略
  await sleep(25); t(5);   // 距上次已 >= 50ms，执行
  await sleep(20);         // 再等一下确认无多余触发
  console.log(JSON.stringify(calls)); // [1,5]
}

run();
