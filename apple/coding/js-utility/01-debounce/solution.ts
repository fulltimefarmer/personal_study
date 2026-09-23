// Debounce — 代码空壳（CoderPad 中填充）
// 实现防抖：停顿 wait 毫秒后才执行一次 fn，支持 immediate 前置触发与 cancel()。

type Procedure = (...args: any[]) => void;

function debounce<F extends Procedure>(
  fn: F,
  wait: number,
  immediate = false
) {
  // TODO: 用闭包持有 timer，实现尾随/前置触发 + cancel
  const stub = function (this: unknown, ...args: any[]) {
    return fn.apply(this, args);
  } as F & { cancel: () => void };
  stub.cancel = () => {};
  return stub;
}

// —— 测试（可运行验证）——
const sleep = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

async function run() {
  // 尾随：连续调用只执行最后一次
  const calls: string[] = [];
  const d = debounce(() => calls.push("trailing"), 50);
  d(); d(); d();
  await sleep(80);
  console.log(JSON.stringify(calls)); // ["trailing"]

  // 前置：第一次立即执行，冷却期内忽略
  const leading: string[] = [];
  const l = debounce(() => leading.push("leading"), 50, true);
  l(); l();
  console.log(JSON.stringify(leading)); // ["leading"]
  await sleep(80);
  console.log(JSON.stringify(leading)); // 仍 ["leading"]

  // cancel：取消后不再触发
  const cancelled: string[] = [];
  const c = debounce(() => cancelled.push("never"), 50);
  c();
  c.cancel();
  await sleep(80);
  console.log(JSON.stringify(cancelled)); // []

  // this 与参数透传
  const obj = { val: 42, log(this: any, x: number) { console.log(this.val + x); } };
  const bound = debounce(function (this: any, x: number) { calls.push(String(this.val + x)); }, 50);
  bound.call(obj, 1);
  await sleep(80);
  console.log(JSON.stringify(calls)); // ["trailing","43"]
}

run();
