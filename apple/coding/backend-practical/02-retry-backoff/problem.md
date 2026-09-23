# Retry with Exponential Backoff · 指数退避重试

- **类型 Type:** 非算法 · 后端 / 可靠性 / Backend / Reliability
- **难度 Difficulty:** Medium
- **标签 Topics:** 异步 / 网络 / 容错 / Async / Networking / Fault Tolerance
- **苹果频率:** 中高频（Apple 后端面经多次出现「retry fetch」「race conditions」「fault tolerance」主题）

## 题干（中文）

实现 `retryWithBackoff(fn, options?)`，对可能失败的异步操作 `fn` 进行重试，重试间隔按**指数退避**增长，并支持可选的**随机抖动（jitter）**。

签名与选项：

```ts
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;                 // 最大重试次数（不含首次），默认 3
    baseDelay?: number;                  // 初始延迟（毫秒），默认 100
    factor?: number;                     // 退避倍数，默认 2
    jitter?: boolean;                    // 是否加随机抖动，默认 true
    shouldRetry?: (error: unknown) => boolean; // 判断该错误是否值得重试，默认全重试
    signal?: AbortSignal;                // 支持取消
  }
): Promise<T>
```

要求：

1. 首次调用失败后进入重试；第 `k` 次重试前等待 `baseDelay * factor^k`（加抖动则为该值的 0.5–1.0 倍随机区间）。
2. 若 `shouldRetry` 返回 `false`，或已用尽重试次数，则把最后一次错误抛出。
3. `signal` 被 abort 时应尽快中止（等待期间也要响应）。

## Problem Statement (English)

Implement `retryWithBackoff(fn, options?)` that retries an async operation `fn` on failure, with delays growing by **exponential backoff** and optional **jitter**.

Requirements:

1. After the first failure, retry; before the k-th retry, wait `baseDelay * factor^k` (with jitter: a random 0.5–1.0 multiple).
2. If `shouldRetry` returns `false`, or retries are exhausted, throw the last error.
3. Respond to `signal` abort promptly (including during the wait).

## 示例 / Examples

```ts
let attempt = 0;
const flaky = async () => {
  if (++attempt < 3) throw new Error("transient");
  return "ok";
};

await retryWithBackoff(flaky, { baseDelay: 50, jitter: false });
// 前两次失败后各等待 50ms、100ms，第三次成功 => "ok"
```

## 约束 / Constraints

- `maxRetries >= 0`，`baseDelay >= 0`，`factor >= 1`
- `fn` 可为同步抛出或返回 reject 的 Promise
