/**
 * 考点：设计、哈希表、链表、双向链表
 * 题目：LRU Cache（LRU 缓存）
 * 题目描述：实现 LRU 缓存，get 和 put 操作 O(1)。容量满时逐出最久未使用的数据。
 *   示例：capacity = 2, put(1,1) put(2,2) get(1) → 1, put(3,3) get(2) → -1
 * 思路：哈希表 + 双向链表。哈希表实现 O(1) 查找，双向链表维护访问顺序。
 *   最近访问的放在链表头部，最久未使用的在尾部。
 * 时间复杂度：O(1)
 * 空间复杂度：O(capacity)
 */

class DLinkedNode {
  key: number;
  value: number;
  prev: DLinkedNode | null;
  next: DLinkedNode | null;
  constructor(key?: number, value?: number) {
    this.key = key === undefined ? 0 : key;
    this.value = value === undefined ? 0 : value;
    this.prev = null;
    this.next = null;
  }
}

class LRUCache {
  private capacity: number;
  private size: number;
  private cache: Map<number, DLinkedNode>;
  private head: DLinkedNode;
  private tail: DLinkedNode;

  constructor(capacity: number) {
    this.capacity = capacity;
    this.size = 0;
    this.cache = new Map();
    this.head = new DLinkedNode();
    this.tail = new DLinkedNode();
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get(key: number): number {
    const node = this.cache.get(key);
    if (node === undefined) {
      return -1;
    }
    this.moveToHead(node);
    return node.value;
  }

  put(key: number, value: number): void {
    const node = this.cache.get(key);
    if (node !== undefined) {
      node.value = value;
      this.moveToHead(node);
    } else {
      const newNode = new DLinkedNode(key, value);
      this.cache.set(key, newNode);
      this.addToHead(newNode);
      this.size++;

      if (this.size > this.capacity) {
        const removed = this.removeTail();
        this.cache.delete(removed.key);
        this.size--;
      }
    }
  }

  private addToHead(node: DLinkedNode): void {
    node.prev = this.head;
    node.next = this.head.next;
    this.head.next!.prev = node;
    this.head.next = node;
  }

  private removeNode(node: DLinkedNode): void {
    node.prev!.next = node.next;
    node.next!.prev = node.prev;
  }

  private moveToHead(node: DLinkedNode): void {
    this.removeNode(node);
    this.addToHead(node);
  }

  private removeTail(): DLinkedNode {
    const node = this.tail.prev!;
    this.removeNode(node);
    return node;
  }
}

export { LRUCache };
