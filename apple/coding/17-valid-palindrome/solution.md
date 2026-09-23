# Valid Palindrome — 考点分析与解题思路

## 考点分析

1. **双指针跳过无效字符**：`left` 从前往后、`right` 从后往前，各自跳过非字母数字字符后比较。重点在于「原地过滤」而非先构造规范化串（可省 O(n) 额外空间）。
2. **字符判断与归一化**：用 `/[a-z0-9]/i`（或 `isAlphanumeric` 工具函数）判断字母数字；比较前统一转小写 `toLowerCase()`。
3. **边界**：空串 / 全非字母数字 → 视为回文返回 `true`；单字符返回 `true`。
4. **大小写**：`'A'` 与 `'a'` 视为相同。

## 解题思路

### 方案 A：双指针（原地，推荐）

- `left = 0`、`right = s.length - 1`。
- 循环 `left < right`：
  - 左指针跳过非字母数字；右指针跳过非字母数字；
  - 比较 `s[left].toLowerCase()` 与 `s[right].toLowerCase()`，不等则返回 `false`；
  - 相等则 `left++`、`right--`。

### 方案 B：先过滤再反转比较

- 过滤出字母数字并转小写得 `clean`；比较 `clean === clean.split('').reverse().join('')`。代码更短但多一次空间。

## 复杂度

- 时间：O(n)，每个字符最多访问一次。
- 空间：方案 A 为 O(1)；方案 B 为 O(n)。

## 参考代码（双指针）

```ts
function isPalindrome(s: string): boolean {
  let left = 0;
  let right = s.length - 1;

  const isAlnum = (c: string) => /[a-zA-Z0-9]/.test(c);

  while (left < right) {
    while (left < right && !isAlnum(s[left])) left++;
    while (left < right && !isAlnum(s[right])) right--;

    if (s[left].toLowerCase() !== s[right].toLowerCase()) {
      return false;
    }
    left++;
    right--;
  }
  return true;
}
```

## 追问 / Follow-ups

1. **判断子串/删除至多一个字符后是否回文**（LeetCode 680 Valid Palindrome II）？→ 双指针遇到不等时，分别跳过左/右字符递归判断。
2. **最长回文子串**（LeetCode 5）？→ 中心扩展或 Manacher。
3. **回文链表**（LeetCode 234）？→ 快慢指针找中点 + 反转后半段比较。
