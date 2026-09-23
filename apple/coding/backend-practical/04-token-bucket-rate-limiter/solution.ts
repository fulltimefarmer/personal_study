// Token Bucket Rate Limiter — 代码空壳（CoderPad 中填充）
// 令牌桶限流：匀速补令牌，请求消耗令牌。

class TokenBucket {
  // TODO: 记录 tokens 与 lastRefill，按时间差连续补令牌

  constructor(capacity: number, refillRate: number) {}

  tryConsume(tokens = 1): boolean {
    return false;
  }
}

// —— 测试（可运行验证）——
const sleep = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

async function run() {
  const bucket = new TokenBucket(5, 1); // 容量 5，每秒补 1

  console.log(bucket.tryConsume());     // true（剩 4）
  console.log(bucket.tryConsume(4));    // true（剩 0）
  console.log(bucket.tryConsume());     // false（不足）

  await sleep(1500);
  console.log(bucket.tryConsume());     // true（已补 ~1.5 个令牌）
  console.log(bucket.tryConsume());     // false（刚又取完）

  // 突发：容量内的令牌可一次性取走
  const burst = new TokenBucket(10, 0.5);
  console.log(burst.tryConsume(10));    // true（初始化即满，容忍突发）
  console.log(burst.tryConsume());      // false
}

run();
