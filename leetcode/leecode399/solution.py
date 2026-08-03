"""
考点：DFS、BFS、并查集、图
题目：Evaluate Division（除法求值）—— LeetCode 399
题目描述：给定变量间的除法等式，回答多个除法查询
思路：带权并查集。每个节点维护 weight[x] = x / parent[x]。
      find 路径压缩时更新权重，union 合并集合。
      查询时同集合则返回 weight[a] / weight[b]。
时间复杂度：O((E + Q) × α(V))
空间复杂度：O(V)
"""

def calcEquation(
    equations: list[list[str]],
    values: list[float],
    queries: list[list[str]],
) -> list[float]:
    # parent[x] 表示 x 在并查集中的父节点
    parent: dict[str, str] = {}
    # weight[x] 表示 x / parent[x] 的值
    weight: dict[str, float] = {}

    def find(x: str) -> str:
        """带权并查集的 find，路径压缩时更新权重"""
        # 首次遇到的变量，初始化为自身根节点，权重为 1
        if x not in parent:
            parent[x] = x
            weight[x] = 1.0

        if parent[x] != x:
            # 递归找根节点，同时进行路径压缩
            root = find(parent[x])
            # 权重更新：x/root = (x/parent) * (parent/root)
            weight[x] = weight[x] * weight[parent[x]]
            parent[x] = root

        return parent[x]

    def union(a: str, b: str, val: float) -> None:
        """合并两个集合，已知 a / b = val"""
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            # 将 root_a 挂到 root_b 下面
            parent[root_a] = root_b
            # 权重计算：w[root_a] = root_a/root_b
            # 已知 a/b=val, a/root_a=w[a], b/root_b=w[b]
            # root_a/root_b = (root_a/a) * (a/b) * (b/root_b) = (1/w[a]) * val * w[b]
            weight[root_a] = (val * weight[b]) / weight[a]

    # 第一步：构建带权并查集
    for (a, b), val in zip(equations, values):
        union(a, b, val)

    # 第二步：处理查询
    result: list[float] = []
    for c, d in queries:
        # 如果查询中有未出现的变量，返回 -1.0
        if c not in parent or d not in parent:
            result.append(-1.0)
            continue

        root_c = find(c)
        root_d = find(d)
        if root_c != root_d:
            # 不在同一连通分量，无法计算
            result.append(-1.0)
        else:
            # c/d = (c/root) / (d/root) = weight[c] / weight[d]
            result.append(weight[c] / weight[d])

    return result


if __name__ == "__main__":
    equations = [["a", "b"], ["b", "c"]]
    values = [2.0, 3.0]
    queries = [["a", "c"], ["b", "a"], ["a", "e"], ["a", "a"], ["x", "x"]]
    result = calcEquation(equations, values, queries)
    assert result[0] == 6.0   # a/c = a/b * b/c = 2*3
    assert result[1] == 0.5   # b/a = 1/2
    assert result[2] == -1.0  # e 不存在
    assert result[3] == 1.0   # a/a = 1
    assert result[4] == -1.0  # x 不存在

    equations2 = [["a", "b"], ["b", "c"], ["bc", "cd"]]
    values2 = [1.5, 2.5, 5.0]
    queries2 = [["a", "c"]]
    result2 = calcEquation(equations2, values2, queries2)
    assert result2[0] == 3.75  # a/c = 1.5 * 2.5

    print("所有断言通过！")
