/**
 * 考点：Array、Sorting
 * 题目：Merge Intervals
 * 题目描述：以数组 intervals 表示若干个区间的集合，其中单个区间为 intervals[i] = [starti, endi]。
 *          请你合并所有重叠的区间，并返回一个不重叠的区间数组，该数组需恰好覆盖输入中的所有区间。
 *          输出可以按任意顺序返回。
 *          示例：输入 intervals = [[1,3],[2,6],[8,10],[15,18]]，输出 [[1,6],[8,10],[15,18]]。
 * 思路：第一步：若 intervals 为空，直接返回 new int[0][2]。
 *       第二步：按区间左端点升序排序，确保只需比较相邻区间。
 *       第三步：创建 List<int[]> res，将排序后的第一个区间加入其中。
 *       第四步：从 i = 1 开始遍历剩余区间：
 *              - 取出 res 中最后一个区间 last 和当前区间 curr。
 *              - 若 curr[0] <= last[1]，说明重叠，更新 last[1] = Math.max(last[1], curr[1])。
 *              - 否则将 curr 加入 res。
 *       第五步：将 res 转换为 int[][] 返回。
 * 算法：排序 + 贪心合并。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(log n) ~ O(n)
 */
import java.util.*;

public class Solution {
    public int[][] merge(int[][] intervals) {
        if (intervals.length == 0) return new int[0][2];
        Arrays.sort(intervals, (a, b) -> a[0] - b[0]);
        List<int[]> res = new ArrayList<>();
        res.add(intervals[0]);
        for (int i = 1; i < intervals.length; i++) {
            int[] last = res.get(res.size() - 1);
            int[] curr = intervals[i];
            if (curr[0] <= last[1]) {
                last[1] = Math.max(last[1], curr[1]);
            } else {
                res.add(curr);
            }
        }
        return res.toArray(new int[res.size()][]);
    }
}
