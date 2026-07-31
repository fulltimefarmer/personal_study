# 题目：Design a File Storage System (like S3)

## 需求澄清（Requirement Clarification）

### 功能需求
1. 用户可上传、下载、删除文件（对象）。
2. 支持大文件分块上传（Multipart Upload），断点续传。
3. 文件存储在 Bucket（存储桶）中，Bucket 级别隔离。
4. 支持文件元数据管理：文件名、大小、类型、自定义标签、创建/修改时间。
5. 版本控制：同一对象保留多个版本，可恢复到历史版本。
6. 权限管理：Bucket 和对象级别的 ACL / IAM 策略（公开/私有/授权访问）。
7. 数据去重：相同内容文件只存一份（内容寻址），节省存储空间。
8. 支持 CDN 加速：热点文件缓存到边缘节点。

### 非功能需求
- **高可用**：99.99% 可用，数据跨 AZ 冗余。
- **持久性（Durability）**：数据耐久性 99.999999999%（11 个 9），极少丢数据。
- **扩展性**：支持 EB 级存储，无限扩展。
- **低延迟**：大文件下载 < 200ms 首字节延迟，CDN 边缘 < 10ms。
- **一致性**：写入后立即读强一致（新对象），覆盖写入最终一致（读旧版本），部分服务如 S3 已支持强一致。

### 容量估算
- **存储总量**：假设日上传 1PB，年增长率 50%。第一年 365PB，第五年 ≈ 3EB。
- **QPS**：假设 10M 日活用户，人均 5 次操作 = 50M 请求/天 ≈ 580 QPS 平均；峰值 ×5 ≈ 3000 QPS（元数据操作）。
- **带宽**：每日上传 = 1PB / 86400 ≈ 11.6GB/s；下载假设 5 倍 = 58GB/s。
- **元数据存储**：每个文件元数据 ~1KB，每天 2.4 亿个文件（1PB / 平均 4MB），年增 ≈ 87B 条 × 1KB ≈ 87TB（不含索引和副本）。

---

## 系统接口（API Design）

### RESTful API（S3 兼容风格）

```
# 创建 Bucket
PUT /{bucket_name}

Response 200 OK:
Location: /{bucket_name}


# 上传对象
PUT /{bucket_name}/{object_key}
Content-Type: application/octet-stream
Content-Length: 1048576
x-amz-meta-custom: myvalue              // 自定义元数据
x-amz-storage-class: STANDARD           // STANDARD / IA / GLACIER

Response 200 OK:
{
  "ETag": "\"d41d8cd98f00b204e9800998ecf8427e\"",
  "version_id": "v2.0"
}


# 下载对象
GET /{bucket_name}/{object_key}
Range: bytes=0-1048575                   // 可选：断点下载

Response 200 OK / 206 Partial Content:
Content-Type: application/octet-stream
Content-Length: 1048576
ETag: "..."
x-amz-version-id: "v2.0"

<binary data>


# 删除对象
DELETE /{bucket_name}/{object_key}

Response 204 No Content

# 带版本删除（指定版本号）
DELETE /{bucket_name}/{object_key}?versionId=v1.0
Response 204 No Content


# 获取对象元数据（HEAD）
HEAD /{bucket_name}/{object_key}

Response 200 OK:
Content-Length: 1048576
Content-Type: application/pdf
ETag: "..."
Last-Modified: "..."
x-amz-version-id: "v2.0"


# 列出对象
GET /{bucket_name}?prefix=photos/&max-keys=100&marker=...

Response 200:
{
  "Contents": [
    {
      "Key": "photos/sunset.jpg",
      "LastModified": "...",
      "ETag": "...",
      "Size": 5242880,
      "StorageClass": "STANDARD"
    }
  ],
  "IsTruncated": false,
  "MaxKeys": 100
}
```

### 分块上传（Multipart Upload）

```
# 1. 初始化分块上传
POST /{bucket_name}/{object_key}?uploads

Response 200:
{
  "UploadId": "upload_abc123",
  "Bucket": "my-bucket",
  "Key": "large_file.zip"
}

# 2. 上传分块
PUT /{bucket_name}/{object_key}?partNumber=1&uploadId=upload_abc123
Content-Length: 5242880

<binary chunk data>

Response 200: { "ETag": "etag_part1" }

# 3. 完成上传（合并分块）
POST /{bucket_name}/{object_key}?uploadId=upload_abc123
Request:
{
  "Parts": [
    { "PartNumber": 1, "ETag": "etag_part1" },
    { "PartNumber": 2, "ETag": "etag_part2" }
  ]
}

Response 200:
{
  "Location": "/my-bucket/large_file.zip",
  "ETag": "final_etag"
}

# 中止上传
DELETE /{bucket_name}/{object_key}?uploadId=upload_abc123
```

---

## 数据模型（Data Model）

### 元数据数据库（MySQL / PostgreSQL 分片）

#### Bucket 表

| 字段 | 类型 | 描述 |
|------|------|------|
| id | BIGINT (PK) | 主键 |
| bucket_name | VARCHAR(63) (UNIQUE) | Bucket 名称（全局唯一） |
| owner_id | BIGINT | 创建者 |
| region | VARCHAR(20) | 存储区域 |
| versioning_enabled | TINYINT | 是否启用版本控制 |
| acl_json | JSON | Bucket 级 ACL |
| created_at | TIMESTAMP | 创建时间 |

#### Object 表（文件元数据）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | BIGINT (PK) | 主键 |
| bucket_id | BIGINT (INDEX) | 关联 Bucket |
| object_key | VARCHAR(1024) | 对象路径/Key |
| version_id | VARCHAR(64) | 版本号（默认 "null"） |
| content_hash | VARCHAR(64) (INDEX) | 内容 SHA256（用于去重） |
| size_bytes | BIGINT | 文件大小（字节） |
| content_type | VARCHAR(255) | MIME 类型 |
| storage_class | VARCHAR(20) | STANDARD / IA / GLACIER |
| chunks_json | JSON | 分块信息：`[{"chunk_id":"...","size":...},...]` |
| metadata_json | JSON | 用户自定义元数据 |
| acl_json | JSON | 对象级 ACL |
| is_delete_marker | TINYINT | 版本控制中的删除标记 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 最后修改时间 |

### 索引策略
- `(bucket_id, object_key, version_id)` 联合唯一索引（对象版本查询）。
- `content_hash` 索引（去重查询）。
- `(bucket_id, object_key)` 联合索引（获取最新版本）。
- `(bucket_id, created_at)` 索引（按时间列出对象）。

### Chunk 表（分块数据映射）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | BIGINT (PK) | 主键 |
| chunk_hash | VARCHAR(64) (UNIQUE) | 分块内容哈希（SHA256） |
| storage_path | VARCHAR(1024) | 实际存储路径（对象存储内部路径） |
| size_bytes | BIGINT | 分块大小 |
| ref_count | INT | 引用计数（去重，多个对象共享同一分块） |
| created_at | TIMESTAMP | 创建时间 |

### 关系型 vs 非关系型选择

**推荐：MySQL（元数据）+ 对象存储（数据）+ Elasticsearch（搜索）**

- **MySQL**：结构化元数据，支持事务（版本控制、ACL），索引能力好。
- **对象存储**：如 MinIO / Ceph / 或自研，存实际文件数据。使用内容寻址（根据 SHA256 作为文件名）天然去重。
- **Elasticsearch**：对文件名和自定义元数据做全文搜索。
- **MySQL 分片**：按 `bucket_id` 哈希分片，每个桶的元数据在有限分片内。

---

## 架构设计（High-Level Design）

### 架构图（ASCII）

```
     ┌─────────────────────────────────────────────┐
     │                 Client / SDK                  │
     └──────────────────┬──────────────────────────┘
                        │
                ┌───────▼────────┐
                │    CDN (DNS)   │
                │  (如 CloudFront)│
                └───────┬────────┘
                        │
         ┌──────────────▼──────────────┐
         │         API Gateway         │
         │    (认证 / 鉴权 / 限流)      │
         └──────────────┬──────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────────┐
│ Metadata API │  │ Upload API │  │ Download API    │
│  (CRUD)      │  │ (分块上传)  │  │ (流式下载/CDN URL)│
└───────┬──────┘  └─────┬──────┘  └─────┬──────────┘
        │               │               │
        │        ┌──────▼──────┐        │
        │        │  Chunk      │        │
        │        │ Processor   │        │
        │        └──────┬──────┘        │
        │               │               │
┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────────┐
│    MySQL     │  │   Object   │  │     CDN        │
│  (元数据)    │  │  Storage   │  │  (Edge Cache)  │
│              │  │  (MinIO /  │  │                │
│              │  │   Ceph /   │  │                │
│              │  │   HDFS)    │  │                │
└──────────────┘  └────────────┘  └────────────────┘
        │
┌───────▼──────┐
│ Elasticsearch│
│  (全文搜索)   │
└──────────────┘
```

### 组件职责

| 组件 | 职责 |
|------|------|
| **API Gateway** | 统一入口；认证鉴权（IAM Token 验证）；请求限流；SSL Termination |
| **Metadata API** | 管理 Bucket、对象、版本控制、ACL 的 CRUD；查询 MySQL 和 Elasticsearch |
| **Upload API** | 接收文件/分块上传；计算内容哈希；调用 Chunk Processor 写入对象存储 |
| **Download API** | 查元数据获取存储路径；从对象存储读数据流式返回；或生成 CDN 预签名 URL |
| **Chunk Processor** | 接收上传数据流 → 分块（默认 5MB）→ 计算 SHA256 → 去重检查 → 写入对象存储 → 更新 Chunk 表和 Object 表 |
| **对象存储（MinIO / Ceph）** | 实际文件/分块数据的持久化存储；按 SHA256 命名的扁平 Key 空间；自带纠删码（Erasure Coding） |
| **CDN** | 缓存热点文件到边缘节点；回源到对象存储；降低延迟和带宽成本 |
| **Elasticsearch** | 异步同步对象元数据，提供文件名的前缀/模糊搜索 |
| **MySQL** | 持久化元数据、权限、版本历史 |

---

## 深入探讨（Deep Dive）

### 1. 对象存储模型与数据去重

#### 对象存储核心概念

| 概念 | 说明 |
|------|------|
| **Object（对象）** | 数据 + 元数据 + 全局唯一 ID。无目录层级，Key 命名模拟路径（如 `photos/2026/sunset.jpg`） |
| **Bucket** | 对象的容器，命名空间隔离，绑定存储区域与权限 |
| **扁平命名空间** | Key 是唯一标识，无传统文件系统的目录树。列举操作通过前缀（Prefix）实现 |
| **不可变性** | 对象写入后不可修改，更新即是创建新版本（版本控制） |

#### 内容寻址去重

核心思路：使用文件内容的哈希值（SHA256）作为存储的物理标识符。不同用户上传相同的文件，在物理层只存一份。

**去重流程**：

```
上传请求 → 客户端计算整个文件的 SHA256 Hash
         → 发送到服务端
         → 服务端查 Chunk 表: hash 是否已存在？
              ├─ 存在: ref_count += 1，无需重复存储
              ├─ 不存在: 存入对象存储，路径 = /data/{hash[0:2]}/{hash}
              └─ 不管哪种情况: 在 Object 表中创建记录（关联到 hash）
```

**去重的粒度**：

| 粒度 | 方法 | 节省空间 | 复杂度 |
|------|------|----------|--------|
| **文件级** | 整个文件一个哈希 | 中（相同文件才去重） | 低 |
| **分块级** | 文件分为固定大小块（如 4MB），每块独立去重 | 高（文件部分修改也可去重） | 中 |
| **字节级** | 使用 Rabin Fingerprint 做内容感知分块（CDC）| 最高 | 高 |

**推荐**：分块级去重（Chunk-Level Dedup）。文件分块上传时，每块独立计算 SHA256，到 Chunk 表中查重。文件修改时只有变化的块需要重新上传，未变化的块直接复用（ref_count++）。

**引用计数与垃圾回收（GC）**：

- 对象删除时：`ref_count--`（延迟删除，标记而非立即清理）。
- 定时任务扫描 `ref_count = 0` 的 Chunk，确认无任何对象引用后物理删除。
- 版本控制场景：创建新版本时旧版本 Chunk 的 ref_count--，旧版本数据本身可能仍被其他对象引用。

### 2. 分块上传（Multipart Upload）

#### 设计挑战
- 大文件（GB 级）一次性上传容易失败（网络抖动、超时）。
- 断点续传：失败后只需重传失败的分块。
- 并行上传来提速。

#### 上传核心流程

```
1. Client 请求 Initiate → 服务端生成 UploadId，返回给 Client，记录到 pending_uploads 表

2. Client 将文件切分为多个 5MB-5GB 的分块（S3 最大 10000 块）
   每个分块独立上传 PUT /{bucket}/{key}?partNumber=N&uploadId=xxx
   - 每块成功后服务端记录 (UploadId, PartNumber, ETag) 到 pending_parts 表
   - 分块可乱序、并行、重传

3. 全部分块上传完成后:
   Client 请求 Complete → 服务端校验所有分块都已存在
   → 合并分块（逻辑合并，不实际拼接）：
       - Object 表的 chunks_json 记录所有分块哈希列表
       - 最终 ETag = MD5(etag1 + etag2 + ...)
   → 清理 pending 表

4. 过期 UploadId 定期清理（如 24 小时未完成的自动中止）
```

#### 断点续传支持

- Client 维护本地状态（已上传分块列表 + ETag）。
- 请求恢复时 Client 调用 ListParts API 获取服务端已记录的分块。
- Client 对比本地与服务端，只上传缺失的分块。
- 重试分块时从上次中断的字节偏移继续（通过 Range 请求，不重传整个分块）。

### 3. CDN 加速

#### 回源策略

```
用户请求文件 → DNS 解析到最近的 CDN Edge 节点
  ├─ Edge 缓存命中 → 直接返回文件（延迟 < 10ms）
  ├─ Edge 缓存未命中 → Edge 向对象存储回源请求
  │                     → 对象存储返回文件
  │                     → Edge 缓存文件（根据 Cache-Control 头决定 TTL）
  │                     → Edge 返回文件给用户
  └─ 对象存储也支持 Range 请求，CDN 可以只缓存部分切片
```

#### 预签名 URL（Presigned URL）

```
Client 通过 API 请求文件的临时下载 URL
→ Metadata API 鉴权通过
→ 使用私有密钥生成时间受限的 URL（含签名）
→ 返回给 Client

URL 格式:
https://cdn.example.com/bucket/object.mp4
  ?Expires=1722345600
  &Signature=hmac_sha256_signature
  &Key-Pair-Id=APKAI...

→ CDN 验证签名通过 → 返回文件或回源
```

- URL 有效期通常 1 分钟到 7 天。
- 无需 CDN 与后端同步权限，签名自包含权限信息。

#### 缓存预热与刷新

- **预热（Prefetch）**：将热点文件提前推送到边缘节点（如新游戏版本发布）。
- **刷新（Purge）**：文件更新后主动清除 CDN 缓存，支持 URL / 目录 / 通配符刷新。
- **版本化 URL**：在 URL 中加入版本号（如 `photo.jpg?v=2`），自然绕过 CDN 缓存。

---

## 扩展与高可用

### 水平扩展
- **Metadata API**：无状态，K8s 水平扩展。
- **MySQL 元数据**：按 `bucket_id` 哈希分片。每个分片一主多从读写分离。
- **对象存储**：Ceph / MinIO 自带水平扩展，增加 OSD 节点自动均衡数据。
- **CDN**：云厂商 CDN 自带扩展，全球数百边缘节点。

### 数据冗余与故障转移
- **对象存储冗余**：纠删码（Erasure Coding），如 `8+3` 配置（8 个数据块 + 3 个校验块），容忍任意 3 个块丢失。比三副本节省 50%+ 存储。
- **AZ 级别冗余**：对象数据跨 3 个可用区分布，单 AZ 故障不影响数据完整性。
- **MySQL 高可用**：MHA / Orchestrator 自动故障转移。
- **元数据缓存**：热点元数据缓存在 Redis，减少 MySQL 压力。

### 数据备份与恢复
- **对象存储**：纠删码本身提供高持久性；可额外配置跨区域异步复制（Bucket Replication）作为异地容灾。
- **MySQL 元数据**：全量备份 + Binlog 实时备份。
- **版本控制的恢复**：删除标记可通过删除 delete marker 恢复对象；永久删除受 Bucket 的 Versioning 策略影响。
- **灾难恢复 DR**：
  - RTO（恢复时间目标）：< 1 小时。
  - RPO（恢复点目标）：< 5 分钟（依赖异步复制延迟）。
  - 定期 DR 演练：从备份恢复至灾备环境并做完整性校验。

---

## 总结

### 关键设计决策回顾
1. **对象存储 + 元数据分离**：文件和元数据分别存储，元数据用 MySQL 管理，文件用对象存储。各组件可独立扩展。
2. **内容寻址去重**：SHA256 哈希作为物理存储标识，分块级去重，大幅节省存储成本（尤其版本控制和相似文件场景）。
3. **分块上传**：5MB 固定块大小；支持并行上传、断点续传；pending 表状态跟踪 + 24h TTL 自动清理。
4. **CDN 集成**：热点文件通过 CDN 边缘节点分发，预签名 URL 实现安全受控访问，降低回源压力。
5. **版本控制**：MySQL 中 object 表支持 version_id 字段，删除时添加 delete marker 而非物理删除，支持回滚。

### 可能的改进方向
- **智能分层（Intelligent Tiering）**：根据访问频率自动将文件在 STANDARD / IA（低频）/ GLACIER（归档）之间迁移，优化成本。
- **生命周期管理**：自动删除过期文件、清理旧版本。可配置规则如「30 天后转 GLACIER，90 天后删除」。
- **事件通知**：文件上传/删除等操作触发事件 → Kafka → 下游处理（缩略图生成、病毒扫描、内容审核）。
- **跨区域复制（CRR）**：文件变更自动异步复制到其他区域，用于合规（数据本地化）与灾备。
- **数据加密**：
  - 传输加密：TLS 1.3。
  - 静态加密：服务端加密（SSE-S3 / SSE-C / SSE-KMS）。使用 AES-256，加密密钥存入 KMS。
  - 客户端加密：SDK 在上传前加密，服务端存密文，密钥完全由客户控制。
- **成本优化**：小文件合并存储减少对象数量（元数据开销）；冷数据使用高密度 HDD 节点；压缩后存储（Snappy / Zstd）。
