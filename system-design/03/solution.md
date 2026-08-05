# 03. 设计信息流/动态系统 (Design News Feed)

## 题目

设计一个类似 Twitter / Facebook / Instagram 的信息流（News Feed / Timeline）系统，用户能够看到自己关注的其他人发布的内容，按时间线排列，支持图片、视频、文本等多种内容类型。

---

## 需求澄清

### 功能性需求

1. **发布内容 (Post/Tweet)**：用户可以发布文本、图片、视频
2. **信息流 (News Feed)**：用户能看到关注的人发布的内容，按时间排序
3. **关注/取关 (Follow/Unfollow)**：用户可以关注或取关其他用户
4. **点赞、评论、转发 (Like/Comment/Retweet/Share)**：互动功能
5. **个性化推荐（可选）**：基于算法排序而非纯时间序
6. **搜索内容（可选）**：全文搜索帖子内容
7. **热门话题/趋势（可选）**：基于互动的实时热门内容（Trending）

### 非功能性需求

1. **低延迟**：信息流加载 P99 < 200ms（首屏 20 条）
2. **高可用**：99.95% ~ 99.99% 可用
3. **高并发**：支持千万级 QPS 读操作
4. **实时性**：新发布的帖文在 5 秒内出现在关注者的信息流中
5. **扩展性**：支持 5 亿+ 日活用户
6. **最终一致性**：信息流可以接受短暂不一致

### 容量估算

**假设条件：**
- DAU: 5 亿
- 每日新帖文: 每用户平均 1 条 → 5 亿条/天
- 平均每个用户关注 200 人
- 平均信息流刷新频率: 每用户每天刷新 30 次，每次 20 条
- 每日信息流读取: 5亿 × 30 × 20 = **3000 亿次/天**
- 读 QPS: 3000亿 / 86400 ≈ **3.47M QPS**（峰值 ×3 ≈ **10M QPS**）
- 写 QPS: 5亿 / 86400 ≈ **5,787 QPS**（峰值 ×3 ≈ **17K QPS**）
- 读写比: ~600:1

**存储估算（5年）：**
- 帖文数据: 5亿 × 365 × 5 = 9125亿条
- 每条帖文约 1KB (文本300B + 媒体URLs 500B + 元数据200B)
- 总存储: 9125亿 × 1KB ≈ **912.5 TB**
- 加上索引和媒体元数据: ~2 PB
- 媒体文件独立存储 (CDN + 对象存储): 另计 ~50 PB

**扇出估算：**
- 平均关注者数 (名人除外): 200
- 写扩散写入量: 5亿 × 200 = 1000 亿次/天 = **1.15M QPS**（缓存写入）
- 对于名人 (粉丝 > 100W): 不能写扩散，需要读扩散
  - 假设 1% 用户是"名人"
  - 1% 的帖文需要读扩散而非写扩散

---

## API 设计

### REST API

```
1. 发布帖文
POST /api/v1/posts
Authorization: Bearer <token>

Request:
{
  "content": "周末去爬山了！",
  "media_ids": ["media_abc", "media_def"],
  "location": {"lat": 40.7128, "lon": -74.0060},
  "visibility": "public"  // public | followers_only | private
}

Response: 201 Created
{
  "post_id": "post_12345",
  "author_id": "user_456",
  "content": "周末去爬山了！",
  "media_urls": ["https://cdn.app.com/media/abc.jpg", ...],
  "created_at": 1704067200000,
  "like_count": 0,
  "comment_count": 0,
  "retweet_count": 0
}
```

```
2. 获取信息流（首页）
GET /api/v1/feed?cursor=xxx&limit=20
Authorization: Bearer <token>

Response: 200 OK
{
  "posts": [
    {
      "post_id": "post_12345",
      "author": {"user_id": "u_456", "name": "张三", "avatar": "..."},
      "content": "周末去爬山了！",
      "media_urls": [...],
      "like_count": 42,
      "comment_count": 8,
      "has_liked": true,
      "created_at": 1704067200000
    },
    ...
  ],
  "next_cursor": "1704067200000_post_12345",
  "has_more": true
}
```

```
3. 获取用户时间线（个人主页）
GET /api/v1/users/{user_id}/posts?cursor=xxx&limit=20

Response: 同 Feed 结构
```

```
4. 关注用户
POST /api/v1/users/{user_id}/follow
Authorization: Bearer <token>

Response: 200 OK
{
  "status": "following",
  "user_id": "u_456",
  "follower_count": 1001
}
```

```
5. 取关用户
DELETE /api/v1/users/{user_id}/follow
```

```
6. 点赞帖文
POST /api/v1/posts/{post_id}/like
Authorization: Bearer <token>

Response: 200 OK {"like_count": 43, "has_liked": true}
```

```
7. 获取帖文详情（含评论）
GET /api/v1/posts/{post_id}?include_comments=true&comment_cursor=xxx

Response: 200 OK
{
  "post": {...},
  "comments": [...],
  "next_comment_cursor": "..."
}
```

---

## 数据模型

### 帖文存储 (分片 MySQL / Cassandra)

```sql
CREATE TABLE posts (
    post_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    content TEXT,
    media_ids JSON,           -- ["media_abc", "media_def"]
    location POINT NULL,      -- 地理坐标
    visibility ENUM('public','followers_only','private') DEFAULT 'public',
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    retweet_count INT DEFAULT 0,
    original_post_id BIGINT,  -- 转发帖文的原始ID
    created_at BIGINT NOT NULL COMMENT 'Unix毫秒时间戳',
    updated_at BIGINT,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_created (created_at DESC)
) ENGINE=InnoDB
PARTITION BY RANGE (created_at) (...);
-- 分片键: post_id (一致性哈希)
```

### 社交关系存储 (图数据库 / MySQL)

```sql
-- 关注关系表
CREATE TABLE follows (
    follower_id BIGINT NOT NULL,   -- 粉丝
    followee_id BIGINT NOT NULL,  -- 被关注者
    created_at BIGINT NOT NULL,
    PRIMARY KEY (follower_id, followee_id),
    INDEX idx_followee (followee_id)
) ENGINE=InnoDB;
-- 分片键: follower_id

-- 粉丝关系表（反向索引，用于查询被关注者的粉丝列表）
CREATE TABLE followers (
    followee_id BIGINT NOT NULL,
    follower_id BIGINT NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (followee_id, follower_id)
) ENGINE=InnoDB;
-- 分片键: followee_id
```

### 信息流存储 (Redis Sorted Set / Cassandra)

```
# 方案A: Redis Sorted Set（最常用）

Key:    feed:{user_id}
Type:   Sorted Set
Score:  created_at_timestamp
Member: post_id

操作:
  ZADD feed:u_123 1704067200000 "post_456"  # 新增帖文到用户信息流
  ZREVRANGEBYSCORE feed:u_123 +inf -inf LIMIT 0 20  # 获取最新20条

容量限制:
  每个 Feed 保持最近 1000 条帖文（超出部分 LRU 淘汰或归档到 Cassandra）

# 方案B: Cassandra (适合大规模)

CREATE TABLE user_feed (
    user_id BIGINT,
    created_at BIGINT,
    post_id BIGINT,
    author_id BIGINT,
    PRIMARY KEY (user_id, created_at, post_id)
) WITH CLUSTERING ORDER BY (created_at DESC);
```

### 互动数据存储

```sql
CREATE TABLE likes (
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (post_id, user_id)
);

CREATE TABLE comments (
    comment_id BIGINT PRIMARY KEY,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    parent_comment_id BIGINT,  -- 回复某条评论
    created_at BIGINT NOT NULL,
    INDEX idx_post_created (post_id, created_at DESC)
);
```

### 缓存策略

```
# 帖文内容缓存
Key:   post:{post_id}
Type:  String (JSON)
Value: 帖文完整内容
TTL:   24小时（频繁访问自动续期）

# 用户信息缓存
Key:   user:{user_id}
Type:  String (JSON)
Value: {"user_id":123,"name":"张三","avatar":"...","follower_count":1000,...}
TTL:   1小时

# 社交关系缓存（粉丝ID集合）
Key:   followers:{user_id}
Type:  Set
Value: [follower_id_1, follower_id_2, ...]
TTL:   1小时（关注/取关时主动失效）

# 关注列表缓存
Key:   following:{user_id}
Type:  Set  
Value: [followee_id_1, followee_id_2, ...]
TTL:   1小时

# 点赞状态缓存（当前用户是否点赞了某帖文）
Key:   like:{user_id}:{post_id}
Type:  String
Value: "1" or NULL
TTL:   与帖文生命周期一致
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────┐
                              │            CDN / Global LB               │
                              └──────────────┬───────────────────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               │                             │                             │
     ┌─────────▼──────────┐        ┌─────────▼──────────┐       ┌─────────▼──────────┐
     │   Feed Read Svc    │        │   Post Write Svc   │       │   Social Graph     │
     │                    │        │                    │       │   Service          │
     │ - 聚合用户信息流    │        │ - 创建帖文          │       │ - 关注/取关         │
     │ - 读扩散(名人)      │        │ - 触发扇出          │       │ - 查询关系          │
     │ - 个性化排序        │        │ - 媒体上传          │       │ - 双向关系维护      │
     └─────────┬──────────┘        └─────────┬──────────┘       └─────────┬──────────┘
               │                             │                             │
     ┌─────────▼─────────────────────────────▼─────────────────────────────▼──────────┐
     │                             消息队列 (Kafka)                                    │
     │  ┌──────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐  │
     │  │ post.created         │  │ feed.fanout         │  │ social.relationship  │  │
     │  │ Topic (64 分区)       │  │ Topic (128 分区)     │  │ Topic (32 分区)       │  │
     │  └──────────────────────┘  └─────────────────────┘  └──────────────────────┘  │
     └──────────────────┬────────────────────────────────────────────────────────────┘
                        │
     ┌──────────────────▼────────────────────────────────────────────────────────────┐
     │                            Fanout Service (扇出服务)                             │
     │                                                                                │
     │   ┌──────────────────────────────────────────────────────────────────────┐    │
     │   │  1. 消费 Kafka post.created 事件                                      │    │
     │   │  2. 查询作者的粉丝列表 (Social Graph Service / 缓存)                    │    │
     │   │  3. 分类判断：                                                         │    │
     │   │     - 普通用户 (粉丝 < 100W): 写扩散 → 写入每个粉丝的 Feed                     │    │
     │   │     - 名人 (粉丝 ≥ 100W): 标记为名人帖文，不做写扩散 (读扩散)               │    │
     │   │  4. 通知推送服务发送 Notification                                       │    │
     │   └──────────────────────────────────────────────────────────────────────┘    │
     └──────────────────┬────────────────────────────────────────────────────────────┘
                        │
     ┌──────────────────▼────────────────────────────────────────────────────────────┐
     │                              存储层                                            │
     │                                                                                │
     │  ┌──────────────────┐  ┌─────────────────────┐  ┌──────────────────────────┐  │
     │  │ Redis Cluster    │  │ MySQL / Cassandra    │  │ Object Store (S3/MinIO)  │  │
     │  │ ──────────────── │  │ ───────────────────  │  │ ──────────────────────── │  │
     │  │ Feed Cache       │  │ Posts Table          │  │ 图片/视频/文件             │  │
     │  │ Timeline Cache   │  │ Social Graph         │  │ + CDN 分发               │  │
     │  │ Like/Comment     │  │ Follows/Followers    │  │ + 缩略图生成              │  │
     │  │ Hot Ranking       │  │ Interactions         │  │                          │  │
     │  └──────────────────┘  └─────────────────────┘  └──────────────────────────┘  │
     └────────────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 扇出策略 (Fanout Strategy)：写扩散 vs 读扩散

这是信息流系统最核心的架构决策。

**写扩散 (Push-based / Fanout-on-Write)：**

```
流程:
  User A 发布帖文
    → Fanout Service 查询 A 的粉丝列表
    → 将帖文 ID 推送到每个粉丝的 Feed Cache 中
    → 粉丝读取时只需查询自己的 Feed Cache

优点:
  - 读取极快: Feed 已预先构建好，O(1) 获取
  - 适合读量大，用户打开 App 后立即看到内容

缺点:
  - 写入放大: 1次写入 → N次写入 (N = 粉丝数)
  - 名人问题: 1M粉丝 = 1M次写入，延迟不可接受
  - 僵尸粉问题: 大量不活跃粉丝的 Feed 被更新，浪费资源
  - 历史粉丝: 新粉看不到关注前的内容 (可接受)

适用: 
  - 普通用户 (粉丝数 < 阈值)
```

**读扩散 (Pull-based / Fanout-on-Read)：**

```
流程:
  User B 打开信息流
    → Feed Service 查询 B 的关注列表
    → 对每个关注的人，拉取最新帖文
    → 聚合、排序、返回

优点:
  - 写入简单: 仅为作者自身的 Timeline 追加
  - 无写入放大
  - 适合名人: 无粉丝限制

缺点:
  - 读取慢: 需要查询 N 个人的最新帖文
  - 关注人数多时，读取开销大
  - 增加数据库/缓存查询数

适用:
  - 名人 (粉丝数 ≥ 阈值)
  - 用户关注人数很少的场景
```

**混合策略（Twitter / Instagram 实际方案）：**

```
┌─────────────────────────────────────────────────────┐
│               混合 Fanout 策略                         │
│                                                     │
│  ┌───────────────┐        ┌───────────────────────┐ │
│  │ 普通用户         │        │ 名人/大V               │ │
│  │ (Followers <   │        │ (Followers >=        │ │
│  │  threshold)   │        │  threshold)          │ │
│  └───────┬───────┘        └───────────┬───────────┘ │
│          │                            │             │
│          ▼                            ▼             │
│  写扩散 (Push)                   读扩散 (Pull)         │
│  推送到粉丝 Feed Cache          不推送，粉丝读取时拉取   │
│          │                            │             │
│          └──────────┬─────────────────┘             │
│                     ▼                               │
│        信息流合并 (Merge + Ranking)                    │
│        - 从 Feed Cache 获取普通用户帖文                 │
│        - 从名人帖文池实时拉取名人帖文                     │
│        - 按时间线/算法排序                             │
│        - 去重、过滤（已读、已屏蔽）                      │
│                                                     │
│  名人阈值建议:                                        │
│    - Twitter: ~100K followers                      │
│    - Instagram: ~500K followers                    │
│    - 中小规模系统: 10K followers                     │
└─────────────────────────────────────────────────────┘
```

```python
class FeedService:
    CELEBRITY_THRESHOLD = 100_000  # 粉丝阈值

    def build_feed(self, user_id: int, cursor: str, limit: int = 20):
        # 1. 从 Redis 获取用户预构建的 Feed (普通用户的写扩散内容)
        pushed_posts = self.get_pushed_feed(user_id, cursor, limit * 2)

        # 2. 获取用户关注的"名人"列表
        celebrity_followings = self.get_celebrity_followings(user_id)

        # 3. 从每个名人的时间线拉取最新帖文 (读扩散)
        pulled_posts = []
        for celeb_id in celebrity_followings:
            celeb_posts = self.get_user_recent_posts(celeb_id, cursor, limit)
            pulled_posts.extend(celeb_posts)

        # 4. 合并、去重、排序
        all_posts = pushed_posts + pulled_posts
        all_posts = self.deduplicate(all_posts)
        all_posts = sorted(all_posts, key=lambda p: p.created_at, reverse=True)

        # 5. 补充帖文详情 (作者信息、媒体URL、点赞/评论计数)
        enriched_posts = self.enrich_posts(all_posts[:limit])

        return {
            "posts": enriched_posts,
            "next_cursor": self.generate_cursor(enriched_posts[-1]),
            "has_more": len(all_posts) > limit
        }
```

### 时间线排序 vs 算法排序

```
时间线排序 (Timeline / Chronological):
  - 按时间倒序排列，简单直观
  - 用户不会错过任何内容
  - 数据一致性要求低
  - 适合 Twitter 早期、微博内容流

算法排序 (Algorithmic / Relevance-based):
  - 基于用户兴趣、互动历史、内容质量评分
  - 使用机器学习模型排序 (CTR预估)
  - 需要特征工程 + 实时排序
  - 适合 Facebook/Instagram/TikTok 推荐流

实现方式:
  ┌─────────────────────────────────────────┐
  │            Ranking Pipeline              │
  │                                         │
  │  Candidate Generation (候选生成)          │
  │    ├── 预构建 Feed (写扩散内容)            │
  │    ├── 名人内容 (读扩散)                   │
  │    ├── 热门内容 (Trending)               │
  │    └── 推荐内容 (协同过滤/内容画像)         │
  │           ↓                              │
  │  Scoring (打分)                          │
  │    ├── 相关性分数 (ML Model)              │
  │    ├── 新鲜度衰减 (Recency Decay)         │
  │    ├── 互动质量 (Engagement Quality)      │
  │    └── 多样性惩罚 (Diversity Penalty)     │
  │           ↓                              │
  │  Re-ranking (混排)                       │
  │    ├── 内容去重                           │
  │    ├── 打散同一作者                       │
  │    ├── 插入广告                           │
  │    └── 截断返回 Top-N                     │
  └─────────────────────────────────────────┘
```

### 粉丝列表分发效率优化

当用户粉丝数达到百万级别时，查一次粉丝列表进行扇出本身就是一大开销。

```python
# 优化1: 分批异步扇出
def fanout_post_async(post, batch_size=1000):
    follower_cursor = 0
    while True:
        batch = social_graph.get_followers(
            post.author_id, offset=follower_cursor, limit=batch_size
        )
        if not batch:
            break
        # 将每一批作为独立消息写入 Kafka，分散消费
        for follower_id in batch:
            kafka.produce("feed.fanout", {
                "post_id": post.id,
                "follower_id": follower_id,
                "created_at": post.created_at
            })
        follower_cursor += batch_size

# 优化2: 名人检测 + 动态切换
# 在粉丝数量超过阈值时，将用户标记为 "celebrity"
# 后续帖文不进行写扩散

# 优化3: 活跃粉丝优先
# 只对近7天活跃的粉丝进行扇出
# 不活跃粉丝下次登录时使用读扩散补数据
```

### 信息流分页 (Cursor-based Pagination)

```python
# Cursor 设计
# 格式: {created_at}_{post_id}
# 例如: "1704067200000_post_12345"

def encode_cursor(post_id: str, created_at: int) -> str:
    return f"{created_at}_{post_id}"

def decode_cursor(cursor: str) -> tuple:
    parts = cursor.split("_", 1)
    return int(parts[0]), parts[1]

# Feed 查询
def get_feed(user_id, cursor=None, limit=20):
    feed_key = f"feed:{user_id}"

    if cursor:
        created_at, post_id = decode_cursor(cursor)
        # ZREVRANGEBYSCORE: 获取 score < cursor_timestamp 的帖文
        post_ids = redis.zrevrangebyscore(
            feed_key,
            max=f"({created_at}",  # 排除当前
            min="-inf",
            start=0, num=limit
        )
    else:
        # 首次加载，获取最新的
        post_ids = redis.zrevrange(feed_key, 0, limit - 1)

    return post_ids
```

### 点赞/评论计数的高并发处理

```python
# 使用 Redis 原子操作处理高并发点赞
# 避免直接更新 MySQL (行锁竞争)

class LikeService:
    def like_post(self, user_id: int, post_id: int):
        # 1. 检查是否已点赞 (Redis Set)
        is_liked = redis.sismember(f"likes:{post_id}", user_id)
        if is_liked:
            raise AlreadyLikedError()

        # 2. 原子添加点赞
        with redis.pipeline() as pipe:
            pipe.sadd(f"likes:{post_id}", user_id)
            pipe.incr(f"like_count:{post_id}")
            pipe.execute()

        # 3. 异步写入 MySQL (最终一致)
        kafka.produce("interaction.like", {
            "post_id": post_id,
            "user_id": user_id,
            "action": "like",
            "timestamp": now()
        })

        # 4. 返回新的计数
        return redis.get(f"like_count:{post_id}")

    def get_like_count(self, post_id: int):
        # 先查 Redis，不存在则回源 MySQL
        count = redis.get(f"like_count:{post_id}")
        if count is None:
            count = db.query("SELECT like_count FROM posts WHERE id = ?", post_id)
            redis.setex(f"like_count:{post_id}", 300, count)  # 缓存5分钟
        return int(count)
```

---

## 扩展性与高可用

### 名人帖文缓存策略

```
名人帖文（读扩散内容）的缓存:

┌────────────────────────────────────────────────┐
│          名人时间线缓存结构                       │
│                                                │
│  Redis Sorted Set:                             │
│    Key:   celebrity:timeline:{user_id}          │
│    Score: created_at_timestamp                  │
│    Member: post_id                              │
│    Max Size: 500 (保留最近500条)                 │
│                                                │
│  独立 Redis 集群:                                │
│    - 名人时间线缓存在专门的高配 Redis 集群         │
│    - 与普通用户 Feed Redis 集群隔离               │
│    - 防止名人热点打垮整个集群                     │
│                                                │
│  本地缓存 (L1 Cache):                            │
│    - 顶级名人 (< 100人) 的最近帖文缓存在服务实例    │
│    - 使用 Caffeine Cache, TTL 10s              │
│    - 大幅减少 Redis 查询                        │
└────────────────────────────────────────────────┘
```

### 数据库分片策略

```
帖文分片 (Shard by post_id):
  - 一致性哈希, 1024 个虚拟节点
  - 查询单条帖文: 根据 post_id 哈希定位分片
  - 查询用户时间线: 根据 user_id 哈希定位分片
  - 帖文查询需要 JOIN 用户信息: 使用用户信息缓存避免跨分片 JOIN

社交关系分片:
  - 关注表 (follows): 按 follower_id 哈希分片
    → "我关注了谁" 查询在单个分片内完成
  - 粉丝表 (followers): 按 followee_id 哈希分片
    → "谁关注了我" / "我的粉丝" 查询在单个分片内完成
```

### 热点处理

```
热点帖文问题: 某爆款帖文被大量用户访问导致缓存热点

解决方案:
  1. 多级缓存副本 (Replication):
     - Redis 集群内复制 10+ 份缓存副本
     - Key: post:hot:{post_id}:{replica_0..N}
     - 客户端随机选取副本读取

  2. 本地缓存 (Caffeine/Guava Cache):
     - 热点帖文直接缓存在应用内存中
     - TTL 短 (5-10秒)，降低 Redis 压力

  3. CDN 缓存:
     - 纯内容帖文（非个性化）可以缓存到 CDN
     - 但点赞状态/评论数需要实时更新
     - 解决方案: 骨架屏 + 异步加载动态数据
```

### 监控与告警

```
信息流系统核心监控指标:

性能指标:
  - Feed 加载延迟 P50/P95/P99 (阈值: P99 > 500ms 告警)
  - 帖文发布延迟 P99 (阈值: > 1s 告警)
  - 扇出延迟 (帖文创建到出现在粉丝 Feed 的时间)
  - Redis 命令延迟 P99

容量指标:
  - Feed Cache 命中率 (阈值: < 95% 告警)
  - 扇出队列积压 (Kafka Lag) (阈值: > 10K 条 告警)
  - Redis 内存使用率 (阈值: > 75% 扩容)
  - 数据库连接池使用率

质量指标:
  - 空 Feed 比例
  - Feed 内容重复率
  - 用户 Feed 刷新频率
  - 互动率 (点赞率 / 评论率 / 转发率)
```

---

## 总结

信息流系统是社交网络的核心，架构挑战集中在：

1. **扇出策略**：写扩散 vs 读扩散 vs 混合策略，名人问题是标志性挑战
2. **读多写少**：读取 QPS 是写入的数百倍，缓存设计是生命线
3. **名人/大V问题**：少数用户的上亿粉丝导致写扩散不可行，需要动态策略切换
4. **实时性要求**：5秒内将新帖文呈现给粉丝，对扇出链路的延迟要求高
5. **一致性权衡**：信息流可以接受最终一致性，但帖文计数和点赞状态要求更强的一致性
6. **个性化排序**：从纯时间线到算法驱动的信息流排序，引入机器学习挑战
7. **高并发互动**：点赞、评论需要 Redis 原子操作 + 异步持久化
8. **数据分片**：帖文、关系、Feed Cache 三套存储各需独立分片策略

**面试核心权衡讨论：**
- write-time fanout vs read-time fanout 的优先级和切换条件
- 名人阈值设定依据（粉丝数、活跃度、内容频率）
- Feed 排序：时间线 vs 算法排序的工程与产品决策
- Redis Sorted Set vs Cassandra 做 Feed 存储的优缺点
- 分页策略：offset vs cursor-based pagination
- 热点缓存：复制写 vs 本地缓存的取舍
- 一致性：点赞数的强一致 vs 最终一致的选择
