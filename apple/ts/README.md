# TypeScript 基础语法学习

本目录包含一系列 **可运行** 的 TypeScript 文件，覆盖日常开发中最常用的语法（数组、循环、函数、对象、类型、泛型、类、异步等）。

每个文件都具备以下特点：

1. **中文注释**：每一处代码都有中文注解，解释语法和作用。
2. **验证方法**：文件末尾有一个「验证」区块，用内置的 `verify` 函数自动比较「期望值」和「实际值」，运行后一眼看出哪些通过（✅）、哪些失败（❌）。

## 文件清单

| 文件 | 内容 |
| --- | --- |
| `01-basic-types.ts` | 基础类型（string/number/boolean/null/undefined/bigint/symbol/any/unknown/never/void）与类型推断 |
| `02-arrays-basics.ts` | 数组基础：创建、访问、长度、二维数组、元组 |
| `03-array-add-remove.ts` | 数组增删改查：push/pop/shift/unshift/splice/slice/concat/indexOf/includes/join |
| `04-array-higher-order.ts` | 数组高阶函数：map/filter/reduce/find/findIndex/some/every/sort/reverse/forEach |
| `05-loops.ts` | 循环：for/while/do-while/for...of/for...in/break/continue/标签 |
| `06-functions.ts` | 函数：声明/表达式/箭头/默认值/可选参数/剩余参数/重载 |
| `07-objects-interfaces.ts` | 对象、interface、type、可选属性、只读属性、索引签名 |
| `08-union-intersection-literal.ts` | 联合类型、交叉类型、字面量类型 |
| `09-type-narrowing.ts` | 类型收窄：typeof/instanceof/in/自定义类型守卫/类型断言 |
| `10-generics.ts` | 泛型：函数/接口/类/约束/默认值 |
| `11-classes.ts` | 类：构造器/访问修饰符/继承/抽象/getter-setter/静态成员 |
| `12-tuples-enums.ts` | 元组与枚举（含常量枚举的现代写法） |
| `13-string-number-operations.ts` | 字符串与数字的常用操作方法 |
| `14-async-promise.ts` | 异步：Promise/async/await/错误处理 |

## 如何运行

先安装依赖（只需一次）：

```bash
cd apple/ts
npm install
```

然后运行单个文件：

```bash
npx tsx 01-basic-types.ts
```

运行全部文件并统一验证：

```bash
npm run verify
```

只做类型检查（不运行）：

```bash
npm run typecheck
```

> 提示：如果你的 Node 版本 ≥ 24，也可以直接用 `node 01-basic-types.ts` 运行（Node 原生支持类型擦除）。
