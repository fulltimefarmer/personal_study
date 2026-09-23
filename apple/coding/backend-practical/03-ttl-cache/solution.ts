// In-Memory Cache with TTL — 代码空壳（CoderPad 中填充）
// 带 TTL 的内存缓存，惰性过期。

class TTLCache {
  // TODO: Map<key, { value, expiresAt }>；get/has 时检查并清除过期键

  set(key: string, value: unknown, ttlMs: number): void {}

  get(key: string): unknown {
    return undefined;
  }

  has(key: string): boolean {
    return false;
  }

  delete(key: string): boolean {
    return false;
  }

  clear(): void {}

  get size(): number {
    return 0;
  }
}

// —— 测试（可运行验证）——
const sleep = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

async function run() {
  const cache = new TTLCache();
  cache.set("a", 1, 100);
  console.log(cache.get("a"));   // 1
  console.log(cache.has("a"));   // true
  console.log(cache.size);       // 1

  await sleep(150);
  console.log(cache.get("a"));   // undefined
  console.log(cache.has("a"));   // false
  console.log(cache.size);       // 0

  cache.set("b", 2, 1000);
  console.log(cache.delete("b")); // true
  console.log(cache.delete("b")); // false
}

run();
