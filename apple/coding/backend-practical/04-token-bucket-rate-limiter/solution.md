# Token Bucket Rate Limiter — 考点分析与解题思路

## 考点分析

1. **令牌桶模型**：桶以 `refillRate` 匀速补令牌、上限 `capacity`，请求消耗令牌。既能限制「平均速率」（refillRate），又能容忍「突发流量」（capacity 内的令牌一次性取走）。
2. **连续补充 vs 离散定时**：不要用 `setInterval` 补令牌（浪费、不精确）。正确做法是记录 `lastRefill` 时间戳，每次操作时按 `elapsed * refillRate` 计算应补令牌数，再取 `min(capacity, ...)`。
3. **三种常见限流对比**（面试高频）：
   - **固定窗口**：窗口内计数，简单但有「窗口边界突发」问题。
   - **滑动窗口**：更平滑，但实现/内存略高。
   - **令牌桶**：允许一定突发，平滑平均速率，最常见。
4. **精度**：用 `Date.now()`（毫秒）即可；高并发场景需考虑原子性。

## 解题思路

- `tokens = capacity`，`lastRefill = Date.now()`。
- `refill()`：`elapsed = (now - lastRefill) / 1000`；`tokens = min(capacity, tokens + elapsed * refillRate)`；`lastRefill = now`。
- `tryConsume(count)`：先 `refill()`；若 `tokens >= count` 则 `tokens -= count` 返回 `true`，否则 `false`。

## 复杂度

- 时间：O(1)。
- 空间：O(1)。

## 参考代码

```ts
class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private capacity: number,
    private refillRate: number
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  tryConsume(count = 1): boolean {
    this.refill();
    if (this.tokens >= count) {
      this.tokens -= count;
      return true;
    }
    return false;
  }
}
```

## 追问 / Follow-ups

1. **固定窗口 vs 滑动窗口 vs 令牌桶**各自优劣？→ 固定窗口实现最简单但有边界突发；滑动窗口平滑但需记录每次请求时间戳（内存高）；令牌桶允许突发、实现简洁，最常用。
2. **并发安全？**→ 单机多线程/多请求下需加锁或原子操作；Node 单线程天然安全，但多个进程各自维护独立桶。
3. **分布式限流？**→ 用 Redis：`INCR + EXPIRE`（固定窗口）、`ZSET`（滑动窗口）、`CL.RATE_LIMITER`/Lua 脚本（令牌桶，保证原子性）。
4. **拒绝策略？**→ 直接拒绝、排队等待、返回 429 + `Retry-After` 头、降级（走缓存）。
