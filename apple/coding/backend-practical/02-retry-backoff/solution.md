# Retry with Exponential Backoff — 考点分析与解题思路

## 考点分析

1. **指数退避**：第 k 次重试前延迟 `baseDelay * factor^k`，随重试次数指数增长，避免对故障下游的「重试风暴」。**抖动（jitter）** 让不同客户端错开重试时刻，防止「惊群」同时重试。
2. **重试策略分层**：`shouldRetry` 用于区分「可重试」（网络抖动、429、5xx）与「不可重试」（4xx 业务错误、幂等失败），避免无效重试。
3. **AbortSignal 取消**：等待延迟期间也要能被 abort，需在 `sleep` 中监听 `abort` 事件并清理计时器。
4. **错误透传**：重试耗尽后抛出**最后一次**错误，保留原始错误信息与堆栈。

## 解题思路

- `for (attempt = 0; attempt <= maxRetries; attempt++)`：
  - 若 `signal.aborted` 抛错。
  - `try { return await fn(); } catch (err) { lastError = err; ... }`
  - 若 `attempt === maxRetries || !shouldRetry(err)`：`throw err`。
  - 计算 `delay = baseDelay * factor^attempt`；加抖动则乘 `0.5 + random*0.5`；`await sleep(delay, signal)`。
- `sleep(ms, signal)`：用 `setTimeout` 实现，`signal` abort 时 `clearTimeout` 并 reject。

## 复杂度

- 时间：取决于重试次数与延迟总和，最坏 `Σ baseDelay*factor^k`。
- 空间：O(1)。

## 参考代码

```ts
function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new Error("Aborted"));
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => { clearTimeout(timer); reject(new Error("Aborted")); },
      { once: true }
    );
  });
}

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
  const {
    maxRetries = 3,
    baseDelay = 100,
    factor = 2,
    jitter = true,
    shouldRetry = () => true,
    signal,
  } = options;

  let lastError: unknown;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    if (signal?.aborted) throw new Error("Aborted");
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt === maxRetries || !shouldRetry(err)) throw err;
      let delay = baseDelay * Math.pow(factor, attempt);
      if (jitter) delay *= 0.5 + Math.random() * 0.5;
      await sleep(delay, signal);
    }
  }
  throw lastError;
}
```

## 追问 / Follow-ups

1. **为什么要抖动？**→ 无抖动时大量客户端在同一时刻重试，会对故障服务形成二次冲击；抖动把重试错峰。
2. **重试与幂等**？→ 重试只对**幂等**操作安全（GET、带幂等键的写）；非幂等写需配合幂等键/去重。
3. **如何测试退避时序？**→ 用假时钟（fake timers）控制时间推进，避免真实等待。
4. **断路（circuit breaker）**与退避的区别？→ 退避在单客户端层面重试；断路器在服务层面「熔断」一段时间内的所有请求，避免雪崩。
