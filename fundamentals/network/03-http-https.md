# 题目：HTTP/1.1、HTTP/2、HTTP/3 的区别与 HTTPS 的 TLS 握手

## 问题
请阐述 HTTP/1.1、HTTP/2、HTTP/3 (QUIC) 的核心改进与区别，详细说明 HTTPS 的 TLS 握手过程（TLS 1.2 与 TLS 1.3 的区别）。

## 考点
- HTTP 各版本的核心特征
- HTTP/2 的多路复用、头部压缩、服务器推送
- HTTP/3 基于 QUIC 解决了什么 TCP 的固有问题
- TLS 握手的加密协商过程
- 对称加密 vs 非对称加密的角色
- 前向安全性（Forward Secrecy）

## 解答

### 一、HTTP 版本演进

| 版本 | 年份 | 传输层 | 核心特征 |
|------|------|--------|---------|
| HTTP/1.0 | 1996 | TCP | 短连接（一次请求一个连接） |
| HTTP/1.1 | 1997 | TCP | 持久连接、管线化、Host 头 |
| HTTP/2 | 2015 | TCP | 多路复用、头部压缩、Server Push、二进制分帧 |
| HTTP/3 | 2022 | QUIC (UDP) | 0-RTT、无队头阻塞、连接迁移 |

---

### 二、HTTP/1.1 的局限性

**1. 队头阻塞（Head-of-Line Blocking）**

一个 TCP 连接上，所有请求按顺序处理。如果第一个请求被阻塞（丢包重传），后面所有请求都必须等待。

```
请求1（慢） → 阻塞
请求2 → 等待请求1
请求3 → 等待请求1
```

**2. 并发连接限制**

浏览器通常对同一域名最多开 6-8 个 TCP 连接来绕过队头阻塞。但这导致：
- 连接建立开销变大（多次握手）
- 每个连接都要经历慢启动
- 竞争带宽

**3. 头部冗余**

每次请求都携带大量重复的 HTTP 头部（Cookie、User-Agent 等），浪费带宽。

**4. 管线化（Pipelining）基本不可用**

理论上可以在一个连接上并发发送多个请求，但由于队头阻塞，实践中基本未启用。

---

### 三、HTTP/2 的改进

#### 1. 二进制分帧（Binary Framing）

HTTP/1.1 是文本协议，HTTP/2 将数据拆分为二进制帧（HEADERS 帧、DATA 帧等）。

```
HTTP/1.1：
GET /index.html HTTP/1.1\r\n
Host: example.com\r\n
\r\n

HTTP/2：
[Stream ID=1, Type=HEADERS, Flags=END_HEADERS, Payload: 压缩后的头部]
[Stream ID=1, Type=DATA, Flags=END_STREAM, Payload: 响应体]
```

#### 2. 多路复用（Multiplexing）

在一个 TCP 连接上同时传输多个 Stream（每个请求/响应对应一个 Stream ID），帧可交错发送。

```
Stream 1: [HEADERS帧] [DATA帧1]               [DATA帧2]
Stream 2:        [HEADERS帧] [DATA帧1] [DATA帧2]
Stream 3:               [HEADERS帧] [DATA帧]  ...
────────────────────────────────────────────────────→ 时间
             所有帧交错在一个 TCP 连接上传输
```

**HTTP/2 仍存在的队头阻塞**：TCP 层面的丢包重传仍会阻塞该连接上的所有 Stream。这是 HTTP/3 要解决的问题。

#### 3. 头部压缩（HPACK）

使用哈夫曼编码 + 静态/动态表压缩重复的 HTTP 头部。

```
第一次请求：
:method: GET
:path: /api/users
:authority: example.com
user-agent: Mozilla/5.0 ...
cookie: session=abc123...（很长）

第二次请求（同连接）：
:method: GET            → 索引 #2（静态表）
:path: /api/products    → 字面量，哈夫曼编码
:authority: example.com → 动态表引用
user-agent: ...         → 动态表引用
cookie: ...             → 动态表引用
```

#### 4. 服务器推送（Server Push）

服务端可以主动推送客户端可能需要的资源，无需客户端先请求。

```
客户端请求 index.html
服务端响应 index.html + 主动推送：
  - style.css
  - app.js
  - logo.png

（实际中 Server Push 使用率不高，Chrome 已计划移除）
```

**HTTP/2 的局限**：
- 仍然是基于 TCP，TCP 的队头阻塞问题依然存在
- TCP 三次握手 + TLS 握手，建立连接延迟仍然较高

---

### 四、HTTP/3 + QUIC

HTTP/3 使用 QUIC 协议（基于 UDP），核心改进：

| 改进 | HTTP/2 (TCP) | HTTP/3 (QUIC) |
|------|-------------|---------------|
| 传输层 | TCP（内核态） | QUIC over UDP（用户态） |
| 连接建立 | 3次握手 + TLS 1.3 = 2-RTT | 0-RTT（重连）/ 1-RTT（首次） |
| 队头阻塞 | TCP 层存在 | 无（每个 Stream 独立） |
| 连接迁移 | 换 IP 必须重建 | 通过 Connection ID 无缝迁移 |
| 拥塞控制 | 内核实现 | 用户态可插拔算法 |

**QUIC 核心设计**：

```
┌───────────────┐
│   HTTP/3      │  ← 应用层
├───────────────┤
│   QUIC        │  ← 传输层（可靠传输、加密、多路复用）
├───────────────┤
│   UDP         │  ← 真正传输层
├───────────────┤
│   IP          │  ← 网络层
└───────────────┘
```

QUIC 把 TCP 的可靠传输、TLS 的加密、HTTP/2 的多路复用全部融合在自己内部，UDP 只作为简单的"包容器"。

---

### 五、HTTPS 的 TLS 握手

#### TLS 1.2 握手（1-RTT，四次通信）

```
客户端                                           服务端

1. ClientHello ──────────────────────────────→
   支持的 TLS 版本
   支持的加密套件（Cipher Suites）
   随机数 Random_C

2.                             ←───── ServerHello ───────
                                  选定的 TLS 版本
                                  选定的加密套件
                                  随机数 Random_S
                             ←───── Certificate ───────
                                  服务器证书（含公钥）
                             ←───── ServerHelloDone ───

3. ClientKeyExchange ────────────────────────→
   用服务端公钥加密的 PreMaster Secret
   (如果是 ECDHE，这里是客户端的 DH 公钥)
   ChangeCipherSpec ─────────────────────────→
   Finished (加密的验证消息) ────────────────→

4.                             ←───── ChangeCipherSpec ──
                              ←───── Finished ──────────

此后双方用对称密钥加密通信
```

**密钥生成**：双方各自用 `Random_C + Random_S + PreMaster Secret` 计算出相同的 `Master Secret`，进而派生出会话密钥（对称加密密钥、MAC 密钥等）。

#### TLS 1.3 握手（1-RTT，两次通信）

TLS 1.3 的简化：

```
客户端                                           服务端

1. ClientHello ──────────────────────────────→
   + 支持的加密套件（仅 AEAD 算法）
   + 密钥交换参数（如 ECDHE 公钥）  ← 提前发送！
   + (可选) 0-RTT 数据（前向安全）

2.                             ←───── ServerHello ───────
   + 选定的加密套件
   + 密钥交换参数（服务端的 DH 公钥）
   + Certificate (加密的)
   + Finished (加密的)
   ← 此时服务端已可以发应用数据

客户端收到后，立即可以发应用数据
```

**TLS 1.3 的提升**：
- 握手减为 1-RTT（比 TLS 1.2 少一个往返）
- 支持 0-RTT（重连时客户端在第一轮就发加密数据）
- 移除不安全算法（RSA 密钥交换、CBC 模式、RC4、3DES、SHA-1）
- 完美前向安全性（PFS）**强制使用**（只保留 ECDHE/DHE）

**TLS 1.2 vs 1.3 对比**：

| 特性 | TLS 1.2 | TLS 1.3 |
|------|---------|---------|
| 握手往返次数 | 2-RTT（4 次通信） | 1-RTT（2 次通信） |
| 0-RTT 重连 | 不支持 | 支持 |
| 加密套件 | 100+ 组合（包含不安全） | 5 种 AEAD 套件 |
| 证书传输 | 明文 | 加密（保护隐私） |
| 密钥交换 | RSA / ECDHE 可选 | 仅 ECDHE/DHE（强制 PFS） |
| 对称算法 | CBC / GCM | 仅 AEAD（GCM/ChaCha20-Poly1305） |

---

### 六、对称加密 vs 非对称加密

| 维度 | 对称加密 | 非对称加密 |
|------|---------|-----------|
| 密钥 | 同一把密钥加解密 | 公钥加密，私钥解密 |
| 速度 | 快（1000x+） | 慢 |
| 示例 | AES, ChaCha20 | RSA, ECDH |
| 用途 | 数据传输加密 | 密钥交换、数字签名 |
| TLS 中的角色 | 握手后用对称密钥加密实际数据 | 握手期间交换会话密钥 |

**TLS 的混合模式**：用非对称加密安全地交换对称密钥（或在 DH 中协商），之后用对称加密高效传输数据。

**前向安全性（Forward Secrecy）**：即使服务端的长期私钥泄露，历史会话仍无法解密。

- **RSA 密钥交换不提供 PFS**：用服务端公钥加密 PreMaster Secret，如果私钥泄露，所有历史会话全部可解密
- **ECDHE 提供 PFS**：每次握手生成临时的 DH 参数，用完即丢弃，无长期密钥可泄露

---

### 七、证书链验证

```
根证书（Root CA）
  └── 中间证书（Intermediate CA）
        └── 网站证书（End-entity）
```

浏览器内置了根 CA 的公钥。验证时逐级向上验证签名（Hash 匹配），直到信任锚（根证书）。

**证书内容**：域名、有效期、公钥、颁发者、签名算法、签名值。

---

## 总结
HTTP/1.1 有队头阻塞和头部冗余问题；HTTP/2 通过二进制分帧、多路复用和 HPACK 压缩大幅改善，但 TCP 层仍有队头阻塞；HTTP/3 基于 QUIC (UDP) 彻底消除队头阻塞，支持 0-RTT 重连和连接迁移。HTTPS 的 TLS 握手（尤其是 ECDHE）确保安全交换密钥，TLS 1.3 把握手从 2-RTT 降到 1-RTT ，并强制了前向安全性。
