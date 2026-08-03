# LeetCode 4. Median of Two Sorted Arrays（寻找两个正序数组的中位数）

## 考点
Array, Binary Search, Divide and Conquer

## 题目描述
给定两个大小分别为 `m` 和 `n` 的正序（从小到大）数组 `nums1` 和 `nums2`。请你找出并返回这两个正序数组的 **中位数**。

算法的时间复杂度应该为 O(log (m+n))。

### 示例 1
```
输入：nums1 = [1,3], nums2 = [2]
输出：2.00000
解释：合并数组 = [1,2,3]，中位数 2
```

### 示例 2
```
输入：nums1 = [1,2], nums2 = [3,4]
输出：2.50000
解释：合并数组 = [1,2,3,4]，中位数 (2 + 3) / 2 = 2.5
```

### 约束
- `nums1.length == m`
- `nums2.length == n`
- `0 <= m <= 1000`
- `0 <= n <= 1000`
- `1 <= m + n <= 2000`
- `-10^6 <= nums1[i], nums2[i] <= 10^6`

## 解题思路

### 方法：二分查找划分
核心思想：在较短的数组上进行二分查找，找到一个划分位置，使得左半部分的所有元素都小于等于右半部分的所有元素。

**步骤：**
1. 确保 `nums1` 是较短的数组（如果不是则交换）。
2. 在 `nums1` 上二分查找划分点 `partitionX`（范围 `[0, m]`）。
3. 根据 `partitionX` 计算 `partitionY = Math.floor((m + n + 1) / 2) - partitionX`。
4. 获取划分点左右两侧的值（边界用 -Infinity 和 Infinity 处理）。
5. 如果 `maxLeftX <= minRightY && maxLeftY <= minRightX`，找到正确划分：
   - 总数为奇数：中位数 = `max(maxLeftX, maxLeftY)`
   - 总数为偶数：中位数 = `(max(maxLeftX, maxLeftY) + min(minRightX, minRightY)) / 2`
6. 如果 `maxLeftX > minRightY`，`partitionX` 太大，向左移动。
7. 如果 `maxLeftY > minRightX`，`partitionX` 太小，向右移动。

**关键点：**
- 在较短数组上二分查找保证 O(log(min(m, n))) 复杂度。
- 边界处理：用 -Infinity / Infinity 处理划分在数组边缘的情况。
- `partitionY` 的计算使用 `(m + n + 1) / 2` 确保左半部分元素数 >= 右半部分。

时间复杂度：O(log(min(m, n)))
空间复杂度：O(1)
