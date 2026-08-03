"""
考点：Design, Hash Table, Linked List, Doubly-Linked List
题目：LRU Cache（LRU缓存）
题目描述：实现 LRU 缓存，get 和 put 操作 O(1)。
示例：容量 2，put(1,1) put(2,2) get(1)→1 put(3,3)→淘汰 2 get(2)→-1 ...
思路：哈希表 + 双向链表。哈希表 O(1) 查找，双向链表 O(1) 移动/删除。虚拟头尾节点简化边界操作。
时间复杂度：get O(1), put O(1)
空间复杂度：O(capacity)
"""


class DLinkedNode:
    """双向链表节点"""
    def __init__(self, key: int = 0, value: int = 0):
        self.key: int = key
        self.value: int = value
        self.prev: DLinkedNode | None = None
        self.next: DLinkedNode | None = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity: int = capacity
        # 哈希表：key → DLinkedNode，O(1) 查找
        self.cache: dict[int, DLinkedNode] = {}
        # 虚拟头尾节点：简化链表边界操作，避免处理 None 情况
        self.head: DLinkedNode = DLinkedNode()
        self.tail: DLinkedNode = DLinkedNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: int) -> int:
        # dict.get() 返回 None 如果 key 不存在（不需要 try/except）
        node: DLinkedNode | None = self.cache.get(key)
        if node is None:
            return -1
        # 访问过的节点移到链表头部，表示最近使用
        self._move_to_head(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        node: DLinkedNode | None = self.cache.get(key)
        if node is not None:
            # key 已存在：更新值并移到头部
            node.value = value
            self._move_to_head(node)
        else:
            # key 不存在：创建新节点并添加到头部
            new_node: DLinkedNode = DLinkedNode(key, value)
            self.cache[key] = new_node
            self._add_to_head(new_node)
            # 超出容量：删除最久未使用的节点（尾部节点）
            if len(self.cache) > self.capacity:
                removed: DLinkedNode = self._remove_tail()
                del self.cache[removed.key]  # del 从哈希表中删除键

    def _add_to_head(self, node: DLinkedNode) -> None:
        """在虚拟头节点之后插入节点"""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: DLinkedNode) -> None:
        """从双向链表中移除节点"""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _move_to_head(self, node: DLinkedNode) -> None:
        """移除节点再添加到头部 = 移到头部"""
        self._remove_node(node)
        self._add_to_head(node)

    def _remove_tail(self) -> DLinkedNode:
        """移除尾部节点（虚拟尾节点的前一个节点）"""
        node: DLinkedNode = self.tail.prev
        self._remove_node(node)
        return node


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1        # 返回 1
    cache.put(3, 3)                  # 淘汰 key 2
    assert cache.get(2) == -1       # 返回 -1（未找到）
    cache.put(4, 4)                  # 淘汰 key 1
    assert cache.get(1) == -1       # 返回 -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4
