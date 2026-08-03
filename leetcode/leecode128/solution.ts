/**
 * 考点：Union Find, Array, Hash Table
 * 题目：Longest Consecutive Sequence（最长连续序列）
 * 题目描述：找出未排序数组中数字连续的最长序列长度，要求 O(n) 时间。
 * 示例 1：[100,4,200,1,3,2]，输出 4（[1,2,3,4]）
 * 示例 2：[0,3,7,2,5,8,4,6,0,1]，输出 9
 * 思路：HashSet，只有当 num-1 不在集合中时才开始查找，保证每个数字最多访问两次。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function longestConsecutive(nums: number[]): number {
    const numSet = new Set(nums);
    let maxLen = 0;

    for (const num of numSet) {
        if (!numSet.has(num - 1)) {
            let currentNum = num;
            let currentLen = 1;

            while (numSet.has(currentNum + 1)) {
                currentNum++;
                currentLen++;
            }

            maxLen = Math.max(maxLen, currentLen);
        }
    }

    return maxLen;
}

export { longestConsecutive };
