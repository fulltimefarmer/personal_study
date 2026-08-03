/**
 * 考点：数组、二分查找、动态规划、排序
 * 题目：Russian Doll Envelopes（俄罗斯套娃信封问题）
 * 题目描述：二维信封套娃，要求宽高都更大才能嵌套，求最大信封数
 * 思路：按宽度升序、高度降序排序，对高度求 LIS（贪心+二分）。
 *       降序确保相同宽度的信封不会被同时选中。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(n)
 */
function maxEnvelopes(envelopes: number[][]): number {
    envelopes.sort((a, b) => a[0] - b[0] || b[1] - a[1]);

    const tails: number[] = [];

    for (const [, h] of envelopes) {
        let left = 0, right = tails.length;
        while (left < right) {
            const mid = (left + right) >> 1;
            if (tails[mid] < h) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        tails[left] = h;
    }

    return tails.length;
}

export { maxEnvelopes };
