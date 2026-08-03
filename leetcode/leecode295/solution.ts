/**
 * 考点：设计、堆（优先队列）、数据流
 * 题目：Find Median from Data Stream（数据流的中位数）
 * 题目描述：设计数据结构支持动态插入和查询中位数
 * 思路：双堆法。最大堆存较小的一半，最小堆存较大的一半。
 *       保持平衡：maxHeap.size >= minHeap.size 且差值 <= 1。
 *       中位数：相等取两堆顶平均，否则取 maxHeap 堆顶。
 * 时间复杂度：O(log n) 插入, O(1) 查询
 * 空间复杂度：O(n)
 */

class MaxHeap {
    private heap: number[] = [];

    push(val: number) {
        this.heap.push(val);
        let i = this.heap.length - 1;
        while (i > 0) {
            const p = (i - 1) >> 1;
            if (this.heap[p] >= this.heap[i]) break;
            [this.heap[p], this.heap[i]] = [this.heap[i], this.heap[p]];
            i = p;
        }
    }

    pop(): number {
        const top = this.heap[0];
        const last = this.heap.pop()!;
        if (this.heap.length > 0) {
            this.heap[0] = last;
            this.sink(0);
        }
        return top;
    }

    peek(): number {
        return this.heap[0];
    }

    size(): number {
        return this.heap.length;
    }

    private sink(i: number) {
        const n = this.heap.length;
        while (true) {
            let largest = i;
            const l = 2 * i + 1;
            const r = 2 * i + 2;
            if (l < n && this.heap[l] > this.heap[largest]) largest = l;
            if (r < n && this.heap[r] > this.heap[largest]) largest = r;
            if (largest === i) break;
            [this.heap[i], this.heap[largest]] = [this.heap[largest], this.heap[i]];
            i = largest;
        }
    }
}

class MinHeap {
    private heap: number[] = [];

    push(val: number) {
        this.heap.push(val);
        let i = this.heap.length - 1;
        while (i > 0) {
            const p = (i - 1) >> 1;
            if (this.heap[p] <= this.heap[i]) break;
            [this.heap[p], this.heap[i]] = [this.heap[i], this.heap[p]];
            i = p;
        }
    }

    pop(): number {
        const top = this.heap[0];
        const last = this.heap.pop()!;
        if (this.heap.length > 0) {
            this.heap[0] = last;
            this.sink(0);
        }
        return top;
    }

    peek(): number {
        return this.heap[0];
    }

    size(): number {
        return this.heap.length;
    }

    private sink(i: number) {
        const n = this.heap.length;
        while (true) {
            let smallest = i;
            const l = 2 * i + 1;
            const r = 2 * i + 2;
            if (l < n && this.heap[l] < this.heap[smallest]) smallest = l;
            if (r < n && this.heap[r] < this.heap[smallest]) smallest = r;
            if (smallest === i) break;
            [this.heap[i], this.heap[smallest]] = [this.heap[smallest], this.heap[i]];
            i = smallest;
        }
    }
}

class MedianFinder {
    private maxHeap = new MaxHeap();
    private minHeap = new MinHeap();

    addNum(num: number): void {
        this.maxHeap.push(num);
        this.minHeap.push(this.maxHeap.pop());

        if (this.minHeap.size() > this.maxHeap.size()) {
            this.maxHeap.push(this.minHeap.pop());
        }
    }

    findMedian(): number {
        if (this.maxHeap.size() > this.minHeap.size()) {
            return this.maxHeap.peek();
        }
        return (this.maxHeap.peek() + this.minHeap.peek()) / 2;
    }
}

export { MedianFinder };
