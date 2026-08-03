/**
 * 考点：Bit Manipulation, Array
 * 题目：Single Number（只出现一次的数字）
 * 题目描述：非空数组，除一个元素出现一次外其余都出现两次，找出那个唯一元素。O(n) 时间，O(1) 空间。
 * 示例 1：[2,2,1]，输出 1
 * 示例 2：[4,1,2,1,2]，输出 4
 * 示例 3：[1]，输出 1
 * 思路：异或，a^a=0, a^0=a。所有数字异或，成对抵消，剩下唯一数字。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function singleNumber(nums: number[]): number {
    let result = 0;
    for (const num of nums) {
        result ^= num;
    }
    return result;
}

export { singleNumber };
