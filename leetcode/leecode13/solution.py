"""
考点：哈希表、数学、字符串
题目：Roman to Integer（罗马数字转整数）
思路：从左到右遍历，比较当前字符和后一个字符的值，当前值小于后值则减去（如 IV），否则加上
时间复杂度：O(n)
空间复杂度：O(1)
"""

def romanToInt(s: str) -> int:
    # 字典：罗马字符 -> 对应数值，O(1) 查找
    roman_map: dict[str, int] = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }

    total = 0

    for i in range(len(s)):
        current = roman_map[s[i]]
        # 获取下一个字符的值，如果 i+1 越界则用 0
        # Python 中索引越界会抛 IndexError，所以需要用条件判断
        next_val = roman_map[s[i + 1]] if i + 1 < len(s) else 0

        # 罗马数字核心规则：当前值小于后面的值则减去，否则加上
        # 例如 "IV"：I(1) < V(5)，所以 1 被减去：-1 + 5 = 4
        # 例如 "VI"：V(5) > I(1)，所以 5 被加上：5 + 1 = 6
        if current < next_val:
            total -= current
        else:
            total += current

    return total

if __name__ == "__main__":
    assert romanToInt("III") == 3
    assert romanToInt("LVIII") == 58
    assert romanToInt("MCMXCIV") == 1994
    print("全部通过 ✓")
