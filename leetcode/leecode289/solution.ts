/**
 * 考点：数组、矩阵、模拟
 * 题目：Game of Life（生命游戏）
 * 题目描述：根据 Conway 生命游戏规则同时更新每个细胞，要求原地操作
 * 思路：用复合状态编码避免覆盖原始信息。
 *       -1: 活→死, 2: 死→活。遍历时判断原始状态（1 或 -1 都是原来活）。
 *       最后将所有 -1 变 0，2 变 1。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(1)
 */
function gameOfLife(board: number[][]): void {
    const m = board.length;
    const n = board[0].length;
    const directions = [
        [-1, -1], [-1, 0], [-1, 1],
        [0, -1],           [0, 1],
        [1, -1],  [1, 0],  [1, 1]
    ];

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            let liveNeighbors = 0;
            for (const [dx, dy] of directions) {
                const ni = i + dx;
                const nj = j + dy;
                if (ni >= 0 && ni < m && nj >= 0 && nj < n) {
                    if (Math.abs(board[ni][nj]) === 1) {
                        liveNeighbors++;
                    }
                }
            }

            if (board[i][j] === 1 && (liveNeighbors < 2 || liveNeighbors > 3)) {
                board[i][j] = -1;
            } else if (board[i][j] === 0 && liveNeighbors === 3) {
                board[i][j] = 2;
            }
        }
    }

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            if (board[i][j] === -1) board[i][j] = 0;
            else if (board[i][j] === 2) board[i][j] = 1;
        }
    }
}

export { gameOfLife };
