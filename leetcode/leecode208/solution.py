"""
考点：设计、字典树（Trie）、哈希表、字符串
题目：Implement Trie (Prefix Tree)（实现 Trie 前缀树）
思路：每个节点维护 26 个子节点和 isEnd 标记。
      insert 沿路径创建，search 检查路径+isEnd，startsWith 只检查路径。
时间复杂度：O(L)，L 为单词长度
空间复杂度：O(T)，T 为所有插入单词字符总数
"""


class TrieNode:
    """Trie 节点：26 个子节点 + 单词结束标记"""

    def __init__(self):
        # 用长度为 26 的列表存储子节点，ord(ch)-97 映射 a-z 到 0-25
        self.children: list["TrieNode | None"] = [None] * 26
        self.isEnd = False


class Trie:
    """前缀树实现"""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            idx = ord(ch) - 97  # 'a' 的 ASCII 码是 97
            if node.children[idx] is None:
                node.children[idx] = TrieNode()  # 路径不存在则创建
            node = node.children[idx]            # 沿路径下移
        node.isEnd = True  # 标记单词结束

    def search(self, word: str) -> bool:
        node = self._traverse(word)
        return node is not None and node.isEnd

    def startsWith(self, prefix: str) -> bool:
        return self._traverse(prefix) is not None

    def _traverse(self, s: str) -> "TrieNode | None":
        """沿字符串路径遍历 Trie，返回终点节点或 None"""
        node = self.root
        for ch in s:
            idx = ord(ch) - 97
            if node.children[idx] is None:
                return None  # 路径中断
            node = node.children[idx]
        return node


if __name__ == "__main__":
    trie = Trie()
    trie.insert("apple")
    assert trie.search("apple") is True    # apple 已插入
    assert trie.search("app") is False     # app 不是完整单词
    assert trie.startsWith("app") is True  # app 是前缀
    trie.insert("app")
    assert trie.search("app") is True      # 插入 app 后可以搜到
    print("全部测试通过")
