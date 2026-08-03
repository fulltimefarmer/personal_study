"""
考点: Array, Hash Table, String, Sorting
题目: Group Anagrams（字母异位词分组）
题目描述: 将字母异位词分组。如 ["eat","tea","tan","ate","nat","bat"] -> [["bat"],["nat","tan"],["ate","eat","tea"]]
思路: 排序后字符串作为哈希表键分组。也可用26字母计数编码作为键优化。
时间复杂度: O(n * k log k)
空间复杂度: O(n * k)
"""

from collections import defaultdict


def groupAnagrams(strs: list[str]) -> list[list[str]]:
    # defaultdict(list): 键不存在时自动创建空 list，无需手动 if key not in map
    # 这是 Python 中处理分组问题最简洁的方式
    groups: dict[str, list[str]] = defaultdict(list)

    for s in strs:
        # sorted(s) 返回排序后的字符列表，如 sorted("eat") -> ['a', 'e', 't']
        # ''.join(...) 将字符列表连接为字符串 "aet"
        # 字母异位词排序后得到相同的 key
        key = ''.join(sorted(s))
        groups[key].append(s)

    # dict.values() 返回视图对象，list() 转换为列表
    return list(groups.values())


if __name__ == "__main__":
    result = groupAnagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    # 因为分组是无序的，我们按分组大小验证
    assert len(result) == 3
    # 验证每个分组的排序键是否一致（即组内所有字符串排序后应相同）
    for group in result:
        canonical = ''.join(sorted(group[0]))
        assert all(''.join(sorted(w)) == canonical for w in group)
