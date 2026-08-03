/**
 * 考点：Array, Hash Table, Matrix
 * 题目：Valid Sudoku（有效的数独）
 * 题目描述：验证9x9数独是否有效（行、列、3x3宫内无重复数字，空格为'.'）。
 * 思路：三组布尔数组记录行/列/宫中数字出现情况。遍历时检查是否重复。
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 */
function isValidSudoku(board: string[][]): boolean {
    const rows: boolean[][] = Array.from({ length: 9 }, () => new Array(9).fill(false));
    const cols: boolean[][] = Array.from({ length: 9 }, () => new Array(9).fill(false));
    const boxes: boolean[][] = Array.from({ length: 9 }, () => new Array(9).fill(false));

    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            if (board[i][j] === '.') continue;
            const num = parseInt(board[i][j]) - 1;
            const boxIndex = Math.floor(i / 3) * 3 + Math.floor(j / 3);

            if (rows[i][num] || cols[j][num] || boxes[boxIndex][num]) {
                return false;
            }
            rows[i][num] = true;
            cols[j][num] = true;
            boxes[boxIndex][num] = true;
        }
    }

    return true;
}

export { isValidSudoku };
