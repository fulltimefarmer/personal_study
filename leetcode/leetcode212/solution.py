"""
考点：字典树、回溯、深度优先搜索、数组、矩阵
题目：Word Search II（单词搜索 II）
题目描述：给定 m×n 字符网格 board 和单词列表 words，找出所有在网格中存在的单词。
  单词由相邻（上下左右）单元格组成，同一单元格不能重复使用。
思路：前缀树（Trie）+ DFS 回溯。先把所有单词插入 Trie，然后遍历网格每个位置开始搜索。
  用 Trie 剪枝：当前前缀不在 Trie 中直接返回。找到单词后从 Trie 中删除或标记，避免重复。
时间复杂度：O(m*n * 4^L)（L 为单词最大长度，Trie 剪枝后实际远小于此）
空间复杂度：O(T)（T 为 Trie 中总字符数）
"""


class TrieNode:
    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.word: str | None = None  # 如果非 None，表示从根到当前节点组成一个完整的单词


def findWords(board: list[list[str]], words: list[str]) -> list[str]:
    # 构建前缀树
    root = TrieNode()
    for w in words:
        node = root
        for ch in w:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.word = w  # 在单词结尾节点存储完整单词

    m, n = len(board), len(board[0])
    result: list[str] = []

    def dfs(i: int, j: int, node: TrieNode) -> None:
        """从 (i,j) 开始深度优先搜索，node 为当前 Trie 节点"""
        ch = board[i][j]
        if ch not in node.children:
            return  # 当前前缀不在 Trie 中，剪枝

        next_node = node.children[ch]
        if next_node.word is not None:
            result.append(next_node.word)  # 找到一个单词
            next_node.word = None  # 标记为已找到，防止重复添加

        # 标记当前格子为已访问（用 # 覆盖原始字符）
        board[i][j] = "#"

        # 向四个方向继续搜索
        for di, dj in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and board[ni][nj] != "#":
                dfs(ni, nj, next_node)

        # 回溯：恢复当前格子字符
        board[i][j] = ch

        # 优化：如果当前 Trie 节点的 children 为空（叶子节点已用完），可以从父节点删除
        if not next_node.children:
            del node.children[ch]

    # 从每个格子开始搜索
    for i in range(m):
        for j in range(n):
            dfs(i, j, root)

    return result


if __name__ == "__main__":
    board1 = [
        ["o", "a", "a", "n"],
        ["e", "t", "a", "e"],
        ["i", "h", "k", "r"],
        ["i", "f", "l", "v"],
    ]
    words1 = ["oath", "pea", "eat", "rain"]
    assert sorted(findWords(board1, words1)) == ["eat", "oath"]

    board2 = [["a", "b"], ["c", "d"]]
    words2 = ["abcb"]
    assert findWords(board2, words2) == []
