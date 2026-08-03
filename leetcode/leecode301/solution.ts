/**
 * 考点：BFS、字符串、回溯
 * 题目：Remove Invalid Parentheses（删除无效的括号）
 * 题目描述：删除最少数量括号使字符串有效，返回所有可能结果
 * 思路：BFS。逐层删除括号，每层检查是否有效，首次发现有效结果即停止。
 * 时间复杂度：O(2^n)
 * 空间复杂度：O(n × 2^n)
 */
function removeInvalidParentheses(s: string): string[] {
    const isValid = (str: string): boolean => {
        let count = 0;
        for (const ch of str) {
            if (ch === '(') count++;
            else if (ch === ')') count--;
            if (count < 0) return false;
        }
        return count === 0;
    };

    const result: string[] = [];
    const visited = new Set<string>();
    const queue: string[] = [s];
    visited.add(s);
    let found = false;

    while (queue.length > 0) {
        const current = queue.shift()!;
        if (isValid(current)) {
            result.push(current);
            found = true;
        }
        if (found) continue;

        for (let i = 0; i < current.length; i++) {
            if (current[i] !== '(' && current[i] !== ')') continue;
            const next = current.substring(0, i) + current.substring(i + 1);
            if (!visited.has(next)) {
                visited.add(next);
                queue.push(next);
            }
        }
    }

    return result;
}

export { removeInvalidParentheses };
