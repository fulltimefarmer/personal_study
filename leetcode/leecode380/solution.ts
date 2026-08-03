/**
 * 考点：设计、数组、哈希表、随机化
 * 题目：Insert Delete GetRandom O(1)（O(1)时间插入删除和获取随机元素）
 * 题目描述：设计数据结构支持 O(1) 插入、删除、随机获取元素
 * 思路：HashMap 存值→索引 + 数组存值。删除时将被删元素与末尾交换后 pop，
 *       实现 O(1) 删除。getRandom 直接从数组随机索引。
 * 时间复杂度：O(1) 各操作
 * 空间复杂度：O(n)
 */
class RandomizedSet {
    private map: Map<number, number>;
    private arr: number[];

    constructor() {
        this.map = new Map();
        this.arr = [];
    }

    insert(val: number): boolean {
        if (this.map.has(val)) return false;
        this.map.set(val, this.arr.length);
        this.arr.push(val);
        return true;
    }

    remove(val: number): boolean {
        if (!this.map.has(val)) return false;
        const index = this.map.get(val)!;
        const last = this.arr[this.arr.length - 1];
        this.arr[index] = last;
        this.map.set(last, index);
        this.arr.pop();
        this.map.delete(val);
        return true;
    }

    getRandom(): number {
        const randomIndex = Math.floor(Math.random() * this.arr.length);
        return this.arr[randomIndex];
    }
}

export { RandomizedSet };
