/**
 * 考点：数组, 哈希表
 * 题目：4Sum II（四数相加II）
 * 题目描述：给你四个整数数组 nums1、nums2、nums3、nums4，计算有多少个元组 (i,j,k,l) 使得 nums1[i]+nums2[j]+nums3[k]+nums4[l]==0。
 * 示例：
 *   输入: nums1=[1,2], nums2=[-2,-1], nums3=[-1,2], nums4=[0,2] → 输出: 2
 * 思路：分组+哈希表。先遍历 nums1/nums2 所有组合，用 map 记录两数之和的出现次数。再遍历 nums3/nums4，在 map 中查找 -(a+b) 的次数并累加。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n²)
 */
function fourSumCount(nums1: number[], nums2: number[], nums3: number[], nums4: number[]): number {
    const map = new Map<number, number>();

    for (const a of nums1) {
        for (const b of nums2) {
            const sum = a + b;
            map.set(sum, (map.get(sum) || 0) + 1);
        }
    }

    let count = 0;

    for (const c of nums3) {
        for (const d of nums4) {
            const target = -(c + d);
            if (map.has(target)) {
                count += map.get(target)!;
            }
        }
    }

    return count;
}

export { fourSumCount };
