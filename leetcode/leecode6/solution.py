"""
考点：字符串
题目：Zigzag Conversion（Z 字形变换）
思路：创建 numRows 个字符串数组模拟各行，遍历字符串按 Z 字形方向填充，最后拼接所有行
时间复杂度：O(n)
空间复杂度：O(n)
"""

def convert(s: str, numRows: int) -> str:
    # 边界条件：只有一行或行数大于字符串长度时，直接返回原字符串
    if numRows == 1 or numRows >= len(s):
        return s

    # 列表推导式：创建 numRows 个空字符串组成的列表
    # rows[i] 代表 Z 字形排列中第 i 行的字符集合
    rows: list[str] = ["" for _ in range(numRows)]
    cur_row = 0  # 当前所在行号
    going_down = False  # 当前移动方向：True 表示向下，False 表示向上

    # 模拟 Z 字形填充过程
    for ch in s:
        rows[cur_row] += ch  # 将当前字符添加到对应行

        # 方向切换逻辑：到达顶行或底行时反转方向
        if cur_row == 0 or cur_row == numRows - 1:
            going_down = not going_down  # 反转方向

        # 根据方向移动行号：向下 +1，向上 -1
        cur_row += 1 if going_down else -1

    # str.join()：使用空字符串连接列表中所有元素，高效拼接
    return "".join(rows)

if __name__ == "__main__":
    assert convert("PAYPALISHIRING", 3) == "PAHNAPLSIIGYIR"
    assert convert("PAYPALISHIRING", 4) == "PINALSIGYAHRPI"
    assert convert("A", 1) == "A"
    print("全部通过 ✓")
