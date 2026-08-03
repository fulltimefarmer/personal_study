/**
 * 考点：Array, Hash Table, Matrix
 * 题目：Valid Sudoku（有效的数独）
 * 题目描述：验证 9x9 数独是否有效，每行、每列、每个 3x3 宫内数字不重复。
 * 示例：board 如题 => true
 * 思路：三组哈希表分别记录行、列、宫已出现的数字，遍历时检查重复
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 */
function isValidSudoku(board: string[][]): boolean {
    const rows: Set<string>[] = Array.from({ length: 9 }, () => new Set());
    const cols: Set<string>[] = Array.from({ length: 9 }, () => new Set());
    const boxes: Set<string>[] = Array.from({ length: 9 }, () => new Set());

    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            const num = board[i][j];
            if (num === ".") continue;

            const boxIndex = Math.floor(i / 3) * 3 + Math.floor(j / 3);

            if (rows[i].has(num) || cols[j].has(num) || boxes[boxIndex].has(num)) {
                return false;
            }

            rows[i].add(num);
            cols[j].add(num);
            boxes[boxIndex].add(num);
        }
    }

    return true;
}
export { isValidSudoku };
