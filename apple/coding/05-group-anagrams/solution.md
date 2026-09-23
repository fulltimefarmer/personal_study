# Group Anagrams — 考点分析与解题思路

## 考点分析

1. **哈希 + 归一化键**：字母异位词的共同特征是「字符多重集相同」。把每个词归一化成一个**规范键(canonical key)**，相同键的词分到一组。核心是「如何设计键」。
2. **两种键设计**：
   - **排序键**：把每个字符串的字符排序后作 key（如 `"eat" -> "aet"`）。简单直观，时间 O(k log k)（k 为词长）。
   - **计数键**：用长度 26 的计数数组，转成带分隔符的字符串（如 `"#1#0#...#1"`）作 key。时间 O(k)，且仅在「小写字母」约束下适用。
3. **数据结构**：`Map<string, string[]>`，键为规范键，值为分组。
4. **边界**：空字符串 `""`（排序/计数后键仍有效）、单词很长、只有小写字母（计数法前提）。

## 解题思路

- 创建 `Map`。
- 遍历每个词 `s`：
  - 计算键：方案 A 排序 `s.split('').sort().join('')`；方案 B 计数数组转字符串。
  - `map.get(key)` 不存在则 `map.set(key, [])`，然后 push `s`。
- 返回 `Array.from(map.values())`。

## 复杂度

- 方案 A（排序）：时间 O(n · k log k)，空间 O(n · k)。
- 方案 B（计数）：时间 O(n · k)，空间 O(n · k)。
- 其中 n 为词数，k 为平均词长。

## 参考代码（计数键，O(n·k)）

```ts
function groupAnagrams(strs: string[]): string[][] {
  const map = new Map<string, string[]>();

  for (const s of strs) {
    const counts = new Array(26).fill(0);
    for (const ch of s) {
      counts[ch.charCodeAt(0) - 97]++;
    }
    const key = counts.join('#');          // 如 "1#0#0#...#1"
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(s);
  }

  return Array.from(map.values());
}
```

## 参考代码（排序键，直观）

```ts
function groupAnagrams(strs: string[]): string[][] {
  const map = new Map<string, string[]>();

  for (const s of strs) {
    const key = s.split('').sort().join('');
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(s);
  }

  return Array.from(map.values());
}
```

## 追问 / Follow-ups

1. 排序键 vs 计数键各有什么取舍？→ 排序键更通用（任意字符集）；计数键更快（O(k)）但依赖有限字母表。
2. 若字符串包含大写/Unicode → 计数键需用 `Map<char, count>` 或排序键。
3. 判断两个字符串是否互为异位词（LeetCode 242 Valid Anagram）→ 同款计数法。
4. 找所有异位词在字符串中的起始位置（LeetCode 438）→ 滑动窗口 + 计数匹配。
