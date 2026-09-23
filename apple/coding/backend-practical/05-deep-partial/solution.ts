// DeepPartial — 代码空壳（类型级，无运行时实现）
// 说明：类型在编译期展开，运行时无代码；请用 `npx tsc --noEmit` 或编辑器验证下方类型断言。

// TODO: 用条件类型 + 映射类型实现递归可选（注意：先判函数，再判数组，最后对象/原始类型）
type DeepPartial<T> = { [K in keyof T]?: T[K] }; // 仅浅层，需改成递归版本

// —— 类型级测试（编译期验证）——
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

// —— 运行时演示（类型在编译期校验；补全实现后用 `npx tsc --noEmit` 验证上方断言）——
function run() {
  console.log("类型题：正确性由上方类型断言在编译期验证（tsc --noEmit）");
}

run();
