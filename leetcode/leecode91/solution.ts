/**
 * 考点：String, Dynamic Programming
 * 题目：Decode Ways（解码方法）
 * 题目描述：数字到字母的映射 A→1,...,Z→26。给定只含数字的字符串 s，计算解码方法总数。
 * 示例：s = "12" → 2（"AB" 或 "L"）
 * 示例：s = "226" → 3（"BZ", "VF", "BBF"）
 * 示例：s = "06" → 0
 * 思路：动态规划。dp[i] = (s[i-1]单独解码?dp[i-1]:0) + (两位数字解码?dp[i-2]:0)。
 *       空间优化为 O(1)。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function numDecodings(s: string): number {
    if (s[0] === '0') return 0;

    let prev2 = 1;
    let prev1 = 1;

    for (let i = 1; i < s.length; i++) {
        let current = 0;

        if (s[i] !== '0') {
            current += prev1;
        }

        const twoDigit = parseInt(s.substring(i - 1, i + 1));
        if (twoDigit >= 10 && twoDigit <= 26) {
            current += prev2;
        }

        prev2 = prev1;
        prev1 = current;
    }

    return prev1;
}

export { numDecodings };
