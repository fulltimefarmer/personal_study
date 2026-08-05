# 设计文本分享网站 (Design Pastebin)

## 题目

设计一个文本分享网站，类似 Pastebin.com。用户可以粘贴文本/代码片段，生成唯一链接分享给他人。支持语法高亮、过期时间设置、访问权限控制。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 创建粘贴 | 用户粘贴文本，生成唯一短链接 |
| 查看粘贴 | 通过短链接访问粘贴内容 |
| 过期设置 | 设置粘贴的过期时间(10分钟/1小时/1天/1周/永久) |
| 语法高亮 | 支持常见编程语言的语法高亮 |
| 权限控制 | 支持公开/私密/密码保护 |
| 编辑/删除 | 粘贴者可以编辑或删除自己的粘贴 |
| 搜索 | 搜索公开的粘贴内容（可选） |
| 用户系统 | 注册/登录，管理个人粘贴历史 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 可用性 | 99.9% |
| 延迟 | 创建/查看 P99 < 200ms |
| 存储 | 高效存储(文本压缩)，支持过期自动清理 |
| 唯一性 | URL key 全局唯一且不可猜测 |
| 扩展性 | 支持海量粘贴内容 |
| 安全性 | 防止 XSS/内容滥用/恶意上传 |

### 容量估算

```
假设:
  - DAU: 100万
  - 每人创建 1 条粘贴/天
  - 每条粘贴平均 10KB
  - 读取是创建的 5 倍

创建 QPS: 100万 / 86400 ≈ 11.6 QPS (平均)
峰值创建: 11.6 × 3 = 34.8 QPS (创建不是瓶颈)

查看 QPS: 11.6 × 5 = 58 QPS (平均)
峰值查看: 58 × 10 = 580 QPS (热点链接峰值更高)

存储:
  日增量: 100万 × 10KB = 10GB/天
  年增量: 10GB × 365 = 3.65TB/年
  考虑压缩(gzip, 10KB -> 3KB): 1.1TB/年

  过期清理: 大部分粘贴1周后过期
  实际活跃存储: ~70GB (1周数据 × 压缩)
  + 永久存储增长: ~1.1TB/年

URL Key 分析:
  用 8位 Base62: 62^8 ≈ 218万亿 种组合
  每天使用: 100万
  碰撞概率: 几乎为0 (365亿年才可能碰撞一次)
  短链长度: 8字符 (如: aB3xK9mW)
```

---

## API设计

### REST API

```
=== 创建粘贴 ===
POST /api/v1/pastes
Content-Type: application/json

{
  "title": "nginx.conf",
  "content": "server {\n    listen 80;\n    server_name example.com;\n    ...\n}",
  "language": "nginx",           // 语法高亮语言
  "expiration": "1w",            // 10m/1h/1d/1w/1M/never
  "exposure": "public",          // public/unlisted/private
  "password": null,              // 可选密码
  "burn_after_read": false       // 阅后即焚
}

Response:
{
  "paste_id": "aB3xK9mW",
  "url": "https://paste.example.com/aB3xK9mW",
  "raw_url": "https://paste.example.com/aB3xK9mW/raw",
  "title": "nginx.conf",
  "language": "nginx",
  "created_at": "2025-01-01T10:00:00Z",
  "expires_at": "2025-01-08T10:00:00Z",
  "is_editable": true,
  "edit_token": "eyJhbG..."     // 用于后续编辑/删除
}

=== 查看粘贴 ===
GET /api/v1/pastes/{paste_id}
Authorization: Bearer {token}   // 可选, 用于访问私有粘贴

Response (公开粘贴):
{
  "paste_id": "aB3xK9mW",
  "title": "nginx.conf",
  "content": "server {\n    listen 80;\n    ...\n}",
  "language": "nginx",
  "highlighted_html": "<pre class='nginx'>...",
  "created_at": "2025-01-01T10:00:00Z",
  "expires_at": "2025-01-08T10:00:00Z",
  "views": 42,
  "author": { "username": "jun", "avatar": "..." },  // 如果登录
  "is_editable": false
}

=== 获取原始内容 ===
GET /api/v1/pastes/{paste_id}/raw
Response: text/plain; charset=utf-8

    server {
        listen 80;
        server_name example.com;
    ...

=== 删除粘贴 ===
DELETE /api/v1/pastes/{paste_id}
Authorization: Bearer {edit_token}

=== 编辑粘贴 ===
PUT /api/v1/pastes/{paste_id}
Authorization: Bearer {edit_token}
{
  "content": "...",
  "language": "python"
}

=== 密码保护粘贴 ===
POST /api/v1/pastes/{paste_id}/unlock
{
  "password": "secret123"
}
Response: { "access_token": "xxx", "expires_in": 3600 }

=== 用户粘贴列表 ===
GET /api/v1/users/{user_id}/pastes?page=1&size=20

=== 搜索 ===
GET /api/v1/search?q=nginx+config&language=nginx&page=1
```

---

## 数据模型

### 数据库设计

```sql
-- ============ 粘贴主表 ============
CREATE TABLE paste (
    paste_id        VARCHAR(16) PRIMARY KEY,    -- aB3xK9mW (8位 Base62)
    user_id         BIGINT,                     -- NULL = 匿名用户
    title           VARCHAR(256),
    content_hash    VARCHAR(64) NOT NULL,       -- SHA-256 去重
    language        VARCHAR(32) DEFAULT 'text',
    exposure        VARCHAR(16) DEFAULT 'public', -- public/unlisted/private
    password_hash   VARCHAR(256),               -- bcrypt hash, NULL=无密码
    burn_after_read TINYINT DEFAULT 0,
    view_count      INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP,                  -- NULL=永不过期
    is_deleted      TINYINT DEFAULT 0,
    deleted_at      TIMESTAMP,

    INDEX idx_user (user_id, created_at),
    INDEX idx_language (language, exposure, created_at),
    INDEX idx_expires (expires_at, is_deleted),
    INDEX idx_created (created_at)
);

-- ============ 粘贴内容表 (分离大字段) ============
CREATE TABLE paste_content (
    paste_id        VARCHAR(16) PRIMARY KEY,
    content         MEDIUMTEXT NOT NULL,        -- 最大 16MB
    content_size    INT NOT NULL,               -- 原始大小(字节)
    compressed      TINYINT DEFAULT 1,
    compressed_size INT,                        -- 压缩后大小
    highlighted_html MEDIUMTEXT,                -- 预渲染语法高亮HTML
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (paste_id) REFERENCES paste(paste_id)
);

-- ============ 用户表 ============
CREATE TABLE user (
    user_id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(32) UNIQUE NOT NULL,
    email           VARCHAR(128) UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    avatar_url      VARCHAR(512),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ 访问日志 (可选, 用于统计) ============
CREATE TABLE paste_access_log (
    log_id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    paste_id        VARCHAR(16) NOT NULL,
    viewer_ip       VARCHAR(45),
    viewer_country  VARCHAR(64),
    user_agent      VARCHAR(512),
    referer         VARCHAR(1024),
    accessed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_paste (paste_id, accessed_at)
) PARTITION BY RANGE (TO_DAYS(accessed_at));

-- ============ 搜索索引 (可选, 供ES) ============
-- paste_search 索引通过 Elasticsearch 维护
```

### 存储分级

```
=== 热数据 (Redis) ===
- 最近 1小时创建/被访问的粘贴
- Key: paste:{paste_id}
  - 缓存内容 + 元数据
  - TTL: 如果 expire < 1小时, 则TTL=expire; 否则 TTL=1小时

- Key: paste:{paste_id}:view_count
  - 访问计数(原子递增)
  - 定期同步回 MySQL

- Key: paste:recent:public
  - ZSET, 最近公开粘贴列表
  - score=timestamp, 定期刷新

=== 温数据 (MySQL) ===
- 大部分粘贴 (1小时 ~ 7天)
- 按 expires_at 索引方便清理

=== 冷数据 (对象存储 S3/OSS) ===
- 过期但尚未物理删除的粘贴(30天宽限期)
- 访问量极低的旧粘贴(> 30天)
- 归档/备份数据
```

### URL Key 生成

```
=== URL Key 生成策略 ===

方案A: 随机 Base62 (推荐)
  function generatePasteId(length=8):
      chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
      id = ""
      bytes = secureRandom(length)  // 密码学安全随机数
      for byte in bytes:
          id += chars[byte % 62]
      return id

  冲突检测: INSERT 失败 -> 重新生成 -> 重试(最多3次)
  
方案B: Snowflake + Base62 编码
  snowflakeId = snowflake.nextId()
  pasteId = base62Encode(snowflakeId)
  // 长度: 11-12个字符
  // 趋势递增 (可猜测)

方案C: Hash 取前 N 位
  pasteId = SHA256(content + userId + timestamp)[:8]
  // 内容+用户+时间 确定后 ID 确定, 天然去重

推荐方案A:
  - 短(8字符)
  - 不可猜测(安全)
  - 足够大的空间(62^8=218万亿)
  - 碰撞重试简单(INSERT失败再生成)
```

---

## 高层次架构

### 系统架构图

```
+------------------------------------------------------------------+
|                        CDN (CloudFlare)                           |
|                (静态资源 + 公开粘贴内容缓存)                        |
+------------------------------+-----------------------------------+
                               |
+------------------------------v-----------------------------------+
|                       Load Balancer (Nginx)                       |
+------+-----------+-----------+-----------+-----------+-----------+
       |           |           |           |           |
+------v-----+ +---v------+ +-v--------+ +v--------+ +v----------+
| API        | | Paste    | | User     | | Search  | | Render    |
| Gateway    | | Service  | | Service  | | Service | | Service   |
| (限流/鉴权)| |          | |          | | (ES)    | | (语法高亮) |
+------+-----+ +----+-----+ +----+-----+ +----+----+ +----+------+
       |            |            |            |            |
       +------+-----+------+-----+------+-----+------+-----+
              |            |            |            |
+-------------v------------v------------v------------v-------------+
|                        数据/存储层                                 |
|  +----------+  +----------+  +----------+  +------------------+  |
|  | Redis    |  | MySQL    |  | ES       |  | Object Storage   |  |
|  | (热缓存)  |  | (元数据)  |  | (搜索)    |  | (冷数据/大文件)   |  |
|  +----------+  +----------+  +----------+  +------------------+  |
+------------------------------------------------------------------+

+--------------------------+     +-------------------------------+
|   定时任务 (Scheduler)    |     |   后台 Job                      |
|  - 过期清理 (每分钟)      |     |  - 语法高亮预渲染               |
|  - 冷热数据迁移          |     |  - 内容安全扫描                 |
|  - 统计汇总              |     |  - ES 索引更新                  |
+--------------------------+     +-------------------------------+
```

### 核心流程

```
=== 创建粘贴流程 ===

用户                API GW            Paste Service        MySQL        Redis       Render
  |                    |                    |                 |            |            |
  | POST /pastes       |                    |                 |            |            |
  |------------------->|                    |                 |            |            |
  |                    | 鉴权 + 限流         |                 |            |            |
  |                    | 内容大小检查(16MB)  |                 |            |            |
  |                    |-------------------->|                 |            |            |
  |                    |                    |                 |            |            |
  |                    |                    | ① 内容安全检测   |            |            |
  |                    |                    | (敏感词/恶意)    |            |            |
  |                    |                    |                 |            |            |
  |                    |                    | ② 生成 paste_id  |            |            |
  |                    |                    | secureRandom(8)  |            |            |
  |                    |                    |                 |            |            |
  |                    |                    | ③ 内容压缩(gzip) |            |            |
  |                    |                    |                 |            |            |
  |                    |                    | ④ INSERT paste  |            |            |
  |                    |                    | INSERT content  |            |            |
  |                    |                    |---------------->|            |            |
  |                    |                    | <-- OK          |            |            |
  |                    |                    |                 |            |            |
  |                    |                    | ⑤ 预热缓存       |            |            |
  |                    |                    |--------------------------->|            |
  |                    |                    |                 | SET paste:id ...     |
  |                    |                    |                 | TTL=expire|1h  |
  |                    |                    |                 |            |            |
  |                    |                    | ⑥ 异步语法高亮   |            |            |
  |                    |                    |--------------------------------------->|
  |                    |                    |                 |            |  渲染HTML  |
  |                    |                    |                 |            |  UPDATE DB |
  |                    |                    |                 |            |            |
  |                    | <-- 返回 paste_id  |                 |            |            |
  | <-- JSON Response  |                    |                 |            |            |
  | (paste_id + URL)   |                    |                 |            |            |

=== 查看粘贴流程 ===

用户                CDN/Cache          API GW         Paste Service     Redis
  |                    |                  |                |              |
  | GET /aB3xK9mW       |                  |                |              |
  |-------------------->|                  |                |              |
  |                    | 公开内容命中缓存?  |                |              |
  |                    | Yes -> 直接返回    |                |              |
  | <-- HTML -----------|                  |                |              |
  |                    |                  |                |              |
  |                    | No (缓存未命中)   |                |              |
  |                    |------------------>|                |              |
  |                    |                  | 查询粘贴        |              |
  |                    |                  |--------------->|              |
  |                    |                  |                | 查 Redis     |
  |                    |                  |                |------------->|
  |                    |                  |                | 命中 -> 返回  |
  |                    |                  |                |<-------------|
  |                    |                  |                |              |
  |                    |                  |                | 未命中       |
  |                    |                  |                | 查 MySQL     |
  |                    |                  |                | 检查过期     |
  |                    |                  |                | 检查权限     |
  |                    |                  |                |              |
  |                    |                  |                | 更新访问计数  |
  |                    |                  |                | INCR view    |
  |                    |                  |                |-------------->
  |                    |                  |                |              |
  |                    |                  |                | 回填缓存      |
  |                    |                  |                | SET paste:id |
  |                    |                  |                |-------------->
  |                    |                  |                |              |
  |                    |                  | <-- 粘贴内容 ---|              |
  | <-- HTML (语法高亮)  |                  |                |              |
```

---

## 核心深入

### 1. 内容存储优化

```
=== 压缩策略 ===

文本压缩效率:
  gzip(level=6): 源文本 10KB -> 压缩后 ~3KB (30%)
  Brotli:       源文本 10KB -> 压缩后 ~2.5KB (25%) 更慢
  LZ4:          源文本 10KB -> 压缩后 ~4KB (40%) 最快

推荐: 
  - 存储前 gzip 压缩
  - CDN 传输时 Brotli 动态压缩
  - API 返回: Accept-Encoding: gzip, br

=== 大文本处理 ===

if content_size <= 64KB:
    直接存入 MySQL paste_content.content (MEDIUMTEXT)
    缓存到 Redis (String, 大小合适)
    
elif 64KB < content_size <= 1MB:
    仍存 MySQL, 但不缓存完整内容到 Redis
    Redis 只缓存元数据
    
elif 1MB < content_size <= 16MB:
    存入对象存储 (S3/OSS)
    MySQL paste_content.content 存 S3 Key
    不再缓存内容
    
else:
    return 413 Payload Too Large
```

### 2. 语法高亮

```
=== 方案对比 ===

+-------------------+------------------+------------------+------------------+
| 方案              | 优点             | 缺点              | 延迟             |
+-------------------+------------------+------------------+------------------+
| 服务端预渲染       | 客户端负载低      | 存储翻倍          | 展示 O(1)        |
| (存highlighted_html)| 一致性高        | 更新需重建        | 创建慢            |
+-------------------+------------------+------------------+------------------+
| 客户端渲染         | 无需额外存储      | 客户端CPU消耗     | 展示 O(N)        |
| (JS高亮库)         | 语言包灵活        | 首屏白屏          | 首次下载大        |
+-------------------+------------------+------------------+------------------+
| 混合方案(推荐)     | 首次快 + 灵活     | 架构复杂          | 首次 O(1)        |
| 预渲染 + 客户端降级|                  |                  | 编辑 O(N)        |
+-------------------+------------------+------------------+------------------+

=== 异步预渲染 ===

创建粘贴后:
  1. 立即返回 paste_id (不等待高亮)
  2. 异步消息 -> Render Service:
     - 下载原始内容
     - 使用 Pygments / highlight.js 服务端渲染 HTML
     - 存入 MySQL paste_content.highlighted_html
     - 更新 Redis 缓存
  3. 前端: 渲染时先展示原始文本(无高亮)
     检测到 highlighted_html 可用后替换

=== 流式渲染 ===
  // 对于大文本, 按行流式渲染和传输
  // 避免服务端消耗大量内存
  async function* streamHighlighted(content, language):
      for line in content.split('\n'):
          yield highlightLine(line, language)
```

### 3. 过期清理机制

```
=== 清理策略 ===

方案A: 定时扫描 (简单)
  // 每分钟扫描一次
  SELECT paste_id FROM paste
  WHERE expires_at < NOW()
    AND is_deleted = 0
  LIMIT 1000

  for each paste:
      paste.is_deleted = 1
      paste.deleted_at = NOW()
      DELETE FROM paste_content WHERE paste_id = ?
      redis.del("paste:" + paste_id)

  优点: 实现简单
  缺点: 扫描开销随数据量增长

方案B: 延迟清理 + 访问时判断 (推荐)
  // 不主动扫描, 访问时检查过期
  function getPaste(pasteId):
      paste = cache.get(pasteId) or db.get(pasteId)
      if paste == null:
          return 404
      
      if paste.expiresAt != null and now() > paste.expiresAt:
          markDeleted(paste)  // 懒删除
          return 410 Gone  // 比 404 更语义化
      
      return paste

  // 后台每小时清理一批已过期但未被标记的
  // 确保存储不会无限增长

方案C: MySQL Event Scheduler
  CREATE EVENT clean_expired_pastes
  ON SCHEDULE EVERY 1 HOUR
  DO
      UPDATE paste SET is_deleted = 1, deleted_at = NOW()
      WHERE expires_at < NOW() AND is_deleted = 0
      LIMIT 10000;

  然后逐步删除 paste_content

=== 多级过期 ===
  过期后 24小时: 软删除 (is_deleted=1), 仍可查看(显示"已过期")
  软删除后 30天: 物理删除 content, 只留元数据
  物理删除 content 后 7天: 彻底删除所有数据
  (根据当地法规调整数据保留期限)
```

### 4. 内容去重

```
=== 内容去重策略 ===

创建粘贴时:
  1. content_hash = SHA256(content)
  2. 查询: SELECT paste_id FROM paste WHERE content_hash = ?
     AND is_deleted = 0 AND (expires_at IS NULL OR expires_at > NOW())
  3. 如果存在相同内容的有效粘贴:
     return 200 OK + 已有 paste_id (指向已存在的粘贴)
     // 而不是创建新粘贴
  4. 如果不存在:
     创建新粘贴

=== 去重 vs 用户体验 ===
  问题: 用户修改已有粘贴的一个字符 -> 不应返回旧链接
  
  解决:
    - 只有显式创建新粘贴时才去重
    - 编辑(update)不去重(更新当前粘贴)
    - 设置选项: POST /pastes?dedup=true (默认开启)
    
=== 去重取消 ===
  当粘贴被编辑后:
    更新 content_hash
    已有的去重链接不再指向它
    提示用户: "还有其他 N 个链接指向相同内容"
```

### 5. 防滥用

```
=== 内容安全 ===

1. 上传限制:
   - 未登录用户: 最大 512KB, 每小时最多 10 条
   - 已登录用户: 最大 16MB, 每分钟最多 5 条
   - VIP用户: 最大 32MB, 无频率限制

2. 内容扫描:
   - 敏感词过滤 (关键词库)
   - 恶意软件签名检测(如果包含 base64 编码文本)
   - 图片链接检测(防止钓鱼)
   - 异步 AI 模型检测(违规内容标记)

3. Rate Limiting:
   // Redis Token Bucket
   key = "rate_limit:" + (userId or ip)
   allowed = ratelimit.check(key, max_requests=10, window=60s)
   if not allowed:
       return 429 Too Many Requests

4. IP 黑名单:
   短时间内大量创建 -> 自动封禁 30分钟
   重复违规 -> 永久封禁

5. XSS 防护:
   - 存储 raw 内容, 展示时转义
   - Content-Security-Policy header
   - 内容中使用 CSP nonce/token

=== 滥发检测 ===
  监控指标:
    - 同一 IP 创建频率
    - 相同内容哈希创建频率
    - 新用户创建速率
    - 包含 URL 比例过高
    - 包含特定关键词(色情/暴力/政治敏感)
```

### 6. 短链接优化

```
=== 短链接 vs 短随机 ID ===

# 极短链接 (如 pastebin.com/xH7k)
优点: 美观、易分享
缺点: ID 空间小(62^4=1476万), 容易碰撞, 可遍历

# 中短链接 (如 pastebin.com/aB3xK9mW)  ← 推荐
优点: 足够空间(62^8=218万亿), 不可遍历
缺点: 稍微长一点

# 自定义短链 (如 pastebin.com/my-nginx-config)
优点: 用户友好, 可记忆
缺点: 需要额外验证唯一性, 防止占坑

=== 自定义短链实现 ===
CREATE TABLE paste_alias (
    alias           VARCHAR(32) PRIMARY KEY,
    paste_id        VARCHAR(16) NOT NULL,
    user_id         BIGINT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_paste (paste_id),
    INDEX idx_user (user_id)
);

POST /api/v1/pastes/{paste_id}/alias
{ "alias": "my-nginx-config" }

// 检查: 
// - 不允许已存在的 alias
// - 不允许黑名单词 (admin, api, login, ...)
// - 正则: [a-zA-Z0-9_-]{3,32}
```

---

## 扩展性与高可用

### 1. 数据库扩展

```
=== 分库分表 ===

按 paste_id 哈希分库:
  dbIndex = hash(paste_id[0:4]) % 16
  保证了基于 paste_id 的查询直接路由到单库

按时间分表 (paste + paste_content):
  paste_2025Q1, paste_2025Q2, ...
  方便历史数据归档和过期数据清理

=== 读写分离 ===
+----------+   异步复制   +----------+
|  Master  | -----------> |  Slave   |
|  (写)    |              |  (读)    |
+----------+              +----------+
      ^                        ^
      |                        |
  创建粘贴                   查看粘贴
  编辑粘贴                   列表查询
  删除粘贴

=== 只读与自动故障切换 ===
  - P99 写入延迟 < 50ms (单表写入)
  - P99 读取延迟 < 20ms (Slave + Redis 缓存)
```

### 2. CDN 缓存策略

```
=== CDN 缓存规则 ===

静态资源 (CSS/JS/图片):
  Cache-Control: public, max-age=31536000, immutable
  文件名加哈希: main.a1b2c3d4.js

公开粘贴页面 (HTML):
  Cache-Control: public, max-age=300, s-maxage=300  // 5min
  过期后回源验证 (ETag/If-None-Match)

原始内容 (raw):
  Cache-Control: public, max-age=86400  // 1天
  因为粘贴创建后不会再变

私有/密码保护粘贴:
  Cache-Control: private, no-cache, no-store
  不缓存 (每次回源验证权限)

=== CDN 热度分层 ===
  高热度粘贴 (> 1000 views/day):
    - 预推送到 Edge CDN 节点
    - 全球用户就近访问

  普通公开粘贴:
    - 首次访问回源, 后续 CDN 缓存
    - 15天无人访问 -> CDN Purge
```

### 3. 监控与备份

```
=== 关键指标 ===

业务:
  - 创建速率 (按用户类型: 匿名/注册/VIP)
  - 查看量 (按粘贴类型: 公开/私密)
  - 过期删除数量
  - 访问量 Top 粘贴
  - 内容安全标记率

技术:
  - API P99 延迟 (创建/查看/搜索)
  - Redis 命中率 / 内存使用
  - MySQL QPS / 慢查询 / 主从延迟
  - CDN 缓存命中率
  - 文件存储 (S3) 增长
  - 语法高亮队列延迟

告警:
  - API 错误率 > 1%
  - P99 延迟 > 500ms
  - Redis 命中率 < 80%
  - 内容滥用检测命中率突增
  - 存储空间增长异常(> 正常2倍)
  - 过期清理失败超过 3 次

=== 备份策略 ===
  MySQL: 每日全量备份 + 实时 Binlog 备份
  Redis: RDB 快照 (每6小时) + AOF (everysec)
  S3/OSS: 跨区域复制 (自动)
  ES: Snapshot 到 S3 (每日)

=== 灾难恢复 ===
  MySQL 从备份恢复: < 1小时 (全量 + Binlog replay)
  Redis 从 AOF/RDB 恢复: < 10分钟
  服务无状态: 自动水平扩展, 零恢复时间
```

---

## 总结

设计 Pastebin 需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **ID生成** | 随机 Base62 (8字符) — 短 + 安全 + 不碰撞 |
| **内容存储** | 分离元数据(MySQL) + 内容(MySQL/S3 按大小分级) + gzip压缩 |
| **语法高亮** | 服务端预渲染(首次展示) + 异步更新(编辑后) |
| **缓存** | CDN公开缓存 + Redis热缓存 + 按访问频率动态调整 |
| **过期清理** | 访问时懒检查 + 后台定时清理 + 多级过期 |
| **去重** | SHA256 内容哈希 + 显式去重选项 |
| **安全** | 速率限制 + 内容扫描 + XSS防护 + 短ID防遍历 |
| **扩展** | 按paste_id哈希分库 + 按时间分表 + 冷热数据分离存储 |

关键面试问答：
1. **如何保证短链接唯一且不可猜测？** — 密码学安全随机数生成8位Base62，碰撞概率极低，重试INSERT处理碰撞
2. **过期粘贴怎么清理？** — 懒删除(访问时检查) + 定时任务批量处理 + 多级过期(软删->物删)
3. **如何支持大文本粘贴？** — 分级存储: ≤64KB存MySQL+Redis, ≤1MB存MySQL(不缓存), ≤16MB存S3
4. **内容去重怎么实现？** — SHA256 哈希 + MySQL索引查询 + 相同内容返回同一链接
5. **如何防滥用？** — 速率限制(匿名vs注册vsVIP) + 内容扫描 + IP黑名单 + CAPTCHA
6. **CDN缓存策略？** — 公开内容缓存5分钟(回源验证) + 私有内容不缓存 + 原始内容缓存24小时
