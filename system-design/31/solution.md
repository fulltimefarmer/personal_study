# 31. 设计协作文档编辑系统 (Google Docs / Collaborative Editing)

## 题目

设计一个类似 Google Docs 的实时协作文档编辑系统，支持多用户同时编辑同一文档，实现实时同步和冲突解决。

---

## 需求澄清

### 功能性需求 (Functional Requirements)

- 用户可以创建、编辑、删除文档
- 多个用户可以同时编辑同一个文档
- 实时同步所有编辑者的操作，延迟 < 200ms
- 显示其他用户的编辑位置（光标和选中区域）
- 支持离线编辑，重连后自动同步
- 支持评论和建议模式
- 支持版本历史，可以回退到任意历史版本
- 支持富文本格式（粗体、斜体、列表、表格、图片等）
- 支持不同权限控制（只读、评论、编辑）
- 编辑历史（谁在什么时候改了什么）

### 非功能性需求 (Non-functional Requirements)

| 指标 | 要求 |
|------|------|
| 可用性 | 99.99%（高可用） |
| 延迟 | 实时同步 < 200ms |
| 一致性 | 最终一致性，操作有序 |
| 持久性 | 数据不丢失（WAL/预写日志） |
| 扩展性 | 支持百万级并发文档 |
| 离线支持 | 支持离线编辑，自动合并 |

### 容量估算 (Capacity Estimation)

假设：
- DAU：1000万
- 每个用户平均编辑 10 个文档
- 平均文档大小：50KB
- 每天活跃编辑用户：100万
- 平均每秒编辑操作：假设活跃用户每小时产生 60 次编辑操作
- 峰值编辑 QPS：100万 × 60 / 3600 ≈ 16,667 ops/s
- 峰值连接数：并发在线用户约 50万

**存储估算：**
- 文档总数：1000万 × 10 = 1亿个文档
- 文档存储：1亿 × 50KB = 5TB
- 操作日志存储：每操作 100B × 16,667ops/s × 86400s ≈ 144GB/天
- 操作日志保留30天：144GB × 30 ≈ 4.3TB
- 总存储：约 10TB（当前）+ 流式增长

**带宽估算：**
- 入站：16,667 ops/s × 500B/op ≈ 8.3 MB/s
- 出站（广播）：16,667 ops/s × 500B/op × 平均3个协作者 ≈ 25 MB/s

---

## API 设计

### RESTful API

```
# 文档 CRUD
POST   /api/v1/documents              # 创建文档
GET    /api/v1/documents/:id          # 获取文档
PUT    /api/v1/documents/:id          # 更新文档元数据
DELETE /api/v1/documents/:id          # 删除文档（软删除）

# 权限管理
POST   /api/v1/documents/:id/collaborators   # 添加协作者
DELETE /api/v1/documents/:id/collaborators/:userId
GET    /api/v1/documents/:id/collaborators

# 版本历史
GET    /api/v1/documents/:id/versions          # 获取版本列表
GET    /api/v1/documents/:id/versions/:version # 获取特定版本
POST   /api/v1/documents/:id/restore/:version  # 恢复版本

# 评论
GET    /api/v1/documents/:id/comments
POST   /api/v1/documents/:id/comments
DELETE /api/v1/documents/:id/comments/:commentId

# 导出
GET    /api/v1/documents/:id/export?format=pdf|docx|txt
```

### WebSocket API（实时协作核心）

```
Client → Server:
{
  "type": "join",           // 加入文档编辑会话
  "docId": "doc123",
  "userId": "user456",
  "token": "jwt_token"
}

{
  "type": "operation",      // 编辑操作（OT/CRDT）
  "docId": "doc123",
  "version": 42,            // 当前文档版本号
  "operations": [...],      // 操作列表
  "cursor": { "line": 10, "col": 5 }  // 光标位置
}

{
  "type": "cursor_update",  // 光标位置更新
  "docId": "doc123",
  "position": { "line": 10, "col": 5 },
  "selection": { "startLine": 10, "startCol": 5, "endLine": 10, "endCol": 10 }
}

{
  "type": "ping"            // 心跳保活
}

Server → Client:
{
  "type": "operation_ack",  // 操作确认
  "docId": "doc123",
  "version": 43,
  "operationId": "op789"
}

{
  "type": "operation_broadcast",  // 广播其他用户的操作
  "docId": "doc123",
  "userId": "user789",
  "version": 43,
  "operations": [...]
}

{
  "type": "presence",       // 在线用户信息
  "docId": "doc123",
  "users": [
    { "userId": "user456", "cursor": {...}, "name": "Alice" }
  ]
}

{
  "type": "error",
  "code": "VERSION_CONFLICT",
  "message": "Version conflict, please retry"
}
```

---

## 数据模型

### 数据库选型

| 数据 | 存储 | 说明 |
|------|------|------|
| 文档元数据 | PostgreSQL (分片) | 用户-文档关系、权限 |
| 文档内容快照 | S3/Object Storage | 定期快照，廉价存储 |
| 操作日志 | Cassandra/HBase | 高写入吞吐，时序数据 |
| 在线状态 | Redis | 内存存储，TTL 自动过期 |
| 光标位置 | Redis Pub/Sub | 低延迟广播 |
| 文档缓存 | Redis | 热点文档缓存 |

### 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id          UUID PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    avatar_url  TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 文档表
CREATE TABLE documents (
    id              UUID PRIMARY KEY,
    title           VARCHAR(500) NOT NULL,
    owner_id        UUID NOT NULL REFERENCES users(id),
    content_snapshot_key TEXT,  -- S3 key for latest snapshot
    current_version BIGINT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    is_deleted      BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_updated ON documents(updated_at DESC);

-- 协作者权限表
CREATE TABLE collaborators (
    document_id UUID NOT NULL REFERENCES documents(id),
    user_id     UUID NOT NULL REFERENCES users(id),
    permission  VARCHAR(20) NOT NULL,  -- 'read', 'comment', 'write', 'owner'
    added_at    TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (document_id, user_id)
);

-- 操作日志表 (Cassandra schema)
CREATE TABLE operation_log (
    document_id UUID,
    version     BIGINT,
    user_id     UUID,
    operations  BLOB,           -- 序列化的操作列表
    created_at  TIMESTAMP,
    PRIMARY KEY (document_id, version)
) WITH CLUSTERING ORDER BY (version DESC);

-- 文档快照表 (定期创建)
CREATE TABLE snapshots (
    document_id UUID,
    version     BIGINT,
    snapshot_key TEXT,          -- S3 key
    size_bytes  BIGINT,
    created_at  TIMESTAMP,
    PRIMARY KEY (document_id, version)
);

-- 评论表
CREATE TABLE comments (
    id              UUID PRIMARY KEY,
    document_id     UUID NOT NULL,
    user_id         UUID NOT NULL,
    content         TEXT NOT NULL,
    anchor_key      VARCHAR(100),  -- 锚定到文档中某位置
    resolved        BOOLEAN DEFAULT FALSE,
    parent_id       UUID,          -- 嵌套回复
    created_at      TIMESTAMP DEFAULT NOW()
);
```

### 文档内容模型

文档内容使用树形结构表示，类似 DOM 树：

```json
{
  "root": {
    "type": "document",
    "children": [
      {
        "type": "paragraph",
        "id": "p1",
        "children": [
          { "type": "text", "text": "Hello ", "attrs": {} },
          { "type": "text", "text": "World", "attrs": { "bold": true } }
        ]
      },
      {
        "type": "table",
        "id": "t1",
        "children": [
          {
            "type": "table_row",
            "children": [
              { "type": "table_cell", "children": [{ "type": "text", "text": "A" }] }
            ]
          }
        ]
      }
    ]
  }
}
```

---

## 高层次架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           CDN / Static Assets                            │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Load Balancer (Nginx)                           │
│                     WebSocket-aware, sticky sessions                     │
└──────────────────────────────────────────────────────────────────────────┘
          │                           │                          │
          ▼                           ▼                          ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   API Gateway    │   │  WebSocket GW 1  │   │  WebSocket GW 2  │
│   (REST APIs)    │   │                  │   │                  │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────────────────────────────┐
│  Document        │   │         Collaboration Service             │
│  Service         │   │                                          │
│ (CRUD, 元数据)    │   │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
└────────┬─────────┘   │  │  OT/CRDT│  │Presence  │  │Cursor  │  │
         │             │  │  Engine  │  │ Service  │  │Service │  │
         │             │  └────┬────┘  └────┬─────┘  └───┬────┘  │
         │             └───────┼────────────┼────────────┼───────┘
         │                     │            │            │
         ▼                     ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Message Bus (Kafka)                        │
│                操作日志/事件/通知 统一消息管道                       │
└─────────────────────────────────────────────────────────────────┘
         │                     │                       │
         ▼                     ▼                       ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  PostgreSQL   │   │    Cassandra      │   │   Redis Cluster   │
│  (元数据/权限) │   │  (操作日志/版本)   │   │  (Session/缓存)   │
└──────────────┘   └──────────────────┘   └──────────────────┘
         │
         ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   S3/Blob Store  │   │  Search Engine   │   │  Analytics       │
│  (文档快照/附件)  │   │  (Elasticsearch)  │   │  (ClickHouse)    │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

### 数据流：实时编辑流程

```
┌─────────┐                    ┌──────────────┐               ┌─────────┐
│ Client A│                    │Collaboration │               │ Client B│
│ (编辑者)│                    │   Service    │               │ (查看者)│
└────┬────┘                    └──────┬───────┘               └────┬────┘
     │                               │                            │
     │  1. WebSocket Connect         │                            │
     │──────────────────────────────>│                            │
     │  2. Join Document Session     │                            │
     │──────────────────────────────>│                            │
     │                               │  3. 加载最新文档快照        │
     │                               │──────> S3/Cache            │
     │  4. 文档内容 + 在线用户列表     │                            │
     │<──────────────────────────────│                            │
     │                               │  5. Presence广播           │
     │                               │───────────────────────────>│
     │                               │                            │
     │  6. 输入操作 (insert/delete)   │                            │
     │──────────────────────────────>│                            │
     │                               │  7. OT/CRDT转换             │
     │                               │  8. 写入操作日志             │
     │                               │──────> Cassandra            │
     │  9. ACK确认                   │                            │
     │<──────────────────────────────│  10. 广播操作给B            │
     │                               │───────────────────────────>│
     │                               │  11. B应用操作              │
     │                               │                            │
     │  12. Cursor位置更新            │                            │
     │──────────────────────────────>│  13. 广播Cursor更新         │
     │                               │───────────────────────────>│
```

---

## 核心深入

### 1. 冲突解决算法：OT vs CRDT

这是协作文档编辑最核心的技术选型。

#### Operational Transformation (OT)

**原理：** 对操作进行变换（transform），使得不同客户端上的操作可以正确合并。

```
客户端A (时间线):  insert("a", 0) ──────────► 收到B的op: insert("b", 3)
                                              transform后: insert("b", 4)

客户端B (时间线):  insert("c", 2) ──────────► 收到A的op: insert("a", 0)
                                              transform后: insert("a", 0)

Server: 确定操作顺序（基于到达时间或逻辑时钟）
  A's op先: insert("a", 0)
  B's op后: insert("c", 2) [不做transform, 直接转发]
```

**OT 变换函数伪代码：**

```python
def transform(op_a, op_b):
    """
    变换 op_a 使其在 op_b 之后执行时仍然正确
    """
    if op_a.type == 'insert' and op_b.type == 'insert':
        if op_a.position < op_b.position:
            return op_a  # 位置不变
        elif op_a.position > op_b.position:
            return InsertOp(op_a.text, op_a.position + len(op_b.text))
        else:  # 同一位置
            # 根据用户ID或优先级决定顺序
            if op_a.user_id < op_b.user_id:
                return op_a
            else:
                return InsertOp(op_a.text, op_a.position + len(op_b.text))
    
    elif op_a.type == 'delete' and op_b.type == 'insert':
        if op_a.position >= op_b.position:
            return DeleteOp(op_a.position + len(op_b.text), op_a.length)
        return op_a
    
    elif op_a.type == 'insert' and op_b.type == 'delete':
        if op_a.position > op_b.position:
            return InsertOp(op_a.text, op_a.position - op_b.length)
        return op_a
    
    # ... 更多组合情况
```

**OT 优缺点：**

| 优点 | 缺点 |
|------|------|
| 经过 Google Docs 验证，成熟方案 | 必须依赖中央服务器做排序 |
| 操作序列直观，易于调试 | 对网络分区（network partition）容忍性差 |
| 转换算法有数学证明 | 增量添加操作类型时，transform 矩阵复杂度 O(n²) |
| 带宽消耗低 | 需要所有客户端连接到同一服务器 |

#### CRDT (Conflict-free Replicated Data Types)

**原理：** 设计数据结构使得并发操作始终可交换（commutative），无需中央协调。

**RGA (Replicated Growable Array) 实现示例：**

```python
class RGADocument:
    """基于 RGA 的 CRDT 文档"""
    
    def __init__(self):
        self.atoms = {}  # atom_id -> Atom
        
    class Atom:
        def __init__(self, id, value, left_origin, right_origin):
            self.id = id            # 全局唯一ID: (lamport_clock, site_id)
            self.value = value      # 字符或删除标记(tombstone)
            self.left = left_origin   # 左邻居ID
            self.right = right_origin # 右邻居ID
            self.deleted = False
    
    def local_insert(self, pos, char):
        """在本地位置插入字符"""
        left_atom = self.find_atom_at(pos - 1)
        right_atom = self.find_atom_at(pos)
        new_id = self.generate_id()  # (lamport++, site_id)
        atom = self.Atom(new_id, char, left_atom.id, right_atom.id)
        self.atoms[new_id] = atom
        return InsertOperation(new_id, char, left_atom.id, right_atom.id)
    
    def apply_remote_insert(self, op):
        """应用远程插入操作（幂等、可交换）"""
        if op.atom_id not in self.atoms:
            atom = self.Atom(op.atom_id, op.char, 
                            op.left_origin, op.right_origin)
            self.atoms[op.atom_id] = atom
    
    def local_delete(self, pos):
        atom_id = self.find_atom_at(pos).id
        self.atoms[atom_id].deleted = True
        return DeleteOperation(atom_id)
    
    def apply_remote_delete(self, op):
        """应用远程删除（幂等）"""
        if op.atom_id in self.atoms:
            self.atoms[op.atom_id].deleted = True
    
    def render(self):
        """渲染当前文档内容"""
        result = []
        # 从左边界 "begin" 开始遍历链表
        current = self.find_right_of("BEGIN_MARKER")
        while current.id != "END_MARKER":
            if not current.deleted:
                result.append(current.value)
            current = self.find_right_of(current.id)
        return "".join(result)
```

**CRDT 优缺点：**

| 优点 | 缺点 |
|------|------|
| 真正的去中心化，支持 P2P | 元数据开销大（每个字符有ID） |
| 不需要中央服务器排序 | Tombstone 永不删除，存储持续增长 |
| 天然支持离线编辑 | 某些格式（如列表）的CRDT实现复杂 |
| 可证明的正确性 | 渲染/排序需要额外计算 |

#### 方案选型建议

对于类似 Google Docs 的系统，推荐 **混合方案**：

- 使用 **OT** 作为主线协调算法（成熟、带宽低）
- 配合 **WAL (Write-Ahead Log)** 持久化操作（防丢失）
- 定期创建 **Snapshot** 减少重放开销
- 使用 **Vector Clock** 追踪因果关系
- 离线编辑场景使用 **CRDT** 策略作为补充

### 2. 文档版本管理

```
版本增长策略:
                                                    
Version 0     Version 1     Version 2     Version 3
   │              │              │              │
   ▼              ▼              ▼              ▼
[Snapshot]──→[Op 1～100]──→[Op 101～200]──→[Op 201～300]
   │                                           │
   │                              需要恢复Version 2时:
   │                              ┌─ 加载Snap V0
   │                              ├─ 重放 Op 1～200
   └──────────────────────────────┘
```

**快照策略：**
- 每 N 个操作（如 500）自动创建快照
- 每个编辑会话结束时创建快照
- 快照存储到 S3 (成本低，高可靠)
- 快照保留所有历史版本

```python
def restore_version(document_id, target_version):
    """恢复文档到指定版本"""
    # 1. 找到 <= target_version 的最近快照
    snapshot = db.find_nearest_snapshot(document_id, target_version)
    content = s3.load(snapshot.snapshot_key)
    
    # 2. 从快照版本开始，重放操作直到目标版本
    ops = db.load_operations(document_id, snapshot.version, target_version)
    for op in ops:
        content = apply_operation(content, op)
    
    return content
```

### 3. 实时通信架构优化

#### 连接管理（长连接 vs 短连接）

```
                        WebSocket 连接生命周期

Client ──WS Handshake──> Gateway ──Auth──> Auth Service
  │                         │
  │                    Subscribe ──> Redis Pub/Sub (doc:userId:presence)
  │                         │
  │                   Heartbeat / Ping 每 15s
  │                         │
  │                   Maintain TTL in Redis
  │                         │
  │                   Connection Drop
  │                         │
  │              Reconnect with last_version
  │                         │
  │              Catch-up: 重放缺失的操作
```

#### 网关层设计

```python
class CollaborationGateway:
    def __init__(self):
        self.connections = {}  # user_id -> WebSocket
        self.doc_sessions = {} # doc_id -> set of user_ids
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer()
        
    async def handle_message(self, user_id, message):
        if message.type == 'join':
            await self.handle_join(user_id, message.doc_id)
        elif message.type == 'operation':
            await self.handle_operation(user_id, message)
        elif message.type == 'cursor':
            # 光标更新直接用Pub/Sub绕过Kafka, 降低延迟
            await redis.publish(f"cursor:{message.doc_id}", {
                'user_id': user_id,
                'position': message.position
            })
    
    async def handle_operation(self, user_id, message):
        doc_id = message.doc_id
        # 1. 分配全局序列号
        seq = await redis.incr(f"doc:{doc_id}:version")
        
        # 2. OT Transform（检查并发操作）
        pending_ops = self.get_pending_ops(doc_id, user_id)
        transformed_ops = self.ot_engine.transform(message.operations, pending_ops)
        
        # 3. 写入Kafka (保证持久顺序)
        await self.kafka_producer.send(f"doc-ops-{doc_id}", {
            'seq': seq,
            'user_id': user_id,
            'operations': transformed_ops,
            'timestamp': now()
        })
        
        # 4. ACK给发送者（不等Kafka确认，异步ack）
        await self.send_to_user(user_id, {
            'type': 'ack',
            'version': seq
        })
        
        # 5. 广播给同一文档的其他用户
        for other_user in self.doc_sessions[doc_id]:
            if other_user != user_id:
                await self.send_to_user(other_user, {
                    'type': 'operation_broadcast',
                    'version': seq,
                    'user_id': user_id,
                    'operations': transformed_ops
                })
```

### 4. 一致性 vs 延迟的权衡

```
强一致性                    ←── 权衡轴 ──→                 弱一致性
    │                                                            │
Google Docs (OT + 中心服务器)                        Notion (类 CRDT + 本地优先)
    │                                                            │
操作延迟: ~100ms                                       操作延迟: ~0ms (本地)
冲突需立即解决                                          冲突稍后合并
依赖服务器可用                                           离线可用
```

**我们的选择：** 结合两者优势
- 在线模式：OT + 服务器仲裁（低延迟 + 强一致性）
- 离线模式：本地 CRDT 操作 + 重连后合并
- 重连合并策略：优先远程操作 → 本地操作重新应用到最新状态

### 5. 建议模式 (Suggestion Mode) 的设计

类似 Google Docs 的"建议"模式，本质上是延迟应用的 OT 操作：

```python
class Suggestion:
    def __init__(self, doc_id, user_id, operations):
        self.id = uuid4()
        self.doc_id = doc_id
        self.author_id = user_id
        self.operations = operations  # 建议的操作
        self.status = 'pending'       # pending / accepted / rejected
        self.base_version = current_version  # 建议基于的文档版本
        
class SuggestionManager:
    def apply_suggestion(self, doc, suggestion):
        """将建议应用到文档的显示副本中（不修改实际文档）"""
        display_doc = deepcopy(doc)
        display_doc.apply(suggestion.operations)
        return display_doc  # 渲染时显示建议的diff
    
    def accept_suggestion(self, suggestion):
        """接受建议：将建议操作正式提交"""
        # 检查建议的base_version是否过时
        if suggestion.base_version < doc.current_version:
            # 对建议进行OT转换，适应最新文档状态
            missing_ops = load_operations(suggestion.base_version, 
                                           doc.current_version)
            suggestion.operations = self.ot.transform(
                suggestion.operations, missing_ops)
        
        # 作为正式操作提交
        self.commit_operations(suggestion.operations)
        suggestion.status = 'accepted'
```

---

## 扩展性与高可用

### 1. 文档服务分片

```
                    ┌──────────────┐
                    │  Router      │
                    │  doc_id % N  │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Shard 0  │    │ Shard 1  │    │ Shard 2  │
    │ doc 0-1M │    │doc 1M-2M │    │doc 2M-3M │
    └──────────┘    └──────────┘    └──────────┘
```

- **分片键：** `document_id` 哈希分片
- **一致性哈希：** 添加/移除节点时最小化数据迁移
- **热点文档处理：** 对高频访问文档使用独立缓存节点

### 2. 缓存策略

```
L1: 客户端本地缓存 (IndexedDB)
    ↓ miss
L2: CDN (文档快照、静态资源)
    ↓ miss
L3: Redis Cluster (文档内容、在线状态、版本号)
    ↓ miss
L4: S3/Cassandra (持久化数据)
```

**缓存失效策略：**
- 文档内容缓存：Write-Through（写操作同时更新缓存）
- 版本号缓存：每次操作自动失效
- 在线用户缓存：TTL 30s + 心跳刷新

### 3. 故障恢复

```
故障场景                          恢复策略
───────────────────────────────────────────────────
WebSocket 连接断开    → 客户端指数退避重连 (1s, 2s, 4s... max 30s)
                      重连后发送 last_ack_version，服务端重放缺失操作
                      
协作服务实例宕机      → 其他实例接手连接（通过 Redis Pub/Sub 订阅）
                      Kafka 消费者组自动 Rebalance
                      
Kafka Broker 宕机     → 多副本 (replication factor = 3)
                      ISR (In-Sync Replicas) 保证数据不丢失
                      
数据库主节点宕机      → 自动 Failover 到从节点
                      应用层重试 + Circuit Breaker
                      
整个区域故障          → 多区域部署 + DNS Failover
                      数据跨区域异步复制
```

### 4. 监控与告警

```
┌─────────────────────────────────────────────────────┐
│                   监控指标体系                        │
├───────────────┬─────────────────────────────────────┤
│ 业务指标       │ 活跃文档数、编辑操作 QPS             │
│               │ 协作会话数、平均延迟                  │
├───────────────┼─────────────────────────────────────┤
│ 系统指标       │ CPU、内存、GC 暂停时间               │
│               │ WebSocket 连接数                     │
│               │ Kafka Consumer Lag                   │
├───────────────┼─────────────────────────────────────┤
│ 告警规则       │ P99 编辑延迟 > 500ms                │
│               │ Kafka Lag > 10000                    │
│               │ 错误率 > 0.1%                       │
│               │ 连接掉线率 > 5%                      │
└───────────────┴─────────────────────────────────────┘
```

### 5. 安全考虑

- **传输层：** WSS ( WebSocket over TLS) 加密所有实时通信
- **认证：** JWT token 在 WebSocket 握手时验证
- **授权：** 每次操作检查用户是否有文档编辑权限
- **速率限制：** 每用户每文档每秒最多 20 次操作
- **输入校验：** 服务端校验操作合法性（位置、类型、长度）
- **内容安全：** 敏感内容检测、XSS 过滤

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 冲突解决 | OT 为主（在线）+ CRDT 为辅（离线），平衡一致性与可用性 |
| 实时通信 | WebSocket + Redis Pub/Sub，Kafka 保证操作持久化与顺序 |
| 数据存储 | PostgreSQL(元数据) + Cassandra(操作日志) + S3(快照) |
| 版本管理 | WAL + 定期快照 + 选择性重放，支持任意版本回退 |
| 扩展性 | 一致性哈希分片 + 多级缓存 + 异步处理 |
| 高可用 | 多副本、自动故障转移、多区域部署 |
| 性能 | P99 同步延迟 < 200ms，支持百万并发协作 |

**CAP 取舍：** 选择 CP 模型（一致性 + 分区容错），在发生网络分区时优先保证数据一致性，牺牲部分可用性。对于实时协作场景，数据一致性（操作顺序一致性）比短暂的不可用更重要——因为不一致的文档内容会导致编辑混乱。

**关键技术创新点：**
1. OT/CRDT 混合策略解决离在线冲突
2. 光标位置使用 Redis Pub/Sub 而非 Kafka，降低延迟到 <50ms
3. 快照增量存储 + 分片操作日志的设计平衡存储成本与恢复速度
