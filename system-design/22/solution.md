# 设计推荐系统 (Design Recommendation System)

## 题目

设计一个大规模推荐系统，类似 YouTube、Netflix、Amazon 的内容/商品推荐，支持个性化推荐。

## 需求澄清

### 功能性需求

1. **个性化推荐**: 根据用户历史行为（浏览、点击、购买、评分、收藏、停留时长）推荐内容
2. **相似内容推荐**: "看了又看"、"买了又买" 类型推荐
3. **热门推荐**: 全局热门内容（解决冷启动问题）
4. **实时推荐**: 用户实时行为能快速影响推荐结果
5. **多样性**: 推荐结果不能单一，需要多样性（如类别、价格区间）
6. **新鲜度**: 推荐内容需要随时间更新
7. **可解释性**: 能告诉用户为什么推荐（因为你看了 X / 类似用户也喜欢）
8. **反馈收集**: 隐式反馈（点击、时长）+ 显式反馈（评分、喜欢/不喜欢）

### 非功能性需求

- **低延迟**: 推荐接口 < 200ms (p99)
- **高可用**: 99.99% SLA
- **高并发**: 支持 100K+ QPS（首页推荐 feed）
- **实时性**: 用户行为 → 推荐更新延迟 < 5分钟
- **冷启动**: 新用户、新内容需要在几分钟内获得合理推荐

### 容量估算

```
假设:
- DAU: 1亿
- 内容总量: 1亿条
- 每个用户平均每天请求推荐: 20次
- 用户历史行为: 每人平均500条

QPS估算:
- 高峰 QPS = 1亿 × 20 / 86400 × 5(高峰系数) ≈ 115,000 QPS
- 推荐接口 p99 < 200ms

存储估算:
- 用户行为数据: 1亿 × 500 × 200bytes ≈ 1 TB (可通过压缩优化)
- 内容特征向量: 1亿 × 512维 × 4 bytes ≈ 200 GB
- 用户特征向量: 1亿 × 512维 × 4 bytes ≈ 200 GB
- 模型文件: ~100 GB
- 总计: ~1.5 TB (实际需要副本和在线离线双存储)

离线训练数据:
- 每天新增行为: 1亿 × 20次 = 20亿条
- 保留90天 → 1800亿条
- 存储: 1800亿 × 200bytes ≈ 36 TB (HDFS/S3)
```

## API设计

```protobuf
// 推荐 API
// POST /api/v1/recommend
message RecommendRequest {
  string user_id = 1;
  string scene = 2;                   // "home_feed", "related_items", "search"
  int32 count = 3;                    // 返回数量, 默认20
  int32 offset = 4;                   // 分页偏移
  repeated string context = 5;        // 上下文: {"device":"mobile","time":"morning"}
  string page_type = 6;               // "homepage", "detail_page", "cart_page"
  UserContext user_context = 7;       // 用户实时上下文
}

message UserContext {
  string device_type = 1;             // "ios", "android", "web"
  string network = 2;                 // "wifi", "4g"
  string region = 3;                  // 用户所在地区
  string language = 4;                // 语言偏好
}

message RecommendResponse {
  repeated RecommendedItem items = 1;
  string request_id = 2;              // 用于追踪/实验
  string experiment_id = 3;           // A/B实验ID
  map<string, string> debug_info = 4; // 调试信息(内部)
}

message RecommendedItem {
  string item_id = 1;
  string title = 2;
  double score = 3;                   // 推荐分数
  string reason = 4;                  // 推荐理由 "热门推荐" "因为你看了X"
  ItemMetadata metadata = 5;          // 封面图、简介等
}

// 反馈 API
// POST /api/v1/feedback
message FeedbackRequest {
  string user_id = 1;
  string item_id = 2;
  FeedbackType type = 3;
  string source = 4;                  // 来源页面/推荐位
  int64 timestamp_ms = 5;
}

enum FeedbackType {
  CLICK = 0;
  LIKE = 1;
  DISLIKE = 2;
  SHARE = 3;
  PURCHASE = 4;
  VIEW_DURATION = 5;                  // 观看时长
  NOT_INTERESTED = 6;
  SKIP = 7;
}

// 行为日志 (流式上报)
// POST /api/v1/events (批量)
message EventBatch {
  repeated UserEvent events = 1;
  string user_id = 2;
  string session_id = 3;
}

message UserEvent {
  string event_type = 1;              // "view", "click", "add_cart", "purchase", "share"
  string item_id = 2;
  int64 timestamp_ms = 3;
  map<string, string> properties = 4; // {"duration_ms":"5000", "scroll_depth":"0.8"}
}
```

## 数据模型

### 内容/商品元数据

```sql
CREATE TABLE items (
    item_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category_id VARCHAR(64),
    category_path VARCHAR(500),       -- "电子产品/手机/iPhone"
    price DECIMAL(10,2),
    status ENUM('active','inactive','deleted') DEFAULT 'active',
    publish_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_status (category_id, status),
    INDEX idx_publish_time (publish_time)
);

CREATE TABLE item_features (
    item_id VARCHAR(64) PRIMARY KEY,
    feature_vector BLOB,              -- 512维 float32 特征向量
    feature_version VARCHAR(32),      -- 特征版本号
    statistical_features JSON,        -- {"ctr":0.05, "cvr":0.02, "avg_rating":4.3, "pv_7d":10000}
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE item_tags (
    item_id VARCHAR(64) NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    tag_type VARCHAR(50) NOT NULL,     -- "brand", "color", "style", "price_range"
    weight DOUBLE DEFAULT 1.0,        -- 标签权重
    PRIMARY KEY (item_id, tag_type, tag_name),
    INDEX idx_tag (tag_type, tag_name)
);
```

### 用户行为存储

```sql
-- 用户行为 (历史行为用 Hive/Spark 离线分析)
-- 在线服务只需要最近N条行为用于实时推荐

-- Redis存储用户最近行为序列
-- Key: user_behavior:{user_id}
-- Type: ZSET (score为时间戳, member为JSON编码行为)

-- MySQL仅存用户画像
CREATE TABLE user_profiles (
    user_id VARCHAR(64) PRIMARY KEY,
    interests JSON,                   -- {"电子":0.8, "运动":0.3, "美食":0.6}
    demographic JSON,                 -- {"age_group":"25-34", "gender":"male", "city":"Beijing"}
    activity_level ENUM('low','medium','high','vip'),
    last_active_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户-内容互动汇总
CREATE TABLE user_item_interactions (
    user_id VARCHAR(64) NOT NULL,
    item_id VARCHAR(64) NOT NULL,
    total_clicks INT DEFAULT 0,
    total_views INT DEFAULT 0,
    total_purchases INT DEFAULT 0,
    avg_view_duration_ms INT DEFAULT 0,
    rating TINYINT,
    last_interaction_at TIMESTAMP,
    PRIMARY KEY (user_id, item_id),
    INDEX idx_user_last (user_id, last_interaction_at DESC)
);
```

### 特征工程数据模型

```
┌────────────────────────────────────────────────────────────┐
│                 特征分类                                    │
│                                                            │
│  1. 用户特征:                                              │
│     - 人口统计特征: 年龄、性别、地域、职业                    │
│     - 行为统计特征: 近7/30天点击数、购买数、活跃时段           │
│     - 兴趣向量: 品类偏好权重分布                              │
│     - 实时行为特征: 当前session浏览序列、搜索词               │
│                                                            │
│  2. 内容特征:                                              │
│     - 基础属性: 品类、价格、品牌、发布时间                     │
│     - 统计特征: CTR(点击率)、CVR(转化率)、Rating、收藏数      │
│     - 内容嵌入(Embedding): NLP/BERT文本特征, CV图像特征       │
│     - 协同过滤隐向量: MF分解得到的latent factors              │
│                                                            │
│  3. 上下文特征:                                            │
│     - 时间: 小时、星期、节假日                                │
│     - 设备: 手机/PC/平板                                    │
│     - 网络: WiFi/4G/5G                                     │
│     - 位置: 城市/省份                                       │
│     - 场景: 首页/详情页/购物车                               │
└────────────────────────────────────────────────────────────┘
```

## 高层次架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         推荐系统端到端架构                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Online Serving Layer                              ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    ││
│  │  │ Recommendation│ │ Reranking    │ │ Diversity    │ │ Ads Insertion│    ││
│  │  │ Recall        │ │ Model        │ │ Module       │ │ Module       │
│  │  │ ────────────  │ │ ──────────── │ │ ──────────── │ │ ──────────── │
│  │  │ 多路召回      │ │ 精排模型     │ │ 多样性策略   │ │ 广告混排     ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Near-line Layer (秒-分钟级别)                        ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                      ││
│  │  │ Flink/Spark  │ │ Feature       │ │ Real-time    │                      ││
│  │  │ Streaming    │ │ Store Update  │ │ Index Update │                      ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Offline Layer (小时-天级别)                          ││
│  │  ┌───────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐     ││
│  │  │ HDFS/S3   │ │ Spark MLlib  │ │ TensorFlow  │ │ Feature Platform │     ││
│  │  │ Data Lake │ │ 协同过滤训练 │ │ DNN 训练     │ │ 特征生产/管理     │     ││
│  │  └───────────┘ └──────────────┘ └─────────────┘ └──────────────────┘     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 推荐流程详解 (多级漏斗架构)

```
                    ┌─────────────────────────────────┐
         物品总量   │        全部内容 (1亿+)           │
                    └───────────────┬─────────────────┘
                                    │
                      ┌─────────────▼─────────────┐
                      │     Recall 召回 (数千)      │
                      │  ┌─────────────────────┐  │
                      │  │ 协同过滤召回         │  │  UserCF/ItemCF
                      │  │ Embedding 召回       │  │  ANN向量检索
                      │  │ 热门召回             │  │  冷启动+兜底
                      │  │ 地理位置召回          │  │  LBS
                      │  │ 实时兴趣召回          │  │  基于最近行为
                      │  │ 社交网络召回          │  │  好友喜欢
                      │  └─────────────────────┘  │
                      └───────────────┬───────────┘
                                      │
                        ┌─────────────▼─────────────┐
                        │   Pre-ranking 粗排 (千级) │
                        │  轻量模型快速过滤          │
                        └───────────────┬───────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │   Ranking 精排 (百级)       │
                          │  ┌───────────────────────┐ │
                          │  │ DeepFM / Wide & Deep  │ │
                          │  │ DCN / DIN / DIEN      │ │
                          │  │ 特征交叉 + Attention   │ │
                          │  └───────────────────────┘ │
                          └───────────────┬─────────────┘
                                          │
                            ┌─────────────▼─────────────┐
                            │   Re-ranking 重排 (十级)   │
                            │  多样性、新鲜度、去重       │
                            │  MMR (最大边际相关性)        │
                            │  DPP (行列式点过程)          │
                            │  业务规则 (去重、已购过滤)    │
                            └───────────────┬─────────────┘
                                            │
                              ┌─────────────▼──────────┐
                              │   最终推荐列表 (20条)    │
                              └────────────────────────┘
```

## 核心深入

### 1. 召回策略 (Recall) 深度对比

```
┌────────────────────────────────────────────────────────────────────────┐
│                       多路召回策略对比                                   │
│                                                                        │
│  策略一: 协同过滤 (Collaborative Filtering)                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
│                                                                        │
│  User-Based CF:                                                       │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │ 用户A看了 [Item1, Item2, Item3]                           │          │
│  │ 用户B看了 [Item1, Item2, Item4]                           │          │
│  │ → A和B相似 → 推荐Item4给A，推荐Item3给B                    │          │
│  │                                                          │          │
│  │ 相似度计算: Cosine Similarity / Pearson Correlation      │          │
│  │ Sim(A,B) = (A·B) / (||A|| × ||B||)                     │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                                                        │
│  Item-Based CF:                                                       │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │ 看了Item1的用户也看了Item2                                │          │
│  │ → Item1和Item2相似 → 看过Item1的人推荐Item2                │          │
│  │                                                          │          │
│  │ 优点: 物品相似度较稳定，可离线计算，更新频率低               │          │
│  │ 缺点: 冷启动问题，不能跨领域推荐                            │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                                                        │
│  策略二: 向量化召回 (Embedding-based)                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │                    Embedding 空间                        │         │
│  │                                                          │         │
│  │    用户BEmbedding                                        │         │
│  │       *                                                  │         │
│  │        \    Item2 *                                      │         │
│  │         \  /                                             │         │
│  │   用户A  *---*  Item1  ← 距离最近                        │         │
│  │    E(u)     /                                            │         │
│  │            / Item3 *                                     │         │
│  │                                                          │         │
│  │  使用 ANN (近似最近邻) 检索: FAISS, ScaNN, Annoy          │         │
│  │  相似度: Cosine / Inner Product (内积)                    │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                        │
│  模型训练: Two-Tower 双塔模型                                          │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │                                                          │         │
│  │  User Tower                    Item Tower                │         │
│  │  ┌──────────┐                  ┌──────────┐              │         │
│  │  │ 用户特征  │                  │ 物品特征  │              │         │
│  │  │ (年龄,    │                  │ (品类,    │              │         │
│  │  │  性别,    │                  │  价格,    │              │         │
│  │  │  历史行为)│                  │  品牌..)  │              │         │
│  │  └────┬─────┘                  └────┬─────┘              │         │
│  │       │                             │                    │         │
│  │       ▼                             ▼                    │         │
│  │  ┌──────────┐                  ┌──────────┐              │         │
│  │  │ DNN      │                  │ DNN      │              │         │
│  │  │ Layers   │                  │ Layers   │              │         │
│  │  └────┬─────┘                  └────┬─────┘              │         │
│  │       │  User Embedding (d维)  │ Item Embedding (d维)    │         │
│  │       └──────────┬─────────────┘                        │         │
│  │                  │                                      │         │
│  │                  ▼                                      │         │
│  │      Score = cos(E_user, E_item) 或 Dot Product        │         │
│  │      损失函数: sampled softmax / triplet loss           │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                        │
│  策略三: 内容召回 (Content-Based)                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
│  - 基于物品标签/属性直接匹配 (用户喜欢"科幻"→推荐"科幻")                │
│  - 用于新物品冷启动                                                   │
│                                                                        │
│  策略四: 实时兴趣召回                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
│  - 用户最近N次点击(5分钟内的行为)                                       │
│  - 基于session-based推荐 (如GRU4Rec, SASRec)                          │
│  - 用户刚搜索"iPhone"→ 推荐iPhone相关商品                              │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. ANN (Approximate Nearest Neighbor) 向量检索

```
向量检索在召回层的核心作用:
给定 User Embedding，从百万/亿级 Item Embedding 中快速找到 Top-K 最相似向量。

┌────────────────────────────────────────────────────────────┐
│             ANN 算法对比                                    │
│                                                            │
│  1. FAISS (Facebook AI Similarity Search):                │
│     ┌────────────────────────────────────────────────┐    │
│     │ IVF (Inverted File):                            │    │
│     │   聚类 → 查询只搜索最近几个聚类                    │    │
│     │   cluster_centers = KMeans(vectors, nlist=1024) │    │
│     │   query → 找最近 nprobe=32 个聚类 → 扫描聚类内向量│    │
│     │   knn_result = topk(distances, k=100)           │    │
│     │                                                 │    │
│     │ IVF_PQ (Product Quantization):                  │    │
│     │   IVF + PQ 量化压缩 → 内存节省10-30x              │    │
│     │   向量分多段，每段独立量化                         │    │
│     │                                                 │    │
│     │ HNSW (Hierarchical Navigable Small World):      │    │
│     │   图索引，分层搜索                                │    │
│     │   构建: 随机层级 → 逐层插入 → 建立边             │    │
│     │   查询: 从顶层 → 逐层下降 → 局部搜索              │    │
│     │   召回率高 (95%+), 但内存占用大                   │    │
│     └────────────────────────────────────────────────┘    │
│                                                            │
│  2. ScaNN (Google):                                       │
│     - 各向异性量化 (Anisotropic Quantization)               │
│     - 优化内积距离，特别适合DNN embedding                   │
│     - 更快的 inference 速度                                │
│                                                            │
│  算法选型 Trade-off:                                       │
│  ┌───────────┬──────────┬──────────┬──────────┐           │
│  │  算法      │ 召回率    │ 内存     │ 延迟     │           │
│  ├───────────┼──────────┼──────────┼──────────┤           │
│  │ IVF_FLAT  │ 低       │ 低       │ 低       │           │
│  │ IVF_PQ    │ 中低     │ 极低     │ 中       │           │
│  │ HNSW      │ 最高     │ 高       │ 最低     │           │
│  │ IVF_SQ8   │ 中       │ 低       │ 中       │           │
│  └───────────┴──────────┴──────────┴──────────┘           │
│                                                            │
│  典型部署: IVF_PQ 做粗召回 (1000→100), HNSW 做精召回       │
└────────────────────────────────────────────────────────────┘

FAISS 使用伪代码:
```python
import faiss
import numpy as np

# 离线构建索引
dim = 512
nlist = 1024
m = 64  # PQ 分段数

quantizer = faiss.IndexFlatIP(dim)  # Inner Product
index = faiss.IndexIVFPQ(quantizer, dim, nlist, m, 8)
index.train(item_vectors)  # 训练 (KMeans + PQ)
index.add(item_vectors)    # 添加向量

# 在线查询
index.nprobe = 64  # 搜索多少个聚类
D, I = index.search(user_vector, k=100)  # 返回 top-100
```

### 3. 精排模型 (Ranking Models)

```
CTR Prediction 模型演进:

┌─────────────────────────────────────────────────────────────────┐
│  1. 线性模型 (LR):                                              │
│     特点: 简单，可解释，需要大量特征工程                          │
│     y = sigmoid(w1*x1 + w2*x2 + ... + wn*xn + b)               │
│     问题: 无法捕捉特征交叉                                       │
├─────────────────────────────────────────────────────────────────┤
│  2. FM (Factorization Machine):                                │
│     特点: 自动二阶特征交叉                                       │
│     y = w0 + Σ(wi*xi) + ΣΣ(<vi,vj> * xi * xj)                 │
│     每个特征有隐向量 vi，通过内积捕捉交叉关系                      │
├─────────────────────────────────────────────────────────────────┤
│  3. Wide & Deep (Google, 2016):                                │
│     ┌──────────────────┐  ┌──────────────────┐                  │
│     │   Wide (线性)     │  │   Deep (DNN)     │                  │
│     │   记忆 (Memory)   │  │   泛化 (Generalize)│                 │
│     │   交叉特征        │  │   全连接+Embedding │                 │
│     └────────┬─────────┘  └────────┬─────────┘                  │
│              └─────────────────────┘                             │
│                        │                                        │
│                     输出层 (sigmoid)                             │
├─────────────────────────────────────────────────────────────────┤
│  4. DeepFM:                                                    │
│     FM取代 Wide 部分 → 自动特征交叉 + DNN 泛化                   │
│     FM 和 Deep 共享 Embedding 层                                │
├─────────────────────────────────────────────────────────────────┤
│  5. DCN (Deep & Cross Network):                                │
│     Cross Network 显式高阶特征交叉 (x0, x1, x0*x1, ...)         │
│     x_{l+1} = x0 * (w_l^T * x_l) + b_l + x_l                  │
├─────────────────────────────────────────────────────────────────┤
│  6. DIN (Deep Interest Network, Alibaba):                      │
│     引入 Attention 机制: 用户有不同的兴趣，不同商品激活不同兴趣    │
│     v_u = Σ(w_i * v_i), w_i = attention(candidate_ad, behavior_i)│
├─────────────────────────────────────────────────────────────────┤
│  7. DIEN (Deep Interest Evolution Network):                    │
│     GRU 建模用户兴趣演化，捕捉时序依赖                            │
└─────────────────────────────────────────────────────────────────┘

精排模型训练架构:
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   训练数据 Pipeline:                                         │
│   ┌─────────┐    ┌──────────┐    ┌───────────┐              │
│   │ 日志     │───►│ 特征抽取  │───►│ 样本生成   │              │
│   │ (曝光,   │    │ (Joining  │    │ (正样本:点击│              │
│   │  点击,   │    │  用户特征, │    │  负样本:曝光│              │
│   │  转化)   │    │  物品特征) │    │  但未点击)  │              │
│   └─────────┘    └──────────┘    └─────┬─────┘              │
│                                       │                      │
│                                       ▼                      │
│                              ┌──────────────┐                │
│                              │ 分布式训练    │                │
│                              │ GPU 集群      │                │
│                              │ Parameter     │                │
│                              │ Server +      │                │
│                              │ Workers       │                │
│                              └──────┬───────┘                │
│                                     │                        │
│                                     ▼                        │
│                              ┌──────────────┐                │
│                              │ Model Store   │                │
│                              │ (模型版本管理) │                │
│                              └──────────────┘                │
│                                                              │
│  模型版本管理:                                               │
│  - 每日训练新模型，保留最近N个版本                            │
│  - A/B 实验框架切换模型流量                                  │
│  - 模型热加载 (Hot-reload) 无需重启服务                       │
└──────────────────────────────────────────────────────────────┘
```

### 4. A/B 实验框架

```
┌──────────────────────────────────────────────────────────────┐
│                 A/B 实验系统                                  │
│                                                              │
│  分流逻辑:                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ user_id → hash → bucket(0-99) → layer → experiment   │   │
│  │                                                      │   │
│  │  Layer 1 (召回层):        Layer 2 (排序层):          │   │
│  │  ┌──────┬──────┐         ┌──────┬──────┐            │   │
│  │  │ Control│ Exp│         │ Control│ Exp│            │   │
│  │  │(CF)   │(DNN)│         │(LR)   │(DeepFM)│         │   │
│  │  └──────┴──────┘         └──────┴──────┘            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  正交分层:                                                    │
│  - Layer 效应相互独立，可同时进行多个实验                        │
│  - hash(user_id + layer_id) 保证同一用户在不同层有不同分配      │
│                                                              │
│  核心指标:                                                    │
│  - CTR (点击率): 点击/曝光                                    │
│  - CVR (转化率): 购买/点击                                    │
│  - ADCTR (广告点击率)                                         │
│  - 用户停留时长、回访率                                        │
│  - 内容多样性 (Entropy / Coverage)                            │
│                                                              │
│  统计检验:                                                    │
│  - t-test / z-test 检验 CTR 差异是否显著                      │
│  - 最小样本量计算 (Power Analysis)                            │
│  - Bonferroni 多重比较校正                                    │
└──────────────────────────────────────────────────────────────┘
```

### 5. 特征存储 (Feature Store)

```
┌──────────────────────────────────────────────────────────────┐
│                Feature Store 架构                             │
│                                                              │
│  问题: 离线训练和在线推理的特征一致性问题                        │
│  解决: 统一的 Feature Store                                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Feature Registry                         │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Feature Definition (声明式):                    │  │   │
│  │  │   name: user_ctr_7d                            │  │   │
│  │  │   owner: rec-team                               │  │   │
│  │  │   type: float                                   │  │   │
│  │  │   entity: user                                  │  │   │
│  │  │   freshness: daily                              │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────┐      ┌─────────────────┐               │
│  │  Offline Store   │      │   Online Store   │               │
│  │  ────────────────│      │   ──────────────   │               │
│  │  Hive/S3 (全量)  │      │   Redis (热点)     │               │
│  │  训练数据生成     │      │   低延迟推理查询    │               │
│  │  批处理特征       │      │   实时特征服务     │               │
│  └─────────────────┘      └─────────────────┘               │
│                                                              │
│  在线特征拼接流程:                                            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐       │
│  │ 推荐请求  │──►│ 特征服务      │──►│ 模型推理          │       │
│  │ user_id   │  │ 查询所有特征  │  │ (拼接后特征向量) │       │
│  └──────────┘  │ user_features │  └──────────────────┘       │
│                │ item_features │                              │
│                │ context_feat. │                              │
│                └──────────────┘                              │
└──────────────────────────────────────────────────────────────┘
```

### 6. 冷启动策略

```
┌──────────────────────────────────────────────────────────────┐
│                    冷启动处理策略                              │
│                                                              │
│  新用户冷启动:                                                │
│  1. 新用户引导: 让用户选择兴趣标签                             │
│  2. 热门推荐: 全站最热门内容兜底                               │
│  3. 地域推荐: 同城市/地区热门                                  │
│  4. 设备推断: iPhone 用户推高端商品                            │
│  5. 探索利用 (Explore & Exploit):                              │
│     - Thompson Sampling / UCB (Upper Confidence Bound)       │
│     - 10%流量随机探索，90%利用已有知识                         │
│                                                              │
│  新物品冷启动:                                                │
│  1. 内容特征: 刚入库就有标签、描述、图片特征                    │
│  2. 流量扶持: 新物品分配额外曝光机会                           │
│  3. 相似推荐: 推荐给喜欢同类物品的用户                          │
│  4. 编辑推荐: 人工精选 (适用于内容平台)                        │
└──────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### 在线服务架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    推荐在线服务架构                                │
│                                                                 │
│                    ┌──────────────┐                              │
│                    │ API Gateway  │                              │
│                    │ (限流/鉴权/路由)│                             │
│                    └──────┬───────┘                              │
│                           │                                      │
│                    ┌──────▼───────┐                              │
│                    │ 推荐编排引擎  │                               │
│                    │ (Orchestrator)│                              │
│                    └──────┬───────┘                              │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                    │
│         │                 │                 │                    │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌─────▼─────┐              │
│  │ 召回服务集群 │  │ 排序服务集群   │  │ 特征服务   │              │
│  │ (多个独立的  │  │ (多模型版本   │  │ (Redis     │              │
│  │  召回策略)   │  │  并存)       │  │  Cluster)  │              │
│  └─────────────┘  └───────────────┘  └───────────┘              │
│                                                                 │
│  性能优化:                                                       │
│  1. 召回并行化: 多路召回并发调用，结果归并                          │
│  2. 缓存预热: 热门用户推荐结果预计算缓存                            │
│  3. 超时熔断: 单路召回 > 50ms 自动熔断丢弃                          │
│  4. 降级策略: 排序模型故障时用召回分数排序                          │
│  5. 模型热加载: 不停服更新模型                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 扩展性

```
1. 召回层扩展:
   - 每个召回策略独立微服务，独立扩缩容
   - Embedding 向量分片存储 (Shard by item_id hash)
   - ANN 索引可部署多副本

2. 排序层扩展:
   - 模型服务无状态，水平扩展
   - 批推理优化 (Batching + TensorRT/ONNX)
   - GPU 弹性扩缩

3. 特征服务扩展:
   - Redis Cluster 水平分片
   - 热点 Key 本地缓存
   - 特征更新增量同步

4. 数据管道扩展:
   - Kafka Partition 按 user_id hash 分区
   - Flink 流处理水平扩展
   - Spark 批处理动态资源分配
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 召回 | 多路召回 (CF + Embedding + 热门) | 互补覆盖，解决不同场景 |
| ANN检索 | FAISS (IVF_PQ + HNSW) | 高召回率 + 低内存 |
| 排序模型 | DeepFM / DCN + Attention | CTR预测 SOTA，特征交叉充分 |
| 特征工程 | Feature Store (Feast) | 离线在线一致性 |
| 实时处理 | Kafka + Flink | 毫秒-秒级延迟 |
| 离线训练 | Spark + TensorFlow (GPU) | 大规模数据训练 |
| A/B实验 | 正交分层分流 | 多实验并行 |
| 缓存 | Redis + 本地缓存 | 热点用户降低延迟 |
| 模型服务 | TensorFlow Serving | 热加载，批推理 |

核心设计要点:
1. **多级漏斗**: 全量(亿) → 召回(千) → 粗排(百) → 精排(十) → 重排(20)，逐级精筛
2. **多路召回**: CF、Embedding、热门、实时、地域多路互补，提高覆盖率和多样性
3. **ANN是关键**: FAISS/HNSW 实现毫秒级从亿级向量中检索Top-K
4. **特征一致性**: Feature Store 保证离线训练和在线推理特征口径一致
5. **A/B实验驱动**: 所有策略变更必须通过A/B实验验证效果
6. **工程优化**: 并行召回、超时熔断、降级兜底保证99.99%可用性
