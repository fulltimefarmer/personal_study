/**
 * 考点：贪心、堆（优先队列）
 * 题目：Meeting Rooms II（会议室II）
 * 题目描述：给定会议时间区间数组，求所需最少会议室数量
 * 思路：按开始时间排序，用最小堆跟踪会议结束时间。每次新会议开始时，
 *       释放已结束的会议室（弹出堆顶），堆的大小就是所需会议室数。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(n)
 */
function minMeetingRooms(intervals: number[][]): number {
    if (intervals.length === 0) return 0;

    intervals.sort((a, b) => a[0] - b[0]);

    const heap: number[] = [];

    const push = (val: number) => {
        heap.push(val);
        let i = heap.length - 1;
        while (i > 0) {
            const p = (i - 1) >> 1;
            if (heap[p] <= heap[i]) break;
            [heap[p], heap[i]] = [heap[i], heap[p]];
            i = p;
        }
    };

    const pop = () => {
        const top = heap[0];
        const last = heap.pop()!;
        if (heap.length > 0) {
            heap[0] = last;
            let i = 0;
            const n = heap.length;
            while (true) {
                let smallest = i;
                const l = 2 * i + 1;
                const r = 2 * i + 2;
                if (l < n && heap[l] < heap[smallest]) smallest = l;
                if (r < n && heap[r] < heap[smallest]) smallest = r;
                if (smallest === i) break;
                [heap[i], heap[smallest]] = [heap[smallest], heap[i]];
                i = smallest;
            }
        }
        return top;
    };

    const peek = () => heap[0];

    for (const [start, end] of intervals) {
        if (heap.length > 0 && peek() <= start) {
            pop();
        }
        push(end);
    }

    return heap.length;
}

export { minMeetingRooms };
