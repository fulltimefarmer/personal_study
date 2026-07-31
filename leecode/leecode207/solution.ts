/**
 * 考点：Graph, BFS, DFS, Topological Sort
 * 题目：Course Schedule
 * 题目描述：
 *   你这个学期必须选修 numCourses 门课程，记为 0 到 numCourses - 1。
 *   在选修某些课程之前需要一些先修课程。先修课程按数组 prerequisites 给出，其中 prerequisites[i] = [ai, bi]，表示如果要学习课程 ai 则必须先学习课程 bi。
 *   请你判断是否可能完成所有课程的学习？如果可以，返回 true；否则，返回 false。
 *   示例 1：输入 numCourses = 2, prerequisites = [[1,0]]，输出 true。
 *   示例 2：输入 numCourses = 2, prerequisites = [[1,0],[0,1]]，输出 false。
 *   提示：1 <= numCourses <= 2000，0 <= prerequisites.length <= 5000，prerequisites[i].length == 2。
 * 思路：
 *   1. 将课程视为图中的节点，先修关系视为有向边（bi -> ai）。
 *   2. 计算每个节点的入度（indegree）。
 *   3. 将所有入度为 0 的节点加入队列，表示可以立即学习的课程。
 *   4. 依次从队列中取出课程，将其后续课程的入度减 1；若后续课程入度变为 0，则加入队列。
 *   5. 统计能学完的课程数，若等于 numCourses，则无环，返回 true；否则返回 false。
 * 数据结构：邻接表 + 入度数组 + 队列 —— 拓扑排序（Kahn's Algorithm）。
 * 时间复杂度：O(V + E)，其中 V 为课程数，E 为先修关系数。
 * 空间复杂度：O(V + E)
 */

function canFinish(numCourses: number, prerequisites: number[][]): boolean {
    const graph: number[][] = Array.from({ length: numCourses }, () => []);
    const indegree: number[] = new Array(numCourses).fill(0);

    for (const [course, prereq] of prerequisites) {
        graph[prereq].push(course);
        indegree[course]++;
    }

    const queue: number[] = [];
    for (let i = 0; i < numCourses; i++) {
        if (indegree[i] === 0) {
            queue.push(i);
        }
    }

    let count = 0;
    while (queue.length > 0) {
        const course = queue.shift()!;
        count++;
        for (const next of graph[course]) {
            indegree[next]--;
            if (indegree[next] === 0) {
                queue.push(next);
            }
        }
    }

    return count === numCourses;
}
