/**
 * 考点：String
 * 题目：Zigzag Conversion（Z字形变换）
 * 题目描述：将字符串按Z字形排列后逐行读取。如 "PAYPALISHIRING", 3 → "PAHNAPLSIIGYIR"
 * 思路：模拟Z字形遍历，用rows数组存储每行字符，curRow在[0, numRows-1]间来回移动。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function convert(s: string, numRows: number): string {
    if (numRows === 1) return s;

    const rows: string[] = new Array(numRows).fill('');
    let curRow = 0;
    let goingDown = false;

    for (const ch of s) {
        rows[curRow] += ch;
        if (curRow === 0 || curRow === numRows - 1) {
            goingDown = !goingDown;
        }
        curRow += goingDown ? 1 : -1;
    }

    return rows.join('');
}

export { convert };
