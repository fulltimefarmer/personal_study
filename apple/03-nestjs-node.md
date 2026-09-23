# NestJS / Node.js 深度问答 · Deep Q&A

> 说明：每题含中文题干、英文题干、中文答案、英文答案。
> Note: Each question has Chinese prompt, English prompt, Chinese answer, English answer.

---

## NN-1. NestJS 与 Express 的区别？为什么企业级项目选 NestJS？
**EN:** NestJS vs Express — why choose NestJS for enterprise projects?

**中文答案：**
Express 极简、无强约束，路由/中间件自由组织，小项目灵活，但大项目易失控（无统一分层、依赖管理靠约定）。NestJS 建立在 Express(默认)/Fastify 之上，提供**强约束架构**：模块化(`@Module`)、依赖注入(IoC)、装饰器、Controller/Service/Guard/Interceptor/Pipe/Filter 分层、内置验证/序列化、开箱测试、Swagger、微服务/GraphQL/WebSocket 支持。选择 NestJS 的核心是**可维护性、可测试性、一致性**——团队协作与长期演进。

**English answer:**
Express is minimal and unopinionated — routing/middleware are free-form, flexible for small projects but hard to control at scale (no standard layering, convention-based deps). NestJS builds on Express (default)/Fastify and provides an **opinionated architecture**: modules (`@Module`), DI (IoC), decorators, layered Controller/Service/Guard/Interceptor/Pipe/Filter, built-in validation/serialization, out-of-the-box testing, Swagger, microservices/GraphQL/WebSocket. The core reason to choose NestJS is **maintainability, testability, and consistency**.

---

## NN-2. NestJS 依赖注入(DI)如何工作？`useClass`/`useValue`/`useFactory`/`useExisting` 的区别？
**EN:** How does NestJS DI work? `useClass` vs `useValue` vs `useFactory` vs `useExisting`.

**中文答案：**
NestJS 内置 IoC 容器，`@Injectable()` 类注册到模块 `providers` 后，容器按构造函数参数类型（元数据反射）自动实例化并注入。
- `useClass`：提供一个**类**，容器实例化它（可做多态替换）。
- `useValue`：提供**固定值**（常量、配置、mock）。
- `useFactory`：提供**工厂函数**，可注入依赖、异步初始化（如读配置后建 DB 连接）。
- `useExisting`：别名，复用已注册的 provider（token 别名）。

```ts
@Module({
  providers: [
    { provide: 'CONFIG', useValue: { env: 'prod' } },
    { provide: DbService, useFactory: async (cfg: ConfigService) => new DbService(await load(cfg)), inject: [ConfigService] },
    { provide: 'DB_ALIAS', useExisting: DbService },
  ],
})
export class AppModule {}
```

**English answer:**
NestJS has a built-in IoC container; classes marked `@Injectable()` and listed in a module's `providers` are instantiated by the container and injected by constructor type (metadata reflection).
- `useClass`: provide a **class** the container instantiates (polymorphic swap).
- `useValue`: provide a **fixed value** (constant, config, mock).
- `useFactory`: provide a **factory** that can inject deps and run async init (build DB connection from config).
- `useExisting`: alias to an already-registered provider.

```ts
@Module({
  providers: [
    { provide: 'CONFIG', useValue: { env: 'prod' } },
    { provide: DbService, useFactory: async (cfg: ConfigService) => new DbService(await load(cfg)), inject: [ConfigService] },
    { provide: 'DB_ALIAS', useExisting: DbService },
  ],
})
export class AppModule {}
```

---

## NN-3. 请求生命周期中 Middleware、Guard、Interceptor、Pipe、ExceptionFilter 的执行顺序？
**EN:** In the request lifecycle, what's the order of Middleware, Guard, Interceptor, Pipe, ExceptionFilter?

**中文答案：**
处理 HTTP 请求的典型顺序：
1. **Middleware**（全局 → 模块）：最先执行，不感知路由上下文。
2. **Guards**（全局 → 控制器 → 路由）：鉴权/授权，决定是否放行。
3. **Interceptors (pre)**：handler 之前。
4. **Pipes**（全局 → 控制器 → 路由 → 参数）：转换 + 验证。
5. **Route Handler**：业务逻辑。
6. **Interceptors (post)**：响应返回前（包装响应、计时）。
7. **Exception Filters**：任一层抛异常时由就近 Filter 捕获统一响应。
口诀：Middleware → Guard → Interceptor(pre) → Pipe → Handler → Interceptor(post) → Filter。

**English answer:**
Typical order for an HTTP request:
1. **Middleware** (global → module): runs first, no route context.
2. **Guards** (global → controller → route): auth/authorization gate.
3. **Interceptors (pre)**: before the handler.
4. **Pipes** (global → controller → route → param): transform + validate.
5. **Route Handler**: business logic.
6. **Interceptors (post)**: before response (wrap/timing).
7. **Exception Filters**: the nearest filter catches any exception for a consistent response.
Mnemonic: Middleware → Guard → Interceptor(pre) → Pipe → Handler → Interceptor(post) → Filter.

---

## NN-4. Guard、Interceptor、Pipe、Middleware、ExceptionFilter 各自的职责？何时用哪个？
**EN:** Responsibilities of Guard, Interceptor, Pipe, Middleware, ExceptionFilter — when to use each?

**中文答案：**
- **Middleware**：请求进入前处理，不感知路由上下文——日志、CORS、body 解析、i18n。
- **Guard**（`CanActivate`）：鉴权/授权，决定是否进入路由——JWT、角色、权限。
- **Interceptor**（`NestInterceptor`）：方法执行前后绑定逻辑——统一响应包装、耗时统计、缓存、序列化。
- **Pipe**（`PipeTransform`）：数据**转换与验证**——`ValidationPipe` 校验 DTO、`ParseIntPipe`；非法抛 400。
- **ExceptionFilter**（`ExceptionFilter`）：捕获异常并统一错误格式——把业务异常映射为规范错误响应。

**English answer:**
- **Middleware**: pre-route handling without route context — logging, CORS, body parsing, i18n.
- **Guard** (`CanActivate`): auth/authorization gate — JWT, roles, permissions.
- **Interceptor** (`NestInterceptor`): logic before/after method execution — response wrapping, timing, caching, serialization.
- **Pipe** (`PipeTransform`): data **transform & validate** — `ValidationPipe` for DTOs, `ParseIntPipe`; throws 400 on invalid.
- **ExceptionFilter** (`ExceptionFilter`): catch exceptions and shape a consistent error response.

---

## NN-5. 如何用 `class-validator` + `class-transformer` 做 DTO 校验与序列化？
**EN:** How to validate DTOs and serialize responses with `class-validator` + `class-transformer`?

**中文答案：**
- **DTO 校验**：DTO 类加 `class-validator` 装饰器，全局 `ValidationPipe` 自动校验，失败返回 400（带错误详情）。`whitelist: true` 剥离未声明字段，`transform: true` 自动把 JSON 转成 DTO 实例。
- **序列化**：`class-transformer` 的 `@Exclude()`/`@Expose()` + `ClassSerializerInterceptor` 控制哪些字段返回（如隐藏密码、内部字段）。

```ts
export class CreateUserDto {
  @IsEmail() email: string;
  @IsString() @MinLength(8) password: string;
}

@UseInterceptors(ClassSerializerInterceptor)
export class UserEntity {
  @Expose() id: number;
  @Expose() email: string;
  @Exclude() passwordHash: string;
}

// main.ts
app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
```

**English answer:**
- **DTO validation**: annotate DTO classes with `class-validator` decorators; a global `ValidationPipe` validates automatically and returns 400 with details on failure. `whitelist: true` strips undeclared fields, `transform: true` converts JSON into DTO instances.
- **Serialization**: `class-transformer`'s `@Exclude()`/`@Expose()` + `ClassSerializerInterceptor` control which fields are returned (hide passwords, internal fields).

```ts
export class CreateUserDto {
  @IsEmail() email: string;
  @IsString() @MinLength(8) password: string;
}

@UseInterceptors(ClassSerializerInterceptor)
export class UserEntity {
  @Expose() id: number;
  @Expose() email: string;
  @Exclude() passwordHash: string;
}

// main.ts
app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
```

---

## NN-6. Node.js 单线程为何能高并发？libuv 线程池是什么？
**EN:** Node.js is single-threaded — how does it handle high concurrency? What is libuv's thread pool?

**中文答案：**
Node 用**事件驱动 + 非阻塞 I/O**：主线程(Event Loop)不阻塞在 I/O 上，把网络/文件 I/O 交给 libuv。libuv 用 OS 异步接口(epoll/kqueue/IOCP)处理网络 I/O，用**线程池**(默认 4 线程，`UV_THREADPOOL_SIZE` 可调)处理阻塞型/CPU 密集操作(文件 I/O、DNS、压缩、加密)。所以「单线程」指 JS **执行**单线程，I/O 是异步并发的，适合 I/O 密集场景(API 网关、电商后端)。CPU 密集任务应交给 `worker_threads` 或拆分服务。

**English answer:**
Node uses **event-driven, non-blocking I/O**. The main thread (Event Loop) doesn't block on I/O; it delegates network/file I/O to libuv, which uses OS async facilities (epoll/kqueue/IOCP) for network I/O and a **thread pool** (default 4, tunable via `UV_THREADPOOL_SIZE`) for blocking/CPU-bound ops (file I/O, DNS, compression, crypto). So "single-threaded" means JS *execution* is single-threaded; I/O is asynchronously concurrent — ideal for I/O-bound workloads (API gateways, e-commerce backends). CPU-bound work belongs in `worker_threads` or separate services.

---

## NN-7. 解释 Node.js 的流(streams)：Readable/Writable/Transform/Duplex，及背压(backpressure)。
**EN:** Explain Node streams — Readable/Writable/Transform/Duplex, and backpressure.

**中文答案：**
流用于**分块处理数据**而非一次性载入内存：
- **Readable**：可读源（文件、HTTP 请求）。
- **Writable**：可写目标（文件、响应）。
- **Duplex**：双工（socket）。
- **Transform**：读写转换（压缩、加密、解析）。
- **背压(backpressure)**：当消费者处理速度慢于生产者，`Writable.write()` 返回 `false` 提示「暂停」，生产者应监听 `drain` 事件再继续，避免内存暴涨。

```js
const read = fs.createReadStream('big.json');
const parse = new Transform({ ... });
const write = fs.createWriteStream('out.ndjson');
read.pipe(parse).pipe(write);   // 流式处理大文件，内存占用恒定
```

**English answer:**
Streams process data in **chunks** instead of loading it all into memory:
- **Readable**: source (file, HTTP request).
- **Writable**: destination (file, response).
- **Duplex**: both (socket).
- **Transform**: read-transform-write (compression, encryption, parsing).
- **Backpressure**: when the consumer is slower than the producer, `Writable.write()` returns `false` to signal "pause"; the producer should listen for `drain` before continuing, preventing memory blowup.

```js
const read = fs.createReadStream('big.json');
const parse = new Transform({ ... });
const write = fs.createWriteStream('out.ndjson');
read.pipe(parse).pipe(write);   // process large file with constant memory
```

---

## NN-8. 解释 EventEmitter，以及它如何支撑 Node 的异步模型。
**EN:** Explain EventEmitter and how it underpins Node's async model.

**中文答案：**
`EventEmitter` 是观察者模式的实现：`on/once` 注册监听器，`emit` 触发，`off` 移除。Node 的 I/O 完成、流事件(`data`/`end`/`error`)、`process` 事件都基于它。要点：`emit` 是同步调用监听器；`error` 事件无人监听会抛异常导致崩溃；监听器过多有 `MaxListenersExceededWarning`。自定义时用 `extends EventEmitter` 或 `class X extends EventEmitter`。

```js
const { EventEmitter } = require('events');
class OrderEvents extends EventEmitter {}
const events = new OrderEvents();
events.on('paid', (order) => console.log('paid', order.id));
events.emit('paid', { id: 1 });
```

**English answer:**
`EventEmitter` is the observer pattern: `on/once` register listeners, `emit` triggers, `off` removes. Node's I/O completion, stream events (`data`/`end`/`error`), and `process` events build on it. Key points: `emit` invokes listeners synchronously; an unhandled `error` event throws and crashes the process; too many listeners trigger `MaxListenersExceededWarning`. Extend it for custom events.

```js
const { EventEmitter } = require('events');
class OrderEvents extends EventEmitter {}
const events = new OrderEvents();
events.on('paid', (order) => console.log('paid', order.id));
events.emit('paid', { id: 1 });
```

---

## NN-9. Node.js 常见性能优化与内存泄漏排查方法？
**EN:** Common Node.js performance optimizations and memory-leak diagnosis?

**中文答案：**
**优化**：多进程(`cluster`/PM2)利用多核；连接池复用 DB；Redis 缓存；避免同步阻塞 API；流式处理大文件；gzip 压缩；负载均衡；DB 索引与查询优化；对 CPU 密集用 `worker_threads`。
**内存泄漏排查**：`process.memoryUsage()` 观察堆增长；`--inspect` + Chrome DevTools 抓 heap snapshot 对比；`--max-old-space-size` 控制；`clinic`/`autocannon` 压测。常见泄漏：未移除监听器、全局变量、闭包持大对象、定时器未清、流未关。

**English answer:**
**Optimizations**: multi-process (`cluster`/PM2) to use cores; connection pooling; Redis caching; avoid sync/blocking APIs; stream large files; gzip; load balancing; DB index/query tuning; `worker_threads` for CPU-bound work.
**Leak diagnosis**: `process.memoryUsage()` for heap growth; `--inspect` + Chrome DevTools heap snapshots to diff; `--max-old-space-size`; load test with `clinic`/`autocannon`. Common leaks: unremoved listeners, globals, closures holding big objects, uncleared timers, unclosed streams.

---

## NN-10. NestJS 模块(module)与动态模块(dynamic module)是什么？什么时候用动态模块？
**EN:** What are NestJS modules and dynamic modules? When to use dynamic modules?

**中文答案：**
- **模块**：`@Module({ imports, controllers, providers, exports })` 是组织边界，把相关功能聚合，控制 provider 可见性（`exports` 对外暴露）。
- **动态模块**：`@Module` 静态定义之外，通过静态方法（如 `forRoot`/`forRootAsync`）**运行时构造**模块，可传入配置、异步初始化——典型如 `TypeOrmModule.forRootAsync`、`ConfigModule.forRoot`。适合「配置驱动的可复用库」（如数据库/消息队列连接封装）。

```ts
@Module({})
export class DbModule {
  static forRoot(options: DbOptions): DynamicModule {
    const provider = { provide: 'DB', useValue: new Db(options) };
    return { module: DbModule, providers: [provider], exports: ['DB'] };
  }
}
```

**English answer:**
- **Modules**: `@Module({ imports, controllers, providers, exports })` are organizational boundaries that group features and control provider visibility (`exports`).
- **Dynamic modules**: beyond static `@Module`, a static method (e.g. `forRoot`/`forRootAsync`) **constructs the module at runtime**, accepting config and async init — e.g. `TypeOrmModule.forRootAsync`, `ConfigModule.forRoot`. Use for config-driven reusable libraries (DB/message-queue connection wrappers).

```ts
@Module({})
export class DbModule {
  static forRoot(options: DbOptions): DynamicModule {
    const provider = { provide: 'DB', useValue: new Db(options) };
    return { module: DbModule, providers: [provider], exports: ['DB'] };
  }
}
```

---

## NN-11. 如何实现统一异常处理（ExceptionFilter）与统一响应格式（Interceptor）？
**EN:** How to implement global exception handling (ExceptionFilter) and a unified response shape (Interceptor)?

**中文答案：**

```ts
// 统一错误响应
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();
    const status = exception instanceof HttpException
      ? exception.getStatus() : 500;
    res.status(status).json({
      success: false,
      statusCode: status,
      message: exception instanceof Error ? exception.message : 'Internal error',
    });
  }
}

// 统一成功响应
@Injectable()
export class TransformInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(map(data => ({ success: true, data })));
  }
}

// main.ts
app.useGlobalFilters(new AllExceptionsFilter());
app.useGlobalInterceptors(new TransformInterceptor());
```

**English answer:**

```ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();
    const status = exception instanceof HttpException
      ? exception.getStatus() : 500;
    res.status(status).json({
      success: false,
      statusCode: status,
      message: exception instanceof Error ? exception.message : 'Internal error',
    });
  }
}

@Injectable()
export class TransformInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(map(data => ({ success: true, data })));
  }
}

// main.ts
app.useGlobalFilters(new AllExceptionsFilter());
app.useGlobalInterceptors(new TransformInterceptor());
```

---

## NN-12. 如何测试 NestJS 应用？单元测试与 E2E 测试怎么做？
**EN:** How to test a NestJS app — unit and E2E?

**中文答案：**
- **单元测试**：用 `Test.createTestingModule()` 构建最小模块，mock 依赖（`jest.fn()` 或 `Test.createTestingModule().overrideProvider(X).useValue(mock)`），只测 service 逻辑。
- **E2E 测试**：`Test.createTestingModule({ imports: [AppModule] })` 起真实应用 + `supertest`（`app.getHttpServer()`）发 HTTP 请求，验证路由、Guard、Pipe、Filter 全链路。
- 覆盖策略（测试金字塔）：单元多、集成中、E2E 少而关键（用户旅程）。

```ts
// E2E
let app: INestApplication;
beforeAll(async () => {
  const moduleRef = await Test.createTestingModule({ imports: [AppModule] }).compile();
  app = moduleRef.createNestApplication();
  await app.init();
});
it('/products (GET)', () => request(app.getHttpServer()).get('/products').expect(200));
```

**English answer:**
- **Unit tests**: use `Test.createTestingModule()` to build a minimal module, mock deps (`jest.fn()` or `.overrideProvider(X).useValue(mock)`), test service logic only.
- **E2E tests**: `Test.createTestingModule({ imports: [AppModule] })` boots a real app + `supertest` (`app.getHttpServer()`) to send HTTP and verify routes/guards/pipes/filters end to end.
- Strategy (test pyramid): many unit, some integration, few but critical E2E (user journeys).

```ts
let app: INestApplication;
beforeAll(async () => {
  const moduleRef = await Test.createTestingModule({ imports: [AppModule] }).compile();
  app = moduleRef.createNestApplication();
  await app.init();
});
it('/products (GET)', () => request(app.getHttpServer()).get('/products').expect(200));
```

---

## NN-13. 如何在 NestJS 中处理数据库事务（TypeORM / Prisma）？
**EN:** How to handle DB transactions in NestJS (TypeORM / Prisma)?

**中文答案：**
- **TypeORM**：`dataSource.transaction(async manager => {...})` 或注入 `@InjectDataSource()` 后用 `manager.transaction`；也可用 `QueryRunner` 精细控制。事务保证「订单 + 库存扣减」原子性。
- **Prisma**：`prisma.$transaction(async (tx) => {...})` 交互式事务，或 `$transaction([...])` 批量。注意：交互式事务默认超时 5s，长事务需调 `timeout`。

```ts
await this.dataSource.transaction(async (manager) => {
  await manager.save(order);
  await manager.update(Product, { id }, { stock: () => 'stock - 1' });
});
```

**English answer:**
- **TypeORM**: `dataSource.transaction(async manager => {...})` or inject `@InjectDataSource()` and use `manager.transaction`; a `QueryRunner` for fine control. Transactions make "order + stock deduction" atomic.
- **Prisma**: `prisma.$transaction(async (tx) => {...})` interactive, or `$transaction([...])` batch. Note interactive transactions default to a 5s timeout — raise `timeout` for long ones.

```ts
await this.dataSource.transaction(async (manager) => {
  await manager.save(order);
  await manager.update(Product, { id }, { stock: () => 'stock - 1' });
});
```

---

## NN-14. TypeORM vs Prisma 的取舍？
**EN:** TypeORM vs Prisma — trade-offs?

**中文答案：**
- **Prisma**：类型安全由 schema 生成（极致 DX）、声明式 schema + 迁移(`prisma migrate`)、查询构建器直观；缺点：复杂 SQL/性能优化场景灵活度略低、多一层引擎、历史包袱较少。
- **TypeORM**：贴近 SQL、支持 QueryBuilder、装饰器实体、更成熟；缺点：类型安全不如 Prisma、部分 API 隐式行为（`save`/`cascade`）易踩坑、迁移工具有坑。
- 选型：新项目/重视 DX 与类型安全 → Prisma；需要精细 SQL 控制/已有 TypeORM 经验 → TypeORM。两者都能配合连接池(pgbouncer)上生产。

**English answer:**
- **Prisma**: schema-generated type safety (excellent DX), declarative schema + migrations (`prisma migrate`), intuitive query builder; cons: less flexibility for complex SQL/perf tuning, extra engine layer.
- **TypeORM**: closer to SQL, QueryBuilder, decorator entities, more mature; cons: weaker type safety, some implicit behaviors (`save`/`cascade`) are traps, migration tooling quirks.
- Choice: new projects valuing DX/type safety → Prisma; need fine SQL control / existing TypeORM experience → TypeORM. Both pair with a connection pool (pgbouncer) in production.

---

## NN-15. Node.js 安全最佳实践：如何防范常见攻击？
**EN:** Node.js security best practices — how to defend common attacks?

**中文答案：**
- **注入**：SQL 用参数化查询/ORM，避免拼接；NoSQL 同理。
- **XSS**：输出转义、`helmet` 设置 CSP 等安全头。
- **CSRF**：SameSite Cookie + CSRF token。
- **认证/授权**：bcrypt/argon2 哈希密码；JWT 短期有效 + 刷新 token；最小权限。
- **限流**：`@nestjs/throttler`/`express-rate-limit` 防暴力破解与 DDoS。
- **依赖安全**：`npm audit`、`npm ci`（锁定版本）、及时更新。
- **敏感信息**：不进代码库，用环境变量/Secret 管理；`helmet` + `cookie` 安全标志；限制请求体大小。

**English answer:**
- **Injection**: parameterized queries/ORM, no string concatenation (SQL & NoSQL).
- **XSS**: output escaping; `helmet` sets CSP and other security headers.
- **CSRF**: SameSite cookies + CSRF tokens.
- **Auth**: bcrypt/argon2 hashing; short-lived JWT + refresh token; least privilege.
- **Rate limiting**: `@nestjs/throttler`/`express-rate-limit` vs brute force & DDoS.
- **Dependency security**: `npm audit`, `npm ci` (locked versions), keep updated.
- **Secrets**: never in code; env vars/secret managers; `helmet` + secure cookie flags; limit request body size.

---

## NN-16. NestJS 如何实现微服务(microservices)？支持哪些传输层？
**EN:** How does NestJS implement microservices? Which transports?

**中文答案：**
NestJS 通过 `@nestjs/microservices` 把应用组织成独立服务，用**传输层**通信，屏蔽底层协议差异。`ClientProxy`/`@MessagePattern`（请求-响应）与 `@EventPattern`（事件，无响应）通信。支持的传输层：TCP、Redis、Kafka、RabbitMQ、NATS、MQTT、gRPC。选择依据：低延迟/内部 → TCP；高吞吐/流 → Kafka；轻量 → Redis/NATS；跨语言 → gRPC。

```ts
const app = await NestFactory.createMicroservice<MicroserviceOptions>(AppModule, {
  transport: Transport.RMQ,
  options: { urls: ['amqp://...'], queue: 'orders', queueOptions: { durable: true } },
});
```

**English answer:**
NestJS uses `@nestjs/microservices` to organize apps into independent services communicating over a **transport**, hiding protocol differences. `ClientProxy` + `@MessagePattern` (request-response) and `@EventPattern` (event, no response). Transports: TCP, Redis, Kafka, RabbitMQ, NATS, MQTT, gRPC. Choice: low-latency/internal → TCP; high-throughput/streaming → Kafka; lightweight → Redis/NATS; cross-language → gRPC.

```ts
const app = await NestFactory.createMicroservice<MicroserviceOptions>(AppModule, {
  transport: Transport.RMQ,
  options: { urls: ['amqp://...'], queue: 'orders', queueOptions: { durable: true } },
});
```

---

## NN-17. `cluster` 模块如何利用多核？`worker_threads` 与它的区别？
**EN:** How does `cluster` use multiple cores? `worker_threads` vs `cluster`?

**中文答案：**
- **`cluster`**：主进程 fork 多个子进程（`cluster.fork()`），共享同一端口，靠 OS 负载均衡分发连接；进程间用 IPC 通信。适合 I/O 密集（HTTP 服务）横向扩容。
- **`worker_threads`**：真正的**线程**，共享进程内存（通过 `SharedArrayBuffer`/消息传递），适合 CPU 密集任务（计算、加密）并行，不必多进程复制资源。
- 区别：cluster 是「多进程」（隔离好、资源重）；worker_threads 是「多线程」（共享内存、开销低、可传引用）。

**English answer:**
- **`cluster`**: the master forks child processes (`cluster.fork()`), sharing one port; the OS load-balances connections; processes communicate via IPC. Good for I/O-bound (HTTP) horizontal scaling.
- **`worker_threads`**: real **threads** sharing process memory (via `SharedArrayBuffer`/message passing), good for CPU-bound (computation, crypto) parallelism without duplicating resources across processes.
- Difference: cluster = multi-process (strong isolation, heavier); worker_threads = multi-thread (shared memory, lower overhead, pass references).
