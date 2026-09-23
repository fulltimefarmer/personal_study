# Java vs TypeScript 基础语法对比

> 面向「会一门、快速上手另一门」的开发者，只讲**基础用法**的区别，不涉及高级/冷门语法。
> 阅读方式：每一节先给结论，再用 `Java` / `TS` 两段等价代码对照。

## 0. 一句话总览

| 维度 | Java | TypeScript |
| --- | --- | --- |
| 类型系统 | 静态强类型（编译期强制） | 静态类型（可选注解 + 自动推断） |
| 运行方式 | 编译成字节码，跑在 JVM | 编译成 JS，跑在浏览器 / Node |
| 一切皆对象？ | 几乎一切在类里（除了基本类型） | 函数可独立存在，对象可字面量创建 |
| 空值 | 只有 `null` | `null` 和 `undefined` 两种 |
| 相等判断 | `==`（基本类型比值，对象比引用） | `===` 严格相等，`==` 会类型转换 |

---

## 1. 变量声明

**Java**：用「类型名」开头，没有 `let/const`；常量用 `final`。
**TS**：用 `let`（可变）/ `const`（常量）开头，类型写在冒号后，且可省略（自动推断）。

```java
// Java
int age = 30;                 // 基本类型
String name = "Apple";        // 引用类型（首字母大写，是类）
final double PI = 3.14;       // final = 常量
```

```ts
// TypeScript
let age: number = 30;         // 类型注解写在冒号后
const name = "Apple";         // const = 常量，类型自动推断为 string
let price = 9999;             // 可省略类型，推断为 number
```

> 关键差异：Java 类型在前（`int x`），TS 类型在后（`x: number`）。

---

## 2. 基本类型

| 概念 | Java | TypeScript |
| --- | --- | --- |
| 整数 | `int` `long`（还有 `byte/short`） | 统一 `number` |
| 小数 | `float` `double` | 统一 `number` |
| 布尔 | `boolean` | `boolean` |
| 字符 | `char`（单字符） | 无（就是 `string`） |
| 字符串 | `String`（类，首字母大写） | `string`（首字母小写） |
| 任意值 | `Object` | `any` / `unknown` |
| 无返回值 | `void` | `void` |
| 大整数 | `BigInteger` 类 | `bigint` |

```java
// Java：整数分好几种
int a = 1;
long b = 100L;          // 长整型字面量加 L
double c = 3.14;
char d = 'A';           // 单引号，只能一个字符
boolean e = true;
```

```ts
// TypeScript：数字不分家
let a: number = 1;
let b: number = 100;
let c: number = 3.14;   // 整数、小数都叫 number
let d: string = "A";    // 没有 char，字符串统一用 string
let e: boolean = true;
```

---

## 3. 字符串

**Java**：`String` 是类，`+` 拼接；**判断相等要用 `.equals()`**，`==` 比的是引用。
**TS**：`string` 是原始类型，`+` 拼接，还支持反引号模板字符串；用 `===` 直接比内容。

```java
// Java
String s = "Hello" + " " + "World";
boolean same = s.equals("Hello World"); // 正确：比内容
// s == "Hello World"                   // 错误：比引用，通常是 false
```

```ts
// TypeScript
const s = "Hello" + " " + "World";
const same = s === "Hello World";        // 直接 === 比内容
const name = "Apple";
const tpl = `Hi ${name}!`;               // 模板字符串（反引号 + ${}）
```

---

## 4. 数组

**Java**：数组**长度固定**，声明要指定长度或用字面量。
**TS**：数组**长度可变**，字面量创建，可随意增删。

```java
// Java
int[] nums = new int[5];        // 固定长度 5，默认都是 0
nums[0] = 1;
int[] arr = {1, 2, 3};          // 字面量初始化，长度 3 不可变
```

```ts
// TypeScript
let nums: number[] = [1, 2, 3]; // 字面量创建
nums.push(4);                   // 可动态增删
let strs: string[] = ["a", "b"];
```

---

## 5. 函数 / 方法

**Java**：方法必须写在**类里**，有 `static` / 访问修饰符，参数类型在前。
**TS**：函数可**独立声明**，支持箭头函数、可选参数 `?`、默认参数，返回值类型写在后面。

```java
// Java：方法必须在类中
public class Math {
    public static int add(int a, int b) {
        return a + b;
    }
}
// 调用：Math.add(1, 2)
```

```ts
// TypeScript：函数可独立存在
function add(a: number, b: number): number {
    return a + b;
}
// 箭头函数
const add2 = (a: number, b: number): number => a + b;
// 可选参数 与 默认参数
function greet(name: string, title?: string, exclaim = false): string {
    return `${title ?? ""}${name}${exclaim ? "!" : ""}`;
}
```

> Java 用**方法重载**实现可选参数；TS 直接用 `?` 或默认值。

---

## 6. 类

两者语法接近，差异点：

| 点 | Java | TypeScript |
| --- | --- | --- |
| 构造函数 | 方法名 = 类名 | `constructor` 关键字 |
| 字段声明 | 显式类型在前 | 类型在后，可用 `readonly` |
| 访问修饰符 | `public/private/protected` | 同，另有参数属性简写 |
| 继承 | `extends` | `extends` |
| 接口实现 | `implements` | `implements` |

```java
// Java
public class Person {
    private String name;
    public Person(String name) {   // 构造方法名 = 类名
        this.name = name;
    }
    public String getName() { return this.name; }
}
```

```ts
// TypeScript
class Person {
    constructor(private name: string) {} // 参数属性简写，自动声明并赋值
    getName(): string { return this.name; }
}
```

---

## 7. 接口

**Java**：`interface` 定义**方法签名**，类去实现（行为契约）。
**TS**：`interface` 主要定义**对象形状**（有哪些字段），属于**结构化类型**。

```java
// Java：接口定义行为
public interface Greeter {
    String greet(String name);
}
public class Hello implements Greeter {
    public String greet(String name) { return "Hello " + name; }
}
```

```ts
// TypeScript：接口定义对象形状
interface User {
    name: string;
    age: number;
}
const u: User = { name: "Apple", age: 30 }; // 结构匹配即可，无需 implements
```

---

## 8. 对象

**Java**：没有「对象字面量」，必须 `new` 一个类；键值对动态结构常用 `Map`。
**TS**：支持对象字面量 `{ key: value }`，配合 `interface`/`type` 描述形状。

```java
// Java：用 Map 模拟动态键值对
Map<String, Object> user = new HashMap<>();
user.put("name", "Apple");
user.put("age", 30);
```

```ts
// TypeScript：直接字面量
const user = { name: "Apple", age: 30 };
user.name; // 直接访问
```

---

## 9. 相等与比较

**Java**：`==` 对基本类型比**值**，对对象比**引用**（要用 `equals`）。
**TS**：`===` 严格相等（类型 + 值），`==` 会做隐式类型转换（不推荐）。

```java
// Java
int x = 1, y = 1;
boolean a = (x == y);          // true，基本类型比值
String s1 = "a", s2 = "a";
boolean b = s1.equals(s2);     // true，对象要用 equals
```

```ts
// TypeScript
const a = 1 === 1;      // true
const b = "1" === 1;    // false，类型不同
const c = "1" == 1;     // true（== 会转换类型，避免使用）
```

---

## 10. 条件与循环

语法大体相同，差异：

| 点 | Java | TypeScript |
| --- | --- | --- |
| 条件 | `if / else`、三元、`switch` | 同 |
| 遍历值 | `for (int i : arr)` | `for (const x of arr)` |
| 遍历键 | 无（需用索引/迭代器） | `for (const k in obj)` |
| 类 C for | `for (int i=0; i<n; i++)` | 同 |

```java
// Java
for (int n : nums) { System.out.println(n); }
for (int i = 0; i < nums.length; i++) { System.out.println(nums[i]); }
```

```ts
// TypeScript
for (const n of nums) { console.log(n); }   // 遍历值
for (const i in obj) { console.log(i); }    // 遍历键（对象属性名）
for (let i = 0; i < nums.length; i++) { console.log(nums[i]); }
```

---

## 11. 空值

**Java**：只有 `null`。
**TS**：`null` 和 `undefined` 是两种不同的值；`undefined` 通常表示「未定义/未赋值」。

```java
// Java
String s = null;
if (s == null) { /* ... */ }
```

```ts
// TypeScript
let a: null = null;          // 明确的 null
let b: undefined = undefined; // 明确的 undefined
let c;                        // 未赋值，默认 undefined
if (a == null) { /* ... */ }
```

---

## 12. 输出

```java
// Java
System.out.println("Hello");
System.out.print("no newline");
```

```ts
// TypeScript
console.log("Hello");
process.stdout.write("no newline"); // 或 console.log 拼接
```

---

## 13. 类型断言 / 转换

**Java**：`(类型)` 强制转换 + 包装类解析。
**TS**：`as` 类型断言（编译期），或 `Number()`/`parseInt` 做真实转换。

```java
// Java
double d = 3.99;
int i = (int) d;              // 3，强制截断
int n = Integer.parseInt("42"); // 字符串转数字
String s = String.valueOf(42);  // 数字转字符串
```

```ts
// TypeScript
const n = Number("42");       // 42，真实转换
const s = String(42);         // "42"
const id = someValue as number; // 类型断言（编译期，不改变运行时值）
```

---

## 14. 泛型

语法几乎一致（`<T>`），语义上 TS 泛型在编译期被擦除，Java 泛型也擦除但约束略有不同（基础用法无差别）。

```java
// Java
public static <T> T identity(T value) { return value; }
List<String> list = new ArrayList<>();
```

```ts
// TypeScript
function identity<T>(value: T): T { return value; }
const list: Array<string> = [];
```

---

## 15. 模块导入导出

**Java**：`package` + `import`，按包路径导入类。
**TS**：`import` / `export`，按文件路径导入。

```java
// Java
package com.app.util;
import java.util.List;
```

```ts
// TypeScript
import { add } from "./math";
export function hello() {}
export default class App {}
```

---

## 16. 枚举

**Java**：`enum` 是特殊类，值不可变。
**TS**：有 `enum`，但日常更推荐**联合字面量类型**。

```java
// Java
enum Color { RED, GREEN, BLUE }
Color c = Color.RED;
```

```ts
// TypeScript
enum Color { Red, Green, Blue }
const c = Color.Red;
// 更常见的轻量写法：联合字面量
type Color2 = "red" | "green" | "blue";
const c2: Color2 = "red";
```

---

## 17. 速查表（背这页就够）

| 场景 | Java | TypeScript |
| --- | --- | --- |
| 声明变量 | `int x = 1;` | `let x: number = 1;` |
| 常量 | `final int X = 1;` | `const X = 1;` |
| 函数 | `int add(int a,int b){...}` | `const add = (a:number,b:number):number => ...` |
| 字符串相等 | `s.equals("x")` | `s === "x"` |
| 数组 | `int[] a = new int[5];` | `let a: number[] = [];` |
| 空值 | `null` | `null` / `undefined` |
| 打印 | `System.out.println(x)` | `console.log(x)` |
| 遍历 | `for(int i: arr)` | `for (const i of arr)` |
| 类型转换 | `(int)x` | `x as number` |
| 对象 | `new Person()` | `{ name: "x" }` |
