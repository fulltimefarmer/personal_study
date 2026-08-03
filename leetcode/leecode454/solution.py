"""
考点：数组, 哈希表
题目：4Sum II（四数相加II）
题目描述：给你四个整数数组 nums1、nums2、nums3、nums4，计算有多少个元组 (i,j,k,l) 使得 nums1[i]+nums2[j]+nums3[k]+nums4[l]==0。
思路：分组+哈希表。先遍历 nums1/nums2 所有组合，用字典记录两数之和的出现次数。再遍历 nums3/nums4，在字典中查找 -(c+d) 的次数并累加。
时间复杂度：O(n²)
空间复杂度：O(n²)
"""


def fourSumCount(nums1: list[int], nums2: list[int], nums3: list[int], nums4: list[int]) -> int:
    # 使用字典记录 nums1 和 nums2 中所有两数之和的出现次数
    # dict 的 key 是 sum，value 是出现次数
    sum_map: dict[int, int] = {}
    for a in nums1:
        for b in nums2:
            s = a + b
            # dict.get(key, default) 如果 key 不存在则返回 default（0），存在则返回对应值
            sum_map[s] = sum_map.get(s, 0) + 1

    count = 0
    # 遍历 nums3 和 nums4 的所有组合，查找 -(c+d) 在 sum_map 中的次数
    for c in nums3:
        for d in nums4:
            target = -(c + d)
            # 如果 target 存在于 sum_map 中，累加对应的组合数
            count += sum_map.get(target, 0)

    return count


if __name__ == "__main__":
    # 示例：nums1=[1,2], nums2=[-2,-1], nums3=[-1,2], nums4=[0,2] → 输出: 2
    assert fourSumCount([1, 2], [-2, -1], [-1, 2], [0, 2]) == 2
    # 示例：nums1=[0], nums2=[0], nums3=[0], nums4=[0] → 输出: 1
    assert fourSumCount([0], [0], [0], [0]) == 1
