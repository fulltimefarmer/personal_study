/**
 * 考点：双指针、字符串、动态规划
 * 题目：Is Subsequence（判断子序列）
 * 题目描述：判断 s 是否为 t 的子序列（删除 t 中若干字符得到 s）
 * 思路：双指针。i 指向 s，j 指向 t，匹配时 i++，j 始终前进。
 *       最终若 i === s.length 则为子序列。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function isSubsequence(s: string, t: string): boolean {
    let i = 0, j = 0;

    while (i < s.length && j < t.length) {
        if (s[i] === t[j]) {
            i++;
        }
        j++;
    }

    return i === s.length;
}

export { isSubsequence };
