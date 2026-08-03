/**
 * 考点：数组、分治、快速选择（Quickselect）、排序、堆
 * 题目：Kth Largest Element in an Array（数组中的第 K 个最大元素）
 * 题目描述：找数组中第 k 大的元素。nums=[3,2,1,5,6,4],k=2 输出 5
 * 思路：快速选择。三路分区——大于/等于/小于 pivot，根据各部分长度决定在哪一部分继续查找。
 *       第 k 大 = 第 n-k 小（从 0 开始），因此 targetIdx = n - k。
 * 时间复杂度：平均 O(n)，最坏 O(n²)
 * 空间复杂度：O(log n)（递归栈）
 */
function findKthLargest(nums: number[], k: number): number {
    const n = nums.length;
    const targetIdx = n - k;

    const quickSelect = (left: number, right: number): number => {
        if (left === right) return nums[left];

        const pivot = nums[Math.floor(Math.random() * (right - left + 1)) + left];
        let lt = left;
        let gt = right;
        let i = left;

        while (i <= gt) {
            if (nums[i] < pivot) {
                [nums[lt], nums[i]] = [nums[i], nums[lt]];
                lt++;
                i++;
            } else if (nums[i] > pivot) {
                [nums[gt], nums[i]] = [nums[i], nums[gt]];
                gt--;
            } else {
                i++;
            }
        }

        if (targetIdx >= lt && targetIdx <= gt) return nums[targetIdx];
        if (targetIdx < lt) return quickSelect(left, lt - 1);
        return quickSelect(gt + 1, right);
    };

    return quickSelect(0, n - 1);
}
export { findKthLargest };
