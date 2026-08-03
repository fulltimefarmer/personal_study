/**
 * 考点：数组、双指针（快慢指针 / Floyd 判圈算法）
 * 题目：Find the Duplicate Number（寻找重复数）
 * 题目描述：数组中有 n+1 个数，值在 [1,n] 范围，只有一个重复数，找出它。
 *          要求不修改数组，O(1) 额外空间。
 * 思路：将数组看作链表，nums[i] 是 i 的后继。有重复数必成环。
 *       快慢指针找环的入口，即 Floyd 判圈算法。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function findDuplicate(nums: number[]): number {
    let slow = nums[0];
    let fast = nums[0];

    do {
        slow = nums[slow];
        fast = nums[nums[fast]];
    } while (slow !== fast);

    slow = nums[0];
    while (slow !== fast) {
        slow = nums[slow];
        fast = nums[fast];
    }

    return slow;
}

export { findDuplicate };
