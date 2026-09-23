// ============================================================
// TypeScript 基础语法 08：条件类型 / infer / 映射类型 / 模板字面量类型
// 运行：npx tsx typescript/08-advanced-conditional-mapped.ts
// ============================================================

// ---------- 1. 条件类型：T extends U ? X : Y ----------
type IsString<T> = T extends string ? true : false;
type A = IsString<"hi">; // true
type B = IsString<42>;   // false

// 分布式条件类型：裸类型参数会对联合逐个判断再合并
type ToArray<T> = T extends any ? T[] : never;
type Arr = ToArray<string | number>; // string[] | number[]

// ---------- 2. infer：在条件类型中“提取”类型 ----------
// 提取函数返回类型（等价于 ReturnType）
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type R = MyReturnType<() => string>; // string

// 提取数组元素类型
type ElementOf<T> = T extends (infer E)[] ? E : never;
type E = ElementOf<number[]>; // number

// 提取 Promise 解包后的类型（等价于 Awaited）
type Unwrap<T> = T extends Promise<infer U> ? Unwrap<U> : T;
type U = Unwrap<Promise<Promise<string>>>; // string

// ---------- 3. 映射类型：遍历键生成新类型 ----------
// 把每个属性变成可选、只读等（工具类型的实现原理）
type MyPartial<T> = { [K in keyof T]?: T[K] };
type MyReadonly<T> = { readonly [K in keyof T]: T[K] };

// 键重映射（as）：给每个属性名加前缀
type Getters<T> = { [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] };
interface Person { name: string; age: number }
type PersonGetters = Getters<Person>; // { getName(): string; getAge(): number }

// ---------- 4. 模板字面量类型 ----------
type ApiPath = `/api/${string}`; // 必须以 /api/ 开头
const goodPath: ApiPath = "/api/users";
// const badPath: ApiPath = "/admin"; // 报错

type EventName = `on${string}`;
type Greeting = `Hello, ${string}!`;

// 模板字面量 + 联合 = 笛卡尔积
type Direction = "top" | "bottom";
type Side = "left" | "right";
type Position = `${Direction}-${Side}`; // "top-left" | "top-right" | ...

// ---------- 5. 实用：从接口派生“可选更新”类型 ----------
interface Settings {
  theme: "light" | "dark";
  notifications: boolean;
  language: string;
}
type UpdateSettings = Partial<Pick<Settings, "theme" | "notifications">>;
// { theme?: ...; notifications?: boolean }

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：用条件类型实现 IsArray<T>，是数组返回 true 否则 false。
// type IsArray<T> = /* 你的代码 */;

// TODO 2：用 infer 实现提取元组第一个元素的类型 First<T>。
// type First<T> = /* 你的代码 */;

// TODO 3：用映射类型把所有属性变成 string 类型。
// type Stringify<T> = { [K in keyof T]: string };

export {};
