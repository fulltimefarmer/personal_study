/**
 * 考点：数组、前缀和（前缀积）
 * 题目：Product of Array Except Self（除自身以外数组的乘积）
 * 题目描述：返回数组 answer[i] = 除 nums[i] 外所有元素乘积，不能用除法，O(n)。nums=[1,2,3,4] 输出 [24,12,8,6]
 * 思路：第一遍从左到右累积左乘积存入 answer；第二遍从右到左累积右乘积乘入 answer。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function productExceptSelf(nums: number[]): number[] {
    const n = nums.length;
    const answer: number[] = new Array(n);

    answer[0] = 1;
    for (let i = 1; i < n; i++) {
        answer[i] = answer[i - 1] * nums[i - 1];
    }

    let rightProduct = 1;
    for (let i = n - 1; i >= 0; i--) {
        answer[i] *= rightProduct;
        rightProduct *= nums[i];
    }

    return answer;
}
export { productExceptSelf };
