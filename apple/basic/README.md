# 基础语法教学 · TS & React Basics

> 本目录是**可动手练习**的 TypeScript 与 React 基础语法教学。
> 每个文件里都用**中文注解**解释语法，附带**可运行的示例代码**，并在文件末尾留了 **`练习`** 区块供你自己补全。

## 目录 / Contents

### TypeScript（`typescript/`）
| 文件 | 主题 |
| --- | --- |
| `01-basic-types.ts` | 基本类型、数组、元组、`any/unknown/never/void` |
| `02-functions.ts` | 函数类型、可选/默认/剩余参数、函数重载 |
| `03-objects-interfaces-types.ts` | 对象类型、`interface`、`type`、只读/可选属性 |
| `04-union-intersection-literal.ts` | 联合类型、交叉类型、字面量类型、`as const` |
| `05-generics.ts` | 泛型函数/接口/约束/类 |
| `06-narrowing-type-guards.ts` | 类型收窄、类型守卫、可辨识联合 |
| `07-utility-types-keyof.ts` | 工具类型、`keyof`/`typeof`/索引访问、`satisfies` |
| `08-advanced-conditional-mapped.ts` | 条件类型、`infer`、映射类型、模板字面量类型 |
| `09-classes.ts` | 类、访问修饰符、继承、抽象类、接口实现、getter/setter |
| `10-modules-enum-decorators.ts` | 模块导入导出、`enum` vs `as const`、类型断言、非空断言 |

### React（`react/`）
| 文件 | 主题 |
| --- | --- |
| `01-jsx-basics.tsx` | JSX 语法、表达式、注释、属性 |
| `02-components-props.tsx` | 函数组件、Props、children |
| `03-state-usestate.tsx` | `useState`、状态更新、不可变更新 |
| `04-effect-useeffect.tsx` | `useEffect`、依赖数组、清理函数 |
| `05-ref-useref.tsx` | `useRef`、访问 DOM、保存可变值 |
| `06-memo-callback.tsx` | `useMemo`、`useCallback`、`React.memo` |
| `07-conditional-lists.tsx` | 条件渲染、列表渲染、`key` |
| `08-events-forms.tsx` | 事件处理、受控组件、表单 |
| `09-context.tsx` | Context、Provider、useContext |
| `10-usereducer.tsx` | `useReducer`、复杂状态管理 |
| `11-custom-hooks.tsx` | 自定义 Hook、复用逻辑 |
| `12-typescript-react.tsx` | TS + React 类型：Props、children、事件、泛型组件 |

### 语言对比（`diff/`）
| 文件 | 主题 |
| --- | --- |
| `01-java-vs-typescript-basic.md` | Java 与 TypeScript 基础语法区别（变量/类型/函数/类/对象等） |

## 怎么练习 / How to Practice

1. **读懂注解**：每个示例都带 `//` 中文注解，先通读理解语法。
2. **运行示例**：
   - TypeScript 文件：`npx tsx typescript/01-basic-types.ts`（或 `npx ts-node`）。
   - React 文件：在 Vite/CRA 项目里引入组件，或复制到在线 Playground（CodeSandbox / StackBlitz）。
3. **做练习**：跳到文件末尾 `练习` 区块，补全 `TODO`，运行验证。
4. **顺序建议**：先 TS 后 React；React 部分依赖 TS 基础。

> 提示：本目录 TS/TSX 文件均保持「可独立运行/复制」，注解用中文，便于面试前快速过一遍语法盲区。
