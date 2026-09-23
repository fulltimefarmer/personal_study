# JavaScript / TypeScript 深度问答 · Deep Q&A

> 说明：每题含中文题干、英文题干、中文答案、英文答案。JS 侧重运行时机制，TS 侧重类型系统与工程实践。
> Note: Each question has Chinese prompt, English prompt, Chinese answer, English answer.

---

# 第一部分 · Part 1：JavaScript

## JS-1. 解释事件循环(Event Loop)，以及浏览器与 Node.js 的差异。
**EN:** Explain the event loop and the differences between browser and Node.js.

**中文答案：**
JS 单线程，事件循环协调执行栈、宏任务队列、微任务队列。每轮：执行一个宏任务 → 清空所有微任务（含新产生的）→ 需要时渲染 → 下一宏任务。
- **宏任务**：`setTimeout`/`setInterval`、I/O、`setImmediate`(Node)、`MessageChannel`、UI 渲染事件。
- **微任务**：`Promise.then/catch/finally`、`queueMicrotask`、`MutationObserver`(浏览器)、`process.nextTick`(Node，优先级更高)。
- **浏览器 vs Node 差异**：Node 的事件循环有分阶段（timers → pending callbacks → idle/prepare → poll → check → close callbacks），`setImmediate` 在 check 阶段、`process.nextTick` 每阶段之间执行；浏览器还有渲染帧(rAF)。核心的「微任务先于宏任务」两者一致。

**English answer:**
JS is single-threaded; the event loop coordinates the call stack, macrotask queue, and microtask queue. Each iteration: run one macrotask → drain all microtasks (including newly spawned) → render if needed → next macrotask.
- **Macrotasks**: `setTimeout`/`setInterval`, I/O, `setImmediate` (Node), `MessageChannel`, UI render events.
- **Microtasks**: `Promise.then/catch/finally`, `queueMicrotask`, `MutationObserver` (browser), `process.nextTick` (Node, higher priority).
- **Browser vs Node**: Node's loop has distinct phases (timers → pending callbacks → idle/prepare → poll → check → close callbacks); `setImmediate` runs in check, `process.nextTick` runs between phases; the browser adds a render frame (rAF). The core "microtasks before macrotasks" rule is the same.

---

## JS-2. 解释闭包，并说明它在 React Hook / 模块模式 / 防抖中的实际应用。
**EN:** Explain closures and their practical use in React hooks, module pattern, and debounce.

**中文答案：**
闭包 = 函数 + 其词法作用域。内层函数即使在外层返回后仍能访问外层变量。应用：
- **模块模式/私有变量**：IIFE 或工厂函数返回对象，隐藏内部状态。
- **React Hook**：`useState` 返回的 `setState` 捕获当前 state（因此有「过期闭包」问题，需用函数式更新或依赖数组）。
- **防抖/节流**：闭包保存 `timer`/`last` 状态。

```js
function createCounter() {
  let count = 0;                 // 私有
  return {
    increment: () => ++count,     // 闭包捕获 count
    get: () => count,
  };
}
```

**English answer:**
A closure is a function plus its lexical scope; an inner function can access outer variables even after the outer returns. Applications:
- **Module pattern / private state**: IIFE or factory returns an object hiding internal state.
- **React hooks**: the `setState` from `useState` captures the current state (hence "stale closure" — use functional updates or dependency arrays).
- **Debounce/throttle**: closure holds `timer`/`last` state.

```js
function createCounter() {
  let count = 0;                 // private
  return {
    increment: () => ++count,     // closure captures count
    get: () => count,
  };
}
```

---

## JS-3. `var`、`let`、`const` 的区别？什么是变量提升(hoisting)与暂时性死区(TDZ)？
**EN:** Differences between `var`/`let`/`const`? What are hoisting and TDZ?

**中文答案：**
- **var**：函数作用域，提升并初始化为 `undefined`，可重复声明，挂到全局对象。
- **let/const**：块级作用域，提升但**不初始化**（TDZ），不可重复声明；`const` 需声明即初始化且不可重新赋值（对象内容仍可变）。
- **提升(hoisting)**：声明在编译阶段被提升到作用域顶部；`var` 连带初始化为 `undefined`，函数声明整体提升（可先调用）。
- **TDZ**：从块开始到声明语句执行前，访问变量抛 `ReferenceError`。

**English answer:**
- **var**: function-scoped, hoisted and initialized to `undefined`, re-declarable, attached to the global object.
- **let/const**: block-scoped, hoisted but *not* initialized (TDZ), no redeclaration; `const` requires init at declaration and disallows reassignment (object contents still mutable).
- **Hoisting**: declarations are moved to the top of scope at compile time; `var` also initializes to `undefined`; function declarations are fully hoisted (callable before definition).
- **TDZ**: from block start until the declaration executes, accessing the variable throws `ReferenceError`.

---

## JS-4. `==` vs `===` vs `Object.is`，以及类型强制转换(type coercion)规则。
**EN:** `==` vs `===` vs `Object.is`, and coercion rules.

**中文答案：**
- `==` 宽松相等：类型不同时按规则转换（ToPrimitive）。经典陷阱：`null == undefined` 为 `true`；`'0' == 0` 为 `true`；`[] == ''` 为 `true`。
- `===` 严格相等：类型不同即 `false`，不转换。
- `Object.is`：与 `===` 几乎相同，但 `Object.is(NaN, NaN) === true`、`Object.is(+0, -0) === false`。
- **Falsy 值**：`false, 0, -0, 0n, '', null, undefined, NaN`（其余都是 truthy）。`[]` 和 `{}` 是 truthy。

**English answer:**
- `==` loose equality: coerces when types differ (ToPrimitive). Classic traps: `null == undefined` is `true`; `'0' == 0` is `true`; `[] == ''` is `true`.
- `===` strict equality: different types → `false`, no coercion.
- `Object.is`: nearly identical to `===`, but `Object.is(NaN, NaN) === true` and `Object.is(+0, -0) === false`.
- **Falsy values**: `false, 0, -0, 0n, '', null, undefined, NaN` (everything else truthy). `[]` and `{}` are truthy.

---

## JS-5. 解释原型链(prototype chain)，以及 `class` 语法与原型的关系。
**EN:** Explain the prototype chain and how `class` syntax relates to prototypes.

**中文答案：**
JS 的继承基于原型：每个对象有内部 `[[Prototype]]`（可通过 `__proto__` 或 `Object.getPrototypeOf` 访问），属性查找沿原型链向上。函数有 `prototype` 属性，`new Fn()` 创建的对象其 `[[Prototype]]` 指向 `Fn.prototype`，其中 `constructor` 指回 `Fn`。
- `class` 只是原型继承的语法糖：`class A extends B` 等价于设置 `A.prototype` 的 `[[Prototype]]` 指向 `B.prototype`（`Object.setPrototypeOf`）。
- `instanceof` 就是沿原型链查找 `prototype`。
- 方法定义在 `prototype` 上共享；字段定义在每个实例上。

```js
function Person(name) { this.name = name; }
Person.prototype.greet = function () { return `Hi ${this.name}`; };
const p = new Person('Tom');
p.greet();                // 沿 p.__proto__ = Person.prototype 找到 greet
Object.getPrototypeOf(p) === Person.prototype; // true
```

**English answer:**
JS inheritance is prototype-based: every object has an internal `[[Prototype]]` (via `__proto__` or `Object.getPrototypeOf`); property lookup walks up the chain. Functions have a `prototype` property; objects created by `new Fn()` have `[[Prototype]]` = `Fn.prototype`, whose `constructor` points back to `Fn`.
- `class` is syntactic sugar over prototype inheritance: `class A extends B` sets `A.prototype`'s `[[Prototype]]` to `B.prototype` (via `Object.setPrototypeOf`).
- `instanceof` walks the prototype chain looking for `prototype`.
- Methods live on the shared `prototype`; fields live on each instance.

```js
function Person(name) { this.name = name; }
Person.prototype.greet = function () { return `Hi ${this.name}`; };
const p = new Person('Tom');
p.greet();                // found via p.__proto__ = Person.prototype
Object.getPrototypeOf(p) === Person.prototype; // true
```

---

## JS-6. `this` 如何确定？`call`/`apply`/`bind` 的区别？箭头函数的 `this`？
**EN:** How is `this` determined? `call` vs `apply` vs `bind`? Arrow function `this`?

**中文答案：**
`this` 由调用方式决定：普通调用 `fn()` → `undefined`(严格)/`globalThis`(非严格)；方法调用 `obj.fn()` → `obj`；`new Fn()` → 新对象；`fn.call/apply/bind` → 显式指定。
- `call(thisArg, a, b)` 与 `apply(thisArg, [a, b])` 立即调用，仅参数形式不同。
- `bind(thisArg)` 返回绑定 `this` 的新函数（可预设参数），不立即调用。
- **箭头函数**没有自己的 `this`/`arguments`，捕获定义时外层作用域的 `this`（词法绑定），不可作构造函数。

**English answer:**
`this` depends on call style: plain `fn()` → `undefined` (strict)/`globalThis` (non-strict); method `obj.fn()` → `obj`; `new Fn()` → a new object; `fn.call/apply/bind` → explicit.
- `call(thisArg, a, b)` and `apply(thisArg, [a, b])` invoke immediately, differing only in argument form.
- `bind(thisArg)` returns a new function with `this` bound (and optional preset args), without invoking.
- **Arrow functions** have no own `this`/`arguments`; they capture the enclosing scope's `this` (lexical), and can't be constructors.

---

## JS-7. 深拷贝 vs 浅拷贝。如何实现一个健壮的 `deepClone`（处理循环引用、Date、Map/Set）？
**EN:** Deep copy vs shallow copy. Implement a robust `deepClone` (cycles, Date, Map/Set).

**中文答案：**
浅拷贝只复制第一层引用（`...` 展开、`Object.assign`、`Array.slice`），深拷贝递归复制所有层级。健壮实现要点：`WeakMap` 记录已拷贝对象处理**循环引用**；特殊处理 `Date`/`RegExp`/`Map`/`Set`/`ArrayBuffer`；区分数组与对象。

```js
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value; // 原始值
  if (value instanceof Date) return new Date(value);
  if (value instanceof RegExp) return new RegExp(value.source, value.flags);
  if (seen.has(value)) return seen.get(value);            // 循环引用
  if (value instanceof Map) {
    const m = new Map(); seen.set(value, m);
    for (const [k, v] of value) m.set(deepClone(k, seen), deepClone(v, seen));
    return m;
  }
  if (value instanceof Set) {
    const s = new Set(); seen.set(value, s);
    for (const v of value) s.add(deepClone(v, seen));
    return s;
  }
  const out = Array.isArray(value) ? [] : Object.create(Object.getPrototypeOf(value));
  seen.set(value, out);
  for (const key of Reflect.ownKeys(value)) out[key] = deepClone(value[key], seen);
  return out;
}
```

**English answer:**
Shallow copy duplicates only the first level (`...` spread, `Object.assign`, `Array.slice`); deep copy recursively duplicates all levels. Robust impl: `WeakMap` records copied objects to handle **cycles**; special-case `Date`/`RegExp`/`Map`/`Set`/`ArrayBuffer`; distinguish arrays from objects.

```js
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value; // primitives
  if (value instanceof Date) return new Date(value);
  if (value instanceof RegExp) return new RegExp(value.source, value.flags);
  if (seen.has(value)) return seen.get(value);            // cycle
  if (value instanceof Map) {
    const m = new Map(); seen.set(value, m);
    for (const [k, v] of value) m.set(deepClone(k, seen), deepClone(v, seen));
    return m;
  }
  if (value instanceof Set) {
    const s = new Set(); seen.set(value, s);
    for (const v of value) s.add(deepClone(v, seen));
    return s;
  }
  const out = Array.isArray(value) ? [] : Object.create(Object.getPrototypeOf(value));
  seen.set(value, out);
  for (const key of Reflect.ownKeys(value)) out[key] = deepClone(value[key], seen);
  return out;
}
```

---

## JS-8. `Promise` 的三种状态、`async/await` 错误处理，以及 `Promise.all/allSettled/race/any` 的区别。
**EN:** Promise states, `async/await` error handling, and `all/allSettled/race/any`.

**中文答案：**
Promise 三种状态：pending → fulfilled / rejected（不可逆）。`async` 函数始终返回 Promise；`await` 后的异常需用 `try/catch` 捕获，未捕获会变成 rejected Promise。
- `all`：全成功才 resolve（结果按序）；任一 reject 立即整体 reject。
- `allSettled`：等全部 settle，返回 `{status, value|reason}`，永不 reject。
- `race`：第一个 settle 的结果/错误（无论成功失败）。
- `any`：第一个成功才 resolve；全部失败抛 `AggregateError`。
- 关键陷阱：`async/await` 中并发用 `Promise.all([a(), b()])` 而非顺序 `await`；错误要就近 try/catch，避免「未处理的 rejected Promise」。

**English answer:**
Promises have three states: pending → fulfilled / rejected (irreversible). `async` functions always return a Promise; exceptions after `await` must be caught by `try/catch`, otherwise they become a rejected Promise.
- `all`: resolves only if all succeed (ordered results); rejects immediately if any rejects.
- `allSettled`: waits for all to settle; returns `{status, value|reason}`; never rejects.
- `race`: settles with the first result/error (success or failure).
- `any`: resolves with the first success; rejects with `AggregateError` if all fail.
- Traps: run concurrent async with `Promise.all([a(), b()])` rather than sequential `await`; catch errors close to the source to avoid unhandled rejections.

---

## JS-9. 防抖(debounce) vs 节流(throttle)，并各举一个电商场景。
**EN:** Debounce vs throttle, with an e-commerce example each.

**中文答案：**
- **防抖**：事件停止触发一段时间后才执行，持续触发则重置计时器。场景：**搜索联想**（停止输入 300ms 才发请求）。
- **节流**：固定时间窗口最多执行一次。场景：**滚动加载更多**、**购物车按钮防连点**、**窗口 resize**。

```ts
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function throttle<T extends (...args: any[]) => void>(fn: T, wait: number) {
  let last = 0;
  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - last >= wait) { last = now; fn(...args); }
  };
}
```

**English answer:**
- **Debounce**: execute only after events stop for a delay; continuous events reset the timer. Use case: **search autocomplete** (fire 300ms after typing stops).
- **Throttle**: execute at most once per fixed window. Use case: **infinite scroll**, **anti-double-click "Add to Cart"**, **window resize**.

```ts
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function throttle<T extends (...args: any[]) => void>(fn: T, wait: number) {
  let last = 0;
  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - last >= wait) { last = now; fn(...args); }
  };
}
```

---

## JS-10. 什么是事件委托(event delegation)？为什么高效？
**EN:** What is event delegation and why is it efficient?

**中文答案：**
利用事件冒泡，把事件监听器挂在**父元素**上，通过 `event.target` 判断实际点击的子元素，从而用一个监听器管理大量/动态生成的子元素。优点：减少监听器数量（内存/性能）、动态添加的子元素无需重新绑定。

```js
document.getElementById('list').addEventListener('click', (e) => {
  const item = (e.target as HTMLElement).closest('[data-id]');
  if (item) console.log('clicked', item.dataset.id);
});
```

**English answer:**
Using event bubbling, attach one listener on a **parent** and use `event.target` to identify the actual child, managing many/dynamically-added children with a single listener. Benefits: fewer listeners (memory/perf), no rebinding for dynamically added children.

```js
document.getElementById('list').addEventListener('click', (e) => {
  const item = (e.target as HTMLElement).closest('[data-id]');
  if (item) console.log('clicked', item.dataset.id);
});
```

---

## JS-11. `map`/`filter`/`reduce` 分别做什么？为什么避免在 `.map` 里做副作用？
**EN:** What do `map`/`filter`/`reduce` do? Why avoid side effects in `.map`?

**中文答案：**
- `map`：对每项变换，返回**等长**新数组。
- `filter`：按谓词保留，返回子集。
- `reduce`：把数组**归约**成单个值（累加/分组/构造对象）。
- 三者都是纯函数式风格、不改变原数组。避免在 `map` 里做副作用（如 `console.log`、修改外部状态），因为它语义是「变换」而非「遍历」，副作用会破坏可读性、可测试性与 React 渲染的纯函数假设。

```js
const total = orders.reduce((sum, o) => sum + o.total, 0);
const active = orders.filter(o => o.status === 'active');
const ids = orders.map(o => o.id);
```

**English answer:**
- `map`: transforms each item, returns a new array of **equal length**.
- `filter`: keeps items matching a predicate, returns a subset.
- `reduce`: **reduces** the array to a single value (sum/group/build object).
- All are pure, non-mutating. Avoid side effects in `map` because its semantics are "transform", not "iterate" — side effects hurt readability, testability, and React's pure-function assumptions.

```js
const total = orders.reduce((sum, o) => sum + o.total, 0);
const active = orders.filter(o => o.status === 'active');
const ids = orders.map(o => o.id);
```

---

## JS-12. 展开/剩余运算符与解构的常见用法，以及浅拷贝陷阱。
**EN:** Spread/rest and destructuring, and the shallow-copy trap.

**中文答案：**
- **展开 `...`**：复制/合并数组、对象（浅拷贝）；`const arr2 = [...arr]` 只复制第一层，嵌套对象仍是共享引用。
- **剩余 `...rest`**：收集剩余参数/属性；`function f(a, ...rest)`、`const { a, ...others } = obj`。
- **解构**：`const { name, age } = user;`、`const [first, second] = arr;`，支持默认值与重命名 `{ name: n }`。
- **陷阱**：展开是浅拷贝，修改嵌套对象会影响原对象；需深拷贝时用 `structuredClone` 或 `deepClone`。

```js
const a = { x: 1, nested: { y: 2 } };
const b = { ...a };            // 浅拷贝
b.nested.y = 99;               // a.nested.y 也被改成 99
```

**English answer:**
- **Spread `...`**: copy/merge arrays & objects (shallow); `const arr2 = [...arr]` copies only the first level — nested objects are still shared references.
- **Rest `...rest`**: collect remaining args/props; `function f(a, ...rest)`; `const { a, ...others } = obj`.
- **Destructuring**: `const { name, age } = user;`, `const [first, second] = arr;` with defaults and renaming `{ name: n }`.
- **Trap**: spread is shallow — mutating nested objects affects the original; use `structuredClone` or `deepClone` for deep copies.

```js
const a = { x: 1, nested: { y: 2 } };
const b = { ...a };            // shallow
b.nested.y = 99;               // a.nested.y is now 99 too
```

---

## JS-13. ES Modules 与 CommonJS 的区别？Node 中如何混用？
**EN:** ES Modules vs CommonJS? How to interop in Node?

**中文答案：**
- **CommonJS**：`require`/`module.exports`，同步、运行时加载、值是拷贝、`this` 指向 `module.exports`；Node 默认（`.js` 在无 `type:module` 时）。
- **ESM**：`import`/`export`，静态（编译期可 tree-shake）、异步、绑定是**只读引用**（活绑定）、支持顶层 `await`；浏览器原生 + Node `type:module` 或 `.mjs`。
- 混用：ESM 可 `import` CJS（默认导出=module.exports）；CJS 不能同步 `require` ESM，需 `await import()`。`import.meta` 代替 `__dirname/__filename`。

**English answer:**
- **CommonJS**: `require`/`module.exports`, synchronous, loaded at runtime, values are copies, `this` = `module.exports`; Node default (`.js` without `type:module`).
- **ESM**: `import`/`export`, static (tree-shakeable), async, bindings are **read-only live bindings**, top-level `await`; native in browsers + Node `type:module` or `.mjs`.
- Interop: ESM can `import` CJS (default export = `module.exports`); CJS cannot synchronously `require` ESM — use `await import()`. Use `import.meta` instead of `__dirname/__filename`.

---

## JS-14. 什么是高阶函数、纯函数、柯里化？各给一个例子。
**EN:** Higher-order functions, pure functions, currying — with examples.

**中文答案：**
- **高阶函数**：接收或返回函数的函数（`map`/`compose`）。
- **纯函数**：相同输入必得相同输出，无副作用（利于测试、缓存、并发）。
- **柯里化**：把多参函数转成链式单参函数，便于部分应用与复用。

```js
const add = a => b => a + b;          // 柯里化
const add5 = add(5);                  // 部分应用
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x); // 高阶 + 组合
```

**English answer:**
- **Higher-order function**: takes or returns functions (`map`/`compose`).
- **Pure function**: same input → same output, no side effects (easy to test, cache, parallelize).
- **Currying**: converts a multi-arg function into chained single-arg functions for partial application.

```js
const add = a => b => a + b;          // currying
const add5 = add(5);                  // partial application
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x); // higher-order + composition
```

---

## JS-15. 什么是内存泄漏？JS 中常见的泄漏来源与排查方法？
**EN:** What are memory leaks? Common sources and diagnosis in JS.

**中文答案：**
内存泄漏 = 不再需要的对象仍被引用，无法被 GC 回收。常见来源：
- 未移除的事件监听器/定时器（`setInterval` 未 `clear`）。
- 全局变量、闭包无意持有大对象。
- 游离 DOM 引用（从 DOM 移除节点但 JS 仍引用）。
- `Promise` 未 resolve/reject 悬挂、单例缓存无限增长。
排查：Chrome DevTools Memory（heap snapshot 对比、allocation timeline）、`Performance` 面板看堆曲线；Node 用 `process.memoryUsage()`、`--inspect` + heap snapshot、`--max-old-space-size`。

**English answer:**
A memory leak is when unneeded objects remain referenced and can't be GC'd. Common sources:
- Unremoved event listeners / timers (`setInterval` without `clear`).
- Globals; closures accidentally holding large objects.
- Detached DOM references (node removed but still referenced in JS).
- Dangling Promises (never resolve/reject); unbounded singleton caches.
Diagnosis: Chrome DevTools Memory (heap snapshot diff, allocation timeline), Performance panel heap curve; Node: `process.memoryUsage()`, `--inspect` + heap snapshots, `--max-old-space-size`.

---

## JS-16. `let` 在 for 循环里与 `var` 的行为差异（经典 setTimeout 题）。
**EN:** `let` vs `var` inside a for loop (classic `setTimeout` question).

**中文答案：**

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i)); // 输出 3 3 3（var 提升到函数作用域，共享同一 i）
}
for (let j = 0; j < 3; j++) {
  setTimeout(() => console.log(j)); // 输出 0 1 2（let 每次迭代都是新的块级绑定）
}
```

原因：`var` 只有函数作用域，循环结束后 `i` 已变成 3，所有回调共享同一变量；`let` 是块级作用域，每次迭代创建一个新的词法环境，回调各自捕获自己的 `j`。

**English answer:**

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i)); // 3 3 3 (var is function-scoped, one shared i)
}
for (let j = 0; j < 3; j++) {
  setTimeout(() => console.log(j)); // 0 1 2 (let creates a fresh binding per iteration)
}
```

Reason: `var` is function-scoped, so after the loop `i` is 3 and all callbacks share it; `let` is block-scoped, each iteration creates a new lexical environment, so each callback captures its own `j`.

---

# 第二部分 · Part 2：TypeScript

## TS-1. `type` 与 `interface` 的区别？何时用哪个？
**EN:** `type` vs `interface` — differences and when to use each.

**中文答案：**
- **interface**：可被类 `implements`、可 `extends`，支持**声明合并**；适合对象/公共 API 契约。
- **type**：可表达**联合/交叉/元组/映射/条件/字面量**类型；不能声明合并，`extends` 用 `&` 代替。
- 经验法则：描述对象形状/对外 API 用 `interface`；需要联合、工具类型、别名时用 `type`。

```ts
interface User { id: number; name: string; }
interface User { email?: string; }        // 声明合并
type ID = string | number;                // 联合只能用 type
```

**English answer:**
- **interface**: implementable/`extends`-able by classes, supports **declaration merging**; good for object/API contracts.
- **type**: can express **unions/intersections/tuples/mapped/conditional/literal** types; no declaration merging; use `&` instead of `extends`.
- Rule of thumb: `interface` for object shapes / public APIs; `type` for unions, utility types, aliases.

```ts
interface User { id: number; name: string; }
interface User { email?: string; }        // declaration merging
type ID = string | number;                // union requires type
```

---

## TS-2. 什么是泛型？写出一个类型安全的 API 封装（含错误联合返回）。
**EN:** What are generics? Write a type-safe API wrapper with union error return.

**中文答案：**
泛型让类型参数化，保持类型安全的同时复用代码。真实工程里常用「Result 模式」区分成功/失败，避免 throw 失控。

```ts
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function request<T>(url: string): Promise<Result<T>> {
  try {
    const res = await fetch(url);
    if (!res.ok) return { ok: false, error: new Error(`HTTP ${res.status}`) };
    return { ok: true, value: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: e as Error };
  }
}

interface Product { id: number; name: string; price: number; }
const r = await request<Product>('/api/products');
if (r.ok) r.value.price;    // 类型收窄为 Product
```

**English answer:**
Generics parameterize types, enabling reuse without losing type safety. In practice a "Result pattern" distinguishes success/failure instead of uncontrolled `throw`.

```ts
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function request<T>(url: string): Promise<Result<T>> {
  try {
    const res = await fetch(url);
    if (!res.ok) return { ok: false, error: new Error(`HTTP ${res.status}`) };
    return { ok: true, value: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: e as Error };
  }
}

interface Product { id: number; name: string; price: number; }
const r = await request<Product>('/api/products');
if (r.ok) r.value.price;    // narrowed to Product
```

---

## TS-3. 类型收窄(type narrowing)的常用手段与可辨识联合(discriminated union)。
**EN:** Type narrowing techniques and discriminated unions.

**中文答案：**
把宽类型收窄为具体类型：`typeof`（原始类型）、`instanceof`（类）、`in`（属性存在性）、`Array.isArray`、字面量相等比较、自定义类型守卫 `x is T`。**可辨识联合**：联合每个成员带共同字面量字段（`kind`/`type`），`switch` 后自动收窄——是表达状态机/消息的黄金模式。

```ts
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rect'; width: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle': return Math.PI * s.radius ** 2;  // s: circle
    case 'rect':   return s.width * s.height;        // s: rect
  }
}

function isNumber(x: unknown): x is number {        // 自定义类型守卫
  return typeof x === 'number';
}
```

**English answer:**
Narrow a wide type: `typeof` (primitives), `instanceof` (classes), `in` (property existence), `Array.isArray`, literal equality, custom type guards `x is T`. **Discriminated unions**: each member has a common literal field (`kind`/`type`); `switch` narrows automatically — the gold pattern for state machines/messages.

```ts
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rect'; width: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle': return Math.PI * s.radius ** 2;  // s: circle
    case 'rect':   return s.width * s.height;        // s: rect
  }
}

function isNumber(x: unknown): x is number {        // custom type guard
  return typeof x === 'number';
}
```

---

## TS-4. 常用工具类型：`Partial`、`Pick`、`Omit`、`Record`、`ReturnType`、`Awaited`、`NonNullable`。
**EN:** Utility types: `Partial`, `Pick`, `Omit`, `Record`, `ReturnType`, `Awaited`, `NonNullable`.

**中文答案：**
- `Partial<T>` 全可选；`Required<T>` 全必选。
- `Pick<T, K>` 保留键 K；`Omit<T, K>` 排除键 K。
- `Record<K, V>` 构造键 K 值 V 的对象。
- `ReturnType<F>` 函数返回类型；`Parameters<F>` 参数元组。
- `Awaited<T>` 递归解包 Promise。
- `NonNullable<T>` 剔除 `null`/`undefined`。

```ts
interface User { id: number; name: string; email: string; }
type NewUser = Omit<User, 'id'>;              // { name; email }
type Patch = Partial<NewUser>;                // 全可选
type ById = Record<string, User>;             // 索引对象
type AwaitedUser = Awaited<Promise<User>>;    // User
type MaybeId = NonNullable<string | null>;    // string
```

**English answer:**
- `Partial<T>` all optional; `Required<T>` all required.
- `Pick<T, K>` keep keys K; `Omit<T, K>` remove keys K.
- `Record<K, V>` object keyed K valued V.
- `ReturnType<F>` return type; `Parameters<F>` parameter tuple.
- `Awaited<T>` recursively unwraps Promises.
- `NonNullable<T>` removes `null`/`undefined`.

```ts
interface User { id: number; name: string; email: string; }
type NewUser = Omit<User, 'id'>;              // { name; email }
type Patch = Partial<NewUser>;                // all optional
type ById = Record<string, User>;             // index object
type AwaitedUser = Awaited<Promise<User>>;    // User
type MaybeId = NonNullable<string | null>;    // string
```

---

## TS-5. `unknown` vs `any` vs `never` 的区别与使用场景。
**EN:** `unknown` vs `any` vs `never`.

**中文答案：**
- `any`：关闭类型检查，可赋值给任何类型、访问任何成员——类型安全黑洞，应尽量避免。
- `unknown`：类型安全的「任意值」。任何值可赋给它，但它只能赋给 `unknown`/`any`，使用前必须收窄。适合 API/JSON 等外部数据。
- `never`：表示「不可能存在的值」——函数永不返回（抛错/死循环）、或穷尽检查后剩的联合分支。用于**穷尽性检查**：`switch` 默认分支赋给 `never`，漏了 case 会编译报错。

```ts
function assertNever(x: never): never { throw new Error('unreachable'); }
```

**English answer:**
- `any`: disables checking — assignable to anything, any member accessible; a type-safety black hole; avoid.
- `unknown`: the type-safe "any". Anything can be assigned to it, but it can only be assigned to `unknown`/`any`; must narrow before use. Use for external data (API/JSON).
- `never`: the "impossible" type — a function that never returns (throws/loops), or the leftover branch after exhaustive checks. Used for **exhaustiveness checking**: assigning the `switch` default to `never` makes a missing case a compile error.

```ts
function assertNever(x: never): never { throw new Error('unreachable'); }
```

---

## TS-6. `keyof`、`typeof`、索引访问类型、`satisfies`、`as const`。
**EN:** `keyof`, `typeof`, indexed access types, `satisfies`, `as const`.

**中文答案：**
- `keyof T`：取对象类型的所有键的联合。
- `typeof x`（类型上下文）：取变量的静态类型。
- 索引访问 `T[K]`：取某键对应的值类型。
- `as const`：把字面量固定为只读字面量类型（`readonly`），防止拓宽。
- `satisfies`：**校验**表达式符合某类型，但保留字面量的更精确推断（不同于断言 `as` 会丢失精度）。

```ts
const config = { theme: 'dark', retries: 3 } as const;
type ConfigKey = keyof typeof config;           // 'theme' | 'retries'

const routes = { home: '/', admin: '/admin' } satisfies Record<string, string>;
// routes.home 仍是字面量 '/'，而不是 string
```

**English answer:**
- `keyof T`: union of all keys of T.
- `typeof x` (type context): the static type of a variable.
- Indexed access `T[K]`: the value type at key K.
- `as const`: locks literals into readonly literal types (prevents widening).
- `satisfies`: **validates** an expression against a type while preserving the more precise literal inference (unlike `as`, which loses precision).

```ts
const config = { theme: 'dark', retries: 3 } as const;
type ConfigKey = keyof typeof config;           // 'theme' | 'retries'

const routes = { home: '/', admin: '/admin' } satisfies Record<string, string>;
// routes.home stays the literal '/', not string
```

---

## TS-7. 条件类型、`infer`、映射类型、模板字面量类型。
**EN:** Conditional types, `infer`, mapped types, template literal types.

**中文答案：**
- **条件类型** `T extends U ? X : Y`：按条件分发；配合泛型 + 裸类型参数会**分布式**（`T extends ...` 对联合逐个判断再合并）。
- **`infer`**：在条件类型中「提取」类型：`T extends Promise<infer R> ? R : never`。
- **映射类型** `{ [K in keyof T]: ... }`：遍历键生成新类型（工具类型的实现基础）。
- **模板字面量类型**：`type Path = \`/api/${string}\`` 约束字符串形态。

```ts
type Unwrap<T> = T extends Promise<infer R> ? R : T;          // 解包
type Getters<T> = { [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] };
type ApiPath = `/api/${string}`;                              // 模板字面量
```

**English answer:**
- **Conditional types** `T extends U ? X : Y`: conditional dispatch; with a naked generic parameter it's **distributive** (evaluates per union member).
- **`infer`**: extracts a type inside a conditional: `T extends Promise<infer R> ? R : never`.
- **Mapped types** `{ [K in keyof T]: ... }`: iterate keys to build a new type (the basis of utility types).
- **Template literal types**: `type Path = \`/api/${string}\`` constrains string shapes.

```ts
type Unwrap<T> = T extends Promise<infer R> ? R : T;          // unwrap
type Getters<T> = { [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] };
type ApiPath = `/api/${string}`;                              // template literal
```

---

## TS-8. 结构类型系统(structural typing) vs 名义类型，以及 `enum` 的坑。
**EN:** Structural typing vs nominal typing; the pitfalls of `enum`.

**中文答案：**
- TS 是**结构类型系统**（鸭子类型）：两个类型只要结构兼容就互相赋值，不看名字。优点：灵活、便于 mock；缺点：可能意外通过（如两个 `{id: number}` 类型互认）。
- 想模拟名义类型可用**品牌类型(brand)**：`type UserId = string & { __brand: 'UserId' }`。
- **`enum` 的坑**：会生成运行时代码；数值 enum 有反向映射；`const enum` 在 `isolatedModules` 下可能有问题。现代实践常改用 `as const` 对象 + 联合类型，更可预测、可 tree-shake。

```ts
const Status = { Active: 'active', Done: 'done' } as const;
type Status = (typeof Status)[keyof typeof Status]; // 'active' | 'done'
```

**English answer:**
- TS is **structurally typed** (duck typing): two types are assignable if their structures are compatible, regardless of names. Pro: flexible, easy mocking; con: accidental compatibility (two `{id: number}` types inter-assign).
- Simulate nominal typing with **branded types**: `type UserId = string & { __brand: 'UserId' }`.
- **`enum` pitfalls**: generates runtime code; numeric enums have reverse mapping; `const enum` breaks under `isolatedModules`. Modern practice prefers `as const` objects + unions — more predictable and tree-shakeable.

```ts
const Status = { Active: 'active', Done: 'done' } as const;
type Status = (typeof Status)[keyof typeof Status]; // 'active' | 'done'
```

---

## TS-9. `strict` 模式有哪些关键选项？为什么开启 `strictNullChecks` 很重要？
**EN:** Key `strict` options? Why is `strictNullChecks` important?

**中文答案：**
`strict` 聚合了 `strictNullChecks`、`noImplicitAny`、`noImplicitThis`、`strictFunctionTypes`、`strictBindCallApply`、`strictPropertyInitialization`、`alwaysStrict`、`useUnknownInCatchVariables` 等。
- **`strictNullChecks`**：让 `null`/`undefined` 成为独立类型，不能赋给普通类型，强制显式处理空值——消除了绝大多数运行时 `Cannot read property of null` 错误，是 TS 最有价值的开关。代价是代码更啰嗦（需用可选链 `?.`、空值合并 `??`、收窄）。

**English answer:**
`strict` bundles `strictNullChecks`, `noImplicitAny`, `noImplicitThis`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `alwaysStrict`, `useUnknownInCatchVariables`, etc.
- **`strictNullChecks`**: makes `null`/`undefined` distinct types that can't be assigned to ordinary types, forcing explicit handling — eliminating most runtime "Cannot read property of null" errors. It's TS's most valuable flag. Cost: more verbose code (optional chaining `?.`, nullish coalescing `??`, narrowing).

---

## TS-10. 装饰器(decorator)的作用，以及它如何支撑 NestJS/Angular。
**EN:** What do decorators do, and how do they power NestJS/Angular?

**中文答案：**
装饰器是一种**声明式元编程**：以 `@expression` 形式附加到类/方法/属性/参数上，在运行时（或编译期）注入元数据或修改行为。NestJS/Angular 用 `reflect-metadata` 把元数据（路由、依赖、注入 token）写入 `Reflect`，框架读取后完成 DI、路由注册等。常见内置装饰器：类装饰器 `@Controller`/`@Injectable`/`@Component`，方法装饰器 `@Get`，参数装饰器 `@Body`/`@Query`。

```ts
function log(target: any, key: string, desc: PropertyDescriptor) {
  const original = desc.value;
  desc.value = function (...args: any[]) {
    console.log(`call ${key}`, args);
    return original.apply(this, args);
  };
}
```

**English answer:**
Decorators are a form of **declarative metaprogramming**: attached as `@expression` to classes/methods/properties/parameters to inject metadata or modify behavior at runtime (or compile time). NestJS/Angular use `reflect-metadata` to store metadata (routes, dependencies, injection tokens) in `Reflect`, which the framework reads to perform DI and route registration. Common built-ins: class decorators `@Controller`/`@Injectable`/`@Component`, method `@Get`, param `@Body`/`@Query`.

```ts
function log(target: any, key: string, desc: PropertyDescriptor) {
  const original = desc.value;
  desc.value = function (...args: any[]) {
    console.log(`call ${key}`, args);
    return original.apply(this, args);
  };
}
```

---

## TS-11. 类型声明文件(`.d.ts`)与 `declare` 的作用？如何给一个无类型的第三方库补类型？
**EN:** What are `.d.ts` and `declare`? How to add types to an untyped third-party lib?

**中文答案：**
`.d.ts` 是**类型声明文件**，只含类型不产生运行时代码，用于描述 JS 库/模块的形状。`declare` 声明一个「运行时存在但 TS 不认识」的变量/模块/全局。给无类型库补类型：新建 `types/xxx.d.ts` 用 `declare module 'xxx' { ... }`（`module augmentation`/通配声明），并在 `tsconfig` 的 `types`/`include` 里引入；或加 `@types/xxx`。

```ts
// types/legacy-lib.d.ts
declare module 'legacy-lib' {
  export function doThing(x: number): string;
  export const VERSION: string;
}
```

**English answer:**
`.d.ts` are **type declaration files**: types only, no runtime code, describing the shape of JS libraries/modules. `declare` declares a variable/module/global that exists at runtime but is unknown to TS. To type an untyped lib: create `types/xxx.d.ts` with `declare module 'xxx' { ... }` (module augmentation/ambient declaration) and include it via `tsconfig` `types`/`include`; or add `@types/xxx`.

```ts
// types/legacy-lib.d.ts
declare module 'legacy-lib' {
  export function doThing(x: number): string;
  export const VERSION: string;
}
```

---

## TS-12. 如何在前端与后端之间共享类型？Monorepo / package / 代码生成的取舍。
**EN:** How to share types between frontend and backend? Monorepo vs package vs codegen.

**中文答案：**
- **Monorepo**（如 Nx/Turborepo）：前后端放同一仓库，共享 `packages/types`，单一事实来源、改动即时可见，但需工具链统一。
- **独立 npm 私有包**：把类型打成 `@org/shared-types` 发布，适合多仓库，但有版本漂移。
- **代码生成(codegen)**：以 OpenAPI/Swagger 或 GraphQL schema 为源，生成前后端类型（如 `openapi-typescript`、`graphql-codegen`），保证契约一致性，最稳妥。
- 实践中常见「共享包 + OpenAPI 生成」结合，避免手工维护双份类型导致契约漂移。

**English answer:**
- **Monorepo** (Nx/Turborepo): FE+BE in one repo sharing `packages/types`; single source of truth, instant visibility, but needs unified tooling.
- **Private npm package**: publish `@org/shared-types`; suits multi-repo but risks version drift.
- **Codegen**: generate types from OpenAPI/Swagger or GraphQL schema (`openapi-typescript`, `graphql-codegen`) for guaranteed contract consistency.
- In practice: combine a shared package with OpenAPI generation to avoid hand-maintaining duplicate types and contract drift.
