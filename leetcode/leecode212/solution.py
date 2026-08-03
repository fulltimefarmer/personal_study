"""
考点：Trie、数组、字符串、回溯、矩阵
题目：Word Search II（单词搜索 II）
思路：Trie + 回溯。将 words 插入 Trie，遍历 board 每个位置 DFS，
      在 Trie 中匹配路径，找到单词加入结果并标记避免重复。
时间复杂度：O(m×n×4×3^(L-1))
空间复杂度：O(W×L)
"""


class TrieNode:
    """Trie 节点，额外存储完整单词用于结果收集"""

    def __init__(self):
        self.children: list["TrieNode | None"] = [None] * 26
        self.isEnd = False
        self.word = ""  # 在叶节点存储完整单词


def findWords(board: list[list[str]], words: list[str]) -> list[str]:
    # 第一步：将所有单词插入 Trie
    root = TrieNode()
    for word in words:
        node = root
        for ch in word:
            idx = ord(ch) - 97
            if node.children[idx] is None:
                node.children[idx] = TrieNode()
            node = node.children[idx]
        node.isEnd = True
        node.word = word   # 在叶节点存储完整单词，方便直接获取

    m = len(board)
    n = len(board[0])
    result: list[str] = []

    def dfs(i: int, j: int, node: TrieNode) -> None:
        """从 (i,j) 出发，在 Trie 中深度搜索单词"""
        # 越界或当前格子已访问（标记为 '#'）则返回
        if i < 0 or i >= m or j < 0 or j >= n or board[i][j] == "#":
            return

        idx = ord(board[i][j]) - 97
        nxt = node.children[idx]
        if nxt is None:
            return  # Trie 中不存在该路径

        # 找到完整单词，加入结果，并标记 isEnd=False 避免重复收集
        if nxt.isEnd:
            result.append(nxt.word)
            nxt.isEnd = False

        # 回溯：标记当前格子为已访问
        ch = board[i][j]
        board[i][j] = "#"
        # 向四个方向探索
        dfs(i - 1, j, nxt)  # 上
        dfs(i + 1, j, nxt)  # 下
        dfs(i, j - 1, nxt)  # 左
        dfs(i, j + 1, nxt)  # 右
        # 恢复当前格子
        board[i][j] = ch

    # 遍历 board 每个起点
    for i in range(m):
        for j in range(n):
            dfs(i, j, root)

    return result


if __name__ == "__main__":
    # 示例
    board = [["o", "a", "a", "n"], ["e", "t", "a", "e"], ["i", "h", "k", "r"], ["i", "f", "l", "v"]]
    words = ["oath", "pea", "eat", "rain"]
    result = findWords(board, words)
    assert sorted(result) == sorted(["eat", "oath"])
    print("全部测试通过")
