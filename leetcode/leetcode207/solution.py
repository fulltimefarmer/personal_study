"""
考点：深度优先搜索、广度优先搜索、图、拓扑排序
题目：Course Schedule（课程表）
题目描述：给定课程数 numCourses 和先修条件 prerequisites，判断是否可以完成所有课程（无环）。
  示例：numCourses = 2, prerequisites = [[1,0]] → true（先修 0 再修 1）
思路：拓扑排序（BFS/DFS）。构建邻接表和入度数组。
  将所有入度为 0 的节点入队，依次取出，将其后继节点入度减 1，入度为 0 时入队。
  最终访问节点数 == numCourses 则无环。
时间复杂度：O(V + E)
空间复杂度：O(V + E)
"""

from collections import deque


def canFinish(numCourses: int, prerequisites: list[list[int]]) -> bool:
    # 邻接表：graph[course] = [后续课程列表]
    graph: list[list[int]] = [[] for _ in range(numCourses)]
    # indegree[i] 表示课程 i 的入度（有多少先修课）
    indegree = [0] * numCourses

    for course, prereq in prerequisites:
        graph[prereq].append(course)  # 先修课指向后续课
        indegree[course] += 1  # 后续课的入度加 1

    # BFS 拓扑排序：将所有入度为 0 的课程（无先修要求）入队
    q: deque[int] = deque(i for i in range(numCourses) if indegree[i] == 0)

    visited = 0  # 记录已完成的课程数
    while q:
        curr = q.popleft()  # 取出一个无先修要求的课程
        visited += 1
        for neighbor in graph[curr]:
            indegree[neighbor] -= 1  # 当前课修完，后续课少一个先修
            if indegree[neighbor] == 0:  # 后续课的先修全部满足
                q.append(neighbor)

    return visited == numCourses  # 全部修完说明无环


if __name__ == "__main__":
    assert canFinish(2, [[1, 0]]) is True
    assert canFinish(2, [[1, 0], [0, 1]]) is False
    assert canFinish(1, []) is True
