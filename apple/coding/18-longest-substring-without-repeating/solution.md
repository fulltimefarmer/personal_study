# Longest Substring Without Repeating Characters — 考点分析与解题思路

## 考点分析

1. **滑动窗口**：维护一个「无重复字符」的窗口 `[left, right]`，不断右移 `right` 扩展，遇到重复字符时收缩 `left` 直到窗口再次无重复。这是字符串问题的核心模式。
2. **哈希表记录字符位置**：用 `Map<字符, 最近出现下标>`。当 `right` 指向的字符已存在且其位置 `>= left` 时，`left` 跳到该位置 + 1。
3. **窗口长度的维护**：每步用 `right - left + 1` 更新答案 `maxLen`。
4. **为什么 `left` 只需右移不回头**：窗口无重复是「单调」性质，`left` 永不回退，因此每个字符入表/出表各一次，整体 O(n)。

## 解题思路

### 方案 A：哈希表（存下标，推荐）

- `map = new Map<string, number>()`，`left = 0`，`maxLen = 0`。
- 遍历 `right`：
  - 若 `map` 中存在 `s[right]`，`left = Math.max(left, map.get(s[right])! + 1)`；
  - `map.set(s[right], right)`；
  - `maxLen = Math.max(maxLen, right - left + 1)`。

### 方案 B：Set（存字符）

- 用 `Set` 维护窗口内字符，右移 `right` 时若字符已存在，则循环 `left++` 并删除 `s[left]` 直到可加入。思路更直观，但每个字符可能被重复删除。

## 复杂度

- 时间：O(n)，每个字符最多被访问两次（方案 A 一次）。
- 空间：O(min(n, 字符集大小))。

## 参考代码（哈希表）

```ts
function lengthOfLongestSubstring(s: string): number {
  const map = new Map<string, number>();
  let left = 0;
  let maxLen = 0;

  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    if (map.has(ch)) {
      left = Math.max(left, map.get(ch)! + 1);
    }
    map.set(ch, right);
    maxLen = Math.max(maxLen, right - left + 1);
  }
  return maxLen;
}
```

## 追问 / Follow-ups

1. **返回最长子串本身**而非长度？→ 记录 `left`/`right` 对应答案区间即可。
2. **最长含至多 k 个不同字符的子串**（LeetCode 340）？→ 同样滑动窗口，用 `Map` 统计种类，超过 k 时收缩 `left`。
3. **最长含至多 1 个重复字符（可替换 k 次）**（LeetCode 424）？→ 维护「窗口内最多字符频次」，判断 `窗口长 - maxFreq <= k`。
4. 字符集很小（如仅小写字母）？→ 可用定长数组 `number[128]` 替代 Map，空间更省。
