/**
 * 考点：Array, Bit Manipulation
 * 题目：Single Number
 * 题目描述：
 * 给你一个非空整数数组 nums，除了某个元素只出现一次以外，其余每个元素均出现两次。找出那个只出现了一次的元素。
 *
 * 你必须设计并实现线性时间复杂度的算法来解决此问题，且该算法只使用常量额外空间。
 *
 * 示例 1：
 * 输入：nums = [2,2,1]
 * 输出：1
 *
 * 示例 2：
 * 输入：nums = [4,1,2,1,2]
 * 输出：4
 *
 * 示例 3：
 * 输入：nums = [1]
 * 输出：1
 *
 * 提示：
 * - 1 <= nums.length <= 3 * 10^4
 * - -3 * 10^4 <= nums[i] <= 3 * 10^4
 * - 除了某个元素只出现一次以外，其余每个元素均出现两次。
 *
 * 思路：
 * 1. 利用异或运算（XOR）的性质：a ^ a = 0，a ^ 0 = a，且运算满足交换律和结合律。
 * 2. 初始化结果变量 result 为 0。
 * 3. 遍历数组中的每个元素 num，将 result 与 num 进行异或运算并保存回 result。
 * 4. 由于出现两次的元素会互相抵消为 0，最后 result 中剩下的就是只出现一次的元素。
 * 5. 返回 result。
 * 数据结构/算法：位运算（XOR）。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
public class Solution {
    public int singleNumber(int[] nums) {
        int result = 0;
        for (int num : nums) {
            result ^= num;
        }
        return result;
    }
}
