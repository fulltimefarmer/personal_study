# 47. 设计服务网格 (Design Service Mesh like Istio)

## 题目

设计一个服务网格（Service Mesh），类似 Istio/Linkerd。服务网格是微服务架构中处理服务间通信的专用基础设施层，通过 Sidecar 代理模式实现流量管理、可观测性和安全性，无需修改应用代码。

## 需求澄清

### 功能性需求

1. **流量管理 (Traffic Management)**: 路由（金丝雀发布/蓝绿部署）、负载均衡、超时、重试、断路器
2. **服务发现 (Service Discovery)**: 自动发现服务实例，健康检查
3. **负载均衡 (Load Balancing)**: 支持 Round-Robin、Least-Conn、一致性哈希等策略
4. **可观测性 (Observability)**: 分布式追踪、指标收集（Prometheus）、日志
5. **安全通信 (Security)**: mTLS（双向TLS）、身份认证、授权（RBAC）
6. **故障注入 (Fault Injection)**: 延迟注入、错误注入（混沌工程）
7. **流量镜像 (Traffic Mirroring)**: 将实时流量复制到测试服务
8. **速率限制 (Rate Limiting)**: 服务级别的请求速率控制

### 非功能性需求

1. **高性能**: Sidecar 代理延迟增量 < 5ms (P99)
2. **低资源消耗**: 每个 Sidecar 内存 < 50MB, CPU < 0.1 core
3. **高可用**: 控制面故障不影响数据面（代理继续工作）
4. **可扩展性**: 支持数万个服务实例
5. **透明性**: 应用代码零改动

### 容量估算

```
假设集群规模:
  服务数: 5,000
  总Pod数: 50,000 (每个服务平均 10 个副本)
  每个Pod一个 Sidecar 代理
  总 Sidecar: 50,000

每秒服务间请求:
  平均 QPS/Pod: 500
  总网格内请求: 50,000 × 500 = 25M QPS

控制面配置推送:
  每服务配置大小: ~10KB (路由规则/策略)
  总配置大小: 5,000 × 10KB ≈ 50MB
  变更频率: 平均 100次/分钟 (服务扩缩、配置更新)
  推送带宽: 50MB × 100/min ≈ 83MB/s

追踪数据:
  采样率 1%: 25M × 0.01 = 250K spans/s
  每个 span ~2KB: 500MB/s 追踪数据

指标数据:
  每个Pod 500 个指标 × 50,000 Pod = 25M 指标
  Prometheus 存储: 25M × ~3 bytes/样本 × 15天 ≈ 100GB
```

## API设计

### 控制面 API (xDS 协议)

服务网格的核心是 Envoy 的 xDS (Discovery Service) 协议，控制面通过 gRPC 流推送配置：

```
xDS API 类型:
  LDS (Listener Discovery Service)      - 监听器配置
  RDS (Route Discovery Service)         - 路由配置
  CDS (Cluster Discovery Service)       - 上游集群
  EDS (Endpoint Discovery Service)      - 集群端点
  SDS (Secret Discovery Service)        - 证书/密钥

控制面 → Sidecar (gRPC 双向流):
  1. Sidecar 启动 → 连接控制面
  2. 发送 Node 信息 (服务名、命名空间、IP等)
  3. 控制面根据 Node 匹配配置
  4. 推送匹配的 xDS 配置 (初始全量, 后续增量)
  5. 持续监听变更, 推送到所有关联的 Sidecar
```

### Istio 自定义资源 (CRD)

```yaml
# VirtualService - 流量路由规则
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews-route
spec:
  hosts:
    - reviews
  http:
    - match:
        - headers:
            end-user:
              exact: jason
      route:
        - destination:
            host: reviews
            subset: v2      # 特定用户路由到 v2
    - route:                # 默认路由
        - destination:
            host: reviews
            subset: v1
          weight: 90        # 90% 流量到 v1
        - destination:
            host: reviews
            subset: v3
          weight: 10        # 10% 流量到 v3 (金丝雀)

---
# DestinationRule - 流量策略
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews-destination
spec:
  host: reviews
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN     # 最少连接负载均衡
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 10
        maxRequestsPerConnection: 5
    outlierDetection:        # 断路器/异常检测
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
    - name: v3
      labels:
        version: v3
```

## 数据模型

### 控制面配置存储

```sql
-- 服务注册表
CREATE TABLE services (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL DEFAULT 'default',
    mesh_name VARCHAR(255) DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name_namespace (namespace, name)
) ENGINE=InnoDB;

-- 服务实例/端点表
CREATE TABLE endpoints (
    id VARCHAR(64) PRIMARY KEY,
    service_id VARCHAR(64) NOT NULL,
    pod_name VARCHAR(255),
    ip_address VARCHAR(45) NOT NULL,
    port INT NOT NULL,
    protocol VARCHAR(16) DEFAULT 'HTTP',
    labels JSON COMMENT '{"version":"v1","region":"us-east"}',
    health_status ENUM('HEALTHY','UNHEALTHY','DRAINING') DEFAULT 'HEALTHY',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_service (service_id, health_status)
) ENGINE=InnoDB;

-- VirtualService 配置表 (也可直接存在 etcd/K8s CRD)
CREATE TABLE virtual_services (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    hosts JSON NOT NULL,
    http_routes JSON,
    tcp_routes JSON,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name_namespace (namespace, name)
) ENGINE=InnoDB;

-- DestinationRule 配置表
CREATE TABLE destination_rules (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    host VARCHAR(255) NOT NULL,
    subsets JSON,
    traffic_policy JSON,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name_namespace (namespace, name)
) ENGINE=InnoDB;
```

## 高层次架构

```
┌──────────────────────────────────────────────────────────────┐
│                      控制面 (Control Plane)                   │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Pilot     │  │   Citadel    │  │    Galley          │   │
│  │  (服务发现)  │  │  (证书管理)   │  │  (配置验证/分发)    │   │
│  │             │  │              │  │                    │   │
│  │ - xDS推送   │  │ - mTLS证书   │  │ - 配置校验          │   │
│  │ - K8s Watch │  │ - 身份认证   │  │ - 配置转译          │   │
│  │ - 路由生成  │  │ - CA服务     │  │                    │   │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘   │
│         │                │                     │              │
│         └────────────────┼─────────────────────┘              │
│                          │ etcd/K8s API Server               │
│                          │ (配置存储)                         │
└──────────────────────────┼──────────────────────────────────┘
                           │ xDS gRPC Stream (双向流)
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                      数据面 (Data Plane)                     │
│                          │                                   │
│  ┌───────────────────────┼───────────────────────────────┐  │
│  │                    Pod (Service A)                     │  │
│  │  ┌───────────┐            ┌──────────────────────┐    │  │
│  │  │  App A    │──localhost─►│  Envoy Sidecar      │    │  │
│  │  │ (业务容器) │            │  ┌────────────────┐ │    │  │
│  │  │           │            │  │ LDS/RDS/CDS/EDS│ │    │  │
│  │  │           │            │  │ 路由/负载均衡    │ │    │  │
│  │  │           │            │  │ mTLS/限流/熔断  │ │    │  │
│  │  │           │            │  │ 指标/追踪/日志  │ │    │  │
│  │  │           │            │  └────────────────┘ │    │  │
│  │  └───────────┘            └──────────┬─────────┘    │  │
│  └──────────────────────────────────────┼──────────────┘  │
│                                         │                  │
│  ┌──────────────────────────────────────┼──────────────┐  │
│  │                    Pod (Service B)    │               │  │
│  │  ┌───────────┐           ┌───────────▼────────┐     │  │
│  │  │  App B    │◄──localhost│  Envoy Sidecar     │     │  │
│  │  └───────────┘           └────────────────────┘     │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 请求流

```
Service A → Service B 的完整请求路径:

1. App A 发出请求: GET http://service-b/api/hello
2. Iptables 规则将流量重定向到 Sidecar (入站:15001, 出站:15006)
3. Envoy Sidecar (出站):
   a. 查 RDS: 目标 service-b → 匹配的路由规则
   b. 查 CDS: service-b 的上游集群配置
   c. 查 EDS: 所有健康的 service-b 端点
   d. 执行负载均衡策略选择一个端点
   e. 应用超时、重试、断路器策略
   f. 发起 mTLS 连接 (如果启用)
4. Envoy Sidecar (入站, Service B 侧):
   a. 验证 mTLS 证书
   b. 应用入站策略 (速率限制、授权检查)
   c. 记录访问日志、指标、追踪span
   d. 转发到 App B (localhost)

流量劫持 (Iptables):
  # 所有出站流量被 REDIRECT 到 Sidecar 的 15001 端口
  iptables -t nat -A OUTPUT -p tcp -j REDIRECT --to-port 15001
```

## 核心深入

### 数据面代理选型

| 代理 | 语言 | 延迟增量 | 内存/实例 | 特点 |
|------|------|---------|----------|------|
| Envoy | C++ | < 2ms | ~30MB | 功能最丰富, 事实标准 |
| Linkerd-proxy | Rust | < 1ms | ~10MB | 极简极快, 功能较少 |
| MOSN | Go | ~5ms | ~50MB | 蚂蚁开源, 阿里系 |
| NGINX | C | < 1ms | ~5MB | 轻量但不支持xDS |

推荐 Envoy（行业标准）或 Linkerd-proxy（对性能极敏感）。

### xDS 协议设计

```protobuf
// Envoy xDS 核心协议

service AggregatedDiscoveryService {
  rpc StreamAggregatedResources(stream DiscoveryRequest)
      returns (stream DiscoveryResponse);
}

message DiscoveryRequest {
  string version_info = 1;          // 上次接收的版本，用于增量更新
  Node node = 2;                     // 请求者身份信息
  repeated string resource_names = 3; // 订阅的具体资源名
  string type_url = 4;              // "type.googleapis.com/envoy.config.listener.v3.Listener"
  string response_nonce = 5;         // ACK/NACK 用的 nonce
  Status error_detail = 6;           // NACK时携带错误信息
}

message DiscoveryResponse {
  string version_info = 1;
  repeated Any resources = 2;        // 匹配的配置资源
  string type_url = 3;
  string nonce = 4;
  bool is_delta = 5;                // 是否增量推送
}
```

**增量 xDS (Delta xDS)** 减少全量推送开销:
```
初始连接: 全量推送所有匹配资源
后续变更: 只推送变更的资源
  - resources_to_add
  - resources_to_remove
  - 大规模集群(10K+服务)必需
```

### 服务发现实现

```
服务发现流程:

1. Pilot 监听 K8s API Server:
   - Watch Service, Endpoints, Pod 资源变化
   - 将 K8s 原生概念转化为 Envoy 的 CDS/EDS 模型

2. 服务抽象层次:
   K8s Service → Envoy Cluster (CDS)
   K8s Endpoints → Envoy ClusterLoadAssignment (EDS)

3. 流量路由:
   VirtualService → Envoy RouteConfiguration (RDS)
   DestinationRule → Envoy Cluster配置

4. 健康检查:
   - 主动检查: Envoy 定期发起 HTTP/TCP 健康探测
   - 被动检查: Outlier Detection (基于请求失败率标记异常端点)
   - K8s 探针: Readiness/Liveness Probe → Endpoint状态
```

### mTLS 实现

```
           ┌───────────┐
           │  Citadel  │  (证书颁发机构 / CA)
           │           │
           │ - 签发证书 │
           │ - 轮换证书 │
           │ - 吊销列表 │
           └─────┬─────┘
                 │ SDS (Secret Discovery Service)
                 │ 推送证书 + 私钥
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│Envoy A│   │Envoy B│   │Envoy C│
│cert_A │   │cert_B │   │cert_C │
│private│   │private│   │private│
│key_A  │   │key_B  │   │key_C  │
└───┬───┘   └───┬───┘   └───┬───┘
    │           │           │
    │  mTLS Handshake       │
    │◄─────────────────────►│
    │    互相验证证书        │
    │    加密通道建立         │
    │                       │

证书结构 (SPIFFE格式):
  spiffe://cluster.local/ns/default/sa/service-a
  └─────┬─────┘ └─────┬─────┘ └────┬─────┘ └───┬───┘
    trust domain   namespace    service     service
                                account     account

认证流程:
1. Sidecar A 发起 TLS 连接到 Sidecar B
2. Sidecar B 出示证书
3. Sidecar A 向 Citadel 验证 B 的证书
4. 检查 B 的身份是否在允许列表中 (AuthorizationPolicy)
5. 建立加密通道
```

### 流量管理核心算法

```python
class TrafficRouter:
    """路由器: HTTP Header/Path 匹配 + 权重分流"""

    def route(self, request, virtual_service):
        for rule in virtual_service.http_routes:
            if self._match(request, rule.match):
                destinations = rule.route
                # 按权重选择一个子集
                subset = self._weighted_select(destinations)
                endpoints = self.get_endpoints(
                    rule.host, subset, request
                )
                return self._load_balance(endpoints, rule.load_balancer)
        return self.get_default_endpoints(virtual_service.hosts[0])

    def _weighted_select(self, destinations):
        """权重随机选择"""
        total = sum(d.weight for d in destinations)
        r = random.randint(0, total - 1)
        cumulative = 0
        for d in destinations:
            cumulative += d.weight
            if r < cumulative:
                return d.subset
        return destinations[-1].subset


class CircuitBreaker:
    """断路器: 防止故障扩散"""

    def __init__(self):
        self.state = 'CLOSED'           # CLOSED → OPEN → HALF_OPEN
        self.failure_count = 0
        self.last_failure_time = 0
        self.threshold = 5              # 连续 5 次失败 → OPEN
        self.timeout = 30               # 30 秒后尝试 HALF_OPEN

    def call(self, func):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpen()

        try:
            result = func()
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = 'OPEN'
            raise


class OutlierDetector:
    """异常检测: 自动剔除不健康的端点"""

    def __init__(self):
        self.consecutive_5xx = {}
        self.ejected_endpoints = {}

    def record_response(self, endpoint, status_code):
        if 500 <= status_code < 600:
            self.consecutive_5xx[endpoint] = \
                self.consecutive_5xx.get(endpoint, 0) + 1

        if self.consecutive_5xx.get(endpoint, 0) >= 5:
            self.eject(endpoint, duration=30)  # 剔除 30 秒

    def eject(self, endpoint, duration):
        self.ejected_endpoints[endpoint] = time.time() + duration

    def is_available(self, endpoint):
        ejected_until = self.ejected_endpoints.get(endpoint, 0)
        return time.time() > ejected_until
```

### 可观测性架构

```
┌─────────────────────────────────────────────────────────┐
│                     Envoy Sidecar                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Metrics    │  │   Tracing    │  │   Access Log  │  │
│  │  (Prometheus)│  │  (Zipkin/Ja- │  │   (stdout)    │  │
│  │              │  │   eger/OTLP) │  │               │  │
│  │ - 请求量     │  │              │  │ - 请求/响应   │  │
│  │ - 延迟分布   │  │ - Span生成   │  │ - 状态码      │  │
│  │ - 错误率     │  │ - B3/Zipkin  │  │ - 延迟        │  │
│  │ - 连接数     │  │   传播       │  │ - 上下游      │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
└─────────┼─────────────────┼─────────────────┼───────────┘
          │                 │                 │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │Prometheus │     │  Jaeger   │     │Fluentd/ES │
    │ + Grafana │     │           │     │           │
    │           │     │           │     │           │
    │ 告警规则  │     │ 调用链    │     │ 日志聚合  │
    └───────────┘     └───────────┘     └───────────┘
```

## 扩展性与高可用

### 控制面多副本

```
┌──────────────────────────────────────┐
│  K8s API Server (内置HA)             │
└──────────────────┬───────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌───▼───┐
│Pilot 1│    │ Pilot 2 │    │Pilot 3│
│(主)    │    │ (备)    │    │ (备)  │
└───┬───┘    └────┬────┘    └───┬───┘
    │              │              │
    │ gRPC Streams │              │
    │              │              │
┌───▼──────────────▼──────────────▼───┐
│          Sidecar Proxies           │
│  (每个 Sidecar 连接一个 Pilot)     │
└────────────────────────────────────┘

- Sidecar 连接到任一 Pilot 实例
- Pilot 实例从 K8s API Server 获得相同的集群状态
- 某 Pilot 宕机 → Sidecar 重连到其他 Pilot
- 控制面故障不影响已有配置 (Sidecar 使用本地配置)
```

### Sidecar 资源优化

```yaml
# Sidecar 资源配置 (限制资源使用)
apiVersion: v1
kind: ResourceQuota
spec:
  containers:
    - name: istio-proxy
      resources:
        requests:
          cpu: 10m      # 0.01 core
          memory: 64Mi
        limits:
          cpu: 200m     # 0.2 core
          memory: 256Mi

# 使用 eBPF 代替 iptables (减少规则开销)
# 新方案: Sidecar-less / Ambient Mesh
```

### 故障模式

| 故障 | 影响 | 缓解 |
|------|------|------|
| 单个 Sidecar 宕机 | 该Pod出站/入站流量中断 | K8s 自动重启Pod |
| Pilot 宕机 | 新配置无法推送  | 多副本 + 已有配置继续工作 |
| Citadel 宕机 | 新证书无法签发 | 证书有TTL(默认24h), 提前轮换 |
| 全控制面宕机 | 无法推送新配置 | 数据面独立运行, 使用本地缓存配置 |

## 总结

1. **Sidecar模式**: 每个Pod注入一个代理，透明拦截所有流量，解耦业务与基础设施
2. **控制面与数据面分离**: 控制面故障不影响已有流量的数据面处理
3. **xDS协议**: Envoy的标准动态配置协议，支持LDS/RDS/CDS/EDS/SDS增量推送
4. **流量管理**: VirtualService(路由规则) + DestinationRule(流量策略) 双CRD模型
5. **mTLS无感加密**: Citadel CA → SDS → Sidecar自动TLS，业务代码零改动
6. **可观测性三件套**: 指标(Metrics) + 追踪(Tracing) + 日志(Access Log)
7. **逐跳断路器**: Envoy的Outlier Detection + Circuit Breaker防止级联故障
8. **渐进式部署**: 金丝雀(权重分流) → 蓝绿(标签切换) → A/B Testing(Header路由)
9. **K8s原生集成**: CRD配置模型 + Admission Webhook注入 + K8s Service Discovery

面试中可能追问: Ambient Mesh (Sidecar-less) vs Sidecar模式的优缺点? eBPF在服务网格中的应用? 大规模集群下xDS推送的性能优化?
