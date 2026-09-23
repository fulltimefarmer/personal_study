# Course Schedule · 课程表（能否完成所有课程）

- **LeetCode:** 207
- **难度 Difficulty:** Medium
- **标签 Topics:** 图 / 拓扑排序 / DFS 判环 / Topological Sort / Cycle Detection
- **苹果频率:** 高频（Apple #16）

## 题干（中文）

你这个学期必须选修 `numCourses` 门课程，记为 `0` 到 `numCourses - 1`。

在选修某些课程之前需要先修一些先修课程。先修课程按数组 `prerequisites` 给出，其中 `prerequisites[i] = [a_i, b_i]`，表示如果要学习课程 `a_i` 则必须先学习课程 `b_i`。

请你判断是否可能完成所有课程的学习？如果可以，返回 `true`；否则返回 `false`。

## Problem Statement (English)

There are a total of `numCourses` courses you have to take, labeled from `0` to `numCourses - 1`. You are given an array `prerequisites` where `prerequisites[i] = [a_i, b_i]` indicates that you must take course `b_i` first if you want to take course `a_i`.

Return `true` if you can finish all courses. Otherwise, return `false`.

## 示例 / Examples

```
输入 / Input:  numCourses = 2, prerequisites = [[1,0]]
输出 / Output: true      // 先修 0 再修 1 即可

输入 / Input:  numCourses = 2, prerequisites = [[1,0],[0,1]]
输出 / Output: false     // 0 和 1 互相依赖，成环，无法完成
```

## 约束 / Constraints

- `1 <= numCourses <= 2000`
- `0 <= prerequisites.length <= 5000`
- `prerequisites[i].length == 2`
- `0 <= a_i, b_i < numCourses`
- `prerequisites[i]` 中所有课程对互不相同
