# 08. 设计文件/对象存储系统 (Design File/Object Storage)

## 题目

设计一个类似 Amazon S3 的对象存储系统。支持文件的上传、下载、版本控制、权限管理、生命周期策略等。系统需要具备极高的持久性和可扩展性。

---

## 需求澄清

### 功能性需求

1. **对象上传**：通过 REST API 上传任意大小文件（支持分片上传）
2. **对象下载**：通过 HTTP GET 下载文件，支持 Range 请求（断点续传/部分下载）
3. **对象管理**：列表查询、复制、移动、删除对象
4. **Bucket 概念**：按 Bucket 组织对象，类似文件夹/命名空间
5. **版本控制**：启用后，同一 key 的多版本被保留，可回滚
6. **权限控制**：IAM Policy、Bucket Policy、ACL、Pre-Signed URL
7. **生命周期管理**：自动归档到冷存储、自动删除过期对象
8. **静态网站托管**：Bucket 可配置为静态网站
9. **事件通知**：对象操作（上传/删除）可触发通知到 SNS/SQS/Lambda
10. **数据加密**：服务端加密 (SSE-S3, SSE-KMS)、客户端加密、传输中加密 (TLS)

### 非功能性需求

1. **极高持久性**：99.999999999%（11 个 9），年数据丢失概率 < 0.000000001%
2. **极高可用性**：99.99%（S3 Standard）
3. **近乎无限扩展**：支持 EB 级存储，万亿级对象
4. **低延迟**：首字节延迟 < 100ms（P99 < 500ms）
5. **强一致性**：read-after-write 一致性（新对象写完即可读）
6. **吞吐量**：每前缀 3,500 PUT/COPY/POST/DELETE req/s，5,500 GET/HEAD req/s

### 容量估算

**假设条件：**
- 总对象数: 1 万亿
- 平均对象大小: 500KB（小文件多，大文件少）
- 日增对象: 10 亿
- 日下载量: 100 亿次
- 读取 QPS: 100亿 / 86400 ≈ **116K QPS**（峰值 ×5 ≈ **580K QPS**）
- 写入 QPS: 10亿 / 86400 ≈ **11.6K QPS**（峰值 ×5 ≈ **58K QPS**）

**存储估算：**
- 总存储: 1万亿 × 500KB = **500 PB**
- 3 副本: 500 PB × 3 = 1.5 EB
- 纠删码存储 (Reed-Solomon, k=12, m=4): 500 PB × 1.33 = 667 PB（更省）
- 元数据存储: 1万亿 × 2KB = 2 PB

**带宽估算：**
- 出站: 116K QPS × 500KB ≈ 58 GB/s = **464 Gbps**
- 入站: 11.6K QPS × 500KB ≈ 5.8 GB/s = **46 Gbps**

---

## API 设计

### REST API (S3 兼容)

```
1. 创建 Bucket
PUT /{bucket_name}
Host: s3.region.amazonaws.com

Headers:
  x-amz-acl: private
  x-amz-region: us-east-1

Response: 200 OK
Location: /{bucket_name}

2. 上传对象
PUT /{bucket_name}/{object_key}
Content-Type: application/octet-stream
Content-Length: 1048576
x-amz-storage-class: STANDARD
x-amz-meta-custom: value
x-amz-server-side-encryption: AES256

[Binary Data]

Response: 200 OK
ETag: "d41d8cd98f00b204e9800998ecf8427e"
x-amz-version-id: version_abc123

3. 分片上传 (Multipart Upload)

# 3a. 初始化分片上传
POST /{bucket}/{key}?uploads

Response:
{
  "UploadId": "upload_xyz",
  "Bucket": "my-bucket",
  "Key": "large-file.mp4"
}

# 3b. 上传分片
PUT /{bucket}/{key}?partNumber=1&uploadId=upload_xyz
Content-Length: 5242880

Response: 200 OK
ETag: "etag_of_part_1"

# 3c. 完成分片上传
POST /{bucket}/{key}?uploadId=upload_xyz
{
  "Parts": [
    {"PartNumber": 1, "ETag": "etag_1"},
    {"PartNumber": 2, "ETag": "etag_2"}
  ]
}

Response:
{
  "Location": "https://my-bucket.s3.region.amazonaws.com/large-file.mp4",
  "Key": "large-file.mp4",
  "ETag": "\"combined_etag\"",
  "VersionId": "ver_xyz"
}

4. 下载对象
GET /{bucket_name}/{object_key}

Response: 200 OK
Content-Type: application/octet-stream
Content-Length: 1048576
ETag: "etag"
Last-Modified: Wed, 01 Jan 2025 00:00:00 GMT

[Binary Data]

# 支持 Range 请求（断点续传）
GET /{bucket_name}/{object_key}
Range: bytes=1024-2047

Response: 206 Partial Content
Content-Range: bytes 1024-2047/1048576

5. 生成 Pre-Signed URL
GET /{bucket}/{key}?X-Amz-Expires=3600&X-Amz-Credential=...&X-Amz-Signature=...

# 签名生成 (HMAC-SHA256)
signature = HMAC-SHA256(
    secret_key,
    "AWS4-HMAC-SHA256\n" +
    timestamp + "\n" +
    scope + "\n" +
    SHA256(canonical_request)
)

6. 列对象
GET /{bucket_name}?prefix=photos/&delimiter=/&max-keys=1000

Response:
{
  "Contents": [
    {"Key": "photos/2025/01/vacation.jpg", "Size": 2048000, "LastModified": "...", "ETag": "...", "StorageClass": "STANDARD"}
  ],
  "CommonPrefixes": [
    {"Prefix": "photos/2025/"}
  ],
  "IsTruncated": false,
  "MaxKeys": 1000
}

7. 删除对象
DELETE /{bucket_name}/{object_key}

# 删除特定版本
DELETE /{bucket_name}/{object_key}?versionId=ver_abc
```

---

## 数据模型

### 对象存储结构

```
逻辑结构:
  Bucket (全局唯一名)
    └── Object (Key 唯一标识)
         ├── Data (实际数据, 存储在 Data Store)
         ├── Metadata (对象元数据, 存储在 Metadata Store)
         │    ├── Key, ETag, Content-Type, Content-Length
         │    ├── Storage Class (STANDARD, IA, GLACIER)
         │    ├── Version ID
         │    ├── Last Modified
         │    ├── Owner
         │    ├── ACL
         │    ├── Custom Metadata (x-amz-meta-*)
         │    └── Encryption Info
         └── Tags (key-value 标签)
```

### 元数据存储 (Metadata Store)

```sql
-- Bucket 表
CREATE TABLE buckets (
    bucket_id VARCHAR(64) PRIMARY KEY,
    bucket_name VARCHAR(63) NOT NULL UNIQUE,
    owner_id BIGINT NOT NULL,
    region VARCHAR(32) NOT NULL,
    versioning_enabled BOOLEAN DEFAULT FALSE,
    default_storage_class VARCHAR(32) DEFAULT 'STANDARD',
    encryption_config JSON,
    created_at BIGINT NOT NULL,
    INDEX idx_owner (owner_id)
);

-- 对象元数据表 (分片存储)
CREATE TABLE object_metadata (
    bucket_id VARCHAR(64) NOT NULL,
    object_key VARCHAR(1024) NOT NULL,
    version_id VARCHAR(64) NOT NULL,
    -- 核心元数据
    content_length BIGINT NOT NULL,
    content_type VARCHAR(255),
    etag VARCHAR(64),
    -- 存储信息
    storage_class VARCHAR(32) DEFAULT 'STANDARD',
    data_chunks JSON NOT NULL,     -- 数据块在 Data Store 中的位置
    -- [{"chunk_id": 0, "store_id": 3, "offset": 1024, "length": 5242880}, ...]
    -- 版本信息
    is_delete_marker BOOLEAN DEFAULT FALSE,
    is_latest BOOLEAN DEFAULT TRUE,
    -- 时间信息
    created_at BIGINT NOT NULL,
    updated_at BIGINT,
    -- 加密
    encryption_algo VARCHAR(32),
    encryption_key_id VARCHAR(128),
    -- ACL
    acl JSON,
    -- 自定义元数据
    custom_metadata JSON,
    PRIMARY KEY ((bucket_id, object_key), version_id DESC),
    INDEX idx_created (created_at)
);
-- 分片策略: 按 bucket_id 进行一致性哈希分片

-- 分片上传状态表 (Redis / DynamoDB)
CREATE TABLE multipart_uploads (
    upload_id VARCHAR(64) PRIMARY KEY,
    bucket_id VARCHAR(64) NOT NULL,
    object_key VARCHAR(1024) NOT NULL,
    storage_class VARCHAR(32),
    total_parts INT,
    uploaded_parts JSON,     -- [{part_num, etag, size, chunk_location}]
    created_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL, -- 7 天未完成则清理
    INDEX idx_expires (expires_at)
);
```

### 数据分块存储 (Data Store)

```
数据块 (Chunk) 存储:

大文件 (> 64MB) 分块策略:
  - 分块大小: 64MB (可配置)
  - 纠删码: Reed-Solomon (12+4) 跨 16 个数据节点
  - 每块存储定位: (data_node_id, disk_id, block_offset, block_size)

纠删码 (Erasure Coding) vs 多副本:

多副本 (3副本):
  存储开销: 3x
  读取: 任意一个副本
  容忍: 2 副本同时故障
  
纠删码 RS(12,4):
  存储开销: 1.33x
  读取: 12 个数据分片 (完整读取)
  容忍: 任意 4 个分片丢失
  写放大: 需要计算校验块

存储层级:
  ┌─────────────────────────────────────────────┐
  │ Storage Tier        │ 延迟  │ 持久性 │ 成本  │
  ├─────────────────────┼───────┼────────┼──────┤
  │ STANDARD (SSD/NVMe) │ < 5ms │ 11个9  │ $$$  │
  │ IA (SSD+HDD混合)     │ <10ms │ 11个9  │ $$   │
  │ GLACIER (HDD)       │ 分钟   │ 11个9  │ $    │
  │ GLACIER DEEP ARCHIVE│ 小时   │ 11个9  │ ¢    │
  └─────────────────────────────────────────────┘
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────────┐
                              │               Client / SDK                    │
                              │  - S3 SDK (Java/Python/Go/JS...)              │
                              │  - CLI (aws s3 cp/sync)                       │
                              │  - HTTP REST API                              │
                              └─────────────────────┬────────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────────┐
                              │              Load Balancer / DNS              │
                              │       (Route53 + Global Accelerator)         │
                              └─────────────────────┬────────────────────────┘
                                                    │
        ┌───────────────────────────────────────────┼───────────────────────────┐
        │                                           │                           │
┌───────▼──────────┐                      ┌─────────▼──────────┐    ┌───────────▼──────────┐
│   Auth & Authz   │                      │   Metadata Store    │    │   Data Store         │
│   Service        │                      │                     │    │                      │
│  ─────────────────│                      │  ┌───────────────┐ │    │  ┌──────────────────┐│
│  - IAM Policy     │                      │  │ Metadata DB   │ │    │  │ Chunk Manager    ││
│    Evaluation     │                      │  │ (MySQL/       │ │    │  │ ──────────────── ││
│  - Bucket Policy  │                      │  │  PostgreSQL   │ │    │  │ - Chunk 分配      ││
│  - ACL            │                      │  │  Sharded)    │ │    │  │ - 副本放置策略     ││
│  - Pre-Signed URL │                      │  └───────────────┘ │    │  │ - 纠删码管理      ││
│    Validation     │                      │                     │    │  │ - 健康检查        ││
│  - Request        │                      │  ┌───────────────┐ │    │  └────────┬─────────┘│
│    Signing V4     │                      │  │ Metadata      │ │    │           │          │
└──────────────────┘                      │  │ Cache (Redis) │ │    │  ┌────────▼─────────┐│
                                          │  └───────────────┘ │    │  │ Storage Nodes     ││
┌──────────────────┐                      └─────────────────────┘    │  │ ─────────────────││
│  Lifecycle       │                                                 │  │ ┌──────────────┐ ││
│  Manager         │                                                 │  │ │ Node 1       │ ││
│  ───────────────  │                                                 │  │ │ (disks x12)  │ ││
│  - 定时扫描        │                                                 │  │ └──────────────┘ ││
│  - 归档/删除      │                                                 │  │ ┌──────────────┐ ││
│  - 跨Region复制   │                                                 │  │ │ Node 2       │ ││
└──────────────────┘                                                 │  │ │ (disks x12)  │ ││
                                                                     │  │ └──────────────┘ ││
┌──────────────────┐                                                 │  │ ┌──────────────┐ ││
│  Event           │                                                 │  │ │ Node N       │ ││
│  Notification    │                                                 │  │ │ (disks x12)  │ ││
│  ─────────────── │                                                 │  │ └──────────────┘ ││
│  - S3 Event      │                                                 │  └──────────────────┘│
│  - SNS/SQS/Lambda│                                                 └─────────────────────┘
└──────────────────┘
```

---

## 核心深入

### 大文件分片上传 (Multipart Upload)

```
分片上传流程:

步骤1: 初始化
  Client → API Gateway: POST /bucket/key?uploads
  → 创建 upload_id, 在 Redis/DynamoDB 记录上传状态
  → 返回 upload_id + 建议分片大小 (5MB min, 5GB max per part)

步骤2: 并行上传分片
  Client → API Gateway: PUT /bucket/key?partNumber=1&uploadId=xxx
  → 接收分片数据
  → 计算 MD5 校验和
  → 写入 Data Store (暂存区域)
  → 返回 ETag
  → 更新上传状态 (已上传分片列表)

步骤3: 完成上传
  Client → API Gateway: POST /bucket/key?uploadId=xxx
  → 校验所有分片 ETag 与客户端上报一致
  → 合并分片 (逻辑合并，不物理拷贝)
  → 写入对象元数据 (Metadata Store)
  → 异步: Data Store 内部将分片整合为最终存储格式
  → 返回最终 ETag (组合哈希: MD5(concat_all_parts_MD5) - count)
```

```python
class MultipartUploadService:
    MIN_PART_SIZE = 5 * 1024 * 1024      # 5MB
    MAX_PART_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
    MAX_PARTS = 10000
    MAX_OBJECT_SIZE = MAX_PARTS * MAX_PART_SIZE  # 5TB

    def initiate_upload(self, bucket, key, total_size=None):
        upload_id = uuid.uuid4()
        if total_size and total_size > self.MAX_OBJECT_SIZE:
            raise ObjectTooLargeError()

        state = {
            'upload_id': upload_id,
            'bucket': bucket,
            'key': key,
            'total_parts': None,
            'parts': [],
            'status': 'in_progress',
            'created_at': time.time(),
            'expires_at': time.time() + 7 * 86400
        }
        # 存储在 Redis / DynamoDB
        redis.hset(f"upload:{upload_id}", mapping=state)
        redis.expire(f"upload:{upload_id}", 7 * 86400)

        return {'upload_id': upload_id, 'min_part_size': self.MIN_PART_SIZE}

    def upload_part(self, upload_id, part_number, data):
        if len(data) < self.MIN_PART_SIZE and part_number > 1:
            raise PartTooSmallError()  # 除最后一块外，每块 >= 5MB

        etag = hashlib.md5(data).hexdigest()
        chunk_location = self.data_store.write_chunk(
            bucket, key, upload_id, part_number, data
        )

        # 原子记录分片
        redis.lpush(
            f"upload:{upload_id}:parts",
            json.dumps({'part': part_number, 'etag': etag, 'location': chunk_location})
        )
        return {'part_number': part_number, 'etag': etag}

    def complete_upload(self, upload_id, parts_list):
        expected_parts = redis.lrange(f"upload:{upload_id}:parts", 0, -1)
        # 校验所有分片 ETag
        if not self._validate_parts(expected_parts, parts_list):
            raise InvalidPartError()

        chunks = [json.loads(p)['location'] for p in expected_parts]

        # 写入元数据
        total_size = sum(c['size'] for c in chunks)
        combined_etag = self._compute_combined_etag(parts_list)

        self.metadata_store.create_object(
            bucket=upload.bucket,
            key=upload.key,
            size=total_size,
            etag=combined_etag,
            chunks=chunks,
            version_enabled=bucket.versioning
        )

        # 清理上传状态
        redis.delete(f"upload:{upload_id}", f"upload:{upload_id}:parts")
```

### 纠删码 (Erasure Coding)

```
Reed-Solomon 纠删码:

原理:
  将数据分成 k 个数据分片
  计算 m 个校验分片
  总共 k + m 个分片分布在 k + m 个存储节点上
  可以从任意 k 个分片中恢复原始数据

参数示例 (k=12, m=4):
  原始数据: 64MB
  k=12 个数据分片: 每片 ~5.33MB
  m=4 个校验分片: 每片 ~5.33MB
  总存储: 64MB * (16/12) ≈ 85.3MB → 存储开销 1.33x

  容错: 任意 4 个分片丢失/损坏 → 数据仍然可恢复
  读取: 需要读取 12 个分片 (比 3 副本多了读取量)

写入流程:
  1. 原始数据 → 分成 k 个数据分片 (striping)
  2. 对 k 个数据分片 → 矩阵运算 → m 个校验分片 (encoding)
  3. 所有 k+m 个分片 → 分布式存储到不同节点/机架/DC
  4. 记录分片位置到元数据

读取流程:
  1. 查询元数据 → 获取分片位置
  2. 并行读取 k+m 个分片
  3. 只要收到 k 个分片 → 矩阵逆运算 → 恢复原始数据 (decoding)
  4. 如果有分片出错/超时 → 使用替代分片

Intel ISA-L 库提供高效的 RS 编解码实现
```

### 元数据存储扩展

```
元数据存储的挑战:
  - 1 万亿对象的元数据需要查询和管理
  - 强一致性的 List/Search 操作

分片策略:
  按 bucket_id 进行一致性哈希分片
  每个分片是一个独立的关系型数据库实例 (或分布式数据库如 Spanner)
  
  热点 Bucket 问题:
    如果某 Bucket 有百亿对象 → 按 (bucket_id, hash(key)%N) 进一步分片

元数据缓存:
  L1: 请求处理节点本地 LRU Cache
  L2: 分布式 Redis 缓存
  L3: 元数据数据库

  缓存策略: Write-Through (写入时同步更新缓存)
  热点对象元数据缓存在 L1, 减少 Redis/DB 查询

列表操作的挑战:
  LIST 是 O(n) 操作, 对万亿对象不可行
  解法:
    - deliminted 分层 (类似文件夹)
    - 使用前缀索引加速
    - 对超大 List 结果流式返回 + 分页 (每次 max-keys=1000)
    - 后台异步构建前缀缓存
```

### 数据持久性：如何达到 11 个 9

```
11 个 9 (99.999999999%) 持久性意味着:
  存储 10,000,000 个对象一年
  预期丢失 0.0001 个对象 (基本为 0)

  年化故障率 (AFR) 分析:
    假设每个磁盘 AFR = 2%
    纠删码 k=12, m=4 → 需要任意 5 块磁盘同时故障才丢数据
    P(5块同时故障) ≈ (0.02)⁵ / 5! 相关因子 ≈ 可忽略

实际保障手段:
  1. 纠删码 (跨磁盘/节点/机架放置分片)
  2. 持续完整性校验 (校验和 + 定期 scrub)
  3. 多可用区 (AZ) 放置
  4. 跨 Region 复制 (可选)
  5. 自动修复 (检测到损坏 → 自动从健康分片重建)
  
数据完整性校验:
  写入: 计算 checksum → 写入时附带 → 读取时回校验
  后台 scrub: 定期扫描所有数据 → 对比 checksum
  发现损坏: 
    - 纠删码: 从其他 k 个分片重建损坏分片
    - 副本: 从健康副本复制
```

---

## 扩展性与高可用

### 数据放置策略

```
数据放置约束 (Placement Policy):

1. 跨磁盘:
   同一对象的 k+m 个分片放置在 k+m 个不同物理磁盘

2. 跨节点:
   同一对象的分片分布在不同存储节点上
   至少 m 个分片不在同一节点

3. 跨机架:
   同一对象的分片分布在至少 3 个不同机架
   防止机架级故障 (交换机/电源)

4. 跨可用区:
   STANDARD 存储类: 数据至少分布在 3 个 AZ
   ONEZONE-IA 存储类: 仅 1 个 AZ (成本更低)

示例放置 (k=12, m=4, 3 AZ):
  每个 AZ 放置: 5-6 个分片
  单个 AZ 故障: 仍然有 ≥ k 个分片可用 → 服务不中断
```

### 生命周期管理

```
生命周期规则:

1. Transition (转换):
   - 创建 30 天后: STANDARD → STANDARD_IA
   - 创建 90 天后: STANDARD_IA → GLACIER
   - 创建 180 天后: GLACIER → DEEP_ARCHIVE

2. Expiration (过期):
   - 创建 365 天后自动删除
   - 指定日期后自动删除

3. 非当前版本管理:
   - 删除旧版本文件

实现:
  Lifecycle Manager (分布式调度器):
  1. 定时轮询对象元数据
  2. 匹配生命周期规则
  3. 生成转换/删除任务 → Kafka
  4. Worker 消费并执行
  5. 批处理, 避免逐对象操作

批量生命周期处理:
  按 (bucket_id, date_range) 成批处理
  避免数据库逐行更新的性能问题
```

### 多 Region 复制

```
跨 Region 复制 (CRR - Cross-Region Replication):

启用后:
  在 Region A 上传的对象自动复制到 Region B

实现:
  1. 对象上传完成 → S3 Event 触发
  2. Event 进入复制队列 (SQS/Kafka)
  3. 复制 Worker 消费事件 → 下载源对象 → 上传到目标 Region
  4. 支持复制过滤规则 (前缀/标签匹配)

一致性:
  异步复制, RPO 通常在几秒到几分钟
  复制时间取决于对象大小和网络带宽
```

### 监控与告警

```
对象存储系统监控:

存储指标:
  - Bucket 数量、对象数量、总存储大小
  - 按存储类的存储分布 (STANDARD / IA / GLACIER)
  - 日均上传/下载对象数
  - 数据增长率

性能指标:
  - API 延迟 (GET/PUT/LIST) P50/P95/P99
  - 错误率 (4xx/5xx 按操作类型)
  - 请求速率 (QPS per API operation)

持久性和一致性:
  - 数据完整性校验通过率
  - 磁盘故障率 (AFR)
  - 数据修复速率
  - 元数据同步延迟

容量规划:
  - 各 Data Node 磁盘使用率 (阈值: > 75% 扩容)
  - 元数据 DB 使用率、连接数
  - 纠删码分片分布均衡性
```

---

## 总结

对象存储系统是云计算的核心基础设施，架构精髓包括：

1. **元数据与数据分离**：元数据存储在可扩展的关系/NoSQL 数据库中，数据以分块/分片形式存储在专用的 Data Store 节点上
2. **纠删码 (Erasure Coding)**：在存储开销和容错能力之间取得最优平衡，RS(12,4) 只需 1.33x 开销就能容忍任意 4 个分片故障
3. **11个9持久性**：纠删码 + 跨 AZ 放置 + 持续 scrubbing + 自动修复的多层保障
4. **分片上传 (Multipart Upload)**：大文件并行分块上传 + 断点续传的标准化方案
5. **生命周期管理**：热/温/冷/冰 四级存储，自动降冷降低存储成本
6. **强一致性**：新对象的 read-after-write 一致性，通过元数据的原子写入保证
7. **权限管理**：IAM + Bucket Policy + ACL + Pre-Signed URL 的四层权限体系
8. **水平扩展**：元数据分片 + Data Store 节点水平扩展 + 前缀哈希分布解决热点

**面试核心权衡讨论：**
- 多副本 vs 纠删码：存储效率 vs 读取延迟
- 元数据存储：关系型 DB（强一致）vs NoSQL（水平扩展）
- 强一致性 vs 最终一致性：S3 的 read-after-write vs 历史系统
- 存储层级：如何在成本、延迟、持久性之间平衡
- 大文件：是否需要分片，分片策略 (64MB vs 128MB)
- Pre-Signed URL vs IAM 认证：适用场景和安全考虑
