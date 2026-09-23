class TrieNode:
    """前缀树节点。"""

    def __init__(self) -> None:
        self.children = {}
        self.is_end = False


class Trie:
    """前缀树：支持 insert / search / startsWith。"""

    def __init__(self) -> None:
        """初始化前缀树。"""
        pass

    def insert(self, word: str) -> None:
        """向前缀树中插入字符串 word。"""
        pass

    def search(self, word: str) -> bool:
        """若字符串 word 在前缀树中返回 True，否则 False。"""
        pass

    def startsWith(self, prefix: str) -> bool:
        """若存在以 prefix 为前缀的字符串返回 True，否则 False。"""
        pass
