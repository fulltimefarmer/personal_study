# 48. 设计协作白板/画图工具 (Design Collaborative Whiteboard like Excalidraw/Miro)

## 题目

设计一个实时协作白板/画图工具，如 Excalidraw、Miro、Figma。支持多人实时协同编辑、图形绘制、撤销/重做、以及离线恢复。核心挑战在于实时冲突解决（CRDT/OT）、低延迟同步和大规模并发协作。

## 需求澄清

### 功能性需求

1. **图形绘制**: 矩形、圆形、线条、文本、自由绘制、图片插入
2. **图形编辑**: 移动、缩放、旋转、改变颜色/样式、组合/取消组合
3. **实时协作**: 多人同时编辑，实时看到彼此的修改
4. **光标同步**: 看到协作者的光标位置（Cursors Presence）
5. **撤销/重做 (Undo/Redo)**: 支持按操作历史撤销/重做
6. **版本历史**: 查看历史版本，可回滚到先前版本
7. **画布操作**: 放大/缩小/平移 (Zoom/Pan)
8. **导出/导入**: PNG、SVG、PDF 导出
9. **离线支持**: 离线编辑，重新上线后同步

### 非功能性需求

1. **低延迟同步**: 操作传播延迟 < 200ms (P99)
2. **冲突解决**: 自动解决冲突，不丢失数据
3. **高并发协作**: 单画布支持 50+ 人同时编辑
4. **数据一致性**: 所有协作者最终看到相同的内容
5. **高可用**: 99.9% 可用性
6. **安全**: 画板权限控制（查看/评论/编辑）

### 容量估算

```
假设:
  DAU: 100万
  平均每人每天创建/参与 3 个画板
  每个画板平均 200 个元素(shapes)
  每个元素 ~500B (JSON 序列化)

存储:
  画板总数 (活跃): 500万
  每个画板: 200 × 500B = 100KB
  总活跃数据: 500万 × 100KB ≈ 500GB
  版本快照: 每画板保持 50 个版本 → 500GB × 50 ≈ 25TB
  (保留最近版本，旧版本归档到S3)

操作频率:
  平均每用户每画板每分钟 10 个操作
  峰值同时在线: 50万用户
  峰值操作 QPS: 50万 × 10 / 60 ≈ 83K QPS

WebSocket 连接:
  峰值连接数: 50万
  每台服务器支撑: 10K 连接 → 需要 50 台 WebSocket 服务器

带宽:
  每个操作平均 200B
  峰值下行带宽: 83K × 200B ≈ 16.6 MB/s (服务器出站)
  (协作时每个操作需广播给房间内其他用户, 实际带宽更大)
```

## API设计

### REST API

```
POST   /api/v1/boards                    创建画板
GET    /api/v1/boards/{board_id}         获取画板元信息
GET    /api/v1/boards/{board_id}/export  导出画板
POST   /api/v1/boards/{board_id}/clone   克隆画板
GET    /api/v1/boards/{board_id}/history 获取版本历史
POST   /api/v1/boards/{board_id}/restore/{version}  回滚到指定版本

# 权限
PUT    /api/v1/boards/{board_id}/members/{user_id}   设置成员权限
```

### WebSocket 协作协议

```json
// Client → Server

// 1. 加入房间
{
  "type": "join",
  "board_id": "board_abc",
  "user_id": "user_123",
  "user_name": "张三",
  "cursor_position": {"x": 100, "y": 200},
  "last_ack_version": 42
}

// 2. 提交操作
{
  "type": "operation",
  "client_id": "client_timestamp_uuid",
  "operations": [
    {
      "op_type": "add_shape",
      "shape_id": "shape_xyz",
      "shape_type": "rectangle",
      "data": {
        "x": 100, "y": 200,
        "width": 300, "height": 200,
        "fill": "#ff0000",
        "stroke": "#000000",
        "stroke_width": 2
      }
    },
    {
      "op_type": "update_shape",
      "shape_id": "shape_abc",
      "data": {"x": 150, "y": 250}
    }
  ]
}

// 3. 光标移动
{
  "type": "cursor_move",
  "position": {"x": 500, "y": 300}
}

// 4. 离开房间
{
  "type": "leave"
}

// Server → Client

// 1. 文档快照 (加入时返回)
{
  "type": "snapshot",
  "board_id": "board_abc",
  "version": 42,
  "elements": [
    {"id": "shape_1", "type": "rectangle", "x": 100, "y": 200, ...},
    {"id": "shape_2", "type": "text", "x": 300, "y": 400, ...}
  ],
  "participants": [
    {"user_id": "user_456", "name": "李四", "cursor": {"x": 400, "y": 300}}
  ]
}

// 2. 远程操作广播
{
  "type": "remote_operation",
  "user_id": "user_456",
  "version": 43,
  "operations": [ ... ]
}

// 3. 确认 (ACK)
{
  "type": "ack",
  "client_id": "client_timestamp_uuid",
  "server_version": 43,
  "status": "applied"  // applied / conflict / rejected
}

// 4. 光标同步
{
  "type": "cursor_sync",
  "user_id": "user_456",
  "position": {"x": 500, "y": 300}
}

// 5. 用户加入/离开
{
  "type": "user_joined",
  "user_id": "user_789",
  "user_name": "王五"
}
{
  "type": "user_left",
  "user_id": "user_789"
}
```

## 数据模型

### 画板数据结构 (JSON)

```json
{
  "board_id": "board_abc",
  "version": 42,
  "elements": {
    "shape_1": {
      "id": "shape_1",
      "type": "rectangle",
      "x": 100, "y": 200,
      "width": 300, "height": 200,
      "angle": 0,
      "fill": "#ff0000",
      "stroke": "#000000",
      "stroke_width": 2,
      "opacity": 1.0,
      "locked": false,
      "group_id": null,
      "z_index": 1,
      "created_by": "user_123",
      "created_at": 1690000000,
      "updated_at": 1690000100
    },
    "text_1": {
      "id": "text_1",
      "type": "text",
      "x": 150, "y": 280,
      "width": 200, "height": 50,
      "text": "Hello World",
      "font_size": 16,
      "font_family": "Arial",
      "color": "#000000",
      "text_align": "center",
      "z_index": 2
    }
  },
  "element_order": ["shape_1", "text_1"],
  "metadata": {
    "title": "产品需求评审",
    "created_by": "user_123",
    "created_at": 1690000000,
    "updated_at": 1690000100
  }
}
```

### CRDT 数据结构设计

```
使用 RGA (Replicated Growable Array) 作为核心 CRDT 数据结构:

每个元素有一个全局唯一的 ID:
  element_id = {lamport_clock}:{client_id}

每个操作携带:
  - operation_id: {lamport_clock}:{client_id}
  - parent_version: 基于哪个版本的文档
  - element_id: 操作的目标元素
  - fields: 修改的字段和值

元素的所有属性均为 Last-Writer-Wins (LWW) Register:
  每个属性有独立的逻辑时钟，最后写入的值生效

元素顺序使用 Fractional Indexing:
  不是数组索引，而是分配可比较的"位置分数"
  z_index = "a0", "a1", "a2", "a0a0" (可无限插值)
  插入不需要更新其他元素
```

```python
class FractionalIndex:
    """分数索引: 用于 CRDT 中无冲突的列表排序"""
    
    @staticmethod
    def generate_between(a: str, b: str) -> str:
        """生成在 a 和 b 之间的索引"""
        if a is None and b is None:
            return "a0"
        if a is None:
            # 在 b 之前
            return chr(ord(b[0]) - 1) + "z" * (len(b) - 1) + "0"
        if b is None:
            # 在 a 之后
            return a + "0"
        
        # 找到第一个不同的字符位置
        i = 0
        while i < len(a) and i < len(b) and a[i] == b[i]:
            i += 1
        
        if i == len(a):
            # a 是 b 的前缀, 在 a 后插入
            return a + "0"
        if i == len(b):
            return b[:-1] + chr(ord(b[-1]) + 1)
        
        # 在 a[i] 和 b[i] 之间
        mid = chr((ord(a[i]) + ord(b[i])) // 2)
        return a[:i] + mid + "0"
```

### 操作日志 / 版本快照存储

```sql
-- 画板元信息
CREATE TABLE boards (
    board_id VARCHAR(32) PRIMARY KEY,
    title VARCHAR(255),
    created_by VARCHAR(64),
    current_version BIGINT NOT NULL DEFAULT 0,
    is_deleted TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 操作日志 (WAL, 所有操作先写这里)
CREATE TABLE operation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    board_id VARCHAR(32) NOT NULL,
    server_version BIGINT NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    client_id VARCHAR(128) NOT NULL,      -- 客户端操作ID(幂等去重用)
    operation_data JSON NOT NULL,         -- 操作内容
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE KEY uk_client_id (client_id),
    INDEX idx_board_version (board_id, server_version)
) ENGINE=InnoDB;

-- 文档快照 (定期生成)
CREATE TABLE board_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    board_id VARCHAR(32) NOT NULL,
    version BIGINT NOT NULL,
    snapshot_data LONGBLOB NOT NULL,      -- 压缩后的完整画板状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_board_version (board_id, version DESC)
) ENGINE=InnoDB;

-- 协作会话 (Redis/内存)
-- board:collab:{board_id} → {
--   participants: [{user_id, user_name, cursor, last_active}],
--   current_version: 42,
--   pending_ops: [...]
-- }
```

## 高层次架构

```
                          ┌──────────────────────────────┐
                          │          Client               │
                          │  ┌──────────────────────────┐ │
                          │  │  Canvas Renderer          │ │
                          │  │  (Canvas/SVG/WebGL)       │ │
                          │  │                           │ │
                          │  │  ┌────────────────────┐   │ │
                          │  │  │ Local CRDT State   │   │ │
                          │  │  │ - Elements Map     │   │ │
                          │  │  │ - Version Clock    │   │ │
                          │  │  │ - Pending Ops      │   │ │
                          │  │  │ - Undo/Redo Stack  │   │ │
                          │  │  └────────┬───────────┘   │ │
                          │  │           │               │ │
                          │  │  ┌────────▼───────────┐   │ │
                          │  │  │ Sync Engine        │   │ │
                          │  │  │ - OT/CRDT Transform │   │ │
                          │  │  │ - Offline Queue     │   │ │
                          │  │  └────────┬───────────┘   │ │
                          │  └───────────┼───────────────┘ │
                          └──────────────┼─────────────────┘
                                         │ WebSocket
                          ┌──────────────▼─────────────────┐
                          │      WebSocket Gateway          │
                          │  ┌────────────────────────────┐  │
                          │  │  Room Manager               │  │
                          │  │  - board_id → connections   │  │
                          │  │  - board_id → collab_state  │  │
                          │  └────────────┬───────────────┘  │
                          └───────────────┼──────────────────┘
                                          │
                          ┌───────────────▼──────────────────┐
                          │      Collaboration Service        │
                          │  ┌──────────────────────────────┐ │
                          │  │  Operation Processor          │ │
                          │  │  - 接收操作                   │ │
                          │  │  - 分配全局版本号              │ │
                          │  │  - 冲突解决 (CRDT/OT)         │ │
                          │  │  - 广播给其他客户端            │ │
                          │  └──────────────┬───────────────┘ │
                          │                 │                 │
                          │  ┌──────────────▼───────────────┐ │
                          │  │  Persistence Layer            │ │
                          │  │  - WAL (操作日志)             │ │
                          │  │  - Snapshot (定期快照)        │ │
                          │  │  - Redis (协作状态缓存)       │ │
                          │  └──────────────────────────────┘ │
                          └──────────────────┬───────────────┘
                                             │
                          ┌──────────────────▼───────────────┐
                          │  MySQL(操作日志) + Redis(缓存)    │
                          │  + S3(版本快照归档)               │
                          └──────────────────────────────────┘
```

### 数据流

```
操作同步流程 (OT/CRDT):

1. 用户在画布上拖拽一个矩形 (x: 100→150)
2. Client:
   a. 乐观应用 (立即在本地显示)
   b. 生成操作: {op: update, element: shape_1, x: 150, version: 42}
   c. 加入 pending queue
   d. 通过 WebSocket 发送到服务器
3. Server:
   a. 接收操作, 分配全局服务端版本号 (version: 43)
   b. 写入操作日志 (WAL)
   c. ACK 给发送方: {client_id: xxx, server_version: 43}
   d. 广播给房间内其他客户端
4. Other Clients:
   a. 接收远程操作
   b. 如果版本号是连续的 → 直接应用
   c. 如果版本号有跳跃 → 请求缺失操作 (catch-up)
   d. Transform 远程操作到本地状态 (如果本地有pending ops)
   e. 渲染新状态
```

## 核心深入

### 冲突解决: OT vs CRDT

| 维度 | OT (Operational Transformation) | CRDT (无冲突数据类型) |
|------|--------------------------------|---------------------|
| 原理 | 操作转换: 变基到一致状态 | 数据结构保证可交换/可结合 |
| 中心化需求 | 通常需要中心服务做转换 | 完全去中心化 |
| 复杂度 | 较高(操作组合爆炸) | 数据模型设计复杂 |
| 性能 | 轻量操作 | 元数据开销较大 |
| 离线支持 | 需要服务端重放 | 天然支持, merge无冲突 |
| 知名产品 | Google Docs, 腾讯文档 | Figma, Excalidraw, Notion |

**推荐 CRDT（对标Figma/Excalidraw）**:
- 场景: 图形编辑 (属性更新为主, 不是文本编辑)
- 优势: 天然支持离线编辑、不需要中心化冲突解决
- 劣势: 元数据开销 (每个属性需要逻辑时钟)

### CRDT 核心实现

```python
import uuid
import time

class LWWRegister:
    """Last-Writer-Wins Register: CRDT 的基础数据类型"""
    
    def __init__(self, value=None):
        self.value = value
        self.timestamp = 0
        self.peer_id = ""
    
    def set(self, value, peer_id):
        """更新值: 只有timestamp更大时才接受"""
        new_ts = self._generate_timestamp()
        if new_ts > self.timestamp or \
           (new_ts == self.timestamp and peer_id > self.peer_id):
            self.value = value
            self.timestamp = new_ts
            self.peer_id = peer_id
    
    def merge(self, other):
        """合并: CRDT 的关键可交换操作"""
        if other.timestamp > self.timestamp or \
           (other.timestamp == self.timestamp and other.peer_id > self.peer_id):
            self.value = other.value
            self.timestamp = other.timestamp
            self.peer_id = other.peer_id
    
    def _generate_timestamp(self):
        """混合逻辑时钟: Lamport + 物理时间的混合"""
        return max(int(time.time() * 1000), self.timestamp + 1)


class CRDTElement:
    """CRDT 画板元素: 每个属性都是 LWWRegister"""
    
    def __init__(self, element_id, peer_id):
        self.id = element_id
        self.type = LWWRegister()
        self.x = LWWRegister()
        self.y = LWWRegister()
        self.width = LWWRegister()
        self.height = LWWRegister()
        self.fill = LWWRegister()
        self.stroke = LWWRegister()
        self.deleted = LWWRegister()
        
        self.peer_id = peer_id
        self._registers = {
            'type': self.type, 'x': self.x, 'y': self.y,
            'width': self.width, 'height': self.height,
            'fill': self.fill, 'stroke': self.stroke, 'deleted': self.deleted
        }
    
    def apply_operation(self, op):
        """应用操作: 更新指定字段"""
        for field, value in op.fields.items():
            if field in self._registers:
                self._registers[field].set(value, self.peer_id)
    
    def merge(self, other):
        """合并另一个副本的此元素"""
        for field, register in self._registers.items():
            other_register = other._registers.get(field)
            if other_register:
                register.merge(other_register)
    
    def to_dict(self):
        """输出为JSON可序列化字典"""
        if self.deleted.value:
            return None
        return {field: reg.value for field, reg in self._registers.items()
                if reg.value is not None}


class CRDTDocument:
    """CRDT 文档: 包含所有元素的Map + 顺序"""
    
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.elements = {}        # element_id → CRDTElement
        self.element_order = []   # FractionalIndex 排序列表
        self.version = 0
    
    def apply_local_operation(self, operation):
        """本地操作: 立即乐观应用 + 分配版本号"""
        element_id = operation.element_id
        
        if operation.op_type == 'add_shape':
            element = CRDTElement(element_id, self.peer_id)
            element.apply_operation(operation)
            self.elements[element_id] = element
            # 分配分数索引位置
            index = FractionalIndex.generate_between(
                self.element_order[-1] if self.element_order else None, None
            )
            self.element_order.append(index)
            
        elif operation.op_type == 'update_shape':
            if element_id in self.elements:
                self.elements[element_id].apply_operation(operation)
                
        elif operation.op_type == 'delete_shape':
            if element_id in self.elements:
                self.elements[element_id].deleted.set(True, self.peer_id)
        
        self.version += 1
    
    def merge_remote_operation(self, operation):
        """合并远程操作到本地状态"""
        element_id = operation.element_id
        
        if operation.op_type == 'add_shape':
            if element_id not in self.elements:
                element = CRDTElement(element_id, operation.peer_id)
                element.apply_operation(operation)
                self.elements[element_id] = element
            else:
                self.elements[element_id].merge(
                    # 创建临时元素来合并
                    create_temp_element(operation)
                )
        elif operation.op_type in ('update_shape', 'delete_shape'):
            if element_id in self.elements:
                self.elements[element_id].apply_operation(operation)
        
        self.version = max(self.version, operation.server_version)
```

### 操作转换 (OT) vs CRDT 选择

```
          CRDT 更适合                           OT 更适合
          ──────────────                        ─────────
          图形/对象编辑                        文本协作编辑
          属性独立更新                         (字符串操作)
          无需中心化服务器                      需要保持操作顺序
          离线优先场景                         操作复杂性高时
          
  本项目 (白板) 选择 CRDT 的理由:
  1. 每个形状的属性更新是独立的 (x, y, width...)
  2. 不需要像文本那样处理字符串偏移
  3. 支持离线编辑 (飞机上/地铁上也能画图)
  4. CRDT merge 逻辑简单, 心智负担小
```

### 撤销/重做设计

```python
class UndoRedoManager:
    """基于操作的撤销/重做"""
    
    def __init__(self):
        self.undo_stack = []   # [(operation, inverse_operation)]
        self.redo_stack = []
        self.max_history = 100
    
    def push(self, operation, inverse_operation):
        """记录操作和它的逆操作"""
        self.undo_stack.append((operation, inverse_operation))
        self.redo_stack.clear()  # 新操作清理 redo
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def undo(self):
        """撤销: 应用逆操作"""
        if not self.undo_stack:
            return None
        op, inverse = self.undo_stack.pop()
        self.redo_stack.append((op, inverse))
        return inverse  # 返回逆操作, 应用到本地和远程
    
    def redo(self):
        """重做: 重新应用操作"""
        if not self.redo_stack:
            return None
        op, inverse = self.redo_stack.pop()
        self.undo_stack.append((op, inverse))
        return op


# 逆操作生成
def compute_inverse(operation, current_state):
    """计算操作的逆操作"""
    if operation.op_type == 'add_shape':
        return {'op_type': 'delete_shape', 'element_id': operation.element_id}
    elif operation.op_type == 'update_shape':
        # 从当前状态获取旧值
        old_values = current_state.get_element(operation.element_id)
        return {'op_type': 'update_shape', 'element_id': operation.element_id,
                'fields': old_values}
    elif operation.op_type == 'delete_shape':
        # 恢复删除: 需要保存删除前的完整状态
        saved_state = operation.saved_state_before_delete
        return {'op_type': 'add_shape', 'element_id': operation.element_id,
                'fields': saved_state}
```

### 离线支持架构

```
┌─────────────────────────────────────────────┐
│              Client 端                       │
│                                              │
│  ┌────────────────────┐                     │
│  │  Operation Queue   │                     │
│  │  (IndexedDB)       │                     │
│  │                    │  Online → 同步到服务端│
│  │  [op1, op2, op3...]│  Offline → 本地存储  │
│  └────────┬───────────┘                     │
│           │                                  │
│  ┌────────▼───────────┐                     │
│  │  Local CRDT State  │                     │
│  │  (IndexedDB/内存)   │                     │
│  └────────────────────┘                     │
│                                              │
└─────────────────────────────────────────────┘
                │ 重新上线
                ▼
┌─────────────────────────────────────────────┐
│           Server                             │
│                                              │
│  1. 客户端上传离线操作队列                      │
│  2. 服务器按操作时间戳排序                      │
│  3. 重新分配服务端版本号                        │
│  4. 合并到操作日志                             │
│  5. 冲突解决: LWW自动处理 (最新时间戳胜出)       │
│  6. 广播合并后的操作                           │
└─────────────────────────────────────────────┘
```

### 版本快照策略

```
快照策略: 混合策略

生成时机:
  - 每 100 个操作 或 每 5 分钟 → 异步生成快照
  - 用户主动保存 → 同步生成快照

快照 + WAL 恢复:
  最新快照 (version=100) + 重放操作101-142 → 当前状态 (version=142)

存储:
  最近 50 个快照 → Redis/MySQL (快速恢复)
  更早的快照 → S3 (归档, 低频访问)
  操作日志 (WAL) → MySQL 分区表 (保留 90 天)
```

## 扩展性与高可用

### 协作房间的扩展

```
单画板 50+ 人同时编辑时的调度策略:

方案1: 负载均衡 + 共享状态
  每个 WebSocket server 维护独立连接池
  操作通过 Kafka/Redis PubSub 跨 server 广播
  优势: 无单点瓶颈

方案2: 房间亲和性 + 状态迁移
  同一画板的所有连接路由到同一 server (一致性哈希)
  房间太大 → 复制房间状态到多个 server
  优势: 减少跨 server 通信

推荐方案: 方案1 (共享状态 + PubSub广播)
```

### 监控告警

| 指标 | 阈值 |
|------|------|
| 操作同步延迟 P99 | > 500ms |
| 操作冲突率 | > 5% |
| WebSocket 断连率 | > 1% |
| 操作日志写入延迟 | > 100ms |
| 快照生成失败率 | > 1% |
| 房间参与人数(异常) | > 200 (可能是攻击) |

## 总结

1. **CRDT over OT**: 图形/白板协作选 CRDT，属性级 LWW Register，天然支持离线 + 自动merge
2. **分数索引排序**: Fractional Indexing 解决列表排序的CRDT问题，插入不需要更新其他元素
3. **操作日志 (WAL)**: 所有操作先写操作日志，再处理，保证不丢数据
4. **快照 + WAL 恢复**: 定期快照 + 操作日志增量恢复，平衡恢复速度与存储成本
5. **乐观应用**: 客户端先显示修改再同步服务端，P99延迟 < 200ms
6. **离线队列**: IndexedDB 持久化离线操作，重上线后按时间戳排序合并
7. **撤销/重做**: 操作级撤销，记录每个操作的逆操作，CUD 都有对应逆操作
8. **光标同步**: 独立于操作同步的低优先级通道，降频 (每100ms最多一次)
9. **权限控制**: 查看者不能操作但能看实时同步，评论者可在侧边栏评论

面试中可能追问: 如果两个用户同时修改了同一个形状的同一个属性(color)，CRDT 如何决策? 如何处理"删除"操作的undo(需要恢复删除前的完整状态)?
