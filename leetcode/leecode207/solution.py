"""
考点：DFS、BFS、图、拓扑排序
题目：Course Schedule（课程表）
思路：BFS Kahn 算法——构建邻接表和入度数组，入度为 0 的入队，BFS 消去入度，
      最终比较出队数与课程数。
时间复杂度：O(V + E)
空间复杂度：O(V + E)
"""

from collections import deque


def canFinish(numCourses: int, prerequisites: list[list[int]]) -> bool:
    # 构建邻接表：adj[b] 存所有依赖 b 的课程（即 a 依赖 b，b→a）
    adj: list[list[int]] = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses  # 入度数组

    for a, b in prerequisites:
        adj[b].append(a)  # b → a
        indegree[a] += 1  # a 的入度 +1

    # 所有入度为 0 的课程入队（不需要先修课程）
    q = deque(i for i in range(numCourses) if indegree[i] == 0)

    count = 0  # 已完成的课程数
    while q:
        cur = q.popleft()  # Python deque 的 popleft 是 O(1)
        count += 1
        # 遍历当前课程的所有后续课程
        for nxt in adj[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    return count == numCourses  # 所有课程都能完成则无环


if __name__ == "__main__":
    # 示例 1: 2, [[1,0]] → true (0→1 可行)
    assert canFinish(2, [[1, 0]]) is True
    # 示例 2: 2, [[1,0],[0,1]] → false (循环依赖)
    assert canFinish(2, [[1, 0], [0, 1]]) is False
    print("全部测试通过")
