/**
 * 考点：String
 * 题目：Zigzag Conversion（Z 字形变换）
 * 题目描述：将字符串 s 根据 numRows 以 Z 字形排列，然后按行读取返回新字符串。
 * 示例：s = "PAYPALISHIRING", numRows = 3 => "PAHNAPLSIIGYIR"
 * 思路：创建 numRows 个字符串数组，模拟从上到下再从下到上的填充过程
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function convert(s: string, numRows: number): string {
    if (numRows === 1 || numRows >= s.length) return s;

    const rows: string[] = Array.from({ length: numRows }, () => "");
    let currRow = 0;
    let goingDown = false;

    for (const char of s) {
        rows[currRow] += char;
        if (currRow === 0 || currRow === numRows - 1) {
            goingDown = !goingDown;
        }
        currRow += goingDown ? 1 : -1;
    }

    return rows.join("");
}
export { convert };
