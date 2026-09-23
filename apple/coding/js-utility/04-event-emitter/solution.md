# Event Emitter — 考点分析与解题思路

## 考点分析

1. **观察者模式**：用 `Map<事件名, Set<监听器>>` 存储订阅关系。`Set` 天然去重（同一函数多次 `on` 只存一份），且增删为 O(1)。
2. **`once` 的实现**：包装原监听器为 `wrapper`，`wrapper` 执行时先 `off(event, wrapper)` 再调用原函数。注意 `off` 要移除的是 `wrapper` 而不是原函数。
3. **emit 中的删除安全**：若直接遍历可变集合，监听器在回调里移除自己/他人会导致「漏触发」或并发修改问题。标准做法是**快照遍历**：`for (const l of [...set])`，先拷贝一份再遍历。
4. **返回值**：`emit` 在无监听器时返回 `false`，否则 `true`；`on`/`off`/`once` 返回 `this` 支持链式。

## 解题思路

- `private events = new Map<string, Set<Listener>>()`。
- `on`：`getOrCreate` 集合后 `add`；返回 `this`。
- `once`：创建 `wrapper`，调用 `this.on(event, wrapper)`。
- `off`：`this.events.get(event)?.delete(listener)`；返回 `this`。
- `emit`：取集合，空则返回 `false`；否则 `[...set]` 快照遍历调用；返回 `true`。
- `removeAllListeners`：有 `event` 删该 key，无则 `clear()`。

## 复杂度

- `on`/`off`/`once`/`removeAllListeners`：O(1)（Set/Map 操作）。
- `emit`：O(k)，k 为该事件监听器数（快照拷贝 O(k) + 调用 O(k)）。

## 参考代码

```ts
type Listener = (...args: any[]) => void;

class EventEmitter {
  private events = new Map<string, Set<Listener>>();

  on(event: string, listener: Listener): this {
    if (!this.events.has(event)) this.events.set(event, new Set());
    this.events.get(event)!.add(listener);
    return this;
  }

  once(event: string, listener: Listener): this {
    const wrapper: Listener = (...args) => {
      this.off(event, wrapper);
      listener(...args);
    };
    return this.on(event, wrapper);
  }

  off(event: string, listener: Listener): this {
    this.events.get(event)?.delete(listener);
    return this;
  }

  emit(event: string, ...args: any[]): boolean {
    const listeners = this.events.get(event);
    if (!listeners || listeners.size === 0) return false;
    for (const l of [...listeners]) l(...args); // 快照遍历，避免 emit 中删除导致的问题
    return true;
  }

  removeAllListeners(event?: string): this {
    if (event === undefined) this.events.clear();
    else this.events.delete(event);
    return this;
  }
}
```

## 追问 / Follow-ups

1. **emit 中移除自己/他人监听器**会怎样？→ 快照遍历保证本轮仍会触发所有「emit 开始时已存在」的监听器；新 `on` 的监听器本轮不触发。
2. **监听器抛异常**是否阻断其他监听器？→ 需要定义策略：try/catch 包裹每个监听器可隔离错误，但会掩盖异常，需和面试官讨论。
3. **通配符 `*` / 命名空间**？→ 在 `emit` 末尾额外触发 `*` 监听器；可用前缀匹配实现命名空间。
4. **`once` 如何支持 `off` 取消未触发的 once？**→ 需要暴露 wrapper 映射，或让 `off` 同时按原函数查找 wrapper。
