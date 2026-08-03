/**
 * 考点：String, Dynamic Programming, Backtracking
 * 题目：Palindrome Partitioning（分割回文串）
 * 题目描述：将字符串分割，使每个子串都是回文串，返回所有可能的分割方案。
 * 示例 1：s = "aab"，输出 [["a","a","b"],["aa","b"]]
 * 示例 2：s = "a"，输出 [["a"]]
 * 思路：回溯 + 回文判断。枚举切割位置，当前子串是回文则递归处理剩余部分。
 * 时间复杂度：O(n * 2^n)
 * 空间复杂度：O(n)
 */
function partition(s: string): string[][] {
    const result: string[][] = [];
    const path: string[] = [];

    function isPalindrome(str: string, left: number, right: number): boolean {
        while (left < right) {
            if (str[left] !== str[right]) return false;
            left++;
            right--;
        }
        return true;
    }

    function backtrack(start: number): void {
        if (start === s.length) {
            result.push([...path]);
            return;
        }

        for (let end = start; end < s.length; end++) {
            if (isPalindrome(s, start, end)) {
                path.push(s.substring(start, end + 1));
                backtrack(end + 1);
                path.pop();
            }
        }
    }

    backtrack(0);
    return result;
}

export { partition };
