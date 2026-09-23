// Retry with Exponential Backoff — 代码空壳（CoderPad 中填充）
// 失败重试，间隔指数增长，支持抖动与 AbortSignal 取消。

interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  factor?: number;
  jitter?: boolean;
  shouldRetry?: (error: unknown) => boolean;
  signal?: AbortSignal;
}

async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  // TODO: for 循环 + try/catch + sleep(退避延迟)，处理 shouldRetry 与 signal
  try {
    return await fn();
  } catch (e) {
    return undefined as T; // 空壳占位：不重试
  }
}

// —— 测试（可运行验证）——
async function run() {
  let attempt = 0;
  const flaky = async () => {
    if (++attempt < 3) throw new Error("transient");
    return "ok";
  };
  console.log(await retryWithBackoff(flaky, { baseDelay: 30, jitter: false })); // ok
  console.log(attempt); // 3（2 次失败 + 1 次成功）

  // 不可重试的错误应立即抛出
  let calls = 0;
  await retryWithBackoff(
    async () => { calls++; throw new Error("bad input"); },
    { shouldRetry: (e) => (e as Error).message !== "bad input", baseDelay: 30 }
  ).then(
    () => console.log("no-error"),
    e => console.log((e as Error).message) // bad input
  );
  console.log(calls); // 1（只调用一次，未重试）

  // 用尽重试次数抛出最后一次错误
  await retryWithBackoff(
    async () => { throw new Error("always fails"); },
    { maxRetries: 2, baseDelay: 20, jitter: false }
  ).then(
    () => console.log("no-error"),
    e => console.log((e as Error).message) // always fails
  );
}

run();
