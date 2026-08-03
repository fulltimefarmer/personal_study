"""
考点：Trie, Memoization, Hash Table, String, DP
题目：Word Break（单词拆分）
题目描述：判断字符串 s 是否可以由字典 wordDict 中的单词拼接而成，单词可重复使用。
示例 1：s="leetcode", wordDict=["leet","code"]，输出 true
示例 2：s="applepenapple", wordDict=["apple","pen"]，输出 true
示例 3：s="catsandog", wordDict=["cats","dog","sand","and","cat"]，输出 false
思路：DP，dp[i] 表示 s[0..i-1] 是否可拆分。dp[i]=true 如果 dp[j] 且 s[j..i-1] 在字典中。
时间复杂度：O(n^2)
空间复杂度：O(n+m)
"""


def wordBreak(s: str, wordDict: list[str]) -> bool:
    # set 是 Python 的哈希集合，O(1) 查找单词
    word_set: set[str] = set(wordDict)
    n: int = len(s)
    # dp[i] 表示 s[0..i-1] 能否被字典单词拆分
    dp: list[bool] = [False] * (n + 1)
    dp[0] = True  # 空字符串可以被拆分

    # 遍历所有可能的结束位置 i
    for i in range(1, n + 1):
        # 枚举分割点 j，检查 s[j..i-1] 是否在字典中
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break  # 找到一个分割方案即可，不需要继续查找

    return dp[n]


if __name__ == "__main__":
    assert wordBreak("leetcode", ["leet", "code"]) is True
    assert wordBreak("applepenapple", ["apple", "pen"]) is True
    assert wordBreak("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False
    assert wordBreak("", ["a"]) is True  # 空字符串视为可拆分
