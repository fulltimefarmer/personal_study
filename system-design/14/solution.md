# 设计附近/邻近服务 (Design Proximity / Nearby Search)

## 题目

设计一个附近服务，类似 Yelp / Google 附近搜索 / 美团/大众点评。用户可以搜索附近的商家、餐厅、POI，支持按距离排序和按条件筛选。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 附近搜索 | 根据用户经纬度，搜索附近 K 米内的商家/POI |
| 距离排序 | 结果按距离由近到远排序 |
| 类别筛选 | 按类别(餐厅/加油站/超市等)过滤 |
| 搜索框 | 按名称/关键词搜索并匹配 |
| POI 详情 | 展示商家详细信息(名称/地址/评分/图片) |
| 动态位置 | 用户移动时实时更新搜索结果 |
| POI CRUD | 商家信息的增加/更新/删除 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 延迟 | 搜索请求 P99 < 200ms |
| 可用性 | 99.99% |
| 精度 | 距离误差 < 50m |
| POI数量 | 支持上亿 POI |
| 并发 | 支持百万级 QPS (节假日高峰) |
| 时效性 | POI 信息变更后 1min 内可搜索到 |

### 容量估算

```
假设:
  - DAU: 1亿
  - 每人平均搜索 5 次/天
  - 搜索 QPS: 1亿 × 5 / 86400 ≈ 5787 QPS (平均)
  - 峰值 QPS: 5787 × 5 = 28,935 QPS
  - POI 总量: 1亿 (全国范围)

POI 存储:
  每个 POI: ~1KB (名称/地址/经纬度/分类/评分等)
  总存储: 1亿 × 1KB = 100GB

空间索引存储:
  GeoHash 索引: ~100B / 条目
  网格索引: ~50B / 条目
  总索引: ~15GB

QPS 放大:
  用户移动时自动刷新: 10% 用户打开 App 持续搜索
  每用户平均移动刷新: 10次/小时
  额外 QPS: 1000万 × 10 / 3600 ≈ 2.8万 QPS
  总峰值 QPS: 2.9万 + 2.8万 ≈ 6万 QPS
```

---

## API设计

### REST API

```
=== 搜索附近 POI ===
GET /api/v1/search/nearby
params:
  - lat: double        // 纬度
  - lng: double        // 经度
  - radius: int        // 搜索半径(米), 默认5000
  - category: string   // 分类过滤, 可选
  - keyword: string    // 关键词搜索, 可选
  - sort: string       // distance / rating / popularity
  - page: int          // 分页, 默认1
  - size: int          // 每页大小, 默认20, 最大50

Response:
{
  "total": 1234,
  "results": [
    {
      "poi_id": "poi_001",
      "name": "海底捞火锅(朝阳大悦城店)",
      "category": "餐厅/火锅",
      "address": "北京市朝阳区朝阳北路101号",
      "lat": 39.9242,
      "lng": 116.5118,
      "distance": 350,               // 距离(米)
      "rating": 4.5,
      "review_count": 2834,
      "avg_price": 150,
      "photos": ["https://cdn.xxx/p1.jpg"],
      "tags": ["火锅", "川菜", "聚会"]
    }
  ]
}

=== 关键词搜索 ===
GET /api/v1/search
params:
  - q: string          // 搜索关键词
  - lat: double        // 可选, 用于结果排序
  - lng: double
  - category: string
  - page: int
  - size: int

Response: 同上

=== 获取 POI 详情 ===
GET /api/v1/poi/{poi_id}

Response:
{
  "poi_id": "poi_001",
  "name": "海底捞火锅(朝阳大悦城店)",
  "category": "餐厅/火锅",
  "address": "...",
  "lat": 39.9242,
  "lng": 116.5118,
  "phone": "010-85551234",
  "hours": "10:00-22:00",
  "rating": 4.5,
  "review_count": 2834,
  "avg_price": 150,
  "photos": [...],
  "reviews": [...]   // 分页加载
}

=== POI CRUD (管理端) ===
POST /api/v1/admin/poi
PUT /api/v1/admin/poi/{poi_id}
DELETE /api/v1/admin/poi/{poi_id}

=== 自动补全 ===
GET /api/v1/search/suggest
params:
  - q: string          // 前缀
  - lat: double        // 可选, 就近优先
  - lng: double
```

---

## 数据模型

### POI 主表 (MySQL / PostgreSQL)

```sql
CREATE TABLE poi (
    poi_id         BIGINT PRIMARY KEY,
    name           VARCHAR(256) NOT NULL,
    category_id    INT NOT NULL,
    address        VARCHAR(512),
    lat            DOUBLE NOT NULL,
    lng            DOUBLE NOT NULL,
    phone          VARCHAR(32),
    hours          VARCHAR(128),
    rating         DECIMAL(3,2) DEFAULT 0,
    review_count   INT DEFAULT 0,
    avg_price      INT,
    status         TINYINT DEFAULT 1,  -- 1:正常 0:下线
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 空间索引
    SPATIAL INDEX idx_location (lat, lng),
    INDEX idx_category (category_id, status),
    INDEX idx_rating (rating),
    FULLTEXT INDEX idx_name (name)
) ENGINE=InnoDB;

CREATE TABLE category (
    category_id    INT PRIMARY KEY,
    name           VARCHAR(64) NOT NULL,
    parent_id      INT,
    icon_url       VARCHAR(256)
);

CREATE TABLE poi_tag (
    poi_id         BIGINT,
    tag            VARCHAR(64),
    PRIMARY KEY (poi_id, tag),
    INDEX idx_tag (tag)
);

-- 分表: 按 city_id 或 poi_id 哈希分16库
-- SHARDING KEY: poi_id % 16
```

### 空间索引数据结构

```
=== GeoHash ===

工作原理:
  1. 经纬度 -> 二分编码
  2. 经度/纬度交替合并
  3. 转换为 Base32 字符串

  纬度 39.92 -> 1011 1000 11...
  经度 116.51 -> 1101 0010 11...
  合并:         11100 11101 00100 01111...
  Base32:       WX4E...

GeoHash 精度:
+----------+--------------+------------------+
| 长度     | 精度(边界)    | 网格大小          |
+----------+--------------+------------------+
| 1        | ±2500km      | 5000km × 5000km  |
| 2        | ±630km       | 1250km × 625km   |
| 3        | ±78km        | 156km × 156km    |
| 4        | ±20km        | 39km × 19.5km    |
| 5        | ±2.4km       | 4.9km × 4.9km    |
| 6        | ±610m        | 1.2km × 609m     |
| 7        | ±76m         | 152m × 152m      |
| 8        | ±19m         | 38m × 19m        |
+----------+--------------+------------------+

搜索时:
  1. 计算用户位置的 GeoHash (如: wx4g0)
  2. 查询相同前缀的 POI
  3. 同时查询相邻8个网格的 POI (边界问题)
  4. 精确计算距离, 过滤超出 radius 的结果
```

### Redis Geo 索引

```
=== Redis GEO 数据结构 ===

Redis Geo 底层是 Sorted Set (ZSet):

# 添加 POI
GEOADD poi:all 116.5118 39.9242 "poi_001"
GEOADD poi:all 116.5120 39.9250 "poi_002"

# 实际上 Geo Set 存储为:
# ZSet member = poi_id, score = GeoHash 编码的数值

# 搜索附近 POI
GEORADIUS poi:all 116.51 39.92 5000 m
    WITHDIST      # 返回距离
    WITHCOORD     # 返回坐标
    WITHHASH      # 返回 GeoHash
    ASC|DESC      # 排序
    COUNT 20      # 限制数量

# 按成员位置搜索
GEORADIUSBYMEMBER poi:all poi_001 5000 m

# 获取两个 POI 的距离
GEODIST poi:all poi_001 poi_002 m

=== Geo Set 内部 ===
# 按城市分片存储
GEOADD poi:beijing 116.51 39.92 "poi_001"
GEOADD poi:shanghai 121.47 31.23 "poi_002"

# 按分类 + 城市分片
GEOADD poi:beijing:restaurant 116.51 39.92 "poi_001"
GEOADD poi:beijing:hotel 116.40 39.91 "poi_003"
```

### 全文搜索索引 (Elasticsearch)

```json
// ES Mapping
{
  "mappings": {
    "properties": {
      "poi_id": { "type": "long" },
      "name": {
        "type": "text",
        "analyzer": "ik_smart",           // 中文分词
        "fields": {
          "keyword": { "type": "keyword" },
          "pinyin": {
            "type": "text",
            "analyzer": "pinyin"           // 拼音搜索
          }
        }
      },
      "category": { "type": "keyword" },
      "address": { "type": "text", "analyzer": "ik_smart" },
      "location": { "type": "geo_point" },
      "rating": { "type": "float" },
      "tags": { "type": "keyword" },
      "status": { "type": "integer" }
    }
  }
}

// 搜索示例
GET /poi/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "火锅" } },
        { "term": { "category": "restaurant" } }
      ],
      "filter": {
        "geo_distance": {
          "distance": "5km",
          "location": { "lat": 39.92, "lon": 116.51 }
        }
      }
    }
  },
  "sort": [
    {
      "_geo_distance": {
        "location": { "lat": 39.92, "lon": 116.51 },
        "order": "asc",
        "unit": "m"
      }
    },
    { "rating": "desc" }
  ]
}
```

---

## 高层次架构

### 系统架构图

```
+----------------------------------------------------------------------+
|                              Load Balancer                            |
|                         (Nginx / HAProxy / Cloud LB)                  |
+--+------------+----------------+-----------------+------------------+
   |            |                |                 |
   v            v                v                 v
+--------+  +--------+    +----------+     +------------+
|Search  |  |Search  |    | Search   |     | Suggest    |
|API GW  |  |API GW  |    | Service  |     | Service    |
+---+----+  +---+----+    +----+------+     +-----+------+
    |           |              |                  |
    +------+----+--------------+-----+------------+
           |                         |
           v                         v
+--------------------+    +-----------------------+
|  Search Service    |    |  Suggestion Service   |
|  (核心搜索逻辑)     |    |  (Trie + 热词缓存)    |
+---------+----------+    +-----------+-----------+
          |                           |
          |         +-----------------+
          |         |
          v         v
+------------------------------------------+
|           数据访问层                       |
|  +----------+ +----------+ +-----------+ |
|  | Redis    | | ES       | | MySQL     | |
|  | Cluster  | | Cluster  | | Shards    | |
|  +----------+ +----------+ +-----------+ |
+------------------------------------------+
          |              |              |
          v              v              v
+----------------+ +-----------+ +--------------+
|  Redis Geo     | | ES Index  | | MySQL        |
|  (空间索引)     | | (全文搜索) | | (主数据存储)  |
+----------------+ +-----------+ +--------------+

+------------------------------------------+
|        数据同步 & 更新管道                   |
|                                          |
|  MySQL Binlog -> Canal -> MQ ->          |
|  -> ES Indexer -> Redis Updater          |
+------------------------------------------+
```

### 搜索流程图

```
用户搜索 "附近的火锅店" (lat=39.92, lng=116.51, radius=5000m)
    |
    v
+------------------+
| API Gateway      |
| (鉴权+限流)      |
+--------+---------+
         |
         v
+------------------+
| Search Service   |
+--------+---------+
         |
         | 1. 获取用户 GeoHash
         |    geoHash = encode(lat, lng, 6)
         |    // "wx4g0c"
         |
         | 2. 计算目标网格及其周围8个网格
         |    neighbors = ["wx4g0c", "wx4g0b", "wx4g1b",
         |                  "wx4g0f", ...]   // 9个网格
         |
         +-----------+
         |           |
         v           v
+------------+ +----------+
| Redis Geo  | | ES Query |
| (快速筛选)  | | (全文搜索)|
+-----+------+ +-----+----+
      |               |
      | 3. GEORADIUS  | 4. geo_distance query
      |   筛选候选POI  |    + keyword match
      v               v
+-----------------------------+
| 合并 & 去重 & 精确距离排序   |
+--------------+--------------+
               |
               v
+-----------------------------+
| 补充详情:                    |
| POI名称/图片/评分/标签       |
| (从Redis缓存或MySQL获取)     |
+--------------+--------------+
               |
               v
+-----------------------------+
| 返回结果 (分页, Top 20)      |
+-----------------------------+
```

### 数据流 - POI更新

```
商家修改信息 (名称/位置/营业时间)
    |
    v
+----------------+
| MySQL          |
| UPDATE poi     |
| SET ...        |
+-------+--------+
        |
        v
+----------------+      +-----------+
| Canal/Binlog   | -->  | Kafka/RMQ |
| 监听变化        |      | (消息队列) |
+----------------+      +-----+-----+
                               |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
+----------------+   +---------------+    +--------------+
| ES Indexer     |   | Redis Updater |    | Cache        |
|                |   |               |    | Invalidation |
| 更新全文索引    |   | 更新Geo索引    |    | 删除旧缓存    |
+----------------+   +---------------+    +--------------+
```

---

## 核心深入

### 1. 空间索引算法对比

```
+---------------+----------------+----------------+----------------+----------------+
| 方案          | 查询复杂度      | 空间复杂度      | 精确度          | 适用场景        |
+---------------+----------------+----------------+----------------+----------------+
| 全表扫描       | O(N)           | O(1)           | 精确            | 数据量极小      |
| GeoHash       | O(logN)        | O(N)           | 近似(需后处理)   | 通用,最常用     |
| QuadTree      | O(logN)        | O(N)           | 精确            | 不均匀分布      |
| R-Tree        | O(logN)        | O(N)           | 精确            | 数据库内建      |
| S2 (Google)   | O(logN)        | O(N)           | 精确            | 球面几何,大规模 |
| H3 (Uber)     | O(logN)        | O(N)           | 精确            | 六边形网格      |
| KD-Tree       | O(logN) (平均) | O(N)           | 精确            | 静态数据,维数低 |
+---------------+----------------+----------------+----------------+----------------+

=== GeoHash 详解 ===

编码算法:
// 输入: lat, lng, precision
// 输出: GeoHash string

function encode(lat, lng, precision):
    latRange = [-90, 90]
    lngRange = [-180, 180]
    isEven = true
    geohash = 0
    bitCount = 0
    result = ""

    while len(result) < precision:
        if isEven:
            mid = (lngRange[0] + lngRange[1]) / 2
            if lng >= mid:
                geohash = (geohash << 1) | 1
                lngRange[0] = mid
            else:
                geohash = (geohash << 1) | 0
                lngRange[1] = mid
        else:
            mid = (latRange[0] + latRange[1]) / 2
            if lat >= mid:
                geohash = (geohash << 1) | 1
                latRange[0] = mid
            else:
                geohash = (geohash << 1) | 0
                latRange[1] = mid

        isEven = !isEven
        bitCount++

        if bitCount == 5:
            result += BASE32[geohash]
            geohash = 0
            bitCount = 0

    return result

=== GeoHash 的边界问题 ===

问题: 两个很近的点可能在 GeoHash 前缀不同
例如:
  A点: (39.999, 116.001) -> GeoHash = "wx4g1"
  B点: (40.001, 116.002) -> GeoHash = "wx4g4"
  (仅隔200m但前缀完全不同)

解决: 查询时同时查询当前格子和周围8个邻居格子

function getNeighbors(geohash):
    directions = ["n", "s", "e", "w", "ne", "nw", "se", "sw"]
    neighbors = []
    for dir in directions:
        neighbors.append(adjacent(geohash, dir))
    return [geohash] + neighbors

=== S2 / H3 为什么更好？ ===

GeoHash 问题:
  - 矩形网格, 边缘距离误差大
  - 不同纬度网格大小不一致
  - 长距离搜索效率低

Google S2:
  - 球面几何, 使用希尔伯特曲线填充
  - 任意位置的网格大小均匀
  - 覆盖查询更精确 (Cells Union)
  - 支持多级精度

Uber H3:
  - 六边形网格
  - 邻居数量固定 (6个)
  - 无边界问题 (所有邻居大小相同)
  - 适合热力图/可视化
```

### 2. 多层搜索架构

```
=== 搜索漏斗 ===

Layer 1: 布隆过滤器 (快速排除)
  - 判断 PoI 是否可能存在
  - 不存在 -> 直接返回空
  - 减少对 Redis 和 ES 的无效查询

Layer 2: Redis Geo (快速筛选)
  - GEORADIUS 获取候选 POI ID 列表
  - 按距离排序
  - 返回 TopK (如 K=200)
  - O(logN + M), M=候选数
  - 延迟: 1-5ms

Layer 3: Elasticsearch (全文匹配+精确过滤)
  - 对 Layer 2 的候选 ID 做 keyword match
  - 或直接 ES geo_distance + fulltext query
  - 延迟: 10-50ms (如果候选集小)

Layer 4: 详情补全
  - 从 Redis 缓存获取 POI 名称/图片/评分
  - 缓存未命中则查 MySQL
  - 延迟: 1-5ms (Redis) / 10-30ms (MySQL)

优先级: Layer1 > Layer2 > Layer3 > Layer4
如果 Layer2 已满足条件, 跳过 Layer3
```

### 3. 全局分片 vs 城市分片

```
=== 方案A: 全局统一分片 ===
Key = CRC32(poi_id) % shard_count
Redis: GEOADD poi:shard_0 ... poi:shard_1 ...
查询: 需要从所有分片取数据再合并排序
优点: 负载均衡, 数据均匀
缺点: 搜索需要广播到所有分片, 网络开销大

=== 方案B: 按城市分片 (推荐) ===
Key = city_id
Redis: GEOADD poi:beijing ... poi:shanghai ...
ES: 按城市分索引
查询: 先定位城市, 只在目标城市搜索

城市定位:
  1. 用户 GPS 经纬度 -> 逆地理编码 -> city_id
  2. 用户手动选择城市
  3. 缓存用户上次所选城市

优点:
  - 搜索范围小, 速度快
  - 索引小, 内存少
  - 各城市独立, 故障隔离

缺点:
  - 跨城市/城市边界搜索需额外处理
  - 城市 POI 量不均匀 (北京 vs 拉萨)

=== 方案C: 分层分片 (QuadTree分区) ===
Level 0: 全局 (热度数据: Top1000商家)
Level 1: 省级 -> 在省级Redis分片搜索
Level 2: 市级 -> 在市级Redis分片搜索

查询策略:
  if (radius <= 5km): Level 2 (精确)
  if (radius <= 50km): Level 1 + Level 2
  else: Level 0 + Level 1 + Level 2 (范围太大)
```

### 4. 距离计算

```
=== Haversine 公式 (球面距离) ===

function haversine(lat1, lng1, lat2, lng2):
    R = 6371000  // 地球半径(米)

    dLat = rad(lat2 - lat1)
    dLng = rad(lng2 - lng1)

    a = sin(dLat/2)^2 + cos(rad(lat1)) * cos(rad(lat2)) * sin(dLng/2)^2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

=== 距离计算优化 ===

1. 矩形快速过滤 (Bounding Box):
   先过滤出候选矩形内的 POI, 减少精确计算次数

   deltaLat = radius / 111320  // 1度纬度 ≈ 111.32km
   deltaLng = radius / (111320 * cos(lat))

   minLat = lat - deltaLat
   maxLat = lat + deltaLat
   minLng = lng - deltaLng
   maxLng = lng + deltaLng

   candidates = POI WHERE lat BETWEEN minLat AND maxLat
                      AND lng BETWEEN minLng AND maxLng

2. 平面近似 (短距离 < 10km):
   x = (lng2 - lng1) * cos((lat1 + lat2) / 2) * 111320
   y = (lat2 - lat1) * 111320
   distance = sqrt(x^2 + y^2)
   误差 < 0.1% (10km内)

3. 提前终止 (Early Termination):
   搜索时按距离排序, 超过 pageSize 个结果后
   只继续搜索距离 < 第N个结果距离的 POI
```

### 5. 热度与个性化排序

```
=== 排序算法 ===

function score(poi, userLat, userLng):
    distance = haversine(userLat, userLng, poi.lat, poi.lng)
    distanceScore = 1 / (1 + distance / 500)  // 越近越高

    ratingScore = poi.rating / 5.0            // 0-1
    popularityScore = log(1 + poi.review_count) / log(1 + maxReviews)
    freshnessScore = decay(poi.updatedAt)      // 时间衰减

    // 个性化 (协同过滤)
    userPrefScore = collaborativeFilter(user, poi)

    // 加权求和
    finalScore = w1 * distanceScore +
                 w2 * ratingScore +
                 w3 * popularityScore +
                 w4 * freshnessScore +
                 w5 * userPrefScore

    return finalScore

=== 热度加权优化 ===

// 热门 POI 单独缓存 + 优先返回
// Redis Sorted Set: 按城市 + 分类
ZADD hot:beijing:restaurant <score> <poi_id>

// score 综合: 点击率 * 距离衰减 + 评分 + 新鲜度
// 搜索时: 
// 1. ZREVRANGE hot:beijing:restaurant 0 100 获取热门候选
// 2. 再从 Geo 索引补充距离近的候选
// 3. 合并排序返回
```

### 6. 动态位置与实时更新

```
=== 用户移动场景 ===

App端轮询 or WebSocket:
  每移动200m / 每5s -> 触发搜索更新

服务端优化:
  // 连续搜索, 使用上一次结果缓存
  // 只更新距离字段, 不重新排序完整列表

  function incrementalUpdate(prevResults, newLat, newLng):
      for poi in prevResults:
          poi.distance = haversine(newLat, newLng, poi.lat, poi.lng)

      // 重新按距离排序
      sort(prevResults, by: distance)

      // 如果用户移动很大(>1km), 重新搜索
      if movedDistance > 1000:
          return fullSearch(newLat, newLng, radius)

      return prevResults

=== 预加载 (Pre-fetch) ===
  用户在 A 位置时, 提前异步加载周边网格的 POI
  用户移动进入新网格时可以立即展示
```

---

## 扩展性与高可用

### 1. 多级缓存策略

```
+------------------------------------------+
|            Client Side Cache              |
| (LocalStorage / local DB, TTL=5min)       |
+--------------------+----------------------+
                     |
+--------------------v----------------------+
|           CDN Cache (图片/静态数据)        |
+--------------------+----------------------+
                     |
+--------------------v----------------------+
|         API Gateway Cache                  |
| (热点搜索词 & 结果缓存, TTL=1-5min)        |
+--------------------+----------------------+
                     |
+--------------------v----------------------+
|         Redis Cluster Cache                |
| (POI详情 / Geo索引 / 热门搜索缓存)         |
+--------------------+----------------------+
                     |
+--------------------v----------------------+
|              MySQL Shards                  |
+--------------------------------------------+
```

### 2. 数据同步

```
=== MySQL -> ES -> Redis 同步链路 ===

+----------+     +--------+     +--------+     +----------+
| MySQL    | --> | Canal  | --> | Kafka  | --> | Consumer |
| (Binlog) |     | (增量)  |     | (MQ)   |     | Group    |
+----------+     +--------+     +--------+     +-----+----+
                                                     |
                                     +---------------+---------------+
                                     |                               |
                                     v                               v
                              +-----------+                   +----------+
                              | ES Index  |                   | Redis    |
                              | Updater   |                   | Updater  |
                              +-----------+                   +----------+

ES 更新策略:
  - 近实时 (Near Real-Time): refresh_interval=1s
  - 使用 Bulk API 批量更新
  - 更新失败 -> 写入死信队列 -> 人工处理

Redis 更新策略:
  - geo: 更新 Geo 索引 (GEOADD/GEODEL)
  - poi: 更新详情缓存 (HSET poi:{id} ...)
  - hot: 异步更新热度排行榜

=== 全量重建流程 ===
1. 从 MySQL 离线导出全量数据 -> Hive/Spark
2. 数据清洗/标准化
3. 生成 ES 索引文件
4. 生成 Redis RDB 快照
5. 切换索引 / 在线加载 (蓝绿部署)
```

### 3. 热点商户处理

```
=== 问题 ===
  网红店/大型商场 QPS 可能比普通店高 100-1000 倍

=== 解决方案 ===

1. 热点 POI 独立缓存:
   // 热点商家单独一个 Redis Key
   GET poi:detail:{hot_poi_id}
   TTL更短, 更频繁刷新

2. 本地缓存 (Caffeine/Guava Cache):
   // 在搜索服务本地内存中缓存 Top10000 热点商家
   LoadingCache<Long, PoiDetail> hotPoiCache = Caffeine.newBuilder()
       .maximumSize(10000)
       .expireAfterWrite(60, TimeUnit.SECONDS)
       .build(id -> loadFromRedis(id));

3. 热点预计算:
   // 定时任务计算热门搜索(搜索次数/点击率)
   // 预加载搜索结果到 Redis
   // "火锅 北京朝阳" -> [poi_001, poi_002, ...]

4. 限流 + 降级:
   // 单个商家 QPS 超限 -> 返回静态缓存数据
   // 实时详情(如排队人数)降级到非实时
```

### 4. 数据倾斜与故障处理

```
=== 数据倾斜 ===
问题: 北京上海 POI 数量是三四线城市的 100 倍
解决:
  1. 按实际数据量动态分配 Redis 内存
  2. 超大城市二次拆分:
     北京 -> 海淀/朝阳/西城... 独立 Redis 分片
  3. 小城市合并分片:
     多个小城市共用一个 Redis 实例

=== 故障场景 ===

Redis Geo 不可用:
  -> ES geo_distance query 降级搜索
  -> MySQL SPATIAL 查询兜底

ES 不可用:
  -> Redis Geo 纯地理位置搜索
  -> 全文搜索降级为 MySQL LIKE 查询 (限流)
  -> 不支持关键词搜索, 只做附近分类搜索

MySQL 不可用:
  -> Redis 缓存兜底 (缓存更长时间)
  -> 只读模式, 不更新数据

=== 异地多活 ===
+---------------------+        +---------------------+
|   Region A (北京)    |        |   Region B (上海)    |
| +-----------------+ |        | +-----------------+ |
| | 华北数据         | |  <==>  | | 华东数据         | |
| +-----------------+ |  同步   | +-----------------+ |
|                     |        |                     |
| 就近访问: 华北用户   |        | 就近访问: 华东用户   |
+---------------------+        +---------------------+

GSLB (全局负载均衡) 按用户 IP 地理位置路由
```

### 5. 监控指标

```
业务指标:
  - 搜索 QPS (按城市/分类)
  - 搜索 P99 延迟 / 平均延迟
  - 搜索空结果比例 (可能需要放宽条件)
  - POI 点击率 CTR
  - 热门搜索词 Top100
  - 缓存命中率 (CDN / Redis / 本地)

系统指标:
  - Redis Geo keys 数量 / 内存使用
  - ES 索引大小 / 查询延迟 / 索引速率
  - MySQL 连接数 / 慢查询
  - 数据同步延迟 (Binlog -> ES/Redis)
  - MQ 消费 Lag

告警规则:
  - 搜索 P99 > 500ms
  - 搜索空结果比例 > 30% (可能索引问题)
  - Redis 内存使用 > 80%
  - ES 集群健康红色
  - 数据同步延迟 > 5min
  - 热点商户 QPS > 单节点阈值
```

---

## 总结

设计附近/邻近服务需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **空间索引** | GeoHash (矩形网格) vs S2 (球面) vs H3 (六边形) — GeoHash最简单通用 |
| **搜索分层** | 城市分片(热数据隔离) -> Bloom Filter(快速排除) -> Redis Geo(快速筛选) -> ES(全文匹配) |
| **距离计算** | Bounding Box快速过滤 + Haversine精确计算 + 平面近似短距离优化 |
| **排序** | 距离 + 评分 + 热度 + 个性化 — 加权综合排序 |
| **缓存** | 本地Caffeine + Redis Cluster + CDN — 多级缓存 |
| **数据同步** | Binlog -> Canal -> MQ -> 多消费者 — 近实时同步 |
| **热点** | 独立缓存 + 预计算 + 限流降级 — 防止热点击穿 |

关键面试问答：
1. **附近搜索怎么实现？** — GeoHash 编码 -> 查询9宫格 -> Redis GEORADIUS -> 精确距离计算和排序
2. **GeoHash 边界问题怎么解决？** — 同时查询周围8个邻居格子；或使用 S2/H3 等更优空间索引
3. **大量POI怎么分片？** — 首选按城市分片，城市分级(超大城市二次拆分，小城市合并)，使搜索范围最小化
4. **如何提高搜索精度和召回率？** — 多级检索(Geo粗筛 + ES细排) + 模糊匹配 + 同义词 + 纠错
5. **移动端体验怎么优化？** — 预加载 + 增量更新距离 + 本地缓存 + 坐标预处理(去噪/纠偏)
6. **为什么不直接用MySQL SPATIAL INDEX？** — 数据量过大(亿级)时MySQL性能下降，Redis Geo内存搜索更快，ES提供更丰富的全文搜索
