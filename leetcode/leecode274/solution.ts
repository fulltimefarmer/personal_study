/**
 * 考点：数组、计数排序
 * 题目：H-Index（H指数）
 * 题目描述：给定论文引用次数数组，求最大 h，使得至少有 h 篇论文被引用至少 h 次
 * 思路：计数排序。统计每个引用次数的论文数量，从高到低累加，
 *       当累计论文数 >= 当前引用次数时即为 h 指数。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function hIndex(citations: number[]): number {
    const n = citations.length;
    const counts = new Array(n + 1).fill(0);

    for (const c of citations) {
        counts[Math.min(c, n)]++;
    }

    let total = 0;
    for (let i = n; i >= 0; i--) {
        total += counts[i];
        if (total >= i) {
            return i;
        }
    }

    return 0;
}

export { hIndex };
