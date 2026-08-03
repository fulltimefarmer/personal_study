/**
 * 考点：Array, Binary Search, Divide and Conquer
 * 题目：Median of Two Sorted Arrays（寻找两个正序数组的中位数）
 * 题目描述：求两个正序数组合并后的中位数。O(log(m+n))。如 [1,3] 和 [2] → 2.0
 * 思路：在较短数组上二分查找划分位置，使得左半部分都≤右半部分。边界用±Infinity处理。
 * 时间复杂度：O(log(min(m, n)))
 * 空间复杂度：O(1)
 */
function findMedianSortedArrays(nums1: number[], nums2: number[]): number {
    if (nums1.length > nums2.length) {
        return findMedianSortedArrays(nums2, nums1);
    }

    const m = nums1.length;
    const n = nums2.length;
    let low = 0;
    let high = m;

    while (low <= high) {
        const partitionX = Math.floor((low + high) / 2);
        const partitionY = Math.floor((m + n + 1) / 2) - partitionX;

        const maxLeftX = partitionX === 0 ? -Infinity : nums1[partitionX - 1];
        const minRightX = partitionX === m ? Infinity : nums1[partitionX];
        const maxLeftY = partitionY === 0 ? -Infinity : nums2[partitionY - 1];
        const minRightY = partitionY === n ? Infinity : nums2[partitionY];

        if (maxLeftX <= minRightY && maxLeftY <= minRightX) {
            if ((m + n) % 2 === 0) {
                return (Math.max(maxLeftX, maxLeftY) + Math.min(minRightX, minRightY)) / 2;
            } else {
                return Math.max(maxLeftX, maxLeftY);
            }
        } else if (maxLeftX > minRightY) {
            high = partitionX - 1;
        } else {
            low = partitionX + 1;
        }
    }

    return 0;
}

export { findMedianSortedArrays };
