"""
考点：设计、字典树、字符串
题目：Implement Trie (Prefix Tree)（实现 Trie/前缀树）
题目描述：实现前缀树的 insert、search、startsWith 三个方法。
思路：每个节点包含一个 children 字典（字符→子节点）和布尔值 is_end（标记是否为一个完整单词）。
  insert：沿字符路径创建节点，最后标记 is_end = True。
  search：沿字符路径查找，最后检查 is_end。
  startsWith：沿字符路径查找，能走完则存在该前缀。
时间复杂度：O(L)（L 为单词长度）
空间复杂度：O(T * 26)（T 为所有插入单词的总字符数）
"""


class TrieNode:
    """Trie 节点：children 存储子节点，is_end 标记是否为单词结尾"""
    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}  # 字符到子节点的映射
        self.is_end: bool = False  # 标记从根到当前节点是否构成一个完整单词


class Trie:
    def __init__(self):
        self.root = TrieNode()  # 根节点不包含任何字符

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()  # 如果字符不存在则创建新节点
            node = node.children[ch]  # 移动到子节点
        node.is_end = True  # 标记单词结束

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False  # 中途字符不存在，单词不存在
            node = node.children[ch]
        return node.is_end  # 走到最后需要检查是否为完整单词（而不仅是前缀）

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False  # 前缀中字符不存在
            node = node.children[ch]
        return True  # 能走到这里说明前缀存在


if __name__ == "__main__":
    trie = Trie()
    trie.insert("apple")
    assert trie.search("apple") is True
    assert trie.search("app") is False  # app 是前缀但不是完整单词
    assert trie.startsWith("app") is True
    trie.insert("app")
    assert trie.search("app") is True
