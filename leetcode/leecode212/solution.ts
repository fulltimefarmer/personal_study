/**
 * 考点：Trie、数组、字符串、回溯、矩阵
 * 题目：Word Search II（单词搜索 II）
 * 题目描述：在二维字符网格中找出所有在字典 words 中的单词。board=[["o","a","a","n"],["e","t","a","e"],...],words=["oath","pea","eat","rain"] 输出 ["eat","oath"]
 * 思路：Trie + 回溯。将 words 插入 Trie，遍历 board 每个位置 DFS，在 Trie 中匹配路径，找到单词加入结果并标记避免重复。
 * 时间复杂度：O(m×n×4×3^(L-1))
 * 空间复杂度：O(W×L)
 */

class TrieNode212 {
    children: (TrieNode212 | null)[];
    isEnd: boolean;
    word: string;

    constructor() {
        this.children = new Array(26).fill(null);
        this.isEnd = false;
        this.word = '';
    }
}

function findWords(board: string[][], words: string[]): string[] {
    const root = new TrieNode212();
    for (const word of words) {
        let node = root;
        for (const ch of word) {
            const idx = ch.charCodeAt(0) - 97;
            if (node.children[idx] === null) {
                node.children[idx] = new TrieNode212();
            }
            node = node.children[idx]!;
        }
        node.isEnd = true;
        node.word = word;
    }

    const result: string[] = [];
    const m = board.length;
    const n = board[0].length;

    const dfs = (i: number, j: number, node: TrieNode212): void => {
        if (i < 0 || i >= m || j < 0 || j >= n || board[i][j] === '#') return;
        const idx = board[i][j].charCodeAt(0) - 97;
        const next = node.children[idx];
        if (next === null) return;

        if (next.isEnd) {
            result.push(next.word);
            next.isEnd = false;
        }

        const char = board[i][j];
        board[i][j] = '#';
        dfs(i - 1, j, next);
        dfs(i + 1, j, next);
        dfs(i, j - 1, next);
        dfs(i, j + 1, next);
        board[i][j] = char;
    };

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            dfs(i, j, root);
        }
    }

    return result;
}
export { findWords };
