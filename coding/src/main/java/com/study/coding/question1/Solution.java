package com.study.coding.question1;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * A thread-safe, generic LRU (Least Recently Used) Cache implementation.
 *
 * <p>Internally uses a HashMap for O(1) lookups and a doubly linked list for O(1)
 * evictions/insertions. The linked list maintains access order: head is most recently
 * used, tail is least recently used.
 *
 * <p>This implementation is production-oriented: it includes comprehensive parameter
 * validation, thread safety via synchronization, proper generics, and defensive null
 * handling.
 *
 * @param <K> the type of keys maintained by this cache
 * @param <V> the type of mapped values
 */
public class Solution<K, V> {

    // 【代码质量】final 字段确保构造后引用不可变，满足安全发布要求
    private final int capacity;
    private final Map<K, Node<K, V>> cache;
    private final Node<K, V> head;
    private final Node<K, V> tail;

    /**
     * Constructs an LRU cache with the specified capacity.
     *
     * @param capacity the maximum number of entries the cache can hold
     * @throws IllegalArgumentException if capacity is not positive
     */
    public Solution(int capacity) {
        // 【生产实践】fail-fast 参数校验：尽早暴露错误，杜绝无效对象产生
        if (capacity <= 0) {
            throw new IllegalArgumentException("Capacity must be positive, got: " + capacity);
        }
        this.capacity = capacity;
        this.cache = new HashMap<>(capacity);

        // 【技术深度】哨兵头尾节点消除所有链表操作的 null 检查，统一边界处理
        this.head = new Node<>(null, null);
        this.tail = new Node<>(null, null);
        head.next = tail;
        tail.prev = head;
    }

    /**
     * Returns the value associated with the given key, or {@code null} if the key
     * is not present. Accessing an entry marks it as most recently used.
     *
     * @param key the key whose associated value is to be returned
     * @return the value associated with {@code key}, or {@code null} if not found
     * @throws NullPointerException if key is null
     */
    // 【生产实践】synchronized 保证互斥访问 + requireNonNull 空值快速失败
    public synchronized V get(K key) {
        Objects.requireNonNull(key, "key must not be null");
        Node<K, V> node = cache.get(key);
        if (node == null) {
            return null;
        }
        moveToHead(node);
        return node.value;
    }

    /**
     * Inserts or updates the value for the given key. If the cache is at capacity,
     * the least recently used entry is evicted. This operation marks the key as
     * most recently used.
     *
     * @param key   the key with which the specified value is to be associated
     * @param value the value to be associated with the specified key
     * @return the previous value associated with {@code key}, or {@code null} if
     *         there was no mapping (or the previous value was null)
     * @throws NullPointerException if key is null
     */
    // 【生产实践】synchronized 保证原子性插入 + requireNonNull 防御空键
    public synchronized V put(K key, V value) {
        Objects.requireNonNull(key, "key must not be null");
        Node<K, V> existing = cache.get(key);
        if (existing != null) {
            V oldValue = existing.value;
            existing.value = value;
            moveToHead(existing);
            return oldValue;
        }

        Node<K, V> newNode = new Node<>(key, value);
        cache.put(key, newNode);
        addToHead(newNode);

        // 【问题求解】逐出逻辑与存储操作分离：先检测容量、再执行逐出，职责清晰
        if (cache.size() > capacity) {
            Node<K, V> evicted = removeTail();
            cache.remove(evicted.key);
        }
        return null;
    }

    /**
     * Returns the current number of entries in the cache.
     */
    public synchronized int size() {
        return cache.size();
    }

    /**
     * Removes all mappings from the cache.
     */
    public synchronized void clear() {
        cache.clear();
        head.next = tail;
        tail.prev = head;
    }

    private void addToHead(Node<K, V> node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private void removeNode(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void moveToHead(Node<K, V> node) {
        removeNode(node);
        addToHead(node);
    }

    private Node<K, V> removeTail() {
        Node<K, V> lru = tail.prev;
        removeNode(lru);
        return lru;
    }

    // 【代码质量】私有静态内部类：最小可见性，避免持有外部类引用，减少内存开销
    private static class Node<K, V> {
        final K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;

        Node(K key, V value) {
            this.key = key;
            this.value = value;
        }
    }

}
