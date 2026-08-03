# LeetCode 208. Implement Trie (Prefix Tree)（实现 Trie 前缀树） — **中等**

## 考点
设计、字典树（Trie）、哈希表、字符串

## 题目描述
**Trie**（发音类似 "try"）或者说**前缀树**是一种树形数据结构，用于高效地存储和检索字符串数据集中的键。这一数据结构有相当多的应用情景，例如自动补全和拼写检查。

请你实现 Trie 类：
- `Trie()` 初始化前缀树对象。
- `void insert(String word)` 向前缀树中插入字符串 `word`。
- `boolean search(String word)` 如果字符串 `word` 在前缀树中，返回 `true`（即，在检索之前已经插入）；否则，返回 `false`。
- `boolean startsWith(String prefix)` 如果之前已经插入的字符串 `word` 的前缀之一为 `prefix`，返回 `true`；否则，返回 `false`。

**示例：**
```
输入：
["Trie", "insert", "search", "search", "startsWith", "insert", "search"]
[[], ["apple"], ["apple"], ["app"], ["app"], ["app"], ["app"]]
输出：
[null, null, true, false, true, null, true]

解释：
Trie trie = new Trie();
trie.insert("apple");
trie.search("apple");   // 返回 True
trie.search("app");     // 返回 False
trie.startsWith("app"); // 返回 True
trie.insert("app");
trie.search("app");     // 返回 True
```

**提示：**
- `1 <= word.length, prefix.length <= 2000`
- `word` 和 `prefix` 仅由小写英文字母组成
- `insert`、`search` 和 `startsWith` 调用次数**总计**不超过 `3 * 10^4` 次

## 解题思路

### 核心思路

Trie（前缀树/字典树）是一种多叉树，每个节点代表一个字符。从根到某节点的路径表示一个前缀。Trie 的核心是快速判断某个字符串或前缀是否存在于树中。

### 数据结构设计

每个 Trie 节点包含：
- `children[26]`：子节点数组，索引对应 'a'~'z'
- `isEnd`：布尔值，标记当前节点是否是一个完整单词的结尾

### 算法步骤

**`insert(word)`**：
1. 从根节点开始 `node = root`
2. 对 word 中每个字符 c：
   - `idx = c - 'a'`
   - 若 `node.children[idx]` 为空，创建新节点
   - `node = node.children[idx]`
3. 设置 `node.isEnd = true`

**`search(word)`**：
1. 从根开始，逐字符向下查找
2. 若某字符对应子节点为空 → 返回 false
3. 到达末尾后检查 `node.isEnd`

**`startsWith(prefix)`**：
1. 与 search 类似，但只要求路径存在，不检查 `isEnd`

### 图解示例

**操作序列**: `insert("apple") → search("apple") → search("app") → startsWith("app") → insert("app") → search("app")`

```
Trie 结构演变:

┌──────────────────────────────────┐
│ insert("apple") 后:              │
│                                   │
│   root                            │
│    │                              │
│    a (children['a'])             │
│    │                              │
│    p                              │
│    │                              │
│    p                              │
│    │                              │
│    l                              │
│    │                              │
│    e ← isEnd=true                │
│                                   │
│ 路径: a→p→p→l→e                 │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ insert("app") 后:                │
│                                   │
│   root                            │
│    │                              │
│    a                              │
│    │                              │
│    p                              │
│    │                              │
│    p ← isEnd=true (新增!)       │
│    │                              │
│    l                              │
│    │                              │
│    e ← isEnd=true                │
│                                   │
│ 树中存储: "app", "apple"         │
│                                    │
│ search("apple") → e.isEnd=true ✓  │
│ search("app")   → p.isEnd=true ✓  │
│ startsWith("ap") → 路径存在 ✓     │
└──────────────────────────────────┘
```

**Trie 通用结构示例（存储 "cat", "car", "dog"）：**

```
        root
      /   |   \
     c    d    ... (其余23个子节点为null)
    /     |
   a      o
  / \     |
 t*  r*   g*
(* = isEnd=true)

查询过程：
  search("cat"): root→c→a→t → t.isEnd=true → true
  search("ca"):  root→c→a → a.isEnd=false → false
  startsWith("ca"): root→c→a → 路径存在 → true
```

### 逐步追踪表

| 操作 | 遍历路径 | 终点 isEnd | 结果 | 说明 |
|------|---------|-----------|------|------|
| insert("apple") | a→p→p→l→e | 设e.isEnd=true | — | 创建全部5个新节点 |
| search("apple") | a→p→p→l→e | true | true | 完整匹配 |
| search("app") | a→p→p | false | false | 是前缀但不是单词 |
| startsWith("app") | a→p→p | — | true | 前缀存在 |
| insert("app") | a→p→p | 设p.isEnd=true | — | 复用已有路径 |
| search("app") | a→p→p | true | true | 现在是一个完成单词了 |

### 边界情况

| 场景 | 处理 |
|------|------|
| 空字符串插入 | 根据题目约定（一般不插入空串）；若插入则 root.isEnd=true |
| 重复插入同一单词 | 遍历已有路径，将末尾 isEnd 设为 true（幂等操作） |
| 搜索比已存单词长的前缀 | 走到中途子节点为空，返回 false |
| 单字符单词 | 如 "a"，root→a，设置 a.isEnd=true |

### 复杂度分析

| 操作 | 时间复杂度 | 说明 |
|------|-----------|------|
| insert | O(L) | L = 单词长度 |
| search | O(L) | 一次遍历单词路径 |
| startsWith | O(L) | 同上 |
| 空间复杂度 | O(T) | T = 所有插入单词的字符总数 |
