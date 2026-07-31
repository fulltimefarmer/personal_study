/**
 * 考点：Binary Search
 * 题目：Search in Rotated Sorted Array
 * 题目描述：整数数组 nums 按升序排列，数组中的值互不相同。
 *          在传递给函数之前，nums 在预先未知的某个下标 k（0 <= k < nums.length）上进行了旋转，
 *          使数组变为 [nums[k], nums[k+1], ..., nums[n-1], nums[0], nums[1], ..., nums[k-1]]（下标从 0 开始计数）。
 *          例如，[0,1,2,4,5,6,7] 在下标 3 处旋转后可能变为 [4,5,6,7,0,1,2]。
 *          给你旋转后的数组 nums 和一个整数 target。
 *          如果 nums 中存在 target，则返回它的下标；否则返回 -1。
 *          你必须设计一个时间复杂度为 O(log n) 的算法解决此问题。
 * 思路：第一步：初始化 left = 0、right = nums.length - 1，进入二分查找循环。
 *       第二步：计算 mid = left + ((right - left) >> 1)，若 nums[mid] 等于 target 则直接返回 mid。
 *       第三步：比较 nums[mid] 与 nums[right]，判断哪一侧区间保持升序：
 *              - 若 nums[mid] < nums[right]，右半区间 [mid+1, right] 升序。
 *                当 target 位于该区间（nums[mid] < target && target <= nums[right]）时，left = mid + 1；否则 right = mid - 1。
 *              - 否则左半区间 [left, mid] 升序。
 *                当 target 位于该区间（nums[left] <= target && target < nums[mid]）时，right = mid - 1；否则 left = mid + 1。
 *       第四步：循环结束仍未命中则返回 -1。
 * 算法：二分查找 —— 每次将搜索范围减半。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
public class Solution {
    public int search(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        while (left <= right) {
            int mid = left + ((right - left) >> 1);
            if (nums[mid] == target) return mid;
            if (nums[mid] < nums[right]) {
                // 右半部分有序
                if (nums[mid] < target && target <= nums[right]) {
                    left = mid + 1;
                } else {
                    right = mid - 1;
                }
            } else {
                // 左半部分有序
                if (nums[left] <= target && target < nums[mid]) {
                    right = mid - 1;
                } else {
                    left = mid + 1;
                }
            }
        }
        return -1;
    }
}
