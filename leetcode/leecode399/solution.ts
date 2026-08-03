/**
 * 考点：DFS、BFS、并查集、图
 * 题目：Evaluate Division（除法求值）
 * 题目描述：给定变量间的除法等式，回答多个除法查询
 * 思路：带权并查集。每个节点维护 weight[x] = x / parent[x]。
 *       find 路径压缩时更新权重，union 合并集合。
 *       查询时同集合则返回 weight[a] / weight[b]。
 * 时间复杂度：O((E + Q) × α(V))
 * 空间复杂度：O(V)
 */
function calcEquation(
    equations: string[][],
    values: number[],
    queries: string[][]
): number[] {
    const parent = new Map<string, string>();
    const weight = new Map<string, number>();

    function find(x: string): string {
        if (!parent.has(x)) {
            parent.set(x, x);
            weight.set(x, 1);
        }
        if (parent.get(x) !== x) {
            const root = find(parent.get(x)!);
            weight.set(x, weight.get(x)! * weight.get(parent.get(x)!)!);
            parent.set(x, root);
        }
        return parent.get(x)!;
    }

    function union(a: string, b: string, val: number) {
        const rootA = find(a);
        const rootB = find(b);
        if (rootA !== rootB) {
            parent.set(rootA, rootB);
            weight.set(rootA, (val * weight.get(b)!) / weight.get(a)!);
        }
    }

    for (let i = 0; i < equations.length; i++) {
        const [a, b] = equations[i];
        union(a, b, values[i]);
    }

    const result: number[] = [];
    for (const [c, d] of queries) {
        if (!parent.has(c) || !parent.has(d)) {
            result.push(-1);
            continue;
        }
        const rootC = find(c);
        const rootD = find(d);
        if (rootC !== rootD) {
            result.push(-1);
        } else {
            result.push(weight.get(c)! / weight.get(d)!);
        }
    }

    return result;
}

export { calcEquation };
