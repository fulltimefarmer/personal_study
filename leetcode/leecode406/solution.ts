/**
 * 考点：贪心、数组、排序
 * 题目：Queue Reconstruction by Height（根据身高重建队列）
 * 题目描述：每人有 [身高, 前面比自己高或等的人数]，重建原始队列
 * 思路：按身高降序、k 升序排序。从高到低处理，将每个人插入结果数组的第 k 位。
 *       因为前面处理的人都比自己高或等，插入 k 位刚好满足条件。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n)
 */
function reconstructQueue(people: number[][]): number[][] {
    people.sort((a, b) => (a[0] === b[0] ? a[1] - b[1] : b[0] - a[0]));

    const result: number[][] = [];

    for (const person of people) {
        result.splice(person[1], 0, person);
    }

    return result;
}

export { reconstructQueue };
