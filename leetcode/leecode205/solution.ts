/**
 * 考点：哈希表、字符串
 * 题目：Isomorphic Strings（同构字符串）
 * 题目描述：判断 s 和 t 是否同构，即 s 中的字符可以一一映射到 t 中的字符。s="egg", t="add" 输出 true
 * 思路：维护两个映射表 s→t 和 t→s，遍历检查双向映射是否一致。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)（ASCII 字符集 256）
 */
function isIsomorphic(s: string, t: string): boolean {
    const mapST: number[] = new Array(256).fill(0);
    const mapTS: number[] = new Array(256).fill(0);

    for (let i = 0; i < s.length; i++) {
        const c1 = s.charCodeAt(i);
        const c2 = t.charCodeAt(i);

        if (mapST[c1] === 0 && mapTS[c2] === 0) {
            mapST[c1] = c2;
            mapTS[c2] = c1;
        } else if (mapST[c1] !== c2 || mapTS[c2] !== c1) {
            return false;
        }
    }

    return true;
}
export { isIsomorphic };
