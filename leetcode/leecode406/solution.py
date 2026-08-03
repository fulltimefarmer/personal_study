"""
考点：贪心、数组、排序
题目：Queue Reconstruction by Height（根据身高重建队列）—— LeetCode 406
题目描述：每人有 [身高, 前面比自己高或等的人数]，重建原始队列
思路：按身高降序、k 升序排序。从高到低处理，将每个人插入结果数组的第 k 位。
      因为前面处理的人都比自己高或等，插入 k 位刚好满足条件。
时间复杂度：O(n²)
空间复杂度：O(n)
"""

def reconstructQueue(people: list[list[int]]) -> list[list[int]]:
    # 排序：先按身高 h 降序，身高相同按 k 升序
    # lambda 返回元组 (-h, k)：负号实现降序排序
    people.sort(key=lambda x: (-x[0], x[1]))

    result: list[list[int]] = []

    for person in people:
        # list.insert(index, value)：在指定索引处插入元素
        # person[1] 是 k，即此人前面应有 k 个身高 >= 他的人
        # 因为先插入的人身高都 >= 当前人（按降序处理），直接插入位置 k 即可
        result.insert(person[1], person)

    return result


if __name__ == "__main__":
    people = [[7, 0], [4, 4], [7, 1], [5, 0], [6, 1], [5, 2]]
    assert reconstructQueue(people) == [[5, 0], [7, 0], [5, 2], [6, 1], [4, 4], [7, 1]]

    people2 = [[6, 0], [5, 0], [4, 0], [3, 2], [2, 2], [1, 4]]
    assert reconstructQueue(people2) == [[4, 0], [5, 0], [2, 2], [3, 2], [1, 4], [6, 0]]

    assert reconstructQueue([]) == []
    assert reconstructQueue([[1, 0]]) == [[1, 0]]

    print("所有断言通过！")
