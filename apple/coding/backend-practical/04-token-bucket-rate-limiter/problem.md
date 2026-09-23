# Token Bucket Rate Limiter · 令牌桶限流器

- **类型 Type:** 非算法 · 后端 / 基础设施 / Backend / Infrastructure
- **难度 Difficulty:** Medium
- **标签 Topics:** 限流 / 令牌桶 / 设计 / Rate Limiting / Token Bucket / Design
- **苹果频率:** 高频（Apple 后端面经多次出现「rate limit」「API gateway」「Redis」限流主题）

## 题干（中文）

实现一个**令牌桶（token bucket）**限流器 `TokenBucket`：

- `constructor(capacity, refillRate)`：桶最多持有 `capacity` 个令牌；令牌以 `refillRate`（个/秒）的速率**匀速补充**，桶满则丢弃多余令牌。
- `tryConsume(tokens = 1)`：尝试取走 `tokens` 个令牌；若当前令牌充足则扣减并返回 `true`，否则返回 `false`（请求被拒绝）。

要求：

1. 令牌补充是**连续匀速**的（按时间差计算，而非离散定时器），避免长时间空闲后仍无令牌可用。
2. 初始化时桶是满的。
3. 线程/调用安全语义：多次调用 `tryConsume` 之间要正确累计已补充令牌。

## Problem Statement (English)

Implement a **token bucket** rate limiter `TokenBucket`:

- `constructor(capacity, refillRate)`: the bucket holds at most `capacity` tokens; tokens refill continuously at `refillRate` (tokens/second), and excess tokens are discarded when full.
- `tryConsume(tokens = 1)`: attempts to take `tokens` tokens; if enough are available, deduct and return `true`, otherwise `false` (request rejected).

Requirements:

1. Refill is **continuous** (computed from elapsed time, not a discrete timer), so tokens accumulate while idle.
2. The bucket starts full.
3. Correctly accumulate refilled tokens across calls to `tryConsume`.

## 示例 / Examples

```ts
const bucket = new TokenBucket(5, 1); // 容量 5，每秒补 1 个令牌

bucket.tryConsume(); // true（剩 4）
bucket.tryConsume(4); // true（剩 0）
bucket.tryConsume(); // false（令牌不足）

await sleep(1500);
bucket.tryConsume(); // true（已补 ~1.5 个令牌）
```

## 约束 / Constraints

- `capacity >= 1`，`refillRate > 0`
- `tokens >= 1`
