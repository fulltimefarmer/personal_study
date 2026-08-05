# 46. 设计带去重和新鲜度管理的URL爬虫 (Design URL Crawler with Dedup & Freshness Management)

## 题目

设计一个大规模分布式URL爬虫系统，核心特性是URL去重（避免重复抓取）和新鲜度管理（已抓取内容按策略重新抓取）。类似Googlebot的网页抓取系统。

## 需求澄清

### 功能性需求

1. **URL抓取 (Crawl)**: 从种子URL开始，递归抓取网页内容
2. **URL去重 (Dedup)**: 避免重复抓取相同URL（精确去重 + 近似去重）
3. **新鲜度管理 (Freshness)**: 实现重抓策略，对已抓取页面按优先级重新抓取以保持内容新鲜
4. **链接提取 (Link Extraction)**: 解析HTML，提取新的URL加入抓取队列
5. **robots.txt 遵守**: 抓取前检查并遵守 robots.txt
6. **抓取频率控制 (Rate Limiting)**: 对同一域名控制抓取频率（politeness）
7. **内容存储**: 存储原始HTML + 元数据（抓取时间、HTTP状态码等）
8. **抓取优先级**: 基于页面重要性（PageRank/站点权威性）调整抓取顺序

### 非功能性需求

1. **可扩展性**: 支持百亿级URL去重，每日数十亿次抓取
2. **高吞吐**: 百万级页面/小时抓取
3. **高可用**: 各组件冗余，单点故障不影响整体抓取
4. **存储效率**: 去重数据结构内存/磁盘占用小
5. **礼貌抓取**: 不压垮目标网站

### 容量估算

```
互联网规模估算（简化）:
  已知URL总量: ~500亿
  每日新发现URL: ~10亿

抓取规模:
  日均抓取量: 50亿页面
  峰值爬取速率: 50亿 / 86400 ≈ 57,800 QPS

去重存储:
  500亿URL的去重过滤器
  使用布隆过滤器: 500亿 × ~10 bits/URL ≈ 62.5GB (可接受)
  使用精确去重: 500亿 × (URL平均80B + 元数据50B) ≈ 6.5TB

内容存储:
  每个页面平均 200KB (压缩后)
  日均增量: 50亿 × 200KB = 1PB/天
  保留 30 天: 30PB

抓取队列:
  待抓取URL优先级队列: ~10亿条 × 100B ≈ 100GB
```

## API设计

### 内部服务API

```protobuf
service CrawlService {
  // 提交URL到抓取队列
  rpc SubmitURL(SubmitURLRequest) returns (SubmitURLResponse);

  // 获取待抓取的URL批次
  rpc FetchURLBatch(FetchURLBatchRequest) returns (FetchURLBatchResponse);

  // 提交抓取结果
  rpc SubmitCrawlResult(SubmitCrawlResultRequest) returns (SubmitCrawlResultResponse);

  // 检查URL是否需要重新抓取
  rpc CheckFreshness(CheckFreshnessRequest) returns (CheckFreshnessResponse);
}

message SubmitURLRequest {
  string url = 1;
  URLSource source = 2;          // SEED / LINK_EXTRACTED / SITEMAP / MANUAL
  float priority = 3;            // 0.0 - 1.0 优先级
  string referrer_url = 4;       // 来源URL
}

enum URLSource {
  SEED = 0;
  LINK_EXTRACTED = 1;
  SITEMAP = 2;
  MANUAL = 3;
  RECRAWL = 4;
}

message SubmitURLResponse {
  bool accepted = 1;             // false = 已去重拒绝
  string reason = 2;             // DUPLICATE / QUEUE_FULL / DOMAIN_BLOCKED
}

message FetchURLBatchRequest {
  string worker_id = 1;
  int32 batch_size = 2;          // 默认 100
  repeated string preferred_domains = 3;  // 优先抓取的域名(如本地化爬虫)
}

message CrawlResult {
  string url = 1;
  int32 http_status = 2;
  string content_hash = 3;       // SHA256 内容哈希
  int64 content_length = 4;
  int64 crawl_timestamp = 5;
  int64 last_modified = 6;       // 从 HTTP Last-Modified 获取
  string etag = 7;
  repeated string extracted_links = 8;
  bool content_changed = 9;      // 与上次内容比较
}
```

## 数据模型

### MySQL 元数据表

```sql
-- URL 元数据表
CREATE TABLE url_metadata (
    url_hash CHAR(32) PRIMARY KEY,          -- MD5(url)
    url TEXT NOT NULL,
    canonical_url TEXT,
    domain VARCHAR(255) NOT NULL,
    first_discovered TIMESTAMP NOT NULL,
    last_crawled TIMESTAMP,
    last_modified_from_server TIMESTAMP,    -- 服务端声称的修改时间
    content_hash CHAR(64),                  -- SHA256 内容哈希
    http_status SMALLINT,
    crawl_count INT DEFAULT 0,
    change_frequency ENUM('HIGH','MEDIUM','LOW','UNKNOWN') DEFAULT 'UNKNOWN',
    page_rank FLOAT DEFAULT 0.0,
    priority FLOAT DEFAULT 0.5,
    is_active TINYINT(1) DEFAULT 1,
    content_length INT,
    content_type VARCHAR(128),
    INDEX idx_domain (domain),
    INDEX idx_last_crawled (last_crawled),
    INDEX idx_priority (priority DESC, last_crawled ASC),
    INDEX idx_change_frequency (change_frequency, last_crawled)
) ENGINE=InnoDB;

-- robots.txt 规则缓存表
CREATE TABLE robots_rules (
    domain VARCHAR(255) NOT NULL,
    user_agent VARCHAR(128) NOT NULL DEFAULT '*',
    rule_type ENUM('ALLOW','DISALLOW','CRAWL_DELAY'),
    path_pattern VARCHAR(512) NOT NULL,
    crawl_delay INT DEFAULT 0,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (domain, user_agent, rule_type, path_pattern)
) ENGINE=InnoDB;

-- 抓取日志表 (分区表)
CREATE TABLE crawl_log (
    id BIGINT AUTO_INCREMENT,
    url_hash CHAR(32) NOT NULL,
    worker_id VARCHAR(64),
    http_status SMALLINT,
    response_time_ms INT,
    content_length INT,
    content_changed TINYINT(1) DEFAULT 0,
    new_links_count INT DEFAULT 0,
    error_message TEXT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, crawled_at),
    INDEX idx_url_hash (url_hash),
    INDEX idx_crawled_at (crawled_at)
) ENGINE=InnoDB
PARTITION BY RANGE (TO_DAYS(crawled_at)) (
    PARTITION p20240101 VALUES LESS THAN (TO_DAYS('2024-01-02')),
    PARTITION p20240102 VALUES LESS THAN (TO_DAYS('2024-01-03'))
    -- ... 按天分区
);
```

### 布隆过滤器 + 精确去重

```
两层去重架构:

Layer 1 (布隆过滤器 - 内存):
  - 快速排除已抓取URL
  - 可能误报 (False Positive)
  - 参数: 500亿URL, 误报率0.1% → ~60GB内存
  - 使用可扩展布隆过滤器(计数布隆)支持删除/过期

Layer 2 (精确去重 - 磁盘/分布式KV):
  - 确认是否真的重复
  - 存储 URL Hash → 元数据
  - 使用 Redis / Cassandra / RocksDB
```

### 新鲜度管理模型

```
重抓优先级 = f(change_frequency, last_crawled, page_rank)

每个URL的重抓间隔基于:
  - 历史变更频率 (统计模型)
  - 页面重要性 (PageRank)
  - 内容类型 (新闻 > 博客 > 静态页面)

变更频率分类:
  HIGH:   每 15 分钟重抓  (新闻首页)
  MEDIUM: 每 4 小时重抓   (博客/论坛)
  LOW:    每 7 天重抓     (关于页面/静态文档)
  UNKNOWN: 每 24 小时重抓  (新发现的URL)
```

## 高层次架构

```
                          ┌──────────────────────────────┐
                          │     种子URL / Sitemap输入     │
                          └──────────────┬───────────────┘
                                         │
                          ┌──────────────▼───────────────┐
                          │       URL Frontier            │
                          │  ┌─────────────────────────┐  │
                          │  │ 优先级队列 (按域名分片)    │  │
                          │  │ - 礼貌性控制 (per domain) │  │
                          │  │ - 优先级调度              │  │
                          │  └─────────────────────────┘  │
                          └──────────────┬───────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
             ┌──────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
             │ Crawler     │    │  Crawler     │    │  Crawler     │
             │ Worker 1    │    │  Worker 2    │    │  Worker N    │
             │             │    │              │    │              │
             │ ┌─────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
             │ │Fetcher  │ │    │ │ Fetcher  │ │    │ │ Fetcher  │ │
             │ │Robots   │ │    │ │ Robots   │ │    │ │ Robots   │ │
             │ │Parser   │ │    │ │ Parser   │ │    │ │ Parser   │ │
             │ │Extractor│ │    │ │ Extractor│ │    │ │ Extractor│ │
             │ └─────────┘ │    │ └──────────┘ │    │ └──────────┘ │
             └──────┬──────┘    └───────┬──────┘    └───────┬──────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
   ┌─────▼─────┐                  ┌──────▼──────┐                ┌───────▼───────┐
   │  去重服务  │                  │  新鲜度管理   │                │  内容存储      │
   │ ┌───────┐ │                  │ ┌──────────┐ │                │ ┌───────────┐ │
   │ │Bloom  │ │                  │ │重抓调度器 │ │                │ │Raw HTML   │ │
   │ │Filter │ │                  │ │变更检测   │ │                │ │(S3/HDFS)  │ │
   │ └───────┘ │                  │ │优先级计算 │ │                │ └───────────┘ │
   │ ┌───────┐ │                  │ └──────────┘ │                │               │
   │ │精确去重│ │                  │               │                │               │
   │ └───────┘ │                  └──────────────┘                └───────────────┘
   └─────┬─────┘
         │
   ┌─────▼─────┐
   │MySQL/Cass │
   │andra 元数据│
   └───────────┘
```

### 核心数据流

```
抓取循环:

1. Worker 从 URL Frontier 获取一批URL (按域名礼貌调度)
2. 检查 robots.txt (缓存)
3. HTTP Fetch (带 If-Modified-Since / If-None-Match)
4. 内容解析 + 链接提取
5. 去重检查:
   a. 布隆过滤器: "probably seen"? → 步骤b
   b. 精确去重: URL hash 已存在? → 跳过
6. 内容新鲜度检查:
   a. 如果内容未变化 (304 Not Modified) → 更新 last_crawled, 调整变更频率
   b. 如果内容变化 → 存储新内容, 计算变更频率
7. 新发现的链接 → 布隆过滤器预检查 → URL Frontier
8. 抓取结果 → 元数据存储 + 内容存储
```

## 核心深入

### URL去重策略

#### 方案A: 仅布隆过滤器

```
布隆过滤器参数:
  n = 500亿 (元素数量)
  p = 0.001 (误报率 0.1%)
  m = -n*ln(p) / (ln(2))^2 ≈ 718亿 bits ≈ 8.4GB

优点: 极低内存
缺点: 有误报 (0.1% 的新URL会被误判为已抓取)
```

#### 方案B: 布隆过滤器 + 精确去重 (推荐)

```python
class URLDedupService:
    def __init__(self):
        self.bloom_filter = ScalableBloomFilter(
            initial_capacity=10_000_000_000,
            error_rate=0.001
        )
        self.precise_store = RocksDB('/data/url_dedup')  # 磁盘KV存储

    def is_duplicate(self, url: str) -> bool:
        url_hash = hashlib.md5(url.encode()).digest()

        # Layer 1: 布隆过滤器快速检查
        if not self.bloom_filter.might_contain(url_hash):
            # 肯定没有 → 添加
            self.bloom_filter.add(url_hash)
            self.precise_store.put(url_hash, self._create_metadata(url))
            return False

        # Layer 2: 精确去重确认
        if self.precise_store.get(url_hash) is not None:
            return True  # 确定重复

        # 布隆过滤器误报 → 添加
        self.precise_store.put(url_hash, self._create_metadata(url))
        return False
```

#### URL 规范化 (Canonicalization)

去重前必须对URL做规范化，否则同一个页面可能以不同形式被多次抓取：

```python
def canonicalize_url(url: str) -> str:
    """URL 规范化: 将语义等价的不同URL形式统一"""
    parsed = urlparse(url)

    # 1. 转小写 scheme 和 host
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()

    # 2. 移除默认端口
    if (scheme == 'http' and parsed.port == 80) or \
       (scheme == 'https' and parsed.port == 443):
        host = host.split(':')[0]

    # 3. 路径规范化: /a/b/../c → /a/c
    path = os.path.normpath(parsed.path)

    # 4. 移除 fragment (#anchor)
    fragment = ''

    # 5. 排序 query 参数
    query = '&'.join(sorted(
        [q for q in parsed.query.split('&') if q],
        key=lambda x: x.split('=')[0]
    ))

    # 6. 移除常见追踪参数 (utm_source, fbclid 等)
    tracking_params = {'utm_source','utm_medium','utm_campaign',
                       'fbclid','gclid','ref','referrer'}
    query_parts = [q for q in query.split('&')
                   if q.split('=')[0] not in tracking_params]
    query = '&'.join(query_parts)

    # 7. 移除末尾斜杠 (视情况)
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]

    # 8. 移除 www 前缀 (视站点而定)
    if host.startswith('www.'):
        host = host[4:]

    return urlunparse((scheme, host, path, '', query, fragment))
```

#### 近似去重 (Near-Duplicate Detection)

内容几乎相同但URL不同的网页也需要去重：

```python
def near_duplicate_check(content: str) -> Optional[str]:
    """
    使用 SimHash 进行近似去重
    
    Google 使用的 SimHash 算法:
    1. 对文档特征(token)计算hash
    2. 加权求和 (按TF-IDF权重)
    3. 降维 (正=1, 负=0) → 64-bit fingerprint
    4. 汉明距离 ≤ 3 → 判定为近似重复
    """
    fingerprint = compute_simhash(content)
    existing_fps = query_simhash_index(fingerprint, max_hamming_distance=3)
    if existing_fps:
        return existing_fps[0].url
    store_fingerprint(fingerprint, url, content_hash)
    return None
```

### 新鲜度管理策略

#### 自适应重抓间隔算法

```python
class FreshnessManager:
    """
    基于历史变更模式自适应调整重抓间隔
    
    核心思路:
    - 记录每次抓取的内容是否变化
    - 计算变更概率
    - 高变更率 → 缩短间隔, 低变更率 → 延长间隔
    """

    def __init__(self):
        # 变更历史窗口: 每个URL记录最近N次抓取的变更情况
        self.change_history_window = 10

    def update_freshness(self, url_hash, content_changed, last_modified):
        """每次抓取后更新新鲜度"""
        url_info = self.get_url_metadata(url_hash)

        # 记录变更
        url_info.change_history.append({
            'timestamp': time.time(),
            'changed': content_changed,
            'last_modified_delta': (time.time() - last_modified) if last_modified else None
        })
        url_info.change_history = url_info.change_history[-self.change_history_window:]

        # 计算变更频率
        change_count = sum(1 for h in url_info.change_history if h['changed'])
        change_ratio = change_count / len(url_info.change_history)

        if change_ratio > 0.5:
            url_info.change_frequency = 'HIGH'
            url_info.recrawl_interval = 900        # 15 分钟
        elif change_ratio > 0.1:
            url_info.change_frequency = 'MEDIUM'
            url_info.recrawl_interval = 14400      # 4 小时
        else:
            url_info.change_frequency = 'LOW'
            url_info.recrawl_interval = 604800     # 7 天

        # 如果 Last-Modified 时间戳暗示变更很快
        if last_modified and (time.time() - last_modified) < 3600:
            url_info.recrawl_interval = min(url_info.recrawl_interval, 3600)

        # 基于重要性调整
        importance_bonus = url_info.page_rank / 10.0  # PageRank (0-10)
        url_info.recrawl_interval = max(60,
            int(url_info.recrawl_interval / (1 + importance_bonus)))

        self.save_url_metadata(url_hash, url_info)

    def get_recrawl_candidates(self, limit=10000):
        """获取需要重新抓取的URL (按紧急程度排序)"""
        now = time.time()
        return db.query("""
            SELECT url_hash, url, last_crawled, recrawl_interval,
                   (now() - last_crawled) / recrawl_interval AS urgency
            FROM url_metadata
            WHERE is_active = 1
              AND (now() - last_crawled) > recrawl_interval * 0.8
            ORDER BY urgency DESC
            LIMIT ?
        """, limit)
```

#### 新鲜度算法对比

| 算法 | 思路 | 优点 | 缺点 |
|------|------|------|------|
| 固定间隔 | 所有URL同一间隔 | 简单 | 浪费资源/遗漏更新 |
| TTL-based | 每个URL独立TTL | 灵活 | TTL如何确定？ |
| 泊松过程建模 | P(change) * 内容陈旧成本 | 理论上最优 | 成本难量化 |
| 自适应学习 | 历史变更率 → 动态调整 | 实用、效果好 | 冷启动问题 |

### URL Frontier 设计 (优先级队列)

```
Frontier 架构:

全局优先级队列
    │
    ├─ 优先级桶 0 (最高): PageRank > 8, 新闻类 → 15分钟间隔
    ├─ 优先级桶 1 (高):   PageRank 5-8, 博客类 → 1小时间隔
    ├─ 优先级桶 2 (中):   新发现的URL, 中等站点 → 4小时间隔
    ├─ 优先级桶 3 (低):   低重要度静态页面 → 24小时间隔
    └─ 优先级桶 4 (最低): robots.txt, sitemap → 每天检查

每个桶内按域名进一步分组:
  domain_group:{domain}
    └─ URL列表 (FIFO/优先级排序)

礼貌性控制:
  per-domain 抓取间隔: crawl_delay (从 robots.txt 获取, 默认 1 秒)
  同一域名同时最多 N 个并发连接 (通常 N=2)
```

```python
class URLFrontier:
    def __init__(self):
        self.queues = {}        # domain → PriorityQueue
        self.domain_last_crawl = {}  # domain → last_crawl_timestamp
        self.domain_inflight = {}    # domain → 当前并发数
        self.max_concurrent_per_domain = 2

    def add_url(self, url, priority, domain):
        if domain not in self.queues:
            self.queues[domain] = PriorityQueue()
        self.queues[domain].put((priority, time.time(), url))

    def get_batch(self, worker_id, batch_size, preferred_domains=None):
        batch = []
        now = time.time()
        candidates = preferred_domains or self.queues.keys()

        for domain in sorted(candidates,
                             key=lambda d: self.get_domain_priority(d),
                             reverse=True):
            if len(batch) >= batch_size:
                break
            if domain not in self.queues or self.queues[domain].empty():
                continue

            # 礼貌性检查
            inflight = self.domain_inflight.get(domain, 0)
            if inflight >= self.max_concurrent_per_domain:
                continue

            last = self.domain_last_crawl.get(domain, 0)
            delay = self.get_crawl_delay(domain)
            if now - last < delay:
                continue

            _, _, url = self.queues[domain].get()
            batch.append(url)
            self.domain_last_crawl[domain] = now
            self.domain_inflight[domain] = inflight + 1

        return batch

    def mark_complete(self, domain):
        self.domain_inflight[domain] = max(0,
            self.domain_inflight.get(domain, 0) - 1)
```

### HTTP 条件请求优化

使用 HTTP 条件请求减少不必要的下载：

```python
async def fetch_url(url, url_metadata):
    headers = {}

    if url_metadata.etag:
        headers['If-None-Match'] = url_metadata.etag
    if url_metadata.last_modified_from_server:
        headers['If-Modified-Since'] = url_metadata.last_modified_from_server

    response = await http_client.get(url, headers=headers)

    if response.status == 304:  # Not Modified
        return CrawlResult(
            url=url,
            http_status=304,
            content_changed=False,
            etag=url_metadata.etag,
            last_modified=url_metadata.last_modified_from_server,
            crawl_timestamp=time.time()
        )

    # 内容已更新
    return CrawlResult(
        url=url,
        http_status=response.status,
        content=response.body,
        content_hash=sha256(response.body).hexdigest(),
        content_changed=True,
        etag=response.headers.get('ETag'),
        last_modified=parse_date(response.headers.get('Last-Modified')),
        crawl_timestamp=time.time()
    )
```

### 布隆过滤器持久化与扩展

```
问题: 布隆过滤器在内存中，重启后丢失

方案: 
  1. Redis Bloom Filter 模块 (RedisBloom)
     BF.RESERVE crawler_urls 0.001 50000000000
     BF.ADD crawler_urls "url_hash_1"
  
  2. 定期持久化到磁盘
     每 30 分钟将布隆过滤器位图 dump 到文件
     启动时加载

  3. 可扩展布隆过滤器 (Scalable Bloom Filter)
     当当前过滤器填满时，创建新过滤器
     查询时检查所有过滤器
```

## 扩展性与高可用

### 分布式部署

```
┌─────────────────────────────────────────────────────┐
│                  Coordinator (主节点)                │
│  - URL Frontier 管理                                │
│  - 全局优先级调度                                    │
│  - Worker 健康检查                                   │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        │              │              │              │
   ┌────▼────┐   ┌─────▼────┐  ┌─────▼────┐  ┌─────▼────┐
   │Worker 1 │   │Worker 2  │  │Worker 3  │  │Worker N  │
   │(US IP)  │   │(EU IP)   │  │(ASIA IP) │  │(US IP)   │
   └─────────┘   └──────────┘  └──────────┘  └──────────┘

  Worker 地理分布: 
    - 使用就近的代理IP
    - Coordinator 按域名地理位置分配任务
```

### 监控告警

| 指标 | 说明 | 告警 |
|------|------|------|
| crawl_success_rate | 抓取成功率 | < 95% |
| new_urls_discovered_rate | 新URL发现率 | 突降 > 50% |
| queue_depth | 待抓取队列深度 | > 3倍基线 |
| domain_block_rate | 被目标站拦截率 | 域名 > 10% |
| robots_check_fail_rate | robots.txt获取失败率 | > 5% |
| dedup_false_positive_rate | 布隆过滤器误报率 | > 0.5% |
| worker_utilization | Worker利用率 | < 50% / > 90% |
| freshness_staleness | 超过重抓时间未抓的URL比例 | > 10% |

## 总结

1. **双层层去重**: 布隆过滤器（快速）+ 精确去重（准确），内存效率与准确性兼得
2. **URL规范化**: 抓取前规范化是去重的前提，包括大小写、默认端口、追踪参数移除
3. **SimHash近似去重**: 内容几乎相同的不同URL也算重复
4. **自适应新鲜度**: 基于历史变更率动态调整重抓间隔，高频变更=短间隔，低频=长间隔
5. **礼貌性抓取**: per-domain 频率控制 + robots.txt 遵守 + 并发限制
6. **优先级队列**: 按 PageRank × 站点重要性 × 新鲜度紧急程度 排序
7. **HTTP条件请求**: If-Modified-Since/If-None-Match 避免下载未变化内容
8. **分布式Worker**: 全局 Coordinator 调度 + 地理分布 Worker + per-domain 亲和性

面试中可能追问: 如何处理无限日历页面? 爬虫陷阱(深度无限链接)? 如何处理JavaScript渲染的SPA页面?
