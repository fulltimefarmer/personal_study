# DeepPartial — 考点分析与解题思路

## 考点分析

1. **类型分支顺序很关键**：条件类型按顺序匹配，必须**先判断函数**（`T extends (...args: any[]) => any`），因为函数在 TS 里也满足 `object`，若把对象分支放前面会把函数「拆」成空对象/可选属性。
2. **数组用 `infer` 提取元素**：`T extends Array<infer U> ? Array<DeepPartial<U>> : ...` 保留数组结构，只对元素递归。
3. **映射类型做递归**：`{ [K in keyof T]?: DeepPartial<T[K]> }` 是递归核心——`?` 让当前层可选，`DeepPartial<T[K]>` 处理下一层。
4. **原始类型兜底**：不满足函数/数组/对象时原样返回 `T`。
5. **常见坑**：只写一层映射 `{ [K in keyof T]?: T[K] }` 只能浅层可选；不处理函数会破坏回调类型；不处理数组会把 `string[]` 变成 `string` 的映射对象。

## 解题思路

```ts
type DeepPartial<T> =
  T extends (...args: any[]) => any   // 1. 函数：原样保留
    ? T
    : T extends Array<infer U>        // 2. 数组：递归元素
      ? Array<DeepPartial<U>>
      : T extends object              // 3. 对象：递归属性
        ? { [K in keyof T]?: DeepPartial<T[K]> }
        : T;                          // 4. 原始类型：原样
```

## 复杂度

- 类型层面无运行时开销（编译期展开）。

## 参考代码

```ts
type DeepPartial<T> =
  T extends (...args: any[]) => any
    ? T
    : T extends Array<infer U>
      ? Array<DeepPartial<U>>
      : T extends object
        ? { [K in keyof T]?: DeepPartial<T[K]> }
        : T;
```

## 类型级测试

```ts
type Equal<A, B> =
  (<T>() => T extends A ? 1 : 2) extends (<T>() => T extends B ? 1 : 2)
    ? true : false;
type Expect<T extends true> = T;

interface Config {
  name: string;
  nested: { enabled: boolean; tags: string[] };
  items: { id: number }[];
  fn: (x: number) => string;
}

type _Test = Expect<Equal<DeepPartial<Config>, {
  name?: string;
  nested?: { enabled?: boolean; tags?: string[] };
  items?: { id?: number }[];
  fn?: (x: number) => string;
}>>;
```

## 追问 / Follow-ups

1. **DeepRequired / DeepReadonly**？→ 同构写法，把 `?` 换成 `-?` 或加 `readonly`，并递归。
2. **`Partial` 与 `DeepPartial` 区别？**→ `Partial` 只处理第一层；`DeepPartial` 递归到所有层级。
3. **递归类型的深度限制？**→ TS 递归类型可能触及「实例化过深」上限，超深结构可改用手写 N 层或 `DeepPartial<T, Depth>` 加深度参数。
4. **如何让函数保持可选但不改签名？**→ 正是「先判函数」分支的作用；漏掉它会导致回调签名丢失。
