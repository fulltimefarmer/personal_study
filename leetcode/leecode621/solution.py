"""
考点：贪心, 数组, 哈希表, 计数, 排序, 堆
题目：Task Scheduler（任务调度器）
题目描述：给定 CPU 任务列表 tasks（A-Z）和冷却时间 n。相同任务间必须间隔 n 个单位时间。求完成所有任务的最短时间。
思路：公式法。统计最高频任务次数 maxCount 和出现 maxCount 次的任务数 maxFreqTasks。最少时间 = max((maxCount-1)*(n+1)+maxFreqTasks, len(tasks))。
时间复杂度：O(N)
空间复杂度：O(1)
"""


def leastInterval(tasks: list[str], n: int) -> int:
    # 统计每个任务的出现频率，因为只有 A-Z 26 种任务，用长度为 26 的列表
    freq = [0] * 26
    for task in tasks:
        # ord(ch) 返回字符的 Unicode 码点，减去 ord('A') 得到 0-25 的索引
        freq[ord(task) - ord("A")] += 1

    # 找出最高频任务的次数
    max_count = max(freq)
    # 统计有多少个任务出现次数等于 max_count
    max_freq_tasks = freq.count(max_count)

    # 公式：最少时间 = 冷却完成所有最高频任务的时间 + 剩余的最高频任务
    # (max_count-1) 个冷却周期，每个周期长度为 n+1（占用 + 冷却）
    min_time = (max_count - 1) * (n + 1) + max_freq_tasks
    # 取较大值，因为排列可能不需要冷却即可完成所有任务
    return max(min_time, len(tasks))


if __name__ == "__main__":
    # 示例：tasks=["A","A","A","B","B","B"], n=2 → 输出: 8
    assert leastInterval(["A", "A", "A", "B", "B", "B"], 2) == 8
    # 示例：tasks=["A","A","A","B","B","B"], n=0 → 输出: 6
    assert leastInterval(["A", "A", "A", "B", "B", "B"], 0) == 6
    # 示例：tasks=["A","A","A","A","A","A","B","C","D","E","F","G"], n=2 → 输出: 16
    assert leastInterval(["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2) == 16
