# Event Emitter · 实现事件发布/订阅

- **类型 Type:** 非算法 · JS/TS 手写实现 / Observer Pattern
- **难度 Difficulty:** Medium
- **标签 Topics:** 观察者模式 / 发布订阅 / 集合 / Observer / Pub-Sub / Set
- **苹果频率:** 高频（观察者模式为 frontendinterviewhandbook 列出的 Apple/前端必考，Node.js `EventEmitter` 的简化版）

## 题干（中文）

实现一个 `EventEmitter` 类（发布/订阅，简化版 Node.js `EventEmitter`），支持：

- `on(event, listener)`：订阅事件；同一事件可有多个监听器；返回 `this`（支持链式调用）。
- `once(event, listener)`：只触发一次的监听器，触发后自动移除。
- `off(event, listener)`：移除指定监听器；返回 `this`。
- `emit(event, ...args)`：按**订阅顺序**依次触发该事件所有监听器，把 `...args` 传给每个监听器；若没有监听器返回 `false`，否则返回 `true`。
- `removeAllListeners(event?)`：移除某事件的全部监听器；不传 `event` 时清空所有事件。

要求处理：`emit` 过程中移除监听器不应影响本轮触发的稳定性（避免漏触发/重复触发）。

## Problem Statement (English)

Implement an `EventEmitter` class (publish/subscribe, a simplified Node.js `EventEmitter`):

- `on(event, listener)`: subscribes; an event may have multiple listeners; returns `this` for chaining.
- `once(event, listener)`: a listener that fires once and is auto-removed.
- `off(event, listener)`: removes a specific listener; returns `this`.
- `emit(event, ...args)`: invokes listeners in **subscription order** with `...args`; returns `false` if there are no listeners, otherwise `true`.
- `removeAllListeners(event?)`: removes all listeners for an event, or clears everything when `event` is omitted.

Handle the case where a listener is removed during `emit` without breaking the current round (no skipped/duplicate invocation).

## 示例 / Examples

```ts
const emitter = new EventEmitter();

emitter.on("data", (x) => console.log("a", x));
emitter.on("data", (x) => console.log("b", x));
emitter.emit("data", 1);
// a 1
// b 1

const once = emitter.once("init", () => console.log("once"));
emitter.emit("init"); // once
emitter.emit("init"); // （无输出）

emitter.off("data", /* 某个 listener */);
emitter.emit("no-such-event"); // 返回 false
```

## 约束 / Constraints

- 事件名用字符串即可（无需处理通配符 `*`）
- 监听器为普通函数 `(...args: any[]) => void`
