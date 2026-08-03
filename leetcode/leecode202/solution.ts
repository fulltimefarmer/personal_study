/**
 * 考点：哈希表、数学、双指针
 * 题目：Happy Number（快乐数）
 * 题目描述：判断一个数是否为快乐数：不断替换为每位数字的平方和，最终能否到 1。
 * 示例：n=19 输出 true（1²+9²=82→68→100→1）
 * 思路：快慢指针（Floyd 判圈）。快指针每次算两步，慢指针算一步，相遇时判是否为 1。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function isHappy(n: number): boolean {
    const getNext = (num: number): number => {
        let sum = 0;
        while (num > 0) {
            const digit = num % 10;
            sum += digit * digit;
            num = Math.floor(num / 10);
        }
        return sum;
    };

    let slow = n;
    let fast = getNext(n);

    while (fast !== 1 && slow !== fast) {
        slow = getNext(slow);
        fast = getNext(getNext(fast));
    }

    return fast === 1;
}
export { isHappy };
