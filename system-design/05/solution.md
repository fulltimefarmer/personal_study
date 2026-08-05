# 05. 设计视频流平台 (Design Video Streaming Platform)

## 题目

设计一个类似 YouTube / Netflix 的视频流平台，支持视频上传、存储、转码、自适应码率流播放（ABR Streaming）、CDN 分发等功能。

---

## 需求澄清

### 功能性需求

1. **视频上传**：用户上传视频文件，支持断点续传
2. **视频转码**：上传后自动转码为多种分辨率/码率（480p, 720p, 1080p, 4K）
3. **自适应流播放 (ABR Streaming)**：客户端根据网络状况自动切换清晰度
4. **视频播放**：支持播放、暂停、进度条拖动、倍速播放
5. **缩略图生成**：自动生成视频缩略图和预览动图
6. **视频搜索与推荐**：基于标题、描述、标签的搜索和推荐
7. **评论、点赞、订阅**：社区互动功能
8. **视频管理**：创作者可管理视频（删除、编辑元数据、查看分析）

### 非功能性需求

1. **低延迟播放**：首帧时间（Time to First Frame） < 1s
2. **高可用**：99.95%+（视频播放核心链路）
3. **高并发**：支持百万级并发播放
4. **多设备适配**：Web、iOS、Android、Smart TV、游戏主机
5. **全球分发**：全球低延迟访问
6. **版权保护**：DRM 支持（Widevine, FairPlay, PlayReady）
7. **存储可靠性**：原始视频 99.999999999%（11个9）持久性

### 容量估算

**假设条件：**
- DAU: 2 亿
- 每日新增视频: 50 万
- 平均视频时长: 10 分钟
- 平均上传大小: 1GB（原始 1080p）
- 转码后平均总大小: 500MB（多码率 + 缩略图）
- 日均播放次数: 20 亿次（每用户 10 次）
- 平均每次播放时长: 5 分钟
- 峰值并发: 1000 万用户同时播放

**存储估算：**
- 日上传存储(原始): 50万 × 1GB = 500 TB/天
- 日转码存储: 50万 × 500MB = 250 TB/天
- 总新增/天: 750 TB/天
- 年存储增量: 750TB × 365 ≈ **274 PB/年**
- 5 年存储（含副本）: 274PB × 5 × 3 ≈ **4.1 EB**

**带宽估算：**
- 平均视频码率: 3 Mbps（混合 480p~1080p 用户）
- 峰值并发带宽: 1000万 × 3Mbps = **30 Tbps**
- 日均总流量: 20亿 × 5分钟 × 3Mbps / 8 = **22.5 PB/天**

**转码算力估算：**
- 每视频转码时间: 原始时长 × (分辨率数) × (设备类型数)
- 粗略估算: 50万视频 × 10分钟 × 3 ≈ 1,500万转码分钟/天
- 需要约 10,000+ 台转码服务器

---

## API 设计

### 视频管理 API

```
1. 视频上传（分块上传 / 断点续传）
POST /api/v1/videos/upload/init
Authorization: Bearer <token>

Request:
{
  "title": "我的旅行 Vlog",
  "description": "2025 年日本之旅",
  "tags": ["travel", "japan", "vlog"],
  "category": "Travel",
  "file_size": 1073741824,   // 1GB
  "mime_type": "video/mp4",
  "visibility": "public"     // public | unlisted | private
}

Response: 201
{
  "video_id": "vid_abc123",
  "upload_url": "https://upload.cdn.com/vid_abc123",
  "upload_id": "upload_xyz",
  "chunk_size": 5242880     // 5MB per chunk, 建议分块大小
}

2. 上传分块
PUT https://upload.cdn.com/vid_abc123?part=1&upload_id=upload_xyz
Content-Type: application/octet-stream
Content-Range: bytes 0-5242879/1073741824

[Binary Data]

Response: 200
{
  "part": 1,
  "etag": "md5_hash_of_part",
  "uploaded_bytes": 1073741824
}

3. 完成上传
POST /api/v1/videos/upload/complete
{
  "video_id": "vid_abc123",
  "upload_id": "upload_xyz",
  "parts": [
    {"part": 1, "etag": "md5_1"},
    {"part": 2, "etag": "md5_2"},
    ...
  ]
}

Response: 200
{
  "video_id": "vid_abc123",
  "status": "processing",  // queued → transcoding → ready
  "estimated_ready_at": 1704070800000
}

4. 获取视频信息
GET /api/v1/videos/vid_abc123

Response:
{
  "video_id": "vid_abc123",
  "title": "我的旅行 Vlog",
  "description": "...",
  "duration_seconds": 600,
  "status": "ready",
  "thumbnail_url": "https://img.cdn.com/vid_abc123/thumb.jpg",
  "streaming_urls": {
    "hls": "https://stream.cdn.com/vid_abc123/master.m3u8",
    "dash": "https://stream.cdn.com/vid_abc123/master.mpd"
  },
  "available_qualities": ["240p", "360p", "480p", "720p", "1080p"],
  "view_count": 10234,
  "like_count": 456,
  "created_at": 1704067200000
}

5. 视频播放（获取流地址）
GET /api/v1/videos/vid_abc123/playback
Authorization: Bearer <token>  // 可选，用于 DRM token

Response:
{
  "manifest_url": "https://stream.cdn.com/vid_abc123/master.m3u8?token=xxx",
  "drm_license_url": "https://drm.service.com/license?video=vid_abc123",
  "max_quality": "1080p",
  "preview_thumbnails": "https://img.cdn.com/vid_abc123/sprite.vtt"
}
```

### 搜索与推荐 API

```
1. 搜索视频
GET /api/v1/search?q=旅行vlog&page_token=xxx&sort=relevance

Response:
{
  "results": [...],
  "total_count": 1234,
  "next_page_token": "yyy"
}

2. 推荐视频（首页）
GET /api/v1/recommendations?user_id=u_123&limit=20

Response:
{
  "videos": [...],
  "recommendation_reason": "Because you watched..."
}
```

---

## 数据模型

### 核心数据表

```sql
-- 视频元数据表
CREATE TABLE videos (
    video_id VARCHAR(32) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSON,
    category VARCHAR(64),
    duration_seconds INT,
    original_file_size BIGINT,
    original_file_path VARCHAR(512),
    status ENUM('uploading','queued','transcoding','ready','failed') DEFAULT 'uploading',
    visibility ENUM('public','unlisted','private') DEFAULT 'public',
    thumbnail_path VARCHAR(512),
    available_qualities JSON,
    view_count BIGINT DEFAULT 0,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_status (status),
    INDEX idx_created (created_at DESC)
);

-- 转码任务表
CREATE TABLE transcode_jobs (
    job_id VARCHAR(64) PRIMARY KEY,
    video_id VARCHAR(32) NOT NULL,
    quality VARCHAR(16) NOT NULL,  -- '240p','360p','480p','720p','1080p','4K'
    codec VARCHAR(32) DEFAULT 'h264',
    status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    input_path VARCHAR(512),
    output_path VARCHAR(512),
    segment_duration INT DEFAULT 6,  -- HLS 分片时长（秒）
    progress FLOAT DEFAULT 0,
    error_message TEXT,
    started_at BIGINT,
    completed_at BIGINT,
    INDEX idx_video (video_id),
    INDEX idx_status (status)
);

-- 缩略图/故事板 (Sprite Sheet)
CREATE TABLE thumbnails (
    video_id VARCHAR(32) NOT NULL,
    type ENUM('poster','sprite') NOT NULL,
    width INT,
    height INT,
    interval_seconds FLOAT,  -- 缩略图间隔（仅 sprite）
    file_path VARCHAR(512),
    PRIMARY KEY (video_id, type)
);

-- 播放事件表（分析用）
CREATE TABLE playback_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(32) NOT NULL,
    user_id BIGINT,
    session_id VARCHAR(64),
    event_type ENUM('play','pause','seek','buffer','quality_change','complete'),
    position_seconds INT,
    quality VARCHAR(16),
    buffering_ms INT,
    device_type VARCHAR(32),
    country CHAR(2),
    timestamp BIGINT NOT NULL,
    INDEX idx_video_time (video_id, timestamp),
    INDEX idx_user_time (user_id, timestamp)
) ENGINE=InnoDB
PARTITION BY RANGE (timestamp) (...);
```

---

## 高层次架构

```
                              ┌────────────────────────────────────────────────┐
                              │                   Clients                       │
                              │        (Web, iOS, Android, Smart TV)           │
                              └───────┬───────────────────────┬────────────────┘
                                      │                       │
                         ┌────────────▼───────────┐  ┌───────▼──────────────────┐
                         │    视频上传服务          │  │    视频播放服务            │
                         │  ┌──────────────────┐  │  │  ┌────────────────────┐  │
                         │  │ Upload Gateway   │  │  │  │ Playback API        │  │
                         │  │ (分块/断点续传)    │  │  │  │ (鉴权/DRM Token)    │  │
                         │  └────────┬─────────┘  │  │  └─────────┬──────────┘  │
                         └───────────┼────────────┘  └────────────┼─────────────┘
                                     │                             │
                         ┌───────────▼─────────────────────────────▼─────────────┐
                         │                   消息队列 (Kafka)                       │
                         │  ┌───────────────────┐  ┌─────────────────────────┐   │
                         │  │ video.uploaded     │  │ video.transcode.request  │   │
                         │  │ Topic              │  │ Topic                     │   │
                         │  └───────────────────┘  └─────────────────────────┘   │
                         └───────────────────────────┬───────────────────────────┘
                                                     │
                         ┌───────────────────────────▼───────────────────────────┐
                         │                   转码流水线                              │
                         │                                                        │
                         │  ┌──────────────┐   ┌──────────────┐   ┌───────────┐ │
                         │  │ Transcode    │──▶│ Package      │──▶│ Thumbnail │ │
                         │  │ (FFmpeg/GPU) │   │ (HLS/DASH)   │   │ Generator │ │
                         │  └──────┬───────┘   └──────┬───────┘   └─────┬─────┘ │
                         │         │                  │                 │       │
                         └─────────┼──────────────────┼─────────────────┼───────┘
                                   │                  │                 │
                         ┌─────────▼──────────────────▼─────────────────▼───────┐
                         │                   对象存储 (S3/OSS)                      │
                         │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
                         │   │ 原始视频   │  │ 转码输出  │  │ 缩略图/Sprite     │   │
                         │   │ (Hot)    │  │ (Standard)│  │ (Standard)       │   │
                         │   └──────────┘  └──────────┘  └──────────────────┘   │
                         └──────────────────────┬────────────────────────────────┘
                                                │
                         ┌──────────────────────▼────────────────────────────────┐
                         │                CDN (Akamai / CloudFront)                │
                         │                                                        │
                         │  ┌──────────────────┐        ┌──────────────────┐     │
                         │  │ Edge POP Asia     │        │ Edge POP US       │     │
                         │  │ - HLS segments    │        │ - HLS segments    │     │
                         │  │ - DASH segments   │        │ - DASH segments   │     │
                         │  │ - Thumbnails      │        │ - Thumbnails      │     │
                         │  └──────────────────┘        └──────────────────┘     │
                         └───────────────────────────────────────────────────────┘
```

---

## 核心深入

### 视频协议：HLS vs DASH vs Progressive Download

| 特性 | Progressive Download | HLS (HTTP Live Streaming) | MPEG-DASH |
|------|---------------------|---------------------------|-----------|
| 开发方 | N/A | Apple | MPEG |
| 支持平台 | 所有 | iOS/macOS 原生，其他需 JS | Android 原生，其他需 JS |
| 自适应码率 | ❌ | ✅ | ✅ |
| 分片格式 | 单文件 | .ts 分片 | .m4s 分片 |
| 清单文件 | 无 | .m3u8 (文本) | .mpd (XML) |
| 加密 | 无原生支持 | AES-128 / SAMPLE-AES | Common Encryption (CENC) |
| 延迟 | 需要缓冲 | 6-30s (HLS Low Latency: 2-8s) | 标准6-30s, LL-DASH: 1-3s |
| 直播支持 | ❌ | ✅ | ✅ |
| 推荐 | 传统短视频 | **最广泛兼容** | 开放标准 |

**推荐策略**：同时输出 HLS + DASH，客户端根据平台选择最合适的协议。

```
HLS Master Playlist (master.m3u8) 示例:
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.4d401e,mp4a.40.2"
360p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720,CODECS="avc1.4d401f,mp4a.40.2"
720p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS="avc1.4d4028,mp4a.40.2"
1080p/index.m3u8

Sub Playlist (720p/index.m3u8) 示例:
#EXTM3U
#EXT-X-TARGETDURATION:6
#EXT-X-VERSION:3
#EXTINF:6.0,
720p_seg_001.ts
#EXTINF:6.0,
720p_seg_002.ts
...
#EXT-X-ENDLIST
```

### 自适应码率 (ABR) 算法

播放器端的 ABR (Adaptive Bitrate) 算法决定何时切换码率：

```
ABR 算法核心逻辑:

1. Buffer-Based (基于缓冲区):
   - buffer > 30s: 提升码率
   - buffer < 10s: 降低码率
   - buffer < 5s: 紧急降级

2. Throughput-Based (基于吞吐量):
   - 根据最近 N 个分片的下载速度估算带宽
   - 选择低于估算带宽最高可用码率
   - EWMA 平滑: throughput = α * current + (1-α) * previous

3. Hybrid (混合, BOLA/MPC 等):
   - BOLA (Buffer Occupancy based Lyapunov Algorithm):
     - 效用函数: utility = (bitrate) / (1 + e^(-buffer))
     - 最大化视频质量的同时避免缓冲
   
4. 传统 YouTube 策略 (简化):
   - 开始时选择最低码率 (快速起播)
   - 5秒后切换到估算带宽的合适码率
   - 保守升码率 (需要持续足够带宽 proof)
   - 激进降码率 (任何缓冲立即降级)
```

```python
class SimpleABRController:
    def __init__(self):
        self.throughput_ewma = None  # 平滑带宽估计
        self.alpha = 0.3             # EWMA 平滑因子

    def select_quality(self, available_bitrates, buffer_seconds, 
                       last_segment_download_time, last_segment_size):
        # 带宽估算
        current_throughput = last_segment_size * 8 / last_segment_download_time
        if self.throughput_ewma is None:
            self.throughput_ewma = current_throughput
        else:
            self.throughput_ewma = (self.alpha * current_throughput + 
                                    (1 - self.alpha) * self.throughput_ewma)

        # 缓冲区决策
        if buffer_seconds < 5:
            return available_bitrates[0]  # 最低码率
        elif buffer_seconds > 30:
            safe_bitrate = self.throughput_ewma * 0.9
            for br in reversed(available_bitrates):
                if br <= safe_bitrate:
                    return br

        # 正常状态
        safe_bitrate = self.throughput_ewma * 0.85
        for br in reversed(available_bitrates):
            if br <= safe_bitrate:
                return br
        return available_bitrates[0]
```

### 转码流水线设计

```
转码流水线架构:

┌─────────────────────────────────────────────────────────────────┐
│                     Transcode Pipeline                           │
│                                                                 │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────┐ │
│  │ 原始文件        │───▶│ 1. 分析 (Probe)   │───▶│ 2. 拆分任务      │ │
│  │ (S3/OSS)     │    │    - 时长         │    │   per 分辨率 +  │ │
│  │              │    │    - 分辨率        │    │   per 编码格式   │ │
│  └──────────────┘    │    - 编码格式      │    └───────┬────────┘ │
│                      └─────────────────┘            │          │
│                                                     ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3. 并行转码 (Worker Pool)                                 │  │
│  │                                                          │  │
│  │   FFmpeg 命令:                                            │  │
│  │   ffmpeg -i input.mp4 \                                   │  │
│  │     -c:v libx264 -preset veryfast \                       │  │
│  │     -b:v 2500k -maxrate 2675k -bufsize 5000k \            │  │
│  │     -vf "scale=1280:720" \                                │  │
│  │     -c:a aac -b:a 128k \                                  │  │
│  │     -g 48 -keyint_min 48 -sc_threshold 0 \                 │  │
│  │     -f hls -hls_time 6 -hls_list_size 0 \                 │  │
│  │     -hls_segment_filename "720p/seg_%03d.ts" \             │  │
│  │     720p/index.m3u8                                       │  │
│  │                                                          │  │
│  │   分辨率-码率对照表:                                        │  │
│  │   240p: 400 kbps    360p: 800 kbps                        │  │
│  │   480p: 1500 kbps   720p: 2500 kbps (HD)                   │  │
│  │   1080p: 5000 kbps (FHD)  4K: 15000-35000 kbps             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                               │                                │
│                    ┌──────────▼──────────┐                     │
│                    │ 4. 生成 Master      │                     │
│                    │    Playlist        │                     │
│                    │  (master.m3u8)     │                     │
│                    └──────────┬──────────┘                     │
│                               │                                │
│                    ┌──────────▼──────────┐                     │
│                    │ 5. 质量检查 (QC)     │                     │
│                    │ - 分片完整性         │                     │
│                    │ - 音画同步          │                     │
│                    │ - 缩略图生成         │                     │
│                    └──────────┬──────────┘                     │
│                               │                                │
│                    ┌──────────▼──────────┐                     │
│                    │ 6. 上传 CDN 源站     │                     │
│                    │   + 更新状态为 ready  │                     │
│                    └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### 转码优化策略

```
1. GPU 加速转码 (NVIDIA NVENC / Intel QSV):
   - 吞吐量提升 5-10x vs CPU 转码
   - 适用于高并发转码场景
   - 图片质量略逊于 CPU (libx264 placebo)，但对在线视频足够

2. 分布式转码 (MapReduce 模型):
   - 长视频切成多段 → 并行转码各段 → 合并分片
   - 缺点: 段间关键帧对齐复杂
   
3. Ladder 优化 (Netflix per-title 方案):
   - 不为所有视频用相同码率 Ladder
   - 简单动画(如卡通)可以用更低码率达到相同质量
   - 复杂动作内容需要更高码率
   - 对每个视频做 per-title 编码优化

4. 内容感知编码 (CAE):
   - 不同场景片段用不同编码参数
   - 模型自动检测场景复杂度
   - 可比固定码率节省 30-50% 带宽

5. 渐进式转码:
   - 先转最常用的分辨率 (480p, 720p)
   - 用户可立即观看
   - 后台再转其他分辨率
```

### 全球 CDN 分发策略

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-CDN 架构                                 │
│                                                                 │
│                        ┌──────────────┐                         │
│                        │   DNS (Geo)  │                         │
│                        └──────┬───────┘                         │
│                               │                                 │
│              ┌────────────────┼────────────────┐                │
│              │                │                │                │
│     ┌────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐       │
│     │ CDN A (主)     │ │ CDN B (备)    │ │ CDN C (特定    │       │
│     │ Akamai/       │ │ CloudFront   │ │ 地区备选)     │       │
│     │ Cloudflare    │ │              │ │              │       │
│     └────────┬──────┘ └──────┬───────┘ └──────┬───────┘       │
│              │               │                │                │
│     ┌────────▼───────────────▼────────────────▼───────┐       │
│     │           Origin Shield Layer (源站保护)          │       │
│     │                                                  │       │
│     │   Regional Caches:                               │       │
│     │   US-Origin → Asia-Mid-Tier → Asia-Edge         │       │
│     │   减少回源请求和延迟                                │       │
│     └──────────────────────┬───────────────────────────┘       │
│                            │                                    │
│     ┌──────────────────────▼───────────────────────────┐       │
│     │              Object Storage (S3)                  │       │
│     │     ✅ 跨 Region 复制   ✅ 版本控制                  │       │
│     └──────────────────────────────────────────────────┘       │
│                                                                 │
│   CDN 选择策略:                                                  │
│   1. 动态 DNS 解析 (根据用户 IP 返回最近 CDN 节点)                 │
│   2. Multi-CDN 冗余 (一个 CDN 故障自动切换)                        │
│   3. Real-time CDN Performance Monitoring                      │
│   4. 地域覆盖优先: 中国 → 阿里云CDN/腾讯云CDN                      │
│                    欧美 → Akamai/CloudFront                     │
└─────────────────────────────────────────────────────────────────┘
```

### DRM (数字版权管理)

```
内容保护层次:

1. 无保护 (Clear): 
   - 公开内容，任何客户端可播放

2. 签名 URL (Signed URL):
   - 带过期时间戳和签名的临时 URL
   - 防止盗链，但可被二次分享
   - 示例: https://cdn.com/video.m3u8?exp=1704067200&sig=HMAC_SHA256

3. 加密 HLS (AES-128):
   - 分片文件 AES-128 加密
   - 密钥通过 HTTPS 获取
   - 中等安全级别

4. 完整 DRM (Widevine / FairPlay / PlayReady):
   - Multi-DRM 架构:
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │   Widevine   │  │   FairPlay   │  │  PlayReady   │
     │ (Chrome/     │  │ (Safari/     │  │ (Edge/       │
     │  Android)    │  │  iOS/tvOS)   │  │  Xbox)       │
     └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │   DRM License Svc   │
                   │  (Common Encryption │
                   │   CENC + MPEG-CENC) │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │   Content Keys      │
                   │   + Business Rules  │
                   └─────────────────────┘
```

---

## 扩展性与高可用

### 分片上传与断点续传

```python
# 分片上传实现
class MultipartUploadService:

    def initiate_upload(self, user_id, filename, total_size):
        upload_id = generate_upload_id()
        video_id = generate_video_id()

        # 存入 DynamoDB / Redis 追踪上传状态
        upload_state = {
            'upload_id': upload_id,
            'video_id': video_id,
            'user_id': user_id,
            'filename': filename,
            'total_size': total_size,
            'chunk_size': 5 * 1024 * 1024,  # 5MB
            'uploaded_parts': [],  # [{part_num, etag, byte_range}]
            'status': 'in_progress',
            'created_at': now(),
            'expires_at': now() + 86400  # 24小时
        }
        redis.hset(f"upload:{upload_id}", mapping=upload_state)
        redis.expire(f"upload:{upload_id}", 86400)

        return {
            'upload_id': upload_id,
            'video_id': video_id,
            'chunk_size': 5 * 1024 * 1024,
            'total_chunks': math.ceil(total_size / (5 * 1024 * 1024))
        }

    def upload_chunk(self, upload_id, part_num, data):
        state = redis.hgetall(f"upload:{upload_id}")
        chunk_key = f"chunk:{upload_id}:{part_num}"

        # 写入 S3 分片
        etag = s3.upload_part(
            bucket='video-uploads',
            key=f"{state['video_id']}/parts/{part_num:05d}",
            data=data
        )

        # 记录已上传分片
        redis.hset(f"upload:parts:{upload_id}", str(part_num), etag)
        return {'part': part_num, 'etag': etag}

    def complete_upload(self, upload_id):
        state = redis.hgetall(f"upload:{upload_id}")
        parts = redis.hgetall(f"upload:parts:{upload_id}")

        # S3 Complete Multipart Upload
        s3.complete_multipart_upload(
            bucket='video-uploads',
            key=f"{state['video_id']}/original.mp4",
            upload_id=upload_id,
            parts=parts
        )

        # 发送转码消息
        kafka.produce('video.uploaded', {
            'video_id': state['video_id'],
            'user_id': state['user_id'],
            'original_path': f"s3://video-uploads/{state['video_id']}/original.mp4",
            'timestamp': now()
        })

        # 清理 Redis
        redis.delete(f"upload:{upload_id}", f"upload:parts:{upload_id}")
```

### 视频处理 Pipeline 弹性伸缩

```
转码服务的弹性伸缩策略:

1. 基于队列深度的自动扩缩容:
   - Kafka Lag > 阈值: 自动增加 Worker
   - Kubernetes HPA (Horizontal Pod Autoscaler)
   - 冷启动时间: GPU 实例 ~3分钟, CPU 实例 ~30秒

2. 优先级队列:
   - 普通用户: 批量队列 (Batch)，低成本实例
   - Premium 用户: 优先队列 (Priority)，快速转码
   - 热门创作者: 即时队列 (Immediate)

3. Spot / 抢占式实例:
   - 使用 AWS Spot / GCP Preemptible VM 降低成本 (60-90%)
   - 配合 Checkpoint/Resume 实现断点续转
   - 被回收时自动迁移到新实例

4. 转码结果缓存:
   - 相同视频重复上传时，匹配原始 Hash
   - 复用以有的转码结果（去重）
```

### 监控与告警

```
视频平台核心监控指标:

播放体验 (QoE - Quality of Experience):
  - 首帧时间 (TTFF) P50/P95/P99 (阈值: P95 > 3s 告警)
  - 卡顿率 (Rebuffering Ratio): 缓冲时长/播放时长 (阈值: > 2% 告警)
  - 视频启动失败率 (VSTF): (阈值: > 1% 告警)
  - 平均码率 (ABR 选择分布)
  - 退出前播放时长

CDN 性能:
  - CDN 缓存命中率 (阈值: < 90% 告警)
  - CDN 回源带宽 (阈值: > 阈值 告警)
  - CDN 各节点响应延迟与错误率
  - 按地域的 CDN 性能分布

转码流水线:
  - 转码队列长度 / 等待时间
  - 转码成功率 (阈值: < 99% 告警)
  - 平均转码时长 (vs 视频原始时长)
  - Worker 利用率

基础设施:
  - 对象存储可用性 / 带宽
  - Kafka 消费延迟
  - 数据库连接池、慢查询
```

### 灾难恢复 (DR)

```
DR 策略:

区域级故障:
  - 对象存储: S3 跨区域复制 (CRR), RPO < 15min
  - 数据库: 跨区域只读副本, RPO < 1s (Aurora Global Database)
  - DNS Failover: Route53 健康检查, 自动切换 到灾备区域
  - CDN: Multi-CDN 策略, 自动切换

数据恢复:
  - RPO (Recovery Point Objective): 15 分钟
  - RTO (Recovery Time Objective): 30 分钟
  - 视频文件: 多副本 (3副本 + 跨区域)
  - 元数据: 数据库备份 + 跨区域复制
```

---

## 总结

视频流平台是挑战最大的分布式系统之一，核心难点：

1. **巨大存储与带宽**：EB 级存储和 Tbps 级带宽是常态，对象存储 + CDN 是必备基础设施
2. **转码流水线**：多分辨率、多编码格式的并行转码是计算密集型任务，需要 GPU 加速和弹性调度
3. **自适应码率 (ABR)**：客户端智能码率切换算法决定最终用户观影体验
4. **延迟 vs 质量**：首帧加载时间的优化是一个系统工程（CDN 预热、gop size、编码参数）
5. **协议选择**：HLS + DASH 双协议以覆盖所有平台
6. **分片上传**：大文件分块、断点续传、完整性校验确保上传可靠性
7. **版权保护**：从 Signed URL 到完整 Multi-DRM 的多级保护体系
8. **全球分发**：Multi-CDN + 跨区域复制 + GeoDNS 确保全球低延迟播放

**面试核心权衡讨论：**
- HLS vs DASH：平台兼容性 vs 开放标准的权衡
- GPU vs CPU 转码：速度 vs 质量 + 成本
- ABR 算法：基于缓冲区 vs 基于吞吐量 vs 混合策略
- CDN 单供应商 vs Multi-CDN：简单性 vs 容错性
- 存储分层：热数据-SSD-即时, 冷数据-HDD-归档
- DRM 投资：安全级别与用户体验/成本的平衡
