class Node:
    """双向链表节点。"""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: int = 0, value: int = 0) -> None:
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    """LRU 缓存：get 与 put 均为 O(1)。"""

    def __init__(self, capacity: int) -> None:
        """以 capacity 为容量初始化缓存。"""
        pass

    def get(self, key: int) -> int:
        """返回 key 对应的值并标记为最近使用；不存在返回 -1。"""
        pass

    def put(self, key: int, value: int) -> None:
        """写入键值对；容量超限时淘汰最久未使用的键值对。"""
        pass
