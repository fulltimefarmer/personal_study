// Valid Parentheses — 代码空壳（CoderPad 中填充）
// 判断括号字符串是否有效（左括号以正确顺序被同类型右括号闭合）。

function isValid(s: string): boolean {
  // TODO: 用栈保存左括号，遇到右括号匹配栈顶
  return false;
}

// —— 测试（可运行验证）——
function run() {
  console.log(isValid("()"));       // true
  console.log(isValid("()[]{}"));   // true
  console.log(isValid("(]"));       // false
  console.log(isValid("([)]"));     // false
  console.log(isValid("{[]}"));     // true
}

run();
