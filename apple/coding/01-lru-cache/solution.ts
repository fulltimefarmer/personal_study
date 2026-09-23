// LRU Cache — 代码空壳（CoderPad 中填充）
// 实现 get / put，要求 O(1) 平均时间。

class DLinkedNode {
  key = 0;
  value = 0;
  prev: DLinkedNode | null = null;
  next: DLinkedNode | null = null;
}

class LRUCache {
  private capacity: number;
  private cache = new Map<number, DLinkedNode>();
  private head = new DLinkedNode();   // 哨兵：最近使用
  private tail = new DLinkedNode();

  constructor(capacity: number) {
    this.capacity = capacity;
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  private remove(node: DLinkedNode) {
    node.next!.prev = node.prev;
    node.prev!.next = node.next;
  }

  private addToHead(node: DLinkedNode) {
    node.prev = this.head;
    node.next = this.head.next;
    this.head.next!.prev = node;
    this.head.next = node;
  }

  private moveToHead(node: DLinkedNode) {
    this.remove(node);
    this.addToHead(node);
  }

  private removeTail(): DLinkedNode {
    const node = this.tail.prev!;
    this.remove(node);
    return node;
  }

  get(key: number): number {
    const node = this.cache.get(key);
    if (!node) {
      return -1;
    }
    this.moveToHead(node);
    return node.value;
  }

  put(key: number, value: number): void {
    let node = this.cache.get(key);
    if (node) {
      node.value = value;
      this.moveToHead(node);
    } else {
      node = new DLinkedNode();
      node.key = key;
      node.value = value;
      this.cache.set(key, node);
      this.addToHead(node);
      if (this.cache.size > this.capacity) {
        const tail = this.removeTail();
        this.cache.delete(tail.key);
      }
    }
  }
}

// —— 测试（可运行验证）——
function run() {
  const cache = new LRUCache(2);
  cache.put(1, 1);        // {1=1}
  cache.put(2, 2);        // {1=1, 2=2}
  console.log(cache.get(1)); // 1
  cache.put(3, 3);        // 淘汰 2 -> {1=1, 3=3}
  console.log(cache.get(2)); // -1
  cache.put(4, 4);        // 淘汰 1 -> {4=4, 3=3}
  console.log(cache.get(1)); // -1
  console.log(cache.get(3)); // 3
  console.log(cache.get(4)); // 4
}

run();
