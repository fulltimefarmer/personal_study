/**
 * 考点：设计、字典树（Trie）、哈希表、字符串
 * 题目：Implement Trie (Prefix Tree)（实现 Trie 前缀树）
 * 题目描述：实现 insert、search、startsWith 方法。
 * 示例：insert("apple")→search("apple")=true, search("app")=false, startsWith("app")=true
 * 思路：每个节点维护 26 个子节点和 isEnd 标记。insert 沿路径创建，search 检查路径+isEnd，startsWith 只检查路径。
 * 时间复杂度：O(L)，L 为单词长度
 * 空间复杂度：O(T)，T 为所有插入单词字符总数
 */

class TrieNode {
    children: (TrieNode | null)[];
    isEnd: boolean;

    constructor() {
        this.children = new Array(26).fill(null);
        this.isEnd = false;
    }
}

class Trie {
    private root: TrieNode;

    constructor() {
        this.root = new TrieNode();
    }

    insert(word: string): void {
        let node = this.root;
        for (const ch of word) {
            const idx = ch.charCodeAt(0) - 97;
            if (node.children[idx] === null) {
                node.children[idx] = new TrieNode();
            }
            node = node.children[idx]!;
        }
        node.isEnd = true;
    }

    search(word: string): boolean {
        const node = this.traverse(word);
        return node !== null && node.isEnd;
    }

    startsWith(prefix: string): boolean {
        return this.traverse(prefix) !== null;
    }

    private traverse(s: string): TrieNode | null {
        let node = this.root;
        for (const ch of s) {
            const idx = ch.charCodeAt(0) - 97;
            if (node.children[idx] === null) return null;
            node = node.children[idx]!;
        }
        return node;
    }
}

export { Trie };
