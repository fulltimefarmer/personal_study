/**
 * 考点：DFS、BFS、图、拓扑排序
 * 题目：Course Schedule II（课程表 II）
 * 题目描述：与 207 类似，但需要返回任意一种拓扑排序序列；无法完成时返回空数组。
 * 示例：numCourses=4,prerequisites=[[1,0],[2,0],[3,1],[3,2]] 输出 [0,1,2,3] 或 [0,2,1,3]
 * 思路：BFS Kahn 算法，入度为 0 入队，出队加入结果，处理入度。结果长度 != numCourses 则返回 []。
 * 时间复杂度：O(V + E)
 * 空间复杂度：O(V + E)
 */
function findOrder(numCourses: number, prerequisites: number[][]): number[] {
    const adj: number[][] = Array.from({ length: numCourses }, () => []);
    const indegree: number[] = new Array(numCourses).fill(0);

    for (const [a, b] of prerequisites) {
        adj[b].push(a);
        indegree[a]++;
    }

    const queue: number[] = [];
    for (let i = 0; i < numCourses; i++) {
        if (indegree[i] === 0) queue.push(i);
    }

    const result: number[] = [];
    while (queue.length > 0) {
        const cur = queue.shift()!;
        result.push(cur);
        for (const next of adj[cur]) {
            indegree[next]--;
            if (indegree[next] === 0) queue.push(next);
        }
    }

    return result.length === numCourses ? result : [];
}
export { findOrder };
