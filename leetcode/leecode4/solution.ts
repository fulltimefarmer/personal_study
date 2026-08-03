/**
 * 考点：Array, Binary Search, Divide and Conquer
 * 题目：Median of Two Sorted Arrays（寻找两个正序数组的中位数）
 * 题目描述：给定两个大小分别为 m 和 n 的正序数组 nums1 和 nums2，找出并返回这两个数组的中位数。
 * 示例：nums1 = [1,3], nums2 = [2] => 2.00000
 * 思路：二分法在较短数组上找分割点，使得左右两部分的最大值 <= 右部分的最小值
 * 时间复杂度：O(log(min(m, n)))
 * 空间复杂度：O(1)
 */
function findMedianSortedArrays(nums1: number[], nums2: number[]): number {
    if (nums1.length > nums2.length) {
        return findMedianSortedArrays(nums2, nums1);
    }

    const m = nums1.length;
    const n = nums2.length;
    const totalLeft = Math.floor((m + n + 1) / 2);

    let left = 0;
    let right = m;

    while (left <= right) {
        const partitionA = Math.floor((left + right) / 2);
        const partitionB = totalLeft - partitionA;

        const maxLeftA = partitionA === 0 ? -Infinity : nums1[partitionA - 1];
        const minRightA = partitionA === m ? Infinity : nums1[partitionA];
        const maxLeftB = partitionB === 0 ? -Infinity : nums2[partitionB - 1];
        const minRightB = partitionB === n ? Infinity : nums2[partitionB];

        if (maxLeftA <= minRightB && maxLeftB <= minRightA) {
            if ((m + n) % 2 === 0) {
                return (Math.max(maxLeftA, maxLeftB) + Math.min(minRightA, minRightB)) / 2;
            }
            return Math.max(maxLeftA, maxLeftB);
        } else if (maxLeftA > minRightB) {
            right = partitionA - 1;
        } else {
            left = partitionA + 1;
        }
    }

    return 0;
}
export { findMedianSortedArrays };
