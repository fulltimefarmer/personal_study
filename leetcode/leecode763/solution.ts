/**
 * 考点：贪心, 哈希表, 双指针, 字符串
 * 题目：Partition Labels（划分字母区间）
 * 题目描述：将字符串划分为尽可能多的片段，使每个字母最多出现在一个片段中。返回每个片段的长度。
 * 示例：
 *   输入: "ababcbacadefegdehijhklij" → 输出: [9,7,8]
 * 思路：记录每个字符最后出现的位置 lastPos。遍历时维护当前片段的最远边界 end。当 i==end 时切分，记录长度。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function partitionLabels(s: string): number[] {
    const lastPos: number[] = new Array(26).fill(0);
    const aCode = 'a'.charCodeAt(0);

    for (let i = 0; i < s.length; i++) {
        lastPos[s.charCodeAt(i) - aCode] = i;
    }

    const result: number[] = [];
    let start = 0;
    let end = 0;

    for (let i = 0; i < s.length; i++) {
        end = Math.max(end, lastPos[s.charCodeAt(i) - aCode]);
        if (i === end) {
            result.push(end - start + 1);
            start = i + 1;
        }
    }

    return result;
}

export { partitionLabels };
