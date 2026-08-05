# 10. 设计搜索自动补全/输入提示 (Design Search Autocomplete)

## 题目

设计一个搜索自动补全（Typeahead / Autocomplete）系统。当用户在搜索框中输入时，系统实时返回最可能的搜索建议（Top K 查询词）。类似 Google Search、百度搜索、Amazon 商品搜索的搜索建议功能。

---

## 需求澄清

### 功能性需求

1. **实时建议**：用户每输入一个字符，返回 Top-K（通常 5~10）个相关搜索建议
2. **前缀匹配**：建议词以用户输入的文本为前缀
3. **排序依据**：按搜索频率（热度）排序，最热门/最相关的排在前面
4. **个性化（可选）**：根据用户的搜索历史、地理位置、语言个性化排序
5. **拼写纠错（可选）**：对输入进行拼写检查和模糊匹配
6. **趋势感知（可选）**：实时热点快速纳入建议（breaking news, 热门事件）
7. **多语言支持**：支持不同语言的输入和建议
8. **过滤机制**：过滤敏感词、违规内容
9. **大小写不敏感**：输入 "ap" 和 "AP" 返回相同结果

### 非功能性需求

1. **极低延迟**：P99 < 100ms（用户无感知），理想 < 50ms
2. **高可用**：搜索建议是用户高频接触的功能，99.99%+ 可用
3. **高并发**：支持百万级 QPS
4. **数据新鲜度**：新热词在分钟级别出现在建议中
5. **可扩展**：支持数十亿不同的搜索词

### 容量估算

**假设条件：**
- DAU: 5 亿
- 每用户日均搜索: 5 次
- 每次搜索平均输入 5 个字符，每字符触发一次建议请求
- 每日建议请求: 5亿 × 5 × 5 = 125 亿次
- 建议 QPS: 125亿 / 86400 ≈ **145K QPS**（峰值 ×3 ≈ **435K QPS**）
- 总独特搜索词: 50 亿（全部历史）
- 活跃搜索词（近 30 天）: 10 亿

**存储估算：**
- Trie 节点存储:
  - 50 亿独特搜索词，假设平均前缀共享率为 80%
  - 每个节点: char(4B) + children_ptr(8B) + freq(8B) + topK_ptr(8B) ≈ 32B
  - 估算节点数: 50亿 × 平均长度(15) × (1-0.8) ≈ 150 亿节点
  - 存储: 150亿 × 32B ≈ **480 GB**（内存压力大，需要优化）
- 按 Top-K 剪枝优化后: 每个词条只存储足够区分度的前缀
  - 优化后: ~5 GB ~ 10 GB
- Top 10 热词缓存:
  - 每个前缀字符数平均 3 个 → 约 5000 万个前缀
  - 每前缀缓存 10 个建议 × 200B ≈ 2000B
  - 缓存: 5000万 × 2000B ≈ **100 GB**

---

## API 设计

### REST API

```
1. 获取搜索建议
GET /api/v1/suggest?q={prefix}&limit=10&locale=zh-CN

Parameters:
  q:       用户输入的搜索前缀 (1-100 字符)
  limit:   返回建议数量 (默认 5, 最大 20)
  locale:  语言/地区 (zh-CN, en-US, ja-JP)
  lat:     纬度（可选，用于个性化/本地化）
  lon:     经度（可选）

Response: 200 OK
{
  "query": "ap",
  "suggestions": [
    {
      "text": "apple",
      "display_text": "apple",         // 可包含高亮标记
      "type": "trending",              // trending | history | popular
      "score": 0.95,
      "metadata": {
        "category": "technology",
        "search_count": 1234567
      }
    },
    {
      "text": "app store",
      "display_text": "app store",
      "type": "popular",
      "score": 0.88
    },
    {
      "text": "apex legends",
      "display_text": "apex legends",
      "type": "popular",
      "score": 0.76
    },
    {
      "text": "apple watch",
      "display_text": "apple watch",
      "type": "popular",
      "score": 0.65
    },
    {
      "text": "apartment rental",
      "display_text": "apartment rental",
      "type": "history",              // 来自用户历史
      "score": 0.50
    }
  ],
  "took_ms": 12,                       // 服务端处理耗时
  "source": "cache"                    // cache | trie | fallback
}

2. 批量获取建议（内部API，供前端预加载）
POST /api/v1/suggest/batch
{
  "prefixes": ["a", "ap", "app", "appl", "apple"],
  "limit": 5
}

Response:
{
  "results": {
    "a": [...],
    "ap": [...],
    "app": [...],
    "appl": [...],
    "apple": [...]
  }
}
```

### 前端交互优化

```javascript
// 前端去抖 (Debounce) 策略
class AutocompleteController {
  constructor() {
    this.debounceTimer = null;
    this.debounceDelay = 150; // 150ms 去抖
    this.pendingRequest = null;
  }

  onInput(input) {
    // 1. 输入长度 < 2 → 不发送请求 (减少无效请求)
    if (input.length < 2) {
      this.hideSuggestions();
      return;
    }

    // 2. 本地缓存匹配 (前缀包含关系)
    const cached = this.localCache.get(input);
    if (cached && Date.now() - cached.timestamp < 60000) {
      this.showSuggestions(cached.results);
      return;
    }

    // 3. 去抖发送
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      // 4. 取消前一个未完成的请求
      if (this.pendingRequest) {
        this.pendingRequest.abort();
      }
      this.pendingRequest = this.fetchSuggestions(input);
    }, this.debounceDelay);
  }

  async fetchSuggestions(prefix) {
    const response = await fetch(
      `/api/v1/suggest?q=${encodeURIComponent(prefix)}&limit=10`
    );
    const data = await response.json();
    this.localCache.put(prefix, data.suggestions);
    this.showSuggestions(data.suggestions);
  }
}
```

---

## 数据模型

### Trie (前缀树) 核心数据结构

```
Trie 节点结构:

┌─────────────────────────────────────────────────┐
│                Trie Node                         │
│                                                  │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐    │
│  │ char    │  │ children │  │ top_sugs    │    │
│  │ (字符)   │  │ (子节点)  │  │ (热门建议)   │    │
│  └─────────┘  └──────────┘  └─────────────┘    │
│                                                  │
│  children: Map<char, Node>  或 Node[26]         │
│  top_sugs:  [{term, freq}, ...]  (Top-K 缓存)    │
│  is_end: bool  (是否为完整词条)                    │
│  freq: int64   (搜索频率, 仅在 is_end=true 有效)  │
└─────────────────────────────────────────────────┘

示例: 插入 "apple"(freq=100), "app"(freq=50), "apex"(freq=30)

        root
         │
         a
         │
         p
         │
    ┌────┴────┐
    p(is_end)  e
    │ freq=50  │
    l          x(is_end)
    │          freq=30
    e(is_end)
    freq=100

    每个节点存储该前缀下 Top-2 热词:
    p: [{app, 50}, {apple, 100}, {apex, 30}]
    pp: [{apple, 100}, {app, 50}]
    ppl: [{apple, 100}]
    pple: [{apple, 100}]
    pe: [{apex, 30}]
```

```python
class TrieNode:
    __slots__ = ('children', 'is_end', 'freq', 'top_terms')

    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.freq: int = 0
        self.top_terms: list[tuple[str, int]] = []  # [(term, freq), ...], sorted desc

class AutocompleteTrie:
    def __init__(self, top_k: int = 10):
        self.root = TrieNode()
        self.top_k = top_k

    def insert(self, term: str, freq: int):
        node = self.root
        # 1. 遍历到叶子节点
        for char in term.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        node.is_end = True
        node.freq = freq

    def update_top_terms(self):
        """DFS 后序遍历: 自底向上更新每个节点的 Top-K 热词"""
        def dfs(node: TrieNode) -> list[tuple[str, int]]:
            candidates = []

            # 当前节点如果是完整词条, 加入候选
            if node.is_end:
                candidates.append(('', node.freq))  # '' 表示当前路径就是完整词

            # 聚合所有子节点的 top_terms
            for char, child in node.children.items():
                child_terms = dfs(child)
                for term, freq in child_terms:
                    candidates.append((char + term, freq))

            # 按频率降序排序, 取 Top-K
            candidates.sort(key=lambda x: x[1], reverse=True)
            node.top_terms = candidates[:self.top_k]
            return candidates[:self.top_k]

        dfs(self.root)

    def suggest(self, prefix: str, limit: int = 10) -> list[tuple[str, int]]:
        """查询给定前缀的 Top-K 建议"""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]

        # 直接返回节点缓存的 Top-K
        suggestions = []
        for remaining, freq in node.top_terms[:limit]:
            suggestions.append((prefix + remaining, freq))
        return suggestions
```

### 大数据量 Trie 存储优化

```
Trie 节点存储优化技术:

1. 紧凑表示 (Radix Tree / Patricia Trie):
   单分支路径压缩: app → le (而非逐个字符存储)
   减少节点数: 150亿节点 → ~20亿节点
   
   示例:
   压缩前: a → p → p → l → e
   压缩后: "apple" (一条边)

2. 按频率剪枝:
   仅保留搜索频率 > 阈值的词条
   低频词 (< 10次/月) 不构建 Trie
   可减少 50%+ 节点

3. 按前 N 个字符剪枝:
   大多数建议只需要前 3-5 个字符就能区分
   超过 N 个字符的前缀不再构建子 Trie

4. 哈希表 vs 数组:
   英文字符 (a-z): 使用数组 Node* children[26]
   中文字符: 先用哈希映射 Unicode → index, 再用数组
   或使用 HashMap<char, Node*> (空间换时间)

5. 整数编码 (Integer Encoding):
   将字符串词条映射为 int32/int64 ID
   Top-K 缓存中存储 ID 而非完整字符串
   减少内存占用 (8 bytes ID vs 平均 15 bytes 字符串)

6. 分片 (Sharded Trie):
   按首字符或 hash(prefix) 分片
   多个小 Trie 分布在多台机器上
```

### 离线数据管道

```
┌──────────────────────────────────────────────────────────────┐
│                      数据更新流水线                             │
│                                                              │
│  每天 (Batch Pipeline):                                      │
│                                                              │
│  ┌─────────────────┐     ┌───────────────────┐              │
│  │ 搜索日志 (HDFS/  │────▶│ 聚合统计 (Spark/   │              │
│  │  S3/ClickHouse) │     │ Flink)             │              │
│  │                  │     │ - 按词条 + 区域聚合  │              │
│  │ raw_search_logs │     │ - 统计日/周/月频次   │              │
│  └─────────────────┘     └─────────┬─────────┘              │
│                                    │                         │
│                          ┌─────────▼─────────┐              │
│                          │ 热度计算           │              │
│                          │ - 近期加权:        │              │
│                          │   衰减因子 =       │              │
│                          │   e^(-λ × days)  │              │
│                          │ - 趋势分:          │              │
│                          │   今日/昨日比率    │              │
│                          └─────────┬─────────┘              │
│                                    │                         │
│                          ┌─────────▼─────────┐              │
│                          │ 敏感词过滤          │              │
│                          │ - 敏感词黑名单      │              │
│                          │ - 违规内容过滤      │              │
│                          │ - 人工审核标记      │              │
│                          └─────────┬─────────┘              │
│                                    │                         │
│                          ┌─────────▼─────────┐              │
│                          │ Trie 构建 (MapReduce│              │
│                          │ / 内存构建)         │              │
│                          │ - 插入词条+频次     │              │
│                          │ - 自底向上计算Top-K │              │
│                          │ - 序列化到文件       │              │
│                          │ - 增量更新到服务    │              │
│                          └───────────────────┘              │
│                                                              │
│  实时 (Stream Pipeline):                                     │
│  ┌─────────────────┐                                         │
│  │ Trending Topics │                                         │
│  │ (Kafka Stream)  │                                         │
│  │ - 检测突增搜索    │                                         │
│  │ - 热词快速入Trie  │                                         │
│  │ - 分钟级延迟     │                                         │
│  └─────────────────┘                                         │
└──────────────────────────────────────────────────────────────┘
```

**热度衰减算法：**

```python
def compute_term_score(term_counts: dict, current_date) -> float:
    """
    基于时间衰减的热度分数计算
    
    term_counts: {date: count, ...}  过去 N 天的每日搜索次数
    """
    score = 0.0
    half_life_days = 7  # 7天半衰期
    decay_lambda = math.log(2) / half_life_days

    for date, count in term_counts.items():
        days_ago = (current_date - date).days
        decay_weight = math.exp(-decay_lambda * days_ago)
        score += count * decay_weight

    # 趋势加分: 当天/昨天比率
    today_count = term_counts.get(current_date, 0)
    yesterday_count = term_counts.get(current_date - timedelta(days=1), 0)
    if yesterday_count > 0:
        trend_ratio = today_count / yesterday_count
        score *= min(trend_ratio, 3.0)  # 趋势因子最多 3x

    return score
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────┐
                              │              前端 (Client)                │
                              │  ┌────────────────────────────────────┐  │
                              │  │  - 去抖 (Debounce) 150ms           │  │
                              │  │  - 本地缓存 (最近查询结果)           │  │
                              │  │  - AbortController 取消过期请求     │  │
                              │  └────────────────────────────────────┘  │
                              └─────────────────────┬────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────┐
                              │              CDN / API Gateway            │
                              │  ┌────────────────────────────────────┐  │
                              │  │  - 热门前缀结果缓存在 CDN 边缘       │  │
                              │  │  - 限流 (Rate Limiting)            │  │
                              │  │  - 路由到最近的 Suggest Service    │  │
                              │  └────────────────────────────────────┘  │
                              └─────────────────────┬────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────┐
                              │            Suggest Service (无状态)        │
                              │                                         │
                              │  ┌─────────────────────────────────────┐ │
                              │  │ L1: 本地内存缓存 (Caffeine Cache)     │ │
                              │  │     - Key: prefix                   │ │
                              │  │     - Value: Top-K suggestions      │ │
                              │  │     - Size: 10K entries             │ │
                              │  │     - TTL: 60s                      │ │
                              │  └──────────────┬──────────────────────┘ │
                              │                 │ miss                    │
                              │  ┌──────────────▼──────────────────────┐ │
                              │  │ L2: 分布式 Redis 缓存               │ │
                              │  │     - Key: suggest:{locale}:{prefix}│ │
                              │  │     - Value: JSON of Top-K          │ │
                              │  │     - TTL: 5 分钟                  │ │
                              │  └──────────────┬──────────────────────┘ │
                              │                 │ miss                    │
                              │  ┌──────────────▼──────────────────────┐ │
                              │  │ L3: Trie Service (有状态)            │ │
                              │  │     - 加载全量 Trie 到内存           │ │
                              │  │     - 或远程查询 Trie 节点           │ │
                              │  └─────────────────────────────────────┘ │
                              └──────────────────────────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────┐
                              │             离线数据管道                    │
                              │  ┌──────────────────┐ ┌────────────────┐ │
                              │  │ 搜索日志聚合       │ │ 实时趋势检测     │ │
                              │  │ (Spark/Hive/Daily)│ │ (Flink/Kafka)  │ │
                              │  └────────┬─────────┘ └───────┬────────┘ │
                              │           │                   │          │
                              │  ┌────────▼───────────────────▼────────┐ │
                              │  │       Trie Builder + Validator       │ │
                              │  │  - 构建新版本 Trie                   │ │
                              │  │  - 与旧版本对比验证                   │ │
                              │  │  - 灰度发布到 Trie Service           │ │
                              │  └──────────────────────────────────────┘ │
                              └──────────────────────────────────────────┘
```

---

## 核心深入

### Trie 的查询优化

**场景一：轻量查询 → Redis 缓存**

```
对于 Top 100 万高频前缀，结果直接缓存在 Redis 中:
  - Key: suggest:{lang}:{prefix}
  - Value: JSON ["apple", "app store", "apex", "apple watch"]
  - TTL: 5 min (平衡新鲜度与缓存命中率)

Redis 分片:
  - 按前缀 hash 分片到不同 Redis Cluster 节点
  - 热点前缀自动复制多份 (避免热点 Key)
  - 预估: 100 万前缀 × 500B = 500 MB ➔ Redis 完全能装下
```

**场景二：缓冲穿透 → Bloom Filter 保护**

```python
class TrieQueryService:
    def __init__(self):
        self.redis = RedisCluster()
        self.trie_service = TrieService()
        self.bloom_filter = BloomFilter(100_000_000)  # 100M 前缀
        # Bloom Filter 预先加载所有有效前缀

    def suggest(self, prefix: str, limit: int = 10) -> list:
        # 1. 本地缓存
        cached = self.local_cache.get(prefix)
        if cached:
            return cached

        # 2. Redis 缓存
        redis_key = f"suggest:{self.locale}:{prefix.lower()}"
        cached = self.redis.get(redis_key)
        if cached:
            self.local_cache.put(prefix, cached)
            return json.loads(cached)

        # 3. Bloom Filter 快速排除不存在的 Trie 前缀
        if not self.bloom_filter.contains(prefix):
            # 不存在的 Trie 前缀也缓存一个空结果 (防止缓存穿透)
            self.redis.setex(redis_key, 60, json.dumps([]))
            return []

        # 4. 回源 Trie Service
        results = self.trie_service.suggest(prefix, limit)
        self.redis.setex(redis_key, 300, json.dumps(results))
        self.local_cache.put(prefix, results)
        return results
```

### 个性化排名重排

```
全局建议 (Trie) vs 个性化建议 (用户行为):

个性化排序策略:
  1. 获取 Trie 返回的全局 Top-K 候选 (e.g., 前 100 个)
  2. 获取用户的个性化特征:
     - 搜索历史 (最近 N 天搜索过哪些词)
     - 关注的类别 (技术、体育、娱乐...)
     - 地理位置 (本地搜索偏向)
     - 语言偏好
  3. 对候选重新排序:
     new_score = global_score × (1 + α × personal_boost)

  个性化乘法因子:
    如果候选词在用户搜索历史中出现过:       boost = 1.5
    如果候选词与用户关注的类别匹配:          boost = 1.3
    如果候选词包含本地地名 (location match): boost = 1.4
    如果候选词是个人作品/联系人:             boost = 2.0

实现:
  - Mixer Service 在返回给用户前进行重排
  - 最多调整 Top-5 顺序，而非完全重新选择
  - 保留 1-2 个全局热门结果 (避免信息茧房)
```

### 热点数据快速生效

```
实时趋势检测 (Flink/Spark Streaming):

流程:
  搜索日志 → Kafka → Flink Window Aggregation
  → 检测 5 分钟内高频上升的搜索词
  → 增长率超过阈值 (e.g., 200%+) → 标记为 Trending
  → 写入 Redis Sorted Set: trending:{locale}
    Score = growth_rate, Member = search_term
  → Suggest Service 查询时检查 trending 列表
  → 将 trending 词插入建议结果头部 (标记为 "trending" 类型)

公式:
  current_window_count / prev_window_count > trend_threshold (2.0)
  AND current_window_count > min_absolute_count (1000)

示例:
  "Taylor Swift" 突然 5 分钟内搜索量从 1000 → 50000
  → 增长率 50x → 标记为 Trending
  → 下次用户输入 "tay" → 建议头部出现 "taylor swift" 🔥
```

### CDN 缓存策略

```
CDN 缓存热门前缀的建议结果:

策略:
  - 分析日志: Top 100,000 高频前缀 (覆盖 90%+ 流量)
  - 将建议结果缓存到 CDN 边缘节点
  - URL: https://suggest.cdn.com/v1/zh-CN/ap
  - Cache-Control: public, max-age=60 (60秒缓存)
  - 返回 JSON-Padding (JSONP) 支持跨域

CDN 缓存键:
  /suggest/{locale}/{prefix}.json

CDN 预热:
  - 每个 Trie 更新后，预加载 Top 100K 前缀到 CDN
  - 使用 CDN 预热 API 批量提交

收益:
  - 90%+ 的请求在 CDN 层返回
  - 延迟 < 5ms (边缘节点)
  - 大幅减少回源到 Suggest Service
```

---

## 扩展性与高可用

### Trie 分片策略

```
当 Trie 无法放入单机内存时, 需要分片:

方案一: 按首字母分片 (简单但不均衡)
  Shard 0: a-d
  Shard 1: e-h
  Shard 2: i-l
  ...
  问题: 's' 开头的搜索词远多于 'q'

方案二: 按 Hash(prefix) 分片 (均匀)
  shard_id = hash(prefix[:3]) % num_shards
  
  优点: 负载均衡
  缺点: 查询需要计算 hash → 可能导致跨分片

方案三: 按首字母范围 + 动态迁移 (推荐)
  1. 统计每个首字母的搜索量分布
  2. 将高负载首字母独立成分片
  3. 低负载首字母按范围合并
  
  例如 (中文搜索):
    分片1: 热门词 (统计 Top 1000 高频词单独处理)
    分片2: A-G
    分片3: H-N
    分片4: O-T
    分片5: U-Z + 数字 + 特殊字符
```

### 灰度发布数据更新

```
Trie 更新策略:

1. 双 Buffer / Blue-Green 部署:
   - 两组 Trie Service 实例
   - Group A: 当前版本 (v1), 正常服务
   - Group B: 新版本 (v2), 部署后预热
   - 先切 5% 流量到 Group B → 监控 → 50% → 100%

2. 全量对比验证:
   - 对随机 10 万前缀请求分别查询 Group A 和 Group B
   - 对比结果差异 (建议词、排序)
   - 差异率 > 1% → 人工审核 → 阻止全量上线

3. 快速回滚:
   - 如果新版本错误率上升或质量下降
   - APM/监控告警 → 自动切回全部旧版本
   - 回滚时间 < 30s

4. 增量热更新 (而不重启):
   - Trie 文件序列化到共享存储
   - 服务定期检查新版本 → 加载到内存
   - 原子切换: 新 Trie 准备就绪后, 更新指针 → 旧 Trie GC
```

### 监控与告警

```
搜索建议系统核心监控:

服务性能:
  - Suggest API 延迟 P50/P95/P99 (目标: P99 < 100ms)
  - 各层缓存命中率: L1 (本地) / L2 (Redis) / L3 (Trie) / CDN
  - 错误率 (4xx/5xx) (阈值: > 0.1% 告警)
  - QPS 趋势和异常检测

数据质量:
  - 空结果率 (返回 [] 的请求比例) (阈值: > 20% 异常)
  - 建议结果更新率 (新旧版本结果差异)
  - 热门前缀 TOP-N 覆盖监控
  - 敏感词漏过滤率

数据更新:
  - Trie 构建耗时 → 数据管道健康
  - Trie 数据大小和节点数
  - 热词实时检测延迟

CDN:
  - CDN 缓存命中率
  - CDN 回源率 (阈值: > 30% 告警)
  - 各区域 CDN 延迟和错误率
```

---

## 总结

搜索自动补全系统设计核心要点：

1. **Trie 是核心数据结构**：前缀匹配的天生利器，自底向上预计算 Top-K 实现 O(len(prefix)) 查询
2. **多层缓存体系**：CDN → 本地内存 → Redis → Trie Service，层层缓存减速
3. **热度排序算法**：指数衰减加权 + 趋势因子的组合评分，平衡长期热度和短期趋势
4. **实时趋势检测**：Flink 滑动窗口检测搜索量突增，快速将突发热词注入建议
5. **数据新鲜度**：离线批量 + 实时增量双通道更新，T+1 天批处理 + 分钟级趋势
6. **分片与扩展**：按首字符范围或前缀哈希分片，热门前缀可独立分片
7. **去抖与剪枝**：前端 150ms 防抖 + min_prefix_length + AbortController 减少服务端压力
8. **灰度发布**：Blue-Green 部署 + 全量对比验证 + 快速回滚
9. **Bloom Filter**：防止不存在的 Trie 前缀导致缓存穿透
10. **个性化重排**：全局 Trie 建议 + 用户特征加权混合排序

**面试核心权衡讨论：**
- Trie vs Inverted Index：前缀匹配 (Trie) vs 全文搜索 (倒排索引)
- 内存 Trie vs Disk Trie：实时性 vs 成本
- 全局热度 vs 个性化：覆盖度和新鲜度 vs 精准度
- CDN 缓存 vs 动态查询：延迟 vs 新鲜度
- 批处理更新 vs 实时更新：一致性 vs 复杂度
- 单层 Trie vs 分层 Trie：简单性 vs 扩展性
- Top-K 预计算 vs 实时计算：查表 O(1) vs 动态排序 O(NlogK)
