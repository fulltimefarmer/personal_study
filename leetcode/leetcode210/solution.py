"""
考点：深度优先搜索、广度优先搜索、图、拓扑排序
题目：Course Schedule II（课程表 II）
题目描述：给定课程数 numCourses 和先修条件 prerequisites，返回一种可行的上课顺序。
  示例：numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]] → [0,2,1,3] 或 [0,1,2,3]
思路：拓扑排序（BFS，Kahn 算法）。同 LeetCode 207，但需要记录拓扑序。
时间复杂度：O(V + E)
空间复杂度：O(V + E)
"""

from collections import deque


def findOrder(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    # 邻接表：graph[pre] = [课程序列]
    graph: list[list[int]] = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses

    for course, prereq in prerequisites:
        graph[prereq].append(course)  # 先修 → 后续
        indegree[course] += 1

    # 所有入度为 0 的课程入队（不需要先修课）
    q: deque[int] = deque(i for i in range(numCourses) if indegree[i] == 0)
    order: list[int] = []  # 记录拓扑顺序

    while q:
        curr = q.popleft()
        order.append(curr)  # 当前课程可以上了
        for neighbor in graph[curr]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                q.append(neighbor)

    # 如果完成课程数不等于总数，说明有环，返回空列表
    return order if len(order) == numCourses else []


if __name__ == "__main__":
    res1 = findOrder(2, [[1, 0]])
    assert res1 == [0, 1]
    assert findOrder(4, [[1, 0], [2, 0], [3, 1], [3, 2]]) in ([0, 1, 2, 3], [0, 2, 1, 3])
    assert findOrder(1, []) == [0]
    assert findOrder(2, [[1, 0], [0, 1]]) == []
