/**
 * 考点：Array, Sorting
 * 题目：Merge Intervals（合并区间）
 * 题目描述：给定区间数组 intervals，合并所有重叠区间，返回不重叠的区间数组。
 * 示例：intervals = [[1,3],[2,6],[8,10],[15,18]] → [[1,6],[8,10],[15,18]]
 * 示例：intervals = [[1,4],[4,5]] → [[1,5]]
 * 思路：按起始位置排序后遍历，若当前区间与结果末尾区间重叠则扩展右边界，否则加入新区间。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(n)
 */
function merge(intervals: number[][]): number[][] {
    if (intervals.length === 0) return [];

    intervals.sort((a, b) => a[0] - b[0]);
    const result: number[][] = [intervals[0]];

    for (let i = 1; i < intervals.length; i++) {
        const last = result[result.length - 1];
        const current = intervals[i];

        if (current[0] <= last[1]) {
            last[1] = Math.max(last[1], current[1]);
        } else {
            result.push(current);
        }
    }

    return result;
}

export { merge };
