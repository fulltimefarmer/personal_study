/**
 * 考点：Array、Sorting
 * 题目：Merge Intervals
 * 题目描述：以数组 intervals 表示若干个区间的集合，其中单个区间为 intervals[i] = [starti, endi]。
 *          请你合并所有重叠的区间，并返回一个不重叠的区间数组，该数组需恰好覆盖输入中的所有区间。
 *          输出可以按任意顺序返回。
 *          示例：输入 intervals = [[1,3],[2,6],[8,10],[15,18]]，输出 [[1,6],[8,10],[15,18]]。
 * 思路：第一步：特判空数组，直接返回空结果。
 *       第二步：将所有区间按左端点 start 升序排序，这样只需比较相邻区间是否重叠。
 *       第三步：初始化结果数组 res，并将排序后的第一个区间加入 res。
 *       第四步：从第二个区间开始遍历：
 *              - 取 res 中最后一个区间 last 和当前区间 curr。
 *              - 若 curr[0] <= last[1]，说明两区间重叠，合并后更新 last[1] = max(last[1], curr[1])。
 *              - 若不重叠，将 curr 直接加入 res。
 *       第五步：遍历结束后返回 res，即为合并后的区间集合。
 * 算法：排序 + 贪心合并。
 * 时间复杂度：O(n log n)，主要由排序决定
 * 空间复杂度：O(log n) ~ O(n)，排序栈空间或输出空间
 */
function merge(intervals: number[][]): number[][] {
    if (intervals.length === 0) return [];
    intervals.sort((a, b) => a[0] - b[0]);
    const res: number[][] = [intervals[0]];
    for (let i = 1; i < intervals.length; i++) {
        const last = res[res.length - 1];
        const curr = intervals[i];
        if (curr[0] <= last[1]) {
            last[1] = Math.max(last[1], curr[1]);
        } else {
            res.push(curr);
        }
    }
    return res;
}
