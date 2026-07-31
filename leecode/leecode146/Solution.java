import java.util.HashMap;
import java.util.Map;

/**
 * 考点：Design, Hash Table, Doubly Linked List
 * 题目：LRU Cache
 * 题目描述：
 * 请你设计并实现一个满足 LRU（最近最少使用）缓存约束的数据结构。
 *
 * 实现 LRUCache 类：
 * - LRUCache(int capacity) 以正整数作为容量 capacity 初始化 LRU 缓存。
 * - int get(int key) 如果关键字 key 存在于缓存中，则返回关键字的值；否则返回 -1。
 * - void put(int key, int value) 如果关键字 key 已经存在，则变更其数据值 value；
 *   如果不存在，则向缓存中插入该组 key-value。如果插入后缓存容量超过 capacity，
 *   则应该逐出最久未使用的关键字。
 * 函数 get 和 put 必须以 O(1) 的平均时间复杂度运行。
 *
 * 示例：
 * 输入：
 * ["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"]
 * [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]
 * 输出：
 * [null, null, null, 1, null, -1, null, -1, 3, 4]
 *
 * 解释：
 * LRUCache lRUCache = new LRUCache(2);
 * lRUCache.put(1, 1); // 缓存是 {1=1}
 * lRUCache.put(2, 2); // 缓存是 {1=1, 2=2}
 * lRUCache.get(1);    // 返回 1
 * lRUCache.put(3, 3); // 该操作会使得关键字 2 作废，缓存是 {1=1, 3=3}
 * lRUCache.get(2);    // 返回 -1（未找到）
 * lRUCache.put(4, 4); // 该操作会使得关键字 1 作废，缓存是 {4=4, 3=3}
 * lRUCache.get(1);    // 返回 -1（未找到）
 * lRUCache.get(3);    // 返回 3
 * lRUCache.get(4);    // 返回 4
 *
 * 提示：
 * - 1 <= capacity <= 3000
 * - 0 <= key <= 10^4
 * - 0 <= value <= 10^5
 * - 最多调用 2 * 10^5 次 get 和 put
 *
 * 思路：
 * 1. 需要同时满足 O(1) 的 get 和 put，因此采用哈希表 + 双向链表的组合结构。
 * 2. 哈希表 key -> DLinkedNode，用于 O(1) 判断 key 是否存在并定位节点。
 * 3. 双向链表按访问顺序维护节点：最近访问的节点靠近头部，最久未访问的节点靠近尾部。
 * 4. get 时：若 key 不存在返回 -1；否则将对应节点移动到链表头部，并返回其 value。
 * 5. put 时：若 key 已存在，更新 value 并将节点移动到头部；若不存在，创建新节点插入头部并加入哈希表。
 * 6. 当 put 后节点数量超过 capacity 时，删除链表尾部节点，并从哈希表中移除该 key。
 * 7. 使用伪头部（head）和伪尾部（tail）节点，简化边界插入和删除操作。
 * 数据结构：
 *   - 双向链表：每个节点含 key/value/prev/next，可在 O(1) 内删除或移动到头部。
 *   - 哈希表：Map<key, DLinkedNode>，实现 O(1) 定位节点。
 * 时间复杂度：get O(1), put O(1)
 * 空间复杂度：O(capacity)
 *
 * 说明：LeetCode 原题模板要求提交 class LRUCache，因此本文件内部使用 class LRUCache（包可见）。
 *      由于 Java 源文件允许没有 public 类，文件名 Solution.java 仍可正常编译。
 */
class LRUCache {
    private static class DLinkedNode {
        int key;
        int value;
        DLinkedNode prev;
        DLinkedNode next;

        DLinkedNode() {}

        DLinkedNode(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }

    private int capacity;
    private int size;
    private Map<Integer, DLinkedNode> cache;
    private DLinkedNode head;
    private DLinkedNode tail;

    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.size = 0;
        this.cache = new HashMap<>();
        this.head = new DLinkedNode();
        this.tail = new DLinkedNode();
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        DLinkedNode node = cache.get(key);
        if (node == null) return -1;
        moveToHead(node);
        return node.value;
    }

    public void put(int key, int value) {
        DLinkedNode node = cache.get(key);
        if (node == null) {
            DLinkedNode newNode = new DLinkedNode(key, value);
            cache.put(key, newNode);
            addToHead(newNode);
            size++;
            if (size > capacity) {
                DLinkedNode tail = popTail();
                cache.remove(tail.key);
                size--;
            }
        } else {
            node.value = value;
            moveToHead(node);
        }
    }

    private void addToHead(DLinkedNode node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private void removeNode(DLinkedNode node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void moveToHead(DLinkedNode node) {
        removeNode(node);
        addToHead(node);
    }

    private DLinkedNode popTail() {
        DLinkedNode node = tail.prev;
        removeNode(node);
        return node;
    }
}
