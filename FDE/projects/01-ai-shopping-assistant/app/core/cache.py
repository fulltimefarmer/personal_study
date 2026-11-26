"""响应缓存层 — 重复查询加速与成本节省

面试考点：
  Q: 如何减少重复 LLM 调用的成本？
  A: 多级缓存策略：
     1. 精确匹配缓存（LRU）：相同查询直接返回缓存
     2. 语义缓存（Semantic Cache）：相似查询（向量距离<阈值）命中缓存
     3. 嵌入缓存：bge-m3 embedding 结果缓存，避免重复向量化
     4. 提示词缓存（Prompt Caching）：DeepSeek/OpenAI 支持的 context caching

面试追问：
  Q: Semantic Cache 和普通 Cache 的区别？
  A: 普通缓存用 hash/exact match，只对完全相同的输入有效。
     Semantic Cache 用向量相似度匹配，对"改写后语义相同"的
     查询也能命中。比如 "推荐消防车乐高" 和 "消防车积木有什么"
     语义相近，可以被同一个缓存命中。

  Q: Semantic Cache 有什么风险？
  A: 主要风险是假阳性（False Positive）：
     - 语义相似但意图不同的查询可能被错误匹配
     - 比如 "推荐便宜的乐高" 和 "便宜的乐高好吗" 语义接近但需求不同
     缓解：设置较高的相似度阈值 + 结合意图分类做二次校验

  Q: 缓存的淘汰策略怎么选？
  A: LRU (Least Recently Used) 适合大多数场景。
     对于客服场景，额外考虑：
     - TTL（时间过期）：商品信息有时效性（价格/库存）
     - 会话级生命周期：多轮对话中用户的偏好会变化
     本模块实现 LRU + TTL 的复合策略。

性能数据（理论）：
  - 精确缓存命中：<1ms（纯内存查字典）
  - 语义缓存命中：~10ms（向量检索 + 相似度计算）
  - 缓存未命中：走完整 LLM 流程（1-5s）
  - 典型命中率：客服场景 ~30-40%（大量相似问题）
"""
import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """线程安全的 LRU 缓存（带 TTL）"""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            value, timestamp = self._cache[key]
            if time.time() - timestamp > self.ttl:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, time.time())
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self):
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


class QueryCache:
    """查询缓存 — 精确匹配 + 可扩展语义缓存接口

    Usage:
        cache = QueryCache()
        cached = cache.get("推荐消防车乐高")
        if cached:
            return cached
        result = agent.run(query)
        cache.set(query, result)
    """

    def __init__(self, max_size: int = 500, ttl_seconds: float = 1800):
        self._exact = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)

    def _normalize(self, query: str) -> str:
        """归一化查询文本以提升精确缓存命中率"""
        return query.strip().lower()

    def _hash(self, query: str) -> str:
        return hashlib.md5(self._normalize(query).encode()).hexdigest()

    def get(self, query: str) -> Optional[str]:
        return self._exact.get(self._hash(query))

    def set(self, query: str, answer: str):
        self._exact.set(self._hash(query), answer)

    def clear(self):
        self._exact.clear()

    def stats(self) -> dict:
        return {
            "size": len(self._exact),
            "max_size": self._exact.max_size,
            "ttl": self._exact.ttl,
        }


# ── 全局查询缓存 ──
_query_cache: QueryCache | None = None


def get_query_cache() -> QueryCache:
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache
