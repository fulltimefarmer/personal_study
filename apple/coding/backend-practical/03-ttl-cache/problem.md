# In-Memory Cache with TTL · 带 TTL 的内存缓存

- **类型 Type:** 非算法 · 后端 / 缓存 / Backend / Caching
- **难度 Difficulty:** Easy
- **标签 Topics:** 缓存 / 过期策略 / Map / Caching / Expiration
- **苹果频率:** 中高频（Apple 面经多次出现「caching」「Map services cache」等缓存主题）

## 题干（中文）

实现一个支持 **TTL（Time To Live，过期时间）** 的内存缓存 `TTLCache`：

- `set(key, value, ttlMs)`：写入键值，`ttlMs` 毫秒后过期。
- `get(key)`：返回对应的值；若键不存在**或已过期**，返回 `undefined`。
- `has(key)`：键存在且未过期返回 `true`，否则 `false`。
- `delete(key)`：删除键，返回是否成功删除。
- `clear()`：清空所有键。
- `size`：当前存活的键数量（过期键不计入）。

要求：采用**惰性过期（lazy expiration）**——不在后台定时清理，而是在 `get`/`has` 访问到过期键时即时移除。

## Problem Statement (English)

Implement an in-memory `TTLCache` with time-to-live expiration:

- `set(key, value, ttlMs)`: stores the value, expiring after `ttlMs` milliseconds.
- `get(key)`: returns the value, or `undefined` if missing **or expired**.
- `has(key)`: `true` if present and not expired, otherwise `false`.
- `delete(key)`: removes the key, returning whether it existed.
- `clear()`: removes all entries.
- `size`: number of live entries (expired ones excluded).

Requirement: use **lazy expiration** — no background sweeper; remove expired entries on access via `get`/`has`.

## 示例 / Examples

```ts
const cache = new TTLCache();
cache.set("a", 1, 100);   // 100ms 后过期
cache.get("a");           // 1
cache.has("a");           // true
cache.size;               // 1

await sleep(150);
cache.get("a");           // undefined（已过期，惰性移除）
cache.has("a");           // false
cache.size;               // 0
```

## 约束 / Constraints

- `ttlMs > 0`
- 键为字符串，值为任意类型
