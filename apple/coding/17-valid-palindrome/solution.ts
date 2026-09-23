// Valid Palindrome — 代码空壳（CoderPad 中填充）
// 忽略非字母数字字符与大小写，判断是否为回文。

function isPalindrome(s: string): boolean {
  // TODO: 双指针跳过非字母数字字符，转小写比较
  return false;
}

// —— 测试（可运行验证）——
function run() {
  console.log(isPalindrome("A man, a plan, a canal: Panama")); // true
  console.log(isPalindrome("race a car"));                     // false
  console.log(isPalindrome(" "));                              // true
  console.log(isPalindrome("0P"));                             // false
}

run();
