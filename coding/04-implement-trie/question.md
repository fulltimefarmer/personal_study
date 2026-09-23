# 第 4 题：前缀树（Implement Trie）

## 题目描述

实现一个前缀树（字典树）`Trie`，支持以下操作：

| 方法 | 说明 |
|------|------|
| `insert(word)` | 向前缀树中插入字符串 `word` |
| `search(word)` | 如果字符串 `word` 在前缀树中，返回 `true`；否则返回 `false` |
| `startsWith(prefix)` | 如果之前插入的字符串中存在以 `prefix` 为前缀的，返回 `true`；否则返回 `false` |

### 示例

```text
trie = Trie()
trie.insert("apple")
trie.search("apple")      -> True
trie.search("app")        -> False
trie.startsWith("app")    -> True
trie.insert("app")
trie.search("app")        -> True
```

## 考察点

- 树形结构 + 哈希表的组合
- 用 `is_end` 标记区分"是完整单词"与"只是前缀"

## 解题思路

前缀树的每个节点表示一个字符，从根到某节点的路径组成一个字符串前缀。

1. 节点结构：`children`（子节点映射，`char -> TrieNode`）+ `is_end`（标记该节点是否为一个完整单词的结尾）。
2. `insert`：逐字符向下走，缺失则新建节点，最后一个字符的节点 `is_end = True`。
3. `search`：逐字符向下走，若中途缺失返回 `False`；走完后返回 `is_end`。
4. `startsWith`：与 `search` 类似，但不需要 `is_end`，只要路径存在即可。

### 复杂度

设 `m` 为单词长度：

| 操作 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| insert / search / startsWith | O(m) | O(m) |
| 总空间 | - | O(字符总数) |
