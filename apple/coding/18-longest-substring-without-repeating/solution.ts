// Longest Substring Without Repeating Characters — 代码空壳（CoderPad 中填充）
// 返回不含重复字符的最长子串长度。

function lengthOfLongestSubstring(s: string): number {
  // TODO: 滑动窗口 + Map 记录字符最近位置
  return 0;
}

// —— 测试（可运行验证）——
function run() {
  console.log(lengthOfLongestSubstring("abcabcbb")); // 3
  console.log(lengthOfLongestSubstring("bbbbb"));    // 1
  console.log(lengthOfLongestSubstring("pwwkew"));   // 3
  console.log(lengthOfLongestSubstring(""));         // 0
  console.log(lengthOfLongestSubstring(" "));        // 1
}

run();
