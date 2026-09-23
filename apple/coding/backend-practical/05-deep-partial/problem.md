# DeepPartial Type · 递归可选类型

- **类型 Type:** 非算法 · TypeScript 类型体操 / Type-Level Programming
- **难度 Difficulty:** Medium
- **标签 Topics:** 泛型 / 映射类型 / 条件类型 / Generics / Mapped Types / Conditional Types
- **苹果频率:** 中高频（JD 明确要求 TypeScript 深度，后端 TS 面试常考工具类型实现）

## 题干（中文）

实现一个 TypeScript 工具类型 `DeepPartial<T>`，把类型 `T` 的**所有层级**的属性都变为可选：

1. 对象的所有属性变为可选（`?`），并递归处理嵌套对象。
2. **数组**：把元素类型递归处理（`DeepPartial<Array<T>> = Array<DeepPartial<T>>`），数组本身仍保留为数组。
3. **函数类型**：保持不变（不要把函数「拆成」可选属性）。
4. **原始类型**（`string`/`number`/`boolean` 等）：保持不变。

即：`DeepPartial` = 递归版的 `Partial`。

## Problem Statement (English)

Implement the TypeScript utility type `DeepPartial<T>` that makes all properties optional **at every level**:

1. All properties of objects become optional (`?`), recursing into nested objects.
2. **Arrays**: recurse into the element type (`DeepPartial<Array<T>> = Array<DeepPartial<T>>`), remaining an array.
3. **Function types**: unchanged (do not "unwrap" a function into optional properties).
4. **Primitives** (`string`/`number`/`boolean`, etc.): unchanged.

In short: `DeepPartial` is the recursive version of `Partial`.

## 示例 / Examples

```ts
interface Config {
  name: string;
  nested: { enabled: boolean; tags: string[] };
  items: { id: number }[];
  fn: (x: number) => string;
}

type P = DeepPartial<Config>;
// 等价于：
type Expected = {
  name?: string;
  nested?: { enabled?: boolean; tags?: string[] };
  items?: { id?: number }[];
  fn?: (x: number) => string;
};

const ok: P = { nested: { enabled: true } }; // 合法：深层属性也是可选
```

## 约束 / Constraints

- 需正确处理对象、数组、函数、原始类型四种分支
- 用条件类型 + 映射类型 + 递归（通过 `infer` 推断数组元素类型）
