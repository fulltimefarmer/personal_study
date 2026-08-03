/**
 * 考点：数组、数学、双指针
 * 题目：Rotate Array（轮转数组）
 * 题目描述：将数组向右轮转 k 步。nums=[1,2,3,4,5,6,7],k=3 输出 [5,6,7,1,2,3,4]
 * 思路：三次反转法——反转整个数组，反转前 k 个，反转后 n-k 个。O(1) 空间。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function rotate(nums: number[], k: number): void {
    const n = nums.length;
    k = k % n;

    const reverse = (start: number, end: number): void => {
        while (start < end) {
            [nums[start], nums[end]] = [nums[end], nums[start]];
            start++;
            end--;
        }
    };

    reverse(0, n - 1);
    reverse(0, k - 1);
    reverse(k, n - 1);
}
export { rotate };
