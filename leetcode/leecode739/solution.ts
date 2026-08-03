/**
 * 考点：栈, 数组, 单调栈
 * 题目：Daily Temperatures（每日温度）
 * 题目描述：给定温度数组 temperatures，返回 answer[i] 表示第 i 天后要等几天才能遇到更高的温度。没有更高的则 answer[i]=0。
 * 示例：
 *   输入: [73,74,75,71,69,72,76,73] → 输出: [1,1,4,2,1,1,0,0]
 * 思路：单调递减栈。遍历温度，当栈非空且当前温度>栈顶温度时，弹出栈顶计算出差值。将当前索引入栈。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function dailyTemperatures(temperatures: number[]): number[] {
    const n = temperatures.length;
    const answer: number[] = new Array(n).fill(0);
    const stack: number[] = [];

    for (let i = 0; i < n; i++) {
        while (stack.length > 0 && temperatures[i] > temperatures[stack[stack.length - 1]]) {
            const prevIndex = stack.pop()!;
            answer[prevIndex] = i - prevIndex;
        }
        stack.push(i);
    }

    return answer;
}

export { dailyTemperatures };
