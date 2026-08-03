/**
 * 考点：Array, Two Pointers, Sorting
 * 题目：Merge Sorted Array（合并两个有序数组）
 * 题目描述：两个非递减数组 nums1(m 个有效元素) 和 nums2(n 个)，合并到 nums1 中保持非递减。
 *       nums1 的长度为 m+n，后 n 位为 0 占位。
 * 示例：nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3 → [1,2,2,3,5,6]
 * 思路：双指针从后向前。p1=m-1, p2=n-1, p=m+n-1，较大值填入末尾。
 *       从后向前避免覆盖 nums1 中未处理的元素。
 * 时间复杂度：O(m + n)
 * 空间复杂度：O(1)
 */
function merge_(nums1: number[], m: number, nums2: number[], n: number): void {
    let p1 = m - 1;
    let p2 = n - 1;
    let p = m + n - 1;

    while (p2 >= 0) {
        if (p1 >= 0 && nums1[p1] > nums2[p2]) {
            nums1[p] = nums1[p1];
            p1--;
        } else {
            nums1[p] = nums2[p2];
            p2--;
        }
        p--;
    }
}

export { merge_ };
