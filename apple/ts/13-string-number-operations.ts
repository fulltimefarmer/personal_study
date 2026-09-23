// ============================================================
// TypeScript 基础语法 13：字符串 与 数字 的常用操作
// 运行：npx tsx 13-string-number-operations.ts
// ============================================================

// ---------- 1. 字符串基础操作 ----------
const str = "Hello, TypeScript";

const len = str.length; // 长度
const upper = str.toUpperCase(); // 转大写
const lower = str.toLowerCase(); // 转小写
const trimmed = "  hi  ".trim(); // 去首尾空格
const hasSub = str.includes("Type"); // 是否包含子串
const idx = str.indexOf("Type"); // 子串首次出现位置
const starts = str.startsWith("Hello"); // 是否以...开头
const ends = str.endsWith("Script"); // 是否以...结尾

// ---------- 2. 字符串截取与拆分 ----------
const sliced = str.slice(7, 13); // 截取索引 7~12 -> "TypeSc"
const sub = str.substring(7, 13); // 同 slice，但不支持负数索引
const parts = str.split(", "); // 按分隔符拆成数组
const chars = [...str].slice(0, 5).join(""); // 展开成字符数组再拼回

// ---------- 3. 字符串查找与替换 ----------
const replaced = str.replace("TypeScript", "TS"); // 替换第一个匹配
const replacedAll = "a-b-a".replaceAll("a", "x"); // 替换所有匹配
const padded = "42".padStart(5, "0"); // 左侧补 0 到长度5

// ---------- 4. 字符串拼接：模板字符串（反引号） ----------
const product = "iPhone";
const price = 6999;
const message = `${product} 的价格是 ${price} 元`; // ${} 内嵌表达式
const calc = `1 + 2 = ${1 + 2}`; // 支持任意表达式

// ---------- 5. 字符串 ↔ 数字转换 ----------
const numFromStr = parseInt("42"); // 字符串转整数
const floatFromStr = parseFloat("3.14"); // 字符串转浮点
const numCoerce = Number("100"); // Number() 转换
const strFromNum = String(255); // 数字转字符串
const strFromNum2 = (255).toString(); // 另一种写法
const notNum = Number("abc"); // 转失败得到 NaN

// ---------- 6. 数字常用方法与常量 ----------
const fixed = (3.14159).toFixed(2); // 保留2位小数 -> "3.14"
const pi = Math.PI; // 圆周率
const rounded = Math.round(3.6); // 四舍五入
const floored = Math.floor(3.9); // 向下取整
const ceiled = Math.ceil(3.1); // 向上取整
const abs = Math.abs(-5); // 绝对值
const maxVal = Math.max(1, 5, 3); // 最大值
const minVal = Math.min(1, 5, 3); // 最小值
const rand = Math.random(); // 0~1 之间的随机数
const isNaNResult = Number.isNaN(notNum); // 判断是否为 NaN

// ---------- 7. 数组与字符串的互相转换 ----------
const csv = "苹果,香蕉,橘子";
const list = csv.split(","); // 字符串 -> 数组
const backToStr = list.join("|"); // 数组 -> 字符串

// ============================================================
// 验证方法
// ============================================================

function verify(label: string, actual: unknown, expected: unknown): void {
  const pass = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(
    `${pass ? "✅ 通过" : "❌ 失败"} | ${label} | 期望=${JSON.stringify(expected)} 实际=${JSON.stringify(actual)}`
  );
}

verify("字符串长度", len, 17);
verify("转大写", upper, "HELLO, TYPESCRIPT");
verify("转小写", lower, "hello, typescript");
verify("去空格", trimmed, "hi");
verify("包含子串", hasSub, true);
verify("子串位置", idx, 7);
verify("以...开头", starts, true);
verify("以...结尾", ends, true);
verify("slice 截取", sliced, "TypeSc");
verify("substring 截取", sub, "TypeSc");
verify("split 拆分", parts, ["Hello", "TypeScript"]);
verify("replace 替换", replaced, "Hello, TS");
verify("replaceAll 全部替换", replacedAll, "x-b-x");
verify("padStart 补零", padded, "00042");
verify("模板字符串", message, "iPhone 的价格是 6999 元");
verify("模板字符串表达式", calc, "1 + 2 = 3");
verify("parseInt 转整数", numFromStr, 42);
verify("parseFloat 转浮点", floatFromStr, 3.14);
verify("Number 转换", numCoerce, 100);
verify("数字转字符串", strFromNum, "255");
verify("toFixed 保留小数", fixed, "3.14");
verify("四舍五入", rounded, 4);
verify("向下取整", floored, 3);
verify("向上取整", ceiled, 4);
verify("绝对值", abs, 5);
verify("最大值", maxVal, 5);
verify("最小值", minVal, 1);
verify("判断 NaN", isNaNResult, true);
verify("字符串转数组", list, ["苹果", "香蕉", "橘子"]);
verify("数组转字符串", backToStr, "苹果|香蕉|橘子");

export {}; // 让本文件成为模块，避免全局变量冲突
