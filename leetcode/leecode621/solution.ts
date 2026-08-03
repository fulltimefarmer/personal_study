/**
 * 考点：贪心, 数组, 哈希表, 计数, 排序, 堆
 * 题目：Task Scheduler（任务调度器）
 * 题目描述：给定 CPU 任务列表 tasks（A-Z）和冷却时间 n。相同任务间必须间隔 n 个单位时间。求完成所有任务的最短时间。
 * 示例：
 *   输入: tasks=["A","A","A","B","B","B"], n=2 → 输出: 8
 * 思路：公式法。统计最高频任务次数 maxCount 和出现 maxCount 次的任务数 maxFreqTasks。最少时间 = max((maxCount-1)*(n+1)+maxFreqTasks, tasks.length)。
 * 时间复杂度：O(N)
 * 空间复杂度：O(1)
 */
function leastInterval(tasks: string[], n: number): number {
    const freq: number[] = new Array(26).fill(0);

    for (const task of tasks) {
        freq[task.charCodeAt(0) - 'A'.charCodeAt(0)]++;
    }

    const maxCount = Math.max(...freq);
    let maxFreqTasks = 0;
    for (const f of freq) {
        if (f === maxCount) maxFreqTasks++;
    }

    const minTime = (maxCount - 1) * (n + 1) + maxFreqTasks;
    return Math.max(minTime, tasks.length);
}

export { leastInterval };
