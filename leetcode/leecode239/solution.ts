/**
 * 考点：队列、数组、滑动窗口、单调队列、堆
 * 题目：Sliding Window Maximum（滑动窗口最大值）
 * 题目描述：大小为 k 的滑动窗口从左到右移动，返回每个窗口的最大值。nums=[1,3,-1,-3,5,3,6,7],k=3 输出 [3,3,5,5,6,7]
 * 思路：单调递减双端队列存索引。移除过期索引；移除队尾所有小于当前值的索引；队首即为当前窗口最大值。
 * 时间复杂度：O(n)
 * 空间复杂度：O(k)
 */
function maxSlidingWindow(nums: number[], k: number): number[] {
    const n = nums.length;
    const result: number[] = new Array(n - k + 1);
    const deque: number[] = [];
    let idx = 0;

    for (let i = 0; i < n; i++) {
        while (deque.length > 0 && deque[0] <= i - k) {
            deque.shift();
        }

        while (deque.length > 0 && nums[deque[deque.length - 1]] < nums[i]) {
            deque.pop();
        }

        deque.push(i);

        if (i >= k - 1) {
            result[idx++] = nums[deque[0]];
        }
    }

    return result;
}
export { maxSlidingWindow };
