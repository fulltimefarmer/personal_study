/**
 * 考点：树、DFS、设计、字符串、二叉树
 * 题目：Serialize and Deserialize Binary Tree（二叉树的序列化与反序列化）
 * 题目描述：设计算法将二叉树序列化为字符串并能反序列化还原
 * 思路：前序遍历 DFS。序列化时用 "null" 标记空节点，逗号分隔。
 *       反序列化时递归按前序构建，遇到 "null" 返回 null。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */

class TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
    constructor(val?: number, left?: TreeNode | null, right?: TreeNode | null) {
        this.val = val === undefined ? 0 : val;
        this.left = left === undefined ? null : left;
        this.right = right === undefined ? null : right;
    }
}

function serialize(root: TreeNode | null): string {
    const result: string[] = [];

    function dfs(node: TreeNode | null) {
        if (node === null) {
            result.push('null');
            return;
        }
        result.push(String(node.val));
        dfs(node.left);
        dfs(node.right);
    }

    dfs(root);
    return result.join(',');
}

function deserialize(data: string): TreeNode | null {
    const nodes = data.split(',');
    let index = 0;

    function dfs(): TreeNode | null {
        if (nodes[index] === 'null') {
            index++;
            return null;
        }
        const node = new TreeNode(Number(nodes[index]));
        index++;
        node.left = dfs();
        node.right = dfs();
        return node;
    }

    return dfs();
}

export { serialize, deserialize, TreeNode };
