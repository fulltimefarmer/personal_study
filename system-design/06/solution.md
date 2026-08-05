# 06. 设计网络爬虫 (Design a Web Crawler)

## 题目

设计一个类似 Googlebot 的分布式网络爬虫系统，能够高效地抓取互联网上的网页内容，用于搜索引擎索引。系统需要具备可扩展性、礼貌性和内容去重能力。

---

## 需求澄清

### 功能性需求

1. **URL 发现**：从种子 URL 出发，递归发现和抓取新页面
2. **HTML 内容抓取**：下载 HTML 页面内容，提取文本、链接、元数据
3. **内容提取与解析**：解析 HTML，提取所有出站链接（outgoing links）
4. **URL 去重**：避免重复抓取相同 URL（URL 规范化）
5. **内容去重**：检测和过滤近似重复的页面内容（Near-Duplicate Detection）
6. **礼貌性抓取 (Politeness)**：遵守 robots.txt 规则，控制抓取频率
7. **优先级调度**：重要页面优先抓取
8. **重试与容错**：网络故障、超时的重试机制
9. **增量抓取**：定期重新抓取已抓页面，检测内容更新
10. **分布式执行**：多节点并行抓取，水平扩展

### 非功能性需求

1. **可扩展性**：支持抓取数十亿甚至数千亿页面
2. **性能**：日均抓取数十亿页面
3. **鲁棒性**：处理各种异常（网络超时、格式错误的 HTML、恶意死循环等）
4. **礼貌性**：不意外地对目标网站造成 DDoS 效应
5. **可配置性**：不同域名/类型的页面可以用不同的策略

### 容量估算

**假设条件：**
- 互联网页面总数: ~500 亿
- 日均新增页面: 约 100 万 ~ 500 万
- 目标抓取规模: 100 亿页面
- 平均页面大小: 100KB（HTML + 资源）
- 每个页面平均出链: 25 个
- 爬虫数量: 1000 个节点
- 单节点抓取速率: 平均 100 req/s（遵守 politeness）

**抓取能力估算：**
- 总量: 1000 × 100 = 100,000 页/秒 = **86.4 亿页/天**
- 100 亿页面全量抓取: ~12 天
- 初始全量后转为增量模式（每日仅抓更新的 1-5%）

**存储估算：**
- 抓取 100 亿页面:
  - HTML 原始内容: 100亿 × 100KB = 1PB
  - 索引数据: 100亿 × 10KB = 100TB
  - URL 去重数据结构 (Bloom Filter): 
    - 假阳性率 0.1%: ~57 GB for 100B URLs
  - URL Frontier (待抓取队列):
    - 1000万个 URL 常驻队列 × 200B = ~2GB
    - 持久化队列: 10亿 URL × 200B = 200GB
  - 总存储(含副本): ~2-3 PB

**网络带宽估算：**
- 100,000 页/秒 × 100KB = 10 GB/s = **80 Gbps**
- 需要高带宽网络连接

**DNS 查询估算：**
- 每个域名大约 10 个页面
- 100,000 页/秒 / 10 = 10,000 次 DNS 查询/秒
- 需 DNS 缓存层减轻压力

---

## API 设计

### 爬虫内部服务接口

```protobuf
// gRPC 内部接口定义

service CrawlerMaster {
    // Worker 注册和心跳
    rpc RegisterWorker(WorkerInfo) returns (RegistrationResponse);
    rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);

    // 分配抓取任务
    rpc FetchTasks(TaskRequest) returns (stream CrawlTask);

    // 上报抓取结果
    rpc ReportResult(CrawlResult) returns (AckResponse);
}

service URLFrontier {
    // 添加 URL 到抓取队列
    rpc EnqueueURLs(stream URLItem) returns (EnqueueResponse);

    // 获取待抓取 URL 批次
    rpc DequeueURLs(DequeueRequest) returns (stream URLItem);

    // 获取域名级别的 URL 队列
    rpc GetDomainQueue(DomainRequest) returns (stream URLItem);
}

message CrawlTask {
    string url = 1;
    string domain = 2;
    int32 priority = 3;           // 1-10, 10 最高
    int64 crawl_deadline = 4;     // 超时时间
    repeated string allowed_paths = 5;  // robots.txt 允许的路径
    int32 crawl_delay_ms = 6;     // 礼貌延迟
}

message CrawlResult {
    string url = 1;
    int32 status_code = 2;
    map<string, string> headers = 3;
    bytes content = 4;            // HTML 内容
    int64 content_hash = 5;      // 内容指纹
    string content_type = 6;
    int64 fetch_time_ms = 7;
    repeated string outgoing_links = 8;  // 提取的超链接
    string redirect_url = 9;     // 如果是重定向
    string error_message = 10;   // 如果出错
    int64 last_modified = 11;    // HTTP Last-Modified 头
}
```

### Robots.txt 处理

```
robots.txt 解析和缓存:

示例 robots.txt:
User-agent: *
Disallow: /private/
Disallow: /admin/
Crawl-delay: 10
Allow: /public/

User-agent: Googlebot
Disallow: /no-google/
Crawl-delay: 1

解析结果缓存 (Redis):
Key:   robots:{domain}
Type:  Hash
Fields:
  - rules: JSON 序列化的规则列表
  - crawl_delay: 爬取延迟 (秒)
  - fetched_at: 上次获取时间
  - etag: robots.txt 的 etag

TTL: 24 小时 (定期更新)
```

---

## 数据模型

### 核心数据存储

```sql
-- 已抓取页面元数据 (Cassandra/宽列存储更适合)
CREATE TABLE crawled_pages (
    url_hash CHAR(32) PRIMARY KEY,      -- MD5/SHA256 of canonical URL
    url TEXT NOT NULL,
    canonical_url TEXT,                  -- 规范化后的 URL
    domain VARCHAR(255) NOT NULL,
    status_code SMALLINT,
    content_hash CHAR(32),               -- SimHash 或 MD5 of content
    content_length INT,
    content_type VARCHAR(128),
    title VARCHAR(512),
    meta_description TEXT,
    fetch_time BIGINT NOT NULL,          -- 上次抓取时间戳
    last_modified BIGINT,                -- HTTP Last-Modified
    etag VARCHAR(255),                   -- HTTP ETag
    outgoing_links_count INT,
    incoming_links_count INT DEFAULT 0,
    page_rank FLOAT DEFAULT 0.0,
    crawl_priority INT DEFAULT 5,
    retry_count INT DEFAULT 0,
    next_crawl_at BIGINT,                -- 下次重抓时间
    INDEX idx_domain_fetch (domain, fetch_time DESC),
    INDEX idx_next_crawl (next_crawl_at)
);

-- URL Frontier (待抓取队列持久化)
CREATE TABLE url_frontier (
    url_hash CHAR(32) PRIMARY KEY,
    url TEXT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    priority INT DEFAULT 5,
    discovered_at BIGINT NOT NULL,
    source_url_hash CHAR(32),           -- 发现该 URL 的来源页面
    depth INT DEFAULT 0,                 -- 链接深度
    INDEX idx_domain_priority (domain, priority DESC, discovered_at),
    INDEX idx_priority (priority DESC, discovered_at)
);

-- 域名策略表
CREATE TABLE domain_policies (
    domain VARCHAR(255) PRIMARY KEY,
    crawl_delay_ms INT DEFAULT 1000,
    max_concurrent_requests INT DEFAULT 3,
    robots_txt_content TEXT,
    robots_txt_fetched_at BIGINT,
    last_crawled_at BIGINT,
    total_pages_crawled BIGINT DEFAULT 0,
    avg_response_time_ms FLOAT,
    error_rate FLOAT DEFAULT 0.0,
    is_blocked BOOLEAN DEFAULT FALSE,
    updated_at BIGINT
);
```

### URL 规范化策略

```
URL 规范化 (Canonicalization) 规则:

1. 协议标准化: http:// → https://
2. 主机名小写: WWW.EXAMPLE.COM → www.example.com
3. 默认端口移除: https://example.com:443/ → https://example.com/
4. 路径规范化:
   - 移除默认页面: /index.html → /
   - 移除尾部斜杠(视情况): /path/ → /path
   - 解码不必要的编码: %7E → ~
5. Fragment 移除: #section → (移除)
6. 查询参数排序: ?b=2&a=1 → ?a=1&b=2
7. 移除空查询参数: ?a=&b=1 → ?b=1
8. 移除跟踪参数: ?utm_source=xxx&id=1 → ?id=1
```

### 内容去重 (SimHash + 海明距离)

```
SimHash 原理:

1. 页面内容分词 (tokenize)
2. 计算每个 token 的 Hash 值 (64-bit)
3. 对每一位进行加权投票: bit=1 → +weight, bit=0 → -weight
4. 得到 64 位的指纹 (fingerprint)

海明距离 (Hamming Distance):
  - 两个 SimHash 指纹中不同位的数量
  - 海明距离 ≤ 3 → 认为近似重复

检测算法:
  将 64-bit SimHash 分成 4 个 16-bit 块
  如果两个页面相似(海明距离 ≤ 3)，至少有一个 16-bit 块完全相同
  → 可以用倒排索引快速查找候选
  
  Key:   simhash:{block_id}:{16bit_value}
  Value: Set of doc_ids with matching block
```

```python
def simhash(tokens: list, weights: list = None) -> int:
    """计算文本的 SimHash 64-bit 指纹"""
    v = [0] * 64
    if weights is None:
        weights = [1] * len(tokens)

    for token, weight in zip(tokens, weights):
        h = hash(token) & 0xFFFFFFFFFFFFFFFF  # 64-bit hash
        for i in range(64):
            if (h >> i) & 1:
                v[i] += weight
            else:
                v[i] -= weight

    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint

def hamming_distance(a: int, b: int) -> int:
    """计算两个 64-bit 值的海明距离"""
    x = a ^ b
    distance = 0
    while x:
        distance += 1
        x &= x - 1  # 清除最低位的 1
    return distance

def find_near_duplicates(doc_simhash: int, threshold: int = 3):
    """在海量 SimHash 中查找近似重复"""
    candidates = set()
    # 将 64-bit 分成 4 段 16-bit
    for i in range(4):
        block_value = (doc_simhash >> (i * 16)) & 0xFFFF
        block_candidates = redis.smembers(f"simhash:{i}:{block_value}")
        candidates.update(block_candidates)

    near_duplicates = []
    for doc_id in candidates:
        existing_simhash = load_simhash(doc_id)
        if hamming_distance(doc_simhash, existing_simhash) <= threshold:
            near_duplicates.append(doc_id)
    return near_duplicates
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────────┐
                              │           Seed URL Database                  │
                              │     (手动精选的高质量起始 URL 列表)              │
                              └─────────────────────┬────────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────────┐
                              │              URL Frontier (URL 边界)           │
                              │                                              │
                              │  ┌──────────────────────────────────────────┐│
                              │  │  优先级队列 (Priority Queue)               ││
                              │  │  ┌─────────┐ ┌─────────┐ ┌───────────┐  ││
                              │  │  │ P1: 高  │ │ P2: 中  │ │ P3: 低     │  ││
                              │  │  │重要页/  │ │正常页/  │ │低价值页/   │  ││
                              │  │  │新发现   │ │已有页   │ │已知重复   │  ││
                              │  │  └─────────┘ └─────────┘ └───────────┘  ││
                              │  └──────────────────────────────────────────┘│
                              │                                              │
                              │  ┌──────────────────────────────────────────┐│
                              │  │  域名级别队列 (Per-Domain Queues)          ││
                              │  │  - 保证礼貌性 (politeness)                  ││
                              │  │  - 同一域名串行或限并发                      ││
                              │  │  - politeness delay 可配置                 ││
                              │  └──────────────────────────────────────────┘│
                              │                                              │
                              │  ┌──────────────────────────────────────────┐│
                              │  │  URL 去重 (Bloom Filter + DB)             ││
                              │  │  - 已抓 URL 集合                           ││
                              │  │  - 队列中待抓 URL 集合                      ││
                              │  └──────────────────────────────────────────┘│
                              └─────────────────────┬────────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────────┐
                              │           Crawler Worker Farm                │
                              │           (分布式抓取节点集群)                   │
                              │                                              │
                              │  ┌──────────────┐   ┌──────────────┐        │
                              │  │  HTML Fetcher │   │  Renderer     │        │
                              │  │  ─────────────│   │  ─────────────│        │
                              │  │  标准HTTP抓取  │   │  JS渲染抓取   │        │
                              │  │  (curl/httpx)│   │  (Headless   │        │
                              │  │              │   │   Chrome/PPTR)│        │
                              │  └──────┬───────┘   └──────┬───────┘        │
                              │         │                   │                │
                              │  ┌──────▼───────────────────▼───────┐        │
                              │  │         HTML Parser               │        │
                              │  │  ──────────────────────────────── │        │
                              │  │  - 提取文本内容（正文抽取）          │        │
                              │  │  - 提取所有 <a href="..."> 链接    │        │
                              │  │  - 提取元数据 (title, description) │        │
                              │  │  - 提取结构化数据 (Schema.org)     │        │
                              │  └──────┬────────────────────────────┘        │
                              └─────────┼──────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────────────────────────────────┐
                              │          处理流水线 (Processing Pipeline)        │
                              │                                                │
                              │  ┌────────────────┐     ┌───────────────────┐ │
                              │  │ 域名解析 + DNS   │────▶│ Robots.txt Check  │ │
                              │  │ 缓存            │     │ 礼貌性校验         │ │
                              │  └────────────────┘     └───────────────────┘ │
                              │                                                │
                              │  ┌────────────────┐     ┌───────────────────┐ │
                              │  │ URL 去重        │────▶│ 内容去重 (SimHash)  │ │
                              │  │ (Bloom Filter) │     │ + 垃圾检测         │ │
                              │  └────────────────┘     └───────────────────┘ │
                              │                                                │
                              │  ┌────────────────┐     ┌───────────────────┐ │
                              │  │ 内容存储         │────▶│ URL 提取 & 标准化   │ │
                              │  │ (S3/HDFS/      │     │ (新链接放入队列)     │ │
                              │  │  BigTable)    │     │                   │ │
                              │  └────────────────┘     └───────────────────┘ │
                              └────────────────────────────────────────────────┘
```

---

## 核心深入

### URL Frontier 设计

URL Frontier 是爬虫系统的大脑，负责管理待抓取的 URL 队列。

```
双层 URL Frontier 架构:

┌───────────────────────────────────────────────────────┐
│              URL Frontier 详细设计                      │
│                                                       │
│  Front Queues (前端队列, 内存中):                       │
│  ┌─────────────────────────────────────────────┐     │
│  │ Per-Domain 优先级队列                         │     │
│  │                                              │     │
│  │ domain:example.com → [url1, url2, url3, ...] │     │
│  │ domain:news.com    → [url4, url5, ...]       │     │
│  │ domain:blog.com    → [url6, ...]             │     │
│  │                                              │     │
│  │ 选择策略:                                     │     │
│  │  - Round-Robin 轮询各域名队列                  │     │
│  │  - 每个域名最多同时抓取 N 个页面 (礼貌)         │     │
│  │  - 高优先级域名获得更多调度机会                 │     │
│  └─────────────────────────────────────────────┘     │
│                                                       │
│  Back Queues (后端队列, 持久化磁盘):                    │
│  ┌─────────────────────────────────────────────┐     │
│  │ Priority 1 (高优先级) Queue:                  │     │
│  │   - 新发现的 URL                              │     │
│  │   - 高 PageRank / 高价值域名                  │     │
│  │                                              │     │
│  │ Priority 2 (中优先级) Queue:                  │     │
│  │   - 正常页面 URL                              │     │
│  │   - 新闻类快速更新页面                         │     │
│  │                                              │     │
│  │ Priority 3 (低优先级) Queue:                  │     │
│  │   - 低价值页面 (已知低质量)                     │     │
│  │   - 可疑/垃圾页面                             │     │
│  │   - 深度过深的页面                            │     │
│  │                                              │     │
│  │ Priority 4 (重爬队列) Queue:                  │     │
│  │   - 需定期重抓的页面                           │     │
│  │   - 上次抓取失败需重试                         │     │
│  └─────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────┘

实现:
  前端: Redis Sorted Set (per-domain)
  后端: Kafka / RabbitMQ 持久化队列
```

### 礼貌性控制 (Politeness)

```
Google 的礼貌策略 (Robust Politeness):

1. 遵守 robots.txt:
   - 每次首次爬取某域名，先获取 robots.txt
   - 缓存 robots.txt，定期更新
   - 遵守 Crawl-delay 指令

2. 域名级限流:
   - 同一域名并发连接 ≤ 2-3 个
   - 同域名请求间隔 ≥ Crawl-delay 或默认 1-5 秒
   - 使用令牌桶对每个域名限流

3. 自适应降速:
   - 如果目标服务器响应变慢 (p99 > 阈值) → 降低爬取速率
   - 如果返回大量 429/503 → 指数退避 (1s → 2s → 4s → ... → 300s)
   - 如果持续失败 → 放入冷却名单 (cool-down list)

4. 域名/IP 映射:
   - 避免对同一 IP 的大量不同域名同时请求 (共享主机)
   - DNS 解析后按 IP 聚合限流

5. HTTP 头部要求:
   - 使用描述性的 User-Agent
   - 提供联系信息 (可在异常时被站长联系)
   - 尊重 If-Modified-Since 头 (节省带宽)
```

```python
class PolitenessController:
    def __init__(self):
        self.per_domain_tokens = {}      # 每域名令牌桶
        self.default_delay = 2000         # 默认 2 秒
        self.max_concurrent = 3           # 每域名最大并发
        self.cool_down_domains = {}       # 冷却域名
        self.robots_cache = RobotsCache()

    def can_crawl(self, domain: str) -> bool:
        # 检查冷却状态
        if domain in self.cool_down_domains:
            if time.time() < self.cool_down_domains[domain]:
                return False
            del self.cool_down_domains[domain]

        # 检查并发限制
        active = self.get_active_count(domain)
        if active >= self.max_concurrent:
            return False

        # 检查 robots.txt 延迟
        delay = self.robots_cache.get_crawl_delay(domain)
        if delay is None:
            delay = self.default_delay

        # 令牌桶检查
        bucket = self.per_domain_tokens.get(domain)
        if bucket is None:
            bucket = TokenBucket(capacity=1, rate=1000.0/delay)
            self.per_domain_tokens[domain] = bucket
        return bucket.try_consume()

    def report_error(self, domain: str, status_code: int):
        if status_code in (429, 503):
            # 指数退避
            cooldown = min(self.current_cooldown.get(domain, 1) * 2, 600)
            self.cool_down_domains[domain] = time.time() + cooldown
            self.current_cooldown[domain] = cooldown
            # 降低令牌生成速率
            self.per_domain_tokens[domain].rate *= 0.5
```

### Bloom Filter 实现 URL 去重

```
Bloom Filter 用于快速判断 URL 是否已经爬取过。

参数计算:
  n = 预期元素数量 = 100 亿 (10B)
  p = 期望假阳性率 (False Positive Rate) = 0.001 (0.1%)
  
  m (位数组大小) = -n × ln(p) / (ln(2))²
    = -10,000,000,000 × ln(0.001) / (0.693²)
    = -10B × (-6.908) / 0.480
    ≈ 143,917,000,000 bits ≈ 18 GB

  k (哈希函数数量) = (m/n) × ln(2)
    = (143.9B / 10B) × 0.693
    ≈ 10 个哈希函数

优势:
  - 存储效率极高: 10 亿 URL 只需 18 GB vs 直接存储需要 200 GB+
  - O(k) 查询时间，常数级

局限性:
  - 假阳性 (False Positive): 0.1% 的 URL 被误判为已抓取 → 接受
  - 不能删除元素 → 使用 Counting Bloom Filter 或定期重建
```

```python
import math
import mmh3  # MurmurHash3

class BloomFilter:
    def __init__(self, expected_elements: int, false_positive_rate: float = 0.001):
        self.size = int(-expected_elements * math.log(false_positive_rate) / (math.log(2) ** 2))
        self.hash_count = int((self.size / expected_elements) * math.log(2))
        self.bit_array = RedisBitArray(f"bloom:crawled_urls", self.size)

    def add(self, url: str):
        for i in range(self.hash_count):
            idx = mmh3.hash(url, i) % self.size
            self.bit_array.set(idx)

    def contains(self, url: str) -> bool:
        for i in range(self.hash_count):
            idx = mmh3.hash(url, i) % self.size
            if not self.bit_array.get(idx):
                return False
        return True

# 生产环境使用 Redis Bitmap 或 RedisBloom 模块
# Redis Bitmap 限制: 单个 key 512MB (2^32 bits)
# 解决方案: 分片 Bloom Filter
class ShardedBloomFilter:
    def __init__(self, expected_elements, shard_count=32):
        self.shards = [
            BloomFilter(expected_elements // shard_count) 
            for _ in range(shard_count)
        ]

    def add(self, url: str):
        shard_idx = hash(url) % len(self.shards)
        self.shards[shard_idx].add(url)

    def contains(self, url: str) -> bool:
        shard_idx = hash(url) % len(self.shards)
        return self.shards[shard_idx].contains(url)
```

### 动态渲染 (JS 渲染)

```
现代网站大量使用 JavaScript 动态渲染内容。传统 HTTP 爬虫无法抓取 SPA 内容。

两种策略:

1. 选择性渲染 (Hybrid Approach)【推荐】
   - 先用轻量级 HTTP 抓取
   - 检测到 JS 依赖信号:
     - 页面 HTML 很小但 URL 复杂
     - 检测到 <div id="root/app"> 容器
     - 关键内容缺失
     - 使用了已知 JS 框架 (<script src="...react...>")
   - 标记为需要渲染的 URL → 进入渲染队列

2. 全部渲染 (Full Rendering)
   - 所有页面都经过 Headless Chrome 渲染
   - 成本高 (CPU/内存密集)
   - 仅适用小规模爬虫

渲染爬虫节点:
  - Headless Chrome / Puppeteer / Playwright
  - 每节点可并行渲染 5-10 个页面
  - 超时 30 秒自动终止
  - 渲染结果缓存 (相同 URL + 相同时间窗口)
```

### 分布式爬虫协调

```
分布式爬虫的挑战:

1. 任务分配:
   - 主控节点将域名分配给不同的 Worker 组
   - 同一域名由固定 Worker 组负责 (避免重复抓取)
   - 基于 Consistent Hashing: worker_group = hash(domain) % num_groups

2. Worker 容错:
   - Worker 定期发送心跳到 Master
   - 心跳超时 → 将其任务重新分配给其他 Worker
   - 使用 WAL (Write-Ahead Log) 确保已抓取结果不丢失

3. 全局状态同步:
   - Bloom Filter: 各 Worker 本地维护一个小的 Bloom Filter
     定期与全局 Bloom Filter 合并 (Redis)
   - URL Frontier: 集中式 Redis + Kafka
   - 域名策略: 集中式配置，本地缓存

4. 抓取进度监控:
   - Prometheus + Grafana 面板
   - 实时指标: URLs/sec, 成功率, 延迟分位数, Bloom Filter 假阳性率
```

---

## 扩展性与高可用

### 弹性伸缩

```
爬虫 Worker 的自动伸缩:

1. 基于队列深度的伸缩:
   - Kafka Lag Monitor 监控待抓取队列深度
   - Lag > 阈值: 自动扩容 Worker (K8s HPA)
   - Lag < 阈值 × 0.5: 自动缩容

2. 时间分段伸缩:
   - 夜间 (UTC 低谷期): 使用 Spot 实例降低成本
   - 日间 (高峰期): 正规实例保证稳定性
   - 使用预热池 (Warm Pool) 快速补充

3. 域名维度负载均衡:
   - 大站 (百万级以上页面): 独立 Worker 组
   - 小站 (< 1000 页): 聚合到一个 Worker 组
```

### 灾难恢复

```
故障场景 & 恢复策略:

1. Worker 节点故障:
   - 未完成的任务由 Master 重新分配给其他 Worker
   - 已开始但未上报结果的任务: 投递到 DLQ (Dead Letter Queue)
   - 人工或自动重试

2. URL Frontier 故障:
   - Kafka 天然持久化 + 副本 (replication factor ≥ 3)
   - 消费进度保存 (offset commit)
   - 故障恢复后从上次位置继续

3. Redis (Bloom Filter) 故障:
   - 定期持久化 Bloom Filter 到磁盘 (RDB/AOF)
   - 从快照恢复 + 重放增量数据
   - 短期降级: 仅在 DB 中查重 (延迟增加，但功能可用)

4. 存储层故障:
   - 数据多副本 (3副本)
   - 跨数据中心备份
   - 关键元数据同步到备用集群
```

### 监控与告警

```
爬虫系统监控:

抓取健康:
  - 抓取速率 (URLs/s/worker, total URLs/s)
  - 各状态码分布 (200/301/404/429/5xx 比例)
  - 各域名抓取成功率
  - 平均抓取延迟 P50/P95/P99
  - DNS 解析延迟 P99

队列健康:
  - URL Frontier 总深度和各优先级队列深度
  - 新 URL 发现速率 vs 抓取速率
  - 各队列消费延迟 (Lag)
  - 去重率 (多少 URL 被 Bloom Filter 拒绝)

质量指标:
  - 内容去重比例 (近似重复检测命中率)
  - 垃圾/低质量内容比例
  - robots.txt 被拒绝的请求比例
  - 新域名发现速率

基础设施:
  - Worker 数/CPU/内存使用率
  - 网络带宽使用 (In/Out)
  - 磁盘 IO
  - Bloom Filter 假阳性率 (抽样估计)
```

---

## 总结

网络爬虫是搜索引擎的基础设施，架构设计核心：

1. **URL Frontier**：优先级队列 + Per-Domain 队列是高效调度和保证礼貌性的关键
2. **礼貌性控制**：robots.txt 遵守、域名级令牌桶、自适应降速、指数退避
3. **URL 去重**：Bloom Filter 是海量 URL 去重的最佳实践，18GB 可以管理 100 亿 URL
4. **内容去重**：SimHash + 海明距离实现近似重复检测，避免存储重复内容
5. **分布式协调**：一致性哈希分配域名、心跳检测 Worker、WAL 保证结果不丢失
6. **JS 渲染**：选择性渲染（快速 HTTP + 按需 Headless Chrome）是最佳性价比策略
7. **增量抓取**：基于 HTTP If-Modified-Since + 页面变化频率动态调整重抓周期
8. **弹性伸缩**：基于队列深度 + 时间段自动调整 Worker 规模，结合 Spot 实例降成本

**面试核心权衡讨论：**
- 集中式 vs 分布式 URL Frontier：简单性 vs 可扩展性
- 礼貌性：如何平衡抓取效率与对目标网站的友好性
- Bloom Filter 参数：假阳性率 (0.1% vs 1%) 对召回率的影响
- 渲染策略：纯 HTTP (快/低成本) vs 全渲染 (完整/高成本) vs 混合
- 增量策略：基于时间 vs 基于变化频率 vs 基于重要性
- 任务分配：按域名分配 vs 按 URL hash 分配 (礼貌 vs 负载均衡)
