/**
 * 考点：DFS、BFS、图、拓扑排序
 * 题目：Course Schedule（课程表）
 * 题目描述：有 numCourses 门课，prerequisites[i]=[a,b] 表示上 a 前必须先上 b。判断能否完成所有课程（判环）。
 * 示例：numCourses=2,prerequisites=[[1,0],[0,1]] 输出 false
 * 思路：BFS Kahn 算法——构建邻接表和入度数组，入度为 0 的入队，BFS 消去入度，最终比较出队数与课程数。
 * 时间复杂度：O(V + E)
 * 空间复杂度：O(V + E)
 */
function canFinish(numCourses: number, prerequisites: number[][]): boolean {
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

    let count = 0;
    while (queue.length > 0) {
        const cur = queue.shift()!;
        count++;
        for (const next of adj[cur]) {
            indegree[next]--;
            if (indegree[next] === 0) queue.push(next);
        }
    }

    return count === numCourses;
}
export { canFinish };
