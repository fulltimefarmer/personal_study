/**
 * 考点：贪心, 数组, 排序
 * 题目：Minimum Number of Arrows to Burst Balloons（用最少数量的箭引爆气球）
 * 题目描述：有一些球形气球 points，points[i] = [x_start, x_end]。一支箭在 x 处射出可引爆满足 x_start <= x <= x_end 的气球。求引爆所有气球的最小弓箭数。
 * 示例：
 *   输入: [[10,16],[2,8],[1,6],[7,12]] → 输出: 2
 *   输入: [[1,2],[3,4],[5,6],[7,8]] → 输出: 4
 * 思路：贪心法。按气球结束位置排序，遍历时如果当前气球开始位置 > 当前箭的位置，需要新箭，更新箭的位置为当前气球结束位置。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(log n)
 */
function findMinArrowShots(points: number[][]): number {
    if (points.length === 0) return 0;

    points.sort((a, b) => a[1] - b[1]);

    let arrows = 1;
    let arrowPos = points[0][1];

    for (let i = 1; i < points.length; i++) {
        if (points[i][0] > arrowPos) {
            arrows++;
            arrowPos = points[i][1];
        }
    }

    return arrows;
}

export { findMinArrowShots };
