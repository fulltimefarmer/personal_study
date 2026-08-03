"""
考点：贪心, 哈希表, 双指针, 字符串
题目：Partition Labels（划分字母区间）
题目描述：将字符串划分为尽可能多的片段，使每个字母最多出现在一个片段中。返回每个片段的长度。
思路：记录每个字符最后出现的位置 lastPos。遍历时维护当前片段的最远边界 end。当 i==end 时切分，记录长度。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def partitionLabels(s: str) -> list[int]:
    # last_pos 数组记录每个字母在字符串中最后出现的位置索引
    # 只包含小写字母 a-z，用大小为 26 的列表
    last_pos = [0] * 26
    a_code = ord("a")  # 预取 'a' 的 Unicode 码点，避免重复计算

    for i, ch in enumerate(s):
        # ord(ch) - a_code 将字符映射到 0-25 的索引
        last_pos[ord(ch) - a_code] = i

    result: list[int] = []
    start = 0  # 当前片段的起始位置
    end = 0  # 当前片段需要到达的最远位置

    for i, ch in enumerate(s):
        # 更新当前片段的最远边界：当前字符的最后出现位置可能更远
        end = max(end, last_pos[ord(ch) - a_code])
        if i == end:
            # 当前位置到达了当前片段的最远边界，可以切分
            result.append(end - start + 1)
            start = i + 1  # 下一个片段的起始位置

    return result


if __name__ == "__main__":
    # 示例："ababcbacadefegdehijhklij" → 输出: [9,7,8]（"ababcbaca", "defegde", "hijhklij"）
    assert partitionLabels("ababcbacadefegdehijhklij") == [9, 7, 8]
    # 示例："eccbbbbdec" → 输出: [10]
    assert partitionLabels("eccbbbbdec") == [10]
