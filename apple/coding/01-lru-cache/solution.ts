// LRU Cache — 代码空壳（CoderPad 中填充）
// 实现 get / put，要求 O(1) 平均时间。

class LRUCache {
  // TODO: 初始化容量，选择合适的数据结构
  constructor(capacity: number) {
    // TODO
  }

  get(key: number): number {
    // TODO: 命中则返回并刷新为最近使用；否则 -1
    return -1;
  }

  put(key: number, value: number): void {
    // TODO: 更新 / 插入；超容量则淘汰最久未使用
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
