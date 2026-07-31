# 题目：负载均衡

## 问题
请阐述负载均衡的概念、分类（四层 L4 vs 七层 L7），常见实现方案（Nginx、HAProxy），以及一致性哈希、session 保持等关键技术。

## 考点
- L4 vs L7 负载均衡的原理差异
- 常见负载均衡算法
- 一致性哈希的原理与虚拟节点
- Session 保持（Sticky Session）的实现方式
- 高可用架构（Keepalived、冗余部署）

## 解答

### 一、负载均衡的分类

#### 按 OSI 层级分类

| 类型 | 工作层 | 数据依据 | 性能 | 功能 |
|------|--------|---------|------|------|
| **L4 负载均衡** | 传输层 (TCP/UDP) | IP + 端口 | 高（只解析到传输层头部） | 简单分发、无法识别应用内容 |
| **L7 负载均衡** | 应用层 (HTTP/HTTPS) | URL、Header、Cookie、请求内容 | 相对低（需解析 HTTP 协议） | 内容路由、A/B 测试、限流 |

```
L4 请求处理：
Client → [L4-LB: 只看 IP:Port] → Backend Server

L7 请求处理：
Client → [L7-LB: 解析 URL/Header/Cookie] → 根据内容路由到不同后端
```

**Nginx 的 L4 vs L7**：
```nginx
# L4 负载均衡（stream 模块，TCP/UDP 代理）
stream {
    upstream mysql_servers {
        server 10.0.0.1:3306;
        server 10.0.0.2:3306;
    }
    server {
        listen 3306;
        proxy_pass mysql_servers;
    }
}

# L7 负载均衡（http 模块，HTTP 代理）
http {
    upstream app_servers {
        server 10.0.0.1:8080;
        server 10.0.0.2:8080;
    }
    server {
        listen 80;
        location /api/ {
            proxy_pass http://app_servers;
        }
        location /admin/ {
            proxy_pass http://admin_backend;  # 按路径分发
        }
    }
}
```

#### 按部署方式分类

| 类型 | 架构 | 优点 | 缺点 |
|------|------|------|------|
| **硬件负载均衡** | 专用设备（F5 BIG-IP） | 性能极高、功能丰富 | 贵 |
| **软件负载均衡** | Nginx / HAProxy / Traefik | 灵活、成本低 | 性能受限于服务器 |

---

### 二、常见负载均衡算法

#### 1. 轮询（Round Robin）

按顺序轮流分发到后端。

```
请求1 → Server A
请求2 → Server B
请求3 → Server C
请求4 → Server A  (循环)
```

#### 2. 加权轮询（Weighted Round Robin）

给不同性能的服务器分配不同权重。

```
Server A: weight=3
Server B: weight=2
Server C: weight=1

按比例分配：A A A B B C A A A B B C ...
```

#### 3. 最少连接（Least Connections）

将请求发送到当前活跃连接数最少的服务器。

#### 4. IP 哈希（IP Hash）

```
取客户端 IP 的哈希值 → 对服务器数量取模 → 分配到固定服务器

问题：服务器增减时，大部分映射会改变（雪崩效应）
```

#### 5. 一致性哈希（Consistent Hashing）

**核心思想**：将哈希值空间组织成一个虚拟的环（0 ~ 2^32-1），把服务器节点和请求都映射到这个环上，请求沿顺时针方向找到第一个节点。

```
哈希环示意图：

       0/2^32
    ┌──────────┐
    │          │
    │  Node A  │ hash("192.168.1.1") = 10000
    │    ●     │ hash("192.168.1.2") = 20000
    │          │ hash("192.168.1.3") = 30000
    │  Node C  │
    │    ●     │
    │          │    请求 hash("user_b") = 25000
    │          │    → 顺时针找到 Node C (30000)
    │          │
    │    ●     │
    │  Node B  │
    └──────────┘
```

**增减服务器的影响**：
- 传统哈希（取模法）：服务器数量变化 → 几乎全部映射失效
- 一致性哈希：只有该节点附近的部分数据需要重新分配

**虚拟节点**：为每个物理节点创建多个虚拟节点，分布在环上，解决数据倾斜问题。

```
Node A → A#1, A#2, A#3
Node B → B#1, B#2, B#3
Node C → C#1, C#2, C#3

这样数据分布更均匀，节点增减时的影响更分散
```

```java
// 一致性哈希简化实现
import java.util.*;

public class ConsistentHashing<T> {
    private final SortedMap<Integer, T> circle = new TreeMap<>();
    private final int virtualNodeCount;
    private final HashFunction hashFunction;

    public ConsistentHashing(int virtualNodeCount, Collection<T> nodes) {
        this.virtualNodeCount = virtualNodeCount;
        for (T node : nodes) add(node);
    }

    public void add(T node) {
        for (int i = 0; i < virtualNodeCount; i++) {
            int hash = hash(node.toString() + "#" + i);
            circle.put(hash, node);
        }
    }

    public void remove(T node) {
        for (int i = 0; i < virtualNodeCount; i++) {
            int hash = hash(node.toString() + "#" + i);
            circle.remove(hash);
        }
    }

    public T get(String key) {
        if (circle.isEmpty()) return null;
        int hash = hash(key);
        SortedMap<Integer, T> tailMap = circle.tailMap(hash);
        Integer nodeHash = tailMap.isEmpty() ? circle.firstKey() : tailMap.firstKey();
        return circle.get(nodeHash);
    }

    private int hash(String key) {
        // 实际使用 MurmurHash 或 MD5，这里简化为 hashCode
        return Math.abs(key.hashCode());
    }

    private interface HashFunction {}
}
```

```typescript
// TypeScript 一致性哈希
class ConsistentHashing<T extends string> {
    private circle: Map<number, T> = new Map();
    private sortedHashes: number[] = [];
    private virtualNodeCount: number;

    constructor(virtualNodeCount: number, nodes: T[]) {
        this.virtualNodeCount = virtualNodeCount;
        nodes.forEach(n => this.addNode(n));
    }

    private hash(key: string): number {
        let h = 0;
        for (let i = 0; i < key.length; i++) {
            h = ((h << 5) - h) + key.charCodeAt(i);
            h |= 0; // 转 32 位整数
        }
        return Math.abs(h);
    }

    addNode(node: T): void {
        for (let i = 0; i < this.virtualNodeCount; i++) {
            const h = this.hash(`${node}#${i}`);
            this.circle.set(h, node);
            this.sortedHashes.push(h);
        }
        this.sortedHashes.sort((a, b) => a - b);
    }

    removeNode(node: T): void {
        for (let i = 0; i < this.virtualNodeCount; i++) {
            const h = this.hash(`${node}#${i}`);
            this.circle.delete(h);
        }
        this.sortedHashes = [...this.circle.keys()].sort((a, b) => a - b);
    }

    getNode(key: string): T | undefined {
        if (this.sortedHashes.length === 0) return undefined;
        const h = this.hash(key);
        const idx = this.sortedHashes.findIndex(hash => hash >= h);
        const nodeHash = idx === -1 ? this.sortedHashes[0] : this.sortedHashes[idx];
        return this.circle.get(nodeHash);
    }
}
```

---

### 三、Nginx vs HAProxy

| 维度 | Nginx | HAProxy |
|------|-------|---------|
| 主要用途 | HTTP 反向代理、Web 服务器 | 专用负载均衡器 |
| L4 支持 | 需要 stream 模块（1.9+） | 原生支持 TCP/UDP |
| L7 支持 | 非常强（HTTP/2、rewrite、caching） | 强 |
| 性能 | 高（事件驱动 epoll） | 极高 |
| 健康检查 | 简单（passive） | 强大（active + passive） |
| 配置复杂度 | 中等 | 中等 |
| 脚本化 | Lua/JS (OpenResty / NJS) | Lua (辅助) |
| 典型场景 | Web 应用的通用代理 | 高并发 TCP/HTTP 代理 |

**实际组合常见**：Nginx 做业务层 L7 代理 → HAProxy 做传输层 L4 代理 → 后端服务

---

### 四、Session 保持（Sticky Session）

**问题**：默认负载均衡可能将同一个用户的请求分发到不同服务器，如果 Session 存储在服务器本地就会找不到。

**方案 1：IP Hash / 一致性哈希**
```
根据客户端 IP 将请求固定到某台服务器
问题：同一 IP 不等于同一用户（NAT 下多用户共享 IP），用户切换网络后 Session 丢失
```

**方案 2：Cookie 植入**
```
负载均衡器在首次响应中插入 Cookie（如 SERVERID=node2），
后续请求携带此 Cookie，负载均衡器据此路由到原服务器
```

```nginx
# Nginx sticky cookie
upstream backend {
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    # 需要 nginx-sticky-module 或 NGINX Plus
    sticky cookie srv_id expires=1h domain=.example.com path=/;
}
```

**方案 3：外部 Session 存储（推荐）**
```
将会话数据存入 Redis / Memcached，所有服务器共享读写
彻底解耦 Session 与具体服务器
```

```java
// Spring Session + Redis
@Configuration
@EnableRedisHttpSession
public class SessionConfig {
    @Bean
    public LettuceConnectionFactory connectionFactory() {
        return new LettuceConnectionFactory("redis-server", 6379);
    }
}
```

---

### 五、高可用（HA）架构

**单点故障问题**：负载均衡器本身如果宕机，全部服务不可用。

**解决方案**：

**VRRP（虚拟路由冗余协议）+ Keepalived**：
```
         VIP: 10.0.0.100 (虚拟 IP)
        ┌────────┴────────┐
   LB1 (Master)    LB2 (Backup)
   10.0.0.1         10.0.0.2

正常时：VIP 绑定在 Master 上
Master 宕机：Backup 检测到 → 接管 VIP → 成为新 Master
```

```bash
# Keepalived 配置示例
vrrp_instance VI_1 {
    state MASTER           # 或 BACKUP
    interface eth0
    virtual_router_id 51
    priority 100           # MASTER 优先级更高
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {
        10.0.0.100
    }
}
```

**DNS 级别高可用**：配置多个 A 记录，DNS 轮询返回不同的负载均衡器 IP。

---

### 六、健康检查

| 类型 | 方式 | 说明 |
|------|------|------|
| **被动健康检查** | 观察后端响应 | 请求失败就临时摘除，恢复后加回 |
| **主动健康检查** | 定期发送探测请求 | HTTP GET /health、TCP connect |
| **Nginx passive** | `max_fails` + `fail_timeout` | 默认被动检查 |
| **HAProxy active** | `check` + `option httpchk` | 支持主动检查 |

```nginx
# Nginx 被动健康检查
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.3:8080 backup;  # 备用服务器
}
```

---

## 总结
L4 负载均衡只看 IP:Port，性能高；L7 负载均衡解析应用协议，可以做内容路由。常见算法中，轮询最简单，加权轮询区分性能，一致性哈希在节点增减时影响最小。Session 保持的最好方案是共享存储（Redis）而非粘性会话。Keepalived + VRRP 提供负载均衡器本身的高可用。
