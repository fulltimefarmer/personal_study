"""
考点：DFS、BFS、图、拓扑排序
题目：Course Schedule II（课程表 II）
思路：BFS Kahn 算法，入度为 0 入队，出队加入结果，处理入度。
      结果长度 != numCourses 则返回 []。
时间复杂度：O(V + E)
空间复杂度：O(V + E)
"""

from collections import deque


def findOrder(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    # 构建邻接表和入度数组
    adj: list[list[int]] = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses

    for a, b in prerequisites:
        adj[b].append(a)
        indegree[a] += 1

    # 所有入度为 0 的课程入队
    q = deque(i for i in range(numCourses) if indegree[i] == 0)

    result: list[int] = []  # 存放拓扑排序结果
    while q:
        cur = q.popleft()
        result.append(cur)  # 当前课程入度为 0，可以修读
        for nxt in adj[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    # 如果结果长度 == 总课程数，说明无环，返回排序；否则返回空列表
    return result if len(result) == numCourses else []


if __name__ == "__main__":
    # 示例 1: numCourses=2, prereqs=[[1,0]] → [0,1]
    assert findOrder(2, [[1, 0]]) == [0, 1]
    # 示例 2: numCourses=4, prereqs=[[1,0],[2,0],[3,1],[3,2]] → [0,1,2,3] 或 [0,2,1,3]
    result = findOrder(4, [[1, 0], [2, 0], [3, 1], [3, 2]])
    assert result in ([0, 1, 2, 3], [0, 2, 1, 3])
    # 示例 3: numCourses=1, prereqs=[] → [0]
    assert findOrder(1, []) == [0]
    print("全部测试通过")
