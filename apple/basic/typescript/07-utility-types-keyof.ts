// ============================================================
// TypeScript 基础语法 07：工具类型 / keyof / typeof / 索引访问 / satisfies
// 运行：npx tsx typescript/07-utility-types-keyof.ts
// ============================================================

interface User {
  id: number;
  name: string;
  email: string;
  age?: number;
}

// ---------- 1. 常用工具类型 ----------
type AllOptional = Partial<User>;    // 所有属性可选
type AllRequired = Required<User>;   // 所有属性必选（含 age）
type ReadonlyUser = Readonly<User>;  // 所有属性只读
type NameAndId = Pick<User, "id" | "name">;   // 只保留指定键
type WithoutEmail = Omit<User, "email">;      // 排除指定键
type ById = Record<string, User>;             // 键 string 值 User

// ---------- 2. 函数相关工具类型 ----------
function fetchUser(): Promise<User> { throw new Error("todo"); }
type UserPromise = ReturnType<typeof fetchUser>; // Promise<User>
type FetchArgs = Parameters<typeof fetchUser>;   // []
type AwaitUser = Awaited<UserPromise>;           // User（解包 Promise）

// ---------- 3. 联合操作工具类型 ----------
type Status = "active" | "pending" | "deleted";
type NotDeleted = Exclude<Status, "deleted">;   // "active" | "pending"
type Keep = Extract<Status, "active" | "pending">; // 同上
type MaybeName = NonNullable<string | null | undefined>; // string

// ---------- 4. keyof：取所有键的联合 ----------
type UserKeys = keyof User; // "id" | "name" | "email" | "age"

// ---------- 5. typeof（类型上下文）：取变量的静态类型 ----------
const config = { host: "localhost", port: 5432 };
type Config = typeof config; // { host: string; port: number }

// ---------- 6. 索引访问类型 T[K] ----------
type UserIdType = User["id"];       // number
type UserIdOrName = User["id" | "name"]; // number | string

// ---------- 7. satisfies：校验类型但保留每个属性自己的类型 ----------
// satisfies 会“校验”对象符合目标类型，但不会把每个属性拓宽成联合/注解类型。
const routes = {
  home: "/",
  port: 3000,
} satisfies Record<string, string | number>;

// 每个属性保留自己的具体类型：
const homeStr: string = routes.home; // string（而非 string | number）
const portNum: number = routes.port; // number（而非 string | number）

// 对比：若用“注解”方式，port 会被拓宽成 string | number，需要额外收窄：
// const routes2: Record<string, string | number> = { home: "/", port: 3000 };
// routes2.port.toFixed(); // 报错：string | number 上无 toFixed

// 若想要字面量类型，配合 as const：
const literal = { home: "/" } as const satisfies Record<string, string>;
const homeLiteral: "/" = literal.home; // 此时才是字面量 "/"

// ---------- 8. 组合示例：keyof + 泛型 + 索引访问 ----------
function pick<T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  const result = {} as Pick<T, K>;
  keys.forEach((k) => (result[k] = obj[k]));
  return result;
}
const picked = pick({ id: 1, name: "x", email: "e" }, ["id", "name"]);
// picked 类型为 { id: number; name: string }

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：定义 Todo 接口，然后用 Pick 取 { id, done } 两个字段组成新类型。
// interface Todo { id: number; title: string; done: boolean }
// type TodoSummary = /* 你的代码 */;

// TODO 2：用 Omit 从 Todo 里去掉 title。
// type TodoWithoutTitle = /* 你的代码 */;

// TODO 3：写一个函数，用 keyof 约束第二个参数是对象的键，返回对应值。
// function get<T, K extends keyof T>(obj: T, key: K): T[K] { /* 你的代码 */ }

export {};
