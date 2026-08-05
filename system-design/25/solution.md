# 设计地图服务 (Design Google Maps)

## 题目

设计一个大规模地图服务系统，支持地理位置搜索、路径规划、实时交通、地图瓦片渲染等功能。

## 需求澄清

### 功能性需求

1. **地图展示**: 按瓦片(Tile)方式展示地图，支持缩放(zoom level 0-21)
2. **地点搜索**: 支持关键词搜索POI(Point of Interest)，支持模糊匹配和自动补全
3. **路径规划**: 点对点路线规划、多途经点优化
4. **实时交通**: 展示实时路况，用颜色标记拥堵程度(绿/黄/红)
5. **两点间距离和ETA计算**: 估算到达时间
6. **地理编码**: 地址 ↔ 经纬度互转 (Geocoding / Reverse Geocoding)
7. **附近搜索**: 查找当前位置附近的POI

### 非功能性需求

- **低延迟**: 地图瓦片 < 50ms, 搜索 < 200ms, 路径规划 < 1s
- **高可用**: 99.99%
- **高并发**: 支持百万级QPS(全球用户)
- **准确性**: 路径规划结果正确，ETA误差 < 5%
- **数据新鲜度**: 实时交通 < 1分钟, POI更新 < 24小时

### 容量估算

```
假设:
- DAU: 5亿
- 人均请求: 50次/天
- 高峰期QPS: 5亿 × 50 / 86400 × 5(高峰系数) ≈ 144万 QPS

按请求类型拆分:
- 地图瓦片: 80% → ~115万 QPS (缓存命中率 >95%)
- 搜索/自动补全: 10% → ~14万 QPS
- 路径规划: 5% → ~7.2万 QPS
- 地理编码: 3% → ~4.3万 QPS
- 实时交通: 2% → ~2.9万 QPS

存储估算:
- 地图瓦片:
  - Zoom 0-14: 全世界预渲染 ≈ 50 TB
  - Zoom 15-21: 热门地区渲染 ≈ 200 TB
  - 总计 ≈ 250 TB

- 道路网络图:
  - 全球道路: 约2亿条路段(segment)
  - 路段元数据: 2亿 × 500 bytes ≈ 100 GB
  - 路段连接关系: 2亿 × 2 × 8 bytes ≈ 3.2 GB
  - 路况数据(traffic tiles): 1 TB/day × 30天 ≈ 30 TB

- POI数据:
  - 全球POI: 5亿个
  - 元数据: 5亿 × 2KB ≈ 1 TB
  - 搜索索引: ~500 GB
```

## API设计

```protobuf
// ============ 地图瓦片 API ============
// GET /tiles/{z}/{x}/{y}.png
// 或向量瓦片格式: GET /tiles/{z}/{x}/{y}.pbf (Protocol Buffers Binary Format)

// ============ 地点搜索 API ============
// GET /api/v1/places/search?query=coffee&location=37.7749,-122.4194&radius=5000&limit=20
// GET /api/v1/places/autocomplete?input=stan&location=37.7,-122.4

message PlaceSearchRequest {
  string query = 1;                     // 搜索关键词
  LatLng location = 2;                  // 搜索中心点
  int32 radius = 3;                     // 搜索半径(meters)
  string type = 4;                      // "restaurant", "gas_station", "hospital"
  int32 limit = 5 [default = 20];
  string language = 6;
  string region = 7;                    // "us", "cn"
}

message LatLng {
  double latitude = 1;
  double longitude = 2;
}

message PlaceSearchResponse {
  repeated Place results = 1;
  int32 total_count = 2;
  string next_page_token = 3;
}

message Place {
  string place_id = 1;
  string name = 2;
  string formatted_address = 3;
  LatLng location = 4;
  repeated string types = 5;            // ["restaurant", "cafe", "food"]
  double rating = 6;
  int32 reviews_count = 7;
  string phone_number = 8;
  string website = 9;
  OpeningHours opening_hours = 10;
  repeated Photo photos = 11;
}

message OpeningHours {
  bool open_now = 1;
  repeated string periods = 2;          // ["Mon: 09:00-18:00", ...]
}

// ============ 路径规划 API ============
// POST /api/v1/directions
message DirectionsRequest {
  LatLng origin = 1;
  LatLng destination = 2;
  repeated LatLng waypoints = 3;        // 途经点 (最多25个)
  TravelMode mode = 4;                  // DRIVING, WALKING, BICYCLING, TRANSIT
  TrafficModel traffic_model = 5;       // BEST_GUESS, OPTIMISTIC, PESSIMISTIC
  int64 departure_time_ms = 6;          // 出发时间 (用于历史路况预测)
  repeated string avoid = 7;            // "tolls", "highways", "ferries"
  string language = 8;
  bool alternatives = 9;                // 是否返回备选路线
}

enum TravelMode {
  DRIVING = 0;
  WALKING = 1;
  BICYCLING = 2;
  TRANSIT = 3;
}

enum TrafficModel {
  BEST_GUESS = 0;
  OPTIMISTIC = 1;
  PESSIMISTIC = 2;
}

message DirectionsResponse {
  repeated Route routes = 1;
  string geocoded_waypoints = 2;        // 途经点地理编码结果
}

message Route {
  string summary = 1;                   // "US-101 N"
  repeated Leg legs = 2;                // 分段(途经点之间)
  Polyline overview_polyline = 3;       // 路线折线(编码格式)
  string copyrights = 4;
  repeated Warning warnings = 5;
  Fare fare = 6;                        // 过路费
}

message Leg {
  Distance distance = 1;                // {"value": 54000, "text": "54.0 km"}
  Duration duration = 2;                // {"value": 2400, "text": "40 mins"}
  Duration duration_in_traffic = 3;     // 考虑路况
  string start_address = 4;
  string end_address = 5;
  repeated Step steps = 6;              // 导航步骤
}

message Step {
  string html_instructions = 1;         // "Turn <b>left</b> onto El Camino Real"
  Distance distance = 2;
  Duration duration = 3;
  LatLng start_location = 4;
  LatLng end_location = 5;
  Polyline polyline = 6;
  string travel_mode = 7;
  string maneuver = 8;                  // "turn-left", "turn-right", "straight"
}

message Polyline {
  string encoded_points = 1;            // 编码的折线字符串
  // Google Encoding: 
  //  将经纬度序列编码为ASCII字符串, 压缩比约10:1
  //  Example: "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
}

// ============ 地理编码 API ============
// GET /api/v1/geocode?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA
// GET /api/v1/reverse-geocode?latlng=37.422,-122.084

message GeocodeResponse {
  repeated GeocodeResult results = 1;
}

message GeocodeResult {
  string formatted_address = 1;
  LatLng location = 2;
  string place_id = 3;
  repeated string types = 4;
  repeated AddressComponent address_components = 5;
  LatLng viewport = 6;                 // 推荐视口
}

// ============ 实时交通 API ============
// GET /api/v1/traffic?bounds=37.7,-122.5|37.8,-122.4

message TrafficResponse {
  repeated TrafficSegment segments = 1;
}

message TrafficSegment {
  Polyline geometry = 1;
  TrafficCondition condition = 2;       // FREE_FLOW, MODERATE, CONGESTED, HEAVY
  int32 speed_kmh = 3;                  // 当前平均车速
  int32 free_flow_speed_kmh = 4;        // 自由流速度
}
```

## 数据模型

### 道路网络图

```
┌────────────────────────────────────────────────────────────┐
│                  道路网络图数据模型                           │
│                                                            │
│  节点 (Node): 道路交叉点/端点                                │
│  ┌──────────────────────────────────────┐                  │
│  │ node_id: int64                       │                  │
│  │ latitude, longitude: double          │                  │
│  │ node_type: intersection/endpoint     │                  │
│  │ elevation: float (可选)              │                  │
│  └──────────────────────────────────────┘                  │
│                                                            │
│  边/路段 (Edge / Segment): 两个节点间的道路段               │
│  ┌──────────────────────────────────────┐                  │
│  │ segment_id: int64                    │                  │
│  │ from_node_id, to_node_id: int64      │                  │
│  │ length_meters: float                 │                  │
│  │ speed_limit_kmh: int                 │                  │
│  │ road_class: motorway/primary/residential│              │
│  │ direction: forward/backward/both      │                  │
│  │ lanes: int                           │                  │
│  │ geometry: list<latlng> (折线点序列)   │                  │
│  │ toll: bool                           │                  │
│  │ turn_restrictions: list<restriction>  │                  │
│  └──────────────────────────────────────┘                  │
│                                                            │
│  路况 (Traffic): 每条路段的实时速度                          │
│  ┌──────────────────────────────────────┐                  │
│  │ segment_id: int64                    │                  │
│  │ timestamp_ms: int64                  │                  │
│  │ current_speed_kmh: int               │                  │
│  │ free_flow_speed_kmh: int             │                  │
│  │ congestion_level: enum (0-3)         │                  │
│  └──────────────────────────────────────┘                  │
│                                                            │
│  历史路况 (用于ETA预测):                                     │
│  ┌──────────────────────────────────────┐                  │
│  │ segment_id: int64                    │                  │
│  │ day_of_week: int (0-6)               │                  │
│  │ hour_of_day: int (0-23)              │                  │
│  │ avg_speed_kmh: float                 │                  │
│  │ stddev_speed_kmh: float              │                  │
│  └──────────────────────────────────────┘                  │
└────────────────────────────────────────────────────────────┘

图构建示例:
┌──────────────────────────────────────────────┐
│                                              │
│  Node A ───── Segment 1 ───── Node B        │
│  (lat,lng)  (length, speed)    (lat,lng)    │
│    │                                          │
│    │ Segment 2                                │
│    │                                          │
│  Node C                                    │
│  (lat,lng)                                   │
│                                              │
│  有向图: 考虑单行道和转弯限制                  │
│  权重: travel_time = length / current_speed   │
│  动态权重: 实时路况和预测路况                   │
└──────────────────────────────────────────────┘
```

### 地图瓦片存储 (Tile Storage)

```
地图瓦片采用 Mercator 投影, 分层组织:

Zoom Level → Tile Count (2^z × 2^z):
Z0:  1 tile   (全世界)     每个 tile: 256×256 pixels
Z1:  4 tiles  (2×2 grid)
Z2:  16 tiles (4×4 grid)
...
Z10: 1,048,576 tiles
Z14: 268,435,456 tiles
Z18: 68,719,476,736 tiles  ← 只有热门区域渲染

瓦片存储格式:
┌───────────────┬──────────────┬────────────────┐
│  Raster Tile  │  Vector Tile  │  Hybrid         │
│  (PNG/JPEG)   │  (.pbf)       │                 │
├───────────────┼──────────────┼────────────────┤
│  预渲染图片    │  矢量数据 +    │  低zoom用raster  │
│  存储大        │  客户端渲染    │  高zoom用vector  │
│  更新需重渲染  │  存储小        │                 │
│  兼容性好      │  灵活,可换样式 │                 │
└───────────────┴──────────────┴────────────────┘

存储层级:
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  CDN Edge (最热瓦片)                                      │
│    ↓ cache miss                                          │
│  Regional Cache (Redis/RAM)                               │
│    ↓ cache miss                                          │
│  Object Storage (S3/GCS, 所有Z0-Z14 tiles)                │
│    ↓ cache miss (Z15+)                                   │
│  Tile Server (动态渲染高zoom瓦片)                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### POI数据模型

```sql
CREATE TABLE poi (
    poi_id BIGINT PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    name_aliases VARCHAR(500),           -- 别名, 逗号分隔
    category_id INT NOT NULL,            -- 类目ID
    category_name VARCHAR(200),
    sub_categories JSON,                 -- ["cafe", "breakfast"]
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    geohash VARCHAR(12),                 -- 用于空间索引
    address VARCHAR(500),
    city VARCHAR(200),
    state VARCHAR(200),
    country VARCHAR(200),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    website VARCHAR(500),
    rating DOUBLE DEFAULT 0,
    reviews_count INT DEFAULT 0,
    popularity_score DOUBLE DEFAULT 0,
    opening_hours JSON,
    attributes JSON,                     -- {"wifi":true, "outdoor_seating":true}
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    INDEX idx_geohash (geohash),
    INDEX idx_category (category_id),
    SPATIAL INDEX idx_location (POINT(latitude, longitude))
);
```

## 高层次架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        地图服务系统架构                                   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                          客户端 (Client)                          │  │
│  │  Map SDK (iOS/Android/Web)  → 瓦片请求/搜索/路径规划/交通          │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                       │
│                                ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        API Gateway                                 │  │
│  │  (认证/限流/GEO路由 → 就近服务)                                    │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                       │
│         ┌──────────────────────┼──────────────────────┐                │
│         │                      │                      │                │
│         ▼                      ▼                      ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐        │
│  │ 地图瓦片服务   │    │ 搜索服务      │    │ 路径规划服务      │        │
│  │ (Tile Server) │    │ (Search)      │    │ (Directions)      │        │
│  │               │    │               │    │                   │        │
│  │ ┌───────────┐ │    │ ┌───────────┐ │    │ ┌───────────────┐ │        │
│  │ │ CDN Cache │ │    │ │ ES集群     │ │    │ │ 图路由引擎    │ │        │
│  │ │ (Varnish) │ │    │ │ 全文搜索   │ │    │ │ (Dijkstra/   │ │        │
│  │ └───────────┘ │    │ │ 地理搜索   │ │    │ │  A*/CH/HSN)  │ │        │
│  │               │    │ └───────────┘ │    │ └───────────────┘ │        │
│  │ ┌───────────┐ │    │               │    │                   │        │
│  │ │ S3/GCS    │ │    │ ┌───────────┐ │    │ ┌───────────────┐ │        │
│  │ │ 瓦片存储   │ │    │ │ 自动补全   │ │    │ │ 路况服务      │ │        │
│  │ └───────────┘ │    │ │ (Trie树)   │ │    │ │ (实时+预测)   │ │        │
│  │               │    │ └───────────┘ │    │ └───────────────┘ │        │
│  └──────────────┘    └──────────────┘    └──────────────────┘        │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     数据处理管道 (Data Pipeline)                   │  │
│  │                                                                   │  │
│  │  ┌───────────┐  ┌────────────┐  ┌─────────────┐  ┌───────────┐  │  │
│  │  │ OSM/地图  │  │ 路况数据    │  │ 用户GPS轨迹  │  │ POI源     │  │  │
│  │  │ 提供商数据 │  │ (传感器/   │  │ (Anonymous) │  │ (商家/    │  │  │
│  │  │           │  │  手机GPS)  │  │             │  │  用户贡献)│  │  │
│  │  └─────┬─────┘  └─────┬──────┘  └──────┬──────┘  └─────┬─────┘  │  │
│  │        │              │                │                │        │  │
│  │        └──────────────┼────────────────┼────────────────┘        │  │
│  │                       │                │                          │  │
│  │                       ▼                ▼                          │  │
│  │              ┌─────────────────────────────┐                     │  │
│  │              │ 数据ETL (Spark/Flink)        │                     │  │
│  │              │ - 地图渲染 (Tile Generation)│                     │  │
│  │              │ - 道路图构建 (Graph Build)  │                     │  │
│  │              │ - 路况推算 (Speed Estimation)│                    │  │
│  │              │ - POI清洗/去重/合并         │                     │  │
│  │              └─────────────────────────────┘                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心深入

### 1. 地图瓦片系统 (Tile System)

```
┌────────────────────────────────────────────────────────────────┐
│                    Web Mercator 投影与瓦片                      │
│                                                                │
│  瓦片坐标系统:                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Tile (z, x, y):                                         │  │
│  │    z = zoom level (0-21)                                 │  │
│  │    x = column (0 to 2^z - 1)                             │  │
│  │    y = row (0 to 2^z - 1)                                │  │
│  │                                                          │  │
│  │  经纬度 → 瓦片坐标:                                        │  │
│  │  n = 2^z                                                  │  │
│  │  x = floor((lon + 180) / 360 * n)                        │  │
│  │  y = floor((1 - ln(tan(lat_rad) + 1/cos(lat_rad)) / π)  │  │
│  │        * n / 2)                                          │  │
│  │                                                          │  │
│  │  缩放比例:                                                 │  │
│  │  Zoom 0:  世界地图 (1 tile)                               │  │
│  │  Zoom 4:  大陆级别 (16×16 tiles)                         │  │
│  │  Zoom 10: 城市级别 (~1000×1000 tiles)                    │  │
│  │  Zoom 14: 街区级别                                        │  │
│  │  Zoom 18: 建筑级别                                        │  │
│  │  Zoom 21: 最高精度 (4.75m/pixel)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  瓦片存储与分发:                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │                    ┌──────────────┐                       │  │
│  │      Client        │ CDN Edge      │  (热门瓦片缓存)     │  │
│  │   请求tile/z/x/y   │ (CloudFront/  │                      │  │
│  │   ──────────────►  │  CloudFlare)  │                      │  │
│  │                    └──────┬───────┘                       │  │
│  │                           │ cache miss                    │  │
│  │                           ▼                               │  │
│  │                    ┌──────────────┐                       │  │
│  │                    │ Origin Server │                      │  │
│  │                    │ (S3/GCS)     │  (Z0-Z14预渲染瓦片)   │  │
│  │                    └──────┬───────┘                       │  │
│  │                           │ Z15+ cache miss               │  │
│  │                           ▼                               │  │
│  │                    ┌──────────────┐                       │  │
│  │                    │ Tile Server   │  (动态渲染)           │  │
│  │                    │ Mapnik/Mapbox │                       │  │
│  │                    │ PostgreSQL +  │                       │  │
│  │                    │ PostGIS       │                       │  │
│  │                    └──────────────┘                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  CDN缓存策略:                                                   │
│  - 热门城市瓦片: Cache-Control: max-age=86400                  │
│  - 一般瓦片: Cache-Control: max-age=604800 (7天)               │
│  - Purge机制: 地图更新后CDN主动失效对应区域瓦片                   │
└────────────────────────────────────────────────────────────────┘
```

### 2. 路径规划算法深度对比

```
┌────────────────────────────────────────────────────────────────┐
│                  路径规划算法对比与选型                          │
│                                                                │
│  全球道路网络图: 约2亿节点, 数亿边                              │
│  核心挑战: 在超大规模图上做毫秒级最短路径查询                    │
│                                                                │
│  算法1: Dijkstra 算法                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  时间复杂度: O((V+E)logV)                                       │
│  特点: 单向搜索，会探索半径内所有节点                             │
│  问题: 对于全球图不可行 (会探索太多节点)                         │
│  适用: 小范围 (市内, <1000节点)                                 │
│                                                                │
│  算法2: A* (A-Star) 算法                                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  时间复杂度: p < O((V+E)logV), 取决于启发式函数                  │
│  启发式: h(n) = 欧几里得距离(n, dest) / max_speed              │
│                                                          │
│  A* 优于Dijkstra的原因: 优先探索估计距离目标更近的节点            │
│  但仍不适合百万节点级别                                           │
│                                                                │
│  算法3: 分层技术 (Multi-level Techniques) - 核心!               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│                                                                │
│  3a. Contraction Hierarchies (CH) - 收缩层次                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  预处理阶段:                                              │  │
│  │  遍历所有节点，按"重要性"排序                              │  │
│  │  对每个节点，执行"收缩"操作:                                │  │
│  │    - 移除节点v                                             │  │
│  │    - 在v的邻居间添加 shortcut 边 (如果有唯一最短路径)       │  │
│  │    - shortcut 权重 = 原路径权重和                         │  │
│  │                                                          │  │
│  │  查询阶段:                                                │  │
│  │  从起点向上搜索(重要性递增), 从终点向上搜索                 │  │
│  │  在某个中间节点汇合 → 最短路径                             │  │
│  │                                                          │  │
│  │  性能: 预处理 O(V log V + E), 查询 O(log V) ~ 微秒级     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  3b. Customizable Route Planning (CRP)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  图分区 (Graph Partitioning):                             │  │
│  │  将全国/全球划分为多层cell                                 │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │ Level 0: 每个 cell ≈ 1000 节点                   │    │  │
│  │  │ Level 1: 合并 → cell ≈ 10000 节点                │    │  │
│  │  │ Level 2: 合并 → cell ≈ 100000 节点               │    │  │
│  │  │ Level N: 全球图                                  │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  查询: Boundary Graph + Cell内部路径查找                   │  │
│  │  优势: 不同路况只需更新 Cell边界权重, metric可定制         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  算法4: 双向搜索 (Bidirectional Search)                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  同时从起点和终点向中间搜索                                       │
│  搜索区域 ≈ 2 × πr²/2 ≈ 一半 (相比单向搜索)                    │
│  与 CH/CRP 结合使用效果最佳                                     │
│                                                                │
│  最终选型: CRP + Bidirectional A* 用于大陆/全球级路径规划       │
│           Dijkstra 用于小范围 (步行/骑行)                       │
│                                                                │
│  技术栈组合:                                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  离线(预处理): 每天一次                                    │  │
│  │  - Graph Partitioning (PUNCH算法)                         │  │
│  │  - Shortcut预计算                                          │  │
│  │  - Turn cost / U-turn restriction 编码                    │  │
│  │                                                          │  │
│  │  在线(查询): < 1ms                                         │  │
│  │  - CRP边界图 直接查询                                      │  │
│  │  - Cell内 A* 搜索                                          │  │
│  │  - 实时路况叠加 (更新边权重)                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

伪代码: CH 查询算法
```python
def ch_query(graph, source, target, forward_upward):
    # forward_upward: [dist, parent_node, settled]
    # backward_upward: [dist, parent_node, settled]
    
    # 双向Dijkstra, 但只探索 importance 递增的节点
    tentative_dist = INF
    meeting_node = None

    while True:
        # 从正向选择的节点
        v_fwd = extract_min(forward_queue)
        if v_fwd is None: break
        forward_upward[v_fwd].settled = True

        for edge in graph.forward_edges[v_fwd]:
            new_dist = forward_upward[v_fwd].dist + edge.weight
            if new_dist < forward_upward[edge.target].dist:
                forward_upward[edge.target].dist = new_dist
                forward_upward[edge.target].parent = v_fwd
                forward_queue.insert(edge.target, new_dist)

        # 检查是否已找到meeting节点
        if backward_upward[v_fwd].settled:
            total = forward_upward[v_fwd].dist + backward_upward[v_fwd].dist
            if total < tentative_dist:
                tentative_dist = total
                meeting_node = v_fwd

        # 对称: 反向搜索
        # ...

    return reconstruct_path(meeting_node)
```

### 3. 实时路况采集与ETA预测

```
┌────────────────────────────────────────────────────────────────┐
│                    实时路况系统                                  │
│                                                                │
│  数据采集:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. 手机GPS匿名数据 (最大数据源)                            │  │
│  │ 2. 车载导航设备                                            │  │
│  │ 3. 路面传感器 (线圈/摄像头)                                │  │
│  │ 4. 众包数据 (用户举报事故/施工)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  路况推算流程:                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  GPS Pings ──► Map Matching ──► Speed Calculation        │  │
│  │  (原始轨迹)     (匹配到路段)     (计算路段车速)             │  │
│  │                                         │                 │  │
│  │                                         ▼                 │  │
│  │                               ┌──────────────────┐       │  │
│  │                               │ Traffic Speeds    │       │  │
│  │                               │ per Segment       │       │  │
│  │                               └────────┬─────────┘       │  │
│  │                                        │                  │  │
│  │                    ┌───────────────────┼───────────────┐ │  │
│  │                    ▼                   ▼               ▼ │  │
│  │              ┌──────────┐    ┌──────────────┐  路由规划 │  │
│  │              │ 实时地图  │    │ ETA预测引擎   │  更新权重 │  │
│  │              │ 路况瓦片  │    │              │          │  │
│  │              └──────────┘    └──────────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ETA 预测引擎:                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  ETA = Σ(segment_length / predicted_speed_at_arrival)    │  │
│  │                                                          │  │
│  │  predicted_speed = combine(                              │  │
│  │    current_speed (实时速度, 最近5分钟平均, 权重: 0.7),     │  │
│  │    historical_speed (历史规律, 权重: 0.3)                 │  │
│  │  )                                                       │  │
│  │                                                          │  │
│  │  分段预测: 用户在A→B, 经过 segment_1, segment_2, ...,    │  │
│  │            到达 segment_k 时路况可能已变化                │  │
│  │            → 按预测到达时间查对应历史路况                  │  │
│  │                                                          │  │
│  │  准确率: 行程 < 30min → 误差 < 1min                      │  │
│  │         行程 30-60min → 误差 < 3min                      │  │
│  │         行程 > 2h → 误差 < 10%                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 4. 地点搜索系统

```
┌────────────────────────────────────────────────────────────────┐
│                    搜索系统架构                                  │
│                                                                │
│  搜索类型:                                                     │
│  1. 前缀搜索: "スタ" → "スターバックス"                        │
│  2. 模糊搜索: "starbacks" → "Starbucks" (Levenshtein 距离)   │
│  3. 地理空间搜索: 当前位置附近 + 关键词                         │
│  4. 类目搜索: "restaurant near me"                            │
│                                                                │
│  自动补全 (Autocomplete):                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Trie 树 + 地理位置过滤:                                   │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │                  (root)                          │    │  │
│  │  │                /    \                           │    │  │
│  │  │              S        ...                        │    │  │
│  │  │            /   \                                 │    │  │
│  │  │          T       A                              │    │  │
│  │  │        /   \    /  \                            │    │  │
│  │  │      A       O  N    ...                         │    │  │
│  │  │     /        |   |                              │    │  │
│  │  │   R        R    J                               │    │  │
│  │  │  /         |    |                               │    │  │
│  │  │ BUCKS*    E    OSE*                             │    │  │
│  │  │           |                                     │    │  │
│  │  │          S*                                     │    │  │
│  │  │  * = leaf node (包含 POI IDs)                   │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  查询 "ST" → "STARBUCKS", "STORE"                       │  │
│  │  每个叶子节点存储: [{poi_id, popularity, location}]       │  │
│  │  排序: popularity × distance_penalty                    │  │
│  │                                                          │  │
│  │  实现: Redis Sorted Set (缓存热点前缀)                    │  │
│  │  Key: autocomplete:{lang}:{prefix}                       │  │
│  │  Members: "Starbucks|poi_123", "Store A|poi_456"        │  │
│  │  Scores: popularity_score                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  全文搜索 + 地理空间搜索 (Elasticsearch):                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  ES Index: places                                        │  │
│  │  {                                                       │  │
│  │    "mappings": {                                         │  │
│  │      "properties": {                                     │  │
│  │        "name": {"type": "text", "analyzer": "standard"}, │  │
│  │        "name_ngram": {"type": "text",                    │  │
│  │          "analyzer": "edge_ngram_analyzer"},             │  │
│  │        "categories": {"type": "keyword"},                 │  │
│  │        "location": {"type": "geo_point"},                │  │
│  │        "popularity": {"type": "double"},                  │  │
│  │        "geohash": {"type": "geo_shape"}                  │  │
│  │      }                                                   │  │
│  │    }                                                     │  │
│  │  }                                                       │  │
│  │                                                          │  │
│  │  查询示例:                                                │  │
│  │  {                                                       │  │
│  │    "query": {                                            │  │
│  │      "bool": {                                           │  │
│  │        "must": [                                         │  │
│  │          {"match": {"name": "coffee"}}                   │  │
│  │        ],                                                │  │
│  │        "filter": [                                       │  │
│  │          {"geo_distance": {                              │  │
│  │            "distance": "5km",                            │  │
│  │            "location": {"lat": 37.77, "lon": -122.42}   │  │
│  │          }}                                              │  │
│  │        ]                                                 │  │
│  │      }                                                   │  │
│  │    },                                                    │  │
│  │    "sort": [                                             │  │
│  │      "_score",                                           │  │
│  │      {"popularity": "desc"}                              │  │
│  │    ]                                                     │  │
│  │  }                                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5. Geohash 空间索引

```
┌────────────────────────────────────────────────────────────────┐
│                    Geohash 空间编码                              │
│                                                                │
│  Geohash 原理:                                                  │
│  - 将经纬度交替二分编码为Base32字符串                             │
│  - 前缀越长相等的点越近                                          │
│                                                                │
│  Example: San Francisco (37.7749, -122.4194)                   │
│  Geohash: "9q8yy"                                              │
│                                                                │
│  优点:                                                          │
│  - 一维索引代替二维空间索引                                       │
│  - 前缀匹配即可做附近搜索                                        │
│  - 作为MySQL/Redis key做range query                            │
│                                                                │
│  附近搜索:                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  要搜索 lat=37.7749, lon=-122.4194 半径5km内的POI:       │  │
│  │                                                          │  │
│  │  1. 计算中心点 geohash: "9q8yy"                          │  │
│  │  2. 5km ≈ geohash precision 5 (误差 ±2.4km)              │  │
│  │  3. 查询所有 geohash LIKE "9q8y%" 的POI                  │  │
│  │  4. 精确过滤: 计算Haversine距离, 保留 <5km               │  │
│  │                                                          │  │
│  │  SQL:                                                     │  │
│  │  SELECT * FROM poi                                       │  │
│  │  WHERE geohash LIKE '9q8y%'                              │  │
│  │  AND haversine(lat, lon, 37.7749, -122.4194) < 5000     │  │
│  │  LIMIT 20                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Geohash 精度表:                                                │
│  ┌──────────┬────────────────┬──────────────┐                  │
│  │ Precision│ 纬度Bit / 经度│  Area (±)    │                  │
│  ├──────────┼────────────────┼──────────────┤                  │
│  │    1     │   2 / 3        │  5000 km     │                  │
│  │    3     │   7 / 8        │  156 km      │                  │
│  │    5     │  12 / 13       │  2.4 km      │                  │
│  │    7     │  17 / 18       │  76 m        │                  │
│  │    9     │  22 / 23       │  1.2 m       │                  │
│  └──────────┴────────────────┴──────────────┘                  │
└────────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### 全球部署架构

```
┌──────────────────────────────────────────────────────────────┐
│                    全球多区域部署                              │
│                                                              │
│  ┌─────────────────┐   ┌─────────────────┐                   │
│  │  US-West         │   │  EU-West         │                  │
│  │  (Oregon)        │   │  (Frankfurt)      │                  │
│  │  ────────────────│   │  ────────────────│                   │
│  │  瓦片缓存        │   │  瓦片缓存         │                   │
│  │  路网图(北美)    │   │  路网图(欧洲)     │                   │
│  │  POI索引(北美)   │   │  POI索引(欧洲)    │                   │
│  └─────────────────┘   └─────────────────┘                   │
│                                                              │
│  ┌─────────────────┐   ┌─────────────────┐                   │
│  │  Asia-East       │   │  Global          │                  │
│  │  (Tokyo)         │   │  Route Planner    │                  │
│  │  ────────────────│   │  (跨国路径规划)   │                   │
│  │  瓦片缓存        │   │                  │                   │
│  │  路网图(亚洲)    │   │  跨区域路由查询   │                   │
│  │  POI索引(亚洲)   │   │  需要访问多个      │                   │
│  └─────────────────┘   │  区域的图数据     │                   │
│                         └─────────────────┘                   │
│                                                              │
│  特点:                                                        │
│  - 各大洲独有路网图，减少内存需求                              │
│  - 跨区域路由走 Global Route Planner                          │
│  - 地图瓦片全球CDN分发                                        │
│  - POI数据全局复制 (最终一致), 搜索走本地索引                  │
└──────────────────────────────────────────────────────────────┘
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 地图瓦片 | 预渲染+CDN(Z0-14) + 动态渲染(Z15+) | 平衡性能和更新频率 |
| 路径规划 | CRP + Bidirectional A* | 毫秒级查询, 支持动态路况 |
| 路况采集 | 手机GPS匿名数据 + 众包 | 最高覆盖率和实时性 |
| 搜索 | Elasticsearch + Geohash | 全文搜索+地理空间搜索一体 |
| 自动补全 | Trie树 + Redis | 高并发前缀搜索 |
| 路网图分区 | 多级分层(Global/Regional/Cell) | 减少搜索空间 |
| CDN | CloudFront/Cloudflare | 全球低延迟 |
| 空间索引 | Geohash + QuadTree | 高效附近搜索 |

核心设计要点:
1. **地图瓦片是80%的流量**: CDN缓存命中率 >95%，只需处理5%的miss
2. **路径规划核心是图预处理**: CRP/CH将查询复杂度从 O(VlogV) 降到近 O(1)
3. **实时路况 = GPS轨迹推断**: 不需要摄像头/线圈，手机定位数据已足够
4. **Geohash使空间搜索简单**: 将2D问题降为1D前缀匹配
5. **全球化 = 区域独立**: 大洲级的图独立存储，只有跨国查询才跨区
6. **数据是最大价值**: 地图数据、POI、路况的持续更新是核心壁垒
