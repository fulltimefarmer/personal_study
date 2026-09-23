# Angular 深度问答 · Deep Q&A

> 说明：每题含中文题干、英文题干、中文答案、英文答案。
> Note: Each question has Chinese prompt, English prompt, Chinese answer, English answer.

---

## NG-1. Angular 变更检测(Change Detection)如何工作？`ChangeDetectionStrategy.OnPush` 的机制、好处与坑？
**EN:** How does Angular change detection work? `OnPush` mechanism, benefits, and pitfalls.

**中文答案：**
默认 `Default` 策略下，Zone.js 拦截异步事件（点击、HTTP、定时器、Promise），任何事件都从根组件**整棵树**做变更检测。`OnPush` 让组件**只在**以下情况检测：① `@Input` 引用变化；② 组件内部事件（模板事件触发）；③ 显式 `ChangeDetectorRef.markForCheck()`/`detectChanges()`；④ 模板 `async` 管道发射新值。
- 好处：跳过大量无关子树，大列表/高频数据性能显著提升。
- 坑：必须用**不可变数据**（每次返回新对象/数组），否则子组件 `@Input` 引用不变就不更新；或用 `markForCheck()` 手动标记。

**English answer:**
Under `Default`, Zone.js intercepts async events (clicks, HTTP, timers, promises), and any event triggers change detection over the **whole tree** from the root. `OnPush` re-checks a component **only** when: ① an `@Input` reference changes; ② an event fires inside the component; ③ `ChangeDetectorRef.markForCheck()`/`detectChanges()` is called; ④ an `async` pipe emits.
- Benefit: skips large irrelevant subtrees; big wins for long lists/high-frequency data.
- Pitfall: you must use **immutable data** (new object/array each time), or the `@Input` reference won't change and updates are missed — or call `markForCheck()` manually.

---

## NG-2. `Observable` vs `Promise`；`Subject` vs `BehaviorSubject` vs `ReplaySubject`。
**EN:** `Observable` vs `Promise`; `Subject` vs `BehaviorSubject` vs `ReplaySubject`.

**中文答案：**
- **Observable**：惰性(订阅才执行)、可多值、可取消(`unsubscribe`)、操作符丰富、可同步可异步。**Promise**：立即执行(eager)、单值、不可取消、无操作符管道。
- **Subject**：既是 Observable 又是 Observer，可 `next` 多播；订阅后只收**之后**的值。
- **BehaviorSubject**：带初始值，新订阅者立即收**当前值**——适合状态（购物车数量、当前用户）。
- **ReplaySubject**：缓存最近 N 个值，新订阅者收到缓存的 N 个值——适合「回放历史」。

**English answer:**
- **Observable**: lazy (runs on subscribe), multi-value, cancellable (`unsubscribe`), rich operators, sync or async. **Promise**: eager, single-value, not cancellable, no operator pipeline.
- **Subject**: both Observable and Observer; `next` multicasts; subscribers only get values emitted **after** subscribing.
- **BehaviorSubject**: has an initial value; new subscribers immediately get the **current** value — great for state (cart count, current user).
- **ReplaySubject**: buffers the last N values; new subscribers receive those N values — great for "replaying history".

---

## NG-3. `switchMap`、`mergeMap`、`concatMap`、`exhaustMap` 的区别与各自场景。
**EN:** Differences among `switchMap`, `mergeMap`, `concatMap`, `exhaustMap` and their use cases.

**中文答案：**
都是「把外层值映射为内层 Observable 并合并」的操作符，区别在**重叠内层流**的处理：
- **mergeMap**：并发执行所有内层流，按完成顺序合并（无数量限制）——适合相互独立的请求。
- **switchMap**：新值到来**取消**上一个内层流，只保留最新——**搜索联想**、防止旧响应覆盖新响应。
- **concatMap**：按顺序排队，一个完成才执行下一个——需要**顺序保证**的保存操作。
- **exhaustMap**：内层流进行中**忽略**新值——**防重复提交**（登录/下单按钮）。

**English answer:**
All map outer values into inner Observables; they differ in how they handle overlapping inner streams:
- **mergeMap**: run all concurrently, merge in completion order (no limit) — independent requests.
- **switchMap**: cancel the previous inner stream on each new value, keep only the latest — **search autocomplete**, prevent stale responses.
- **concatMap**: queue in order, one at a time — operations needing **ordered** execution.
- **exhaustMap**: ignore new values while an inner stream is in-flight — **prevent duplicate submits** (login/checkout).

---

## NG-4. Angular 组件通信方式：父子、跨组件、以及新版本 Signals 的定位。
**EN:** Angular component communication — parent/child, cross-component, and Signals.

**中文答案：**
- 父→子：`@Input()`；子→父：`@Output()` + `EventEmitter`。
- 父访问子实例：`@ViewChild`；`@ContentChild` 访问投影内容。
- 跨组件：共享**服务**（单例 + `BehaviorSubject`/`Signal` 状态）、路由参数、状态库（NgRx/Akita）。
- **Signals**（v16+）：`signal()`/`computed()`/`effect()`，细粒度响应式，未来可替代部分 Zone.js 变更检测（`zoneless`）。`input()`/`output()`/`model()` 提供声明式组件通信。

```ts
// 共享状态服务
@Injectable({ providedIn: 'root' })
export class CartService {
  private _count = signal(0);
  readonly count = this._count.asReadonly();
  add() { this._count.update(c => c + 1); }
}
```

**English answer:**
- Parent→child: `@Input()`; child→parent: `@Output()` + `EventEmitter`.
- Parent access child: `@ViewChild`; projected content via `@ContentChild`.
- Cross-component: shared **service** (singleton + `BehaviorSubject`/`Signal` state), route params, state libs (NgRx/Akita).
- **Signals** (v16+): `signal()`/`computed()`/`effect()` for fine-grained reactivity, eventually replacing Zone.js change detection (`zoneless`). `input()`/`output()`/`model()` give declarative component communication.

```ts
@Injectable({ providedIn: 'root' })
export class CartService {
  private _count = signal(0);
  readonly count = this._count.asReadonly();
  add() { this._count.update(c => c + 1); }
}
```

---

## NG-5. Angular 生命周期钩子有哪些？`ngOnInit` 与构造函数(constructor)的区别？
**EN:** Angular lifecycle hooks? `ngOnInit` vs constructor?

**中文答案：**
常用钩子（顺序）：`ngOnChanges`（`@Input` 变化，含首次）、`ngOnInit`（一次）、`ngDoCheck`、`ngAfterContentInit`、`ngAfterContentChecked`、`ngAfterViewInit`、`ngAfterViewChecked`、`ngOnDestroy`（清理）。
- **constructor**：仅 DI 注入与简单字段初始化；`@Input` 尚未绑定。
- **ngOnInit**：首次 `ngOnChanges` 之后执行，`@Input` 已就绪，适合初始化逻辑（加载数据）。这也是「分离构造与初始化」的最佳实践。

**English answer:**
Common hooks (in order): `ngOnChanges` (`@Input` changes, incl. first), `ngOnInit` (once), `ngDoCheck`, `ngAfterContentInit`, `ngAfterContentChecked`, `ngAfterViewInit`, `ngAfterViewChecked`, `ngOnDestroy` (cleanup).
- **constructor**: DI injection and simple field init only; `@Input` not bound yet.
- **ngOnInit**: runs after the first `ngOnChanges`, when `@Input` is ready — the right place for init logic (loading data).

---

## NG-6. 如何优化 Angular 应用性能？（含 `trackBy`、懒加载、AOT）
**EN:** How to optimize Angular performance (incl. `trackBy`, lazy loading, AOT)?

**中文答案：**
- **变更检测**：`OnPush` + 不可变数据；模板里避免方法调用（用管道/缓存）；`*ngFor` 加 `trackBy` 避免整列表重建。
- **懒加载**：路由 `loadChildren` 拆 chunk；`PreloadAllModules` 平衡首屏。
- **AOT 编译**：生产默认开启，模板编译到 JS，减少运行时、提升渲染；Tree-shaking 去除未用代码。
- **RxJS**：避免泄漏（`takeUntil`/`async`），`shareReplay` 复用，合并/去抖请求。
- **构建预算** `ng build --budgets` 控包体积；图片懒加载/压缩；CDN 静态资源。
- 非 UI 重任务用 `runOutsideAngular` 跑在 `ngZone` 外。

**English answer:**
- **Change detection**: `OnPush` + immutable data; avoid method calls in templates (pipes/cached); `trackBy` in `*ngFor` to avoid full-list rebuild.
- **Lazy loading**: `loadChildren` route chunking; `PreloadAllModules` balances first paint.
- **AOT**: on by default in prod — compiles templates to JS, faster render; tree-shaking drops unused code.
- **RxJS**: avoid leaks (`takeUntil`/`async`), `shareReplay`, merge/debounce requests.
- **Build budgets** (`ng build --budgets`) to cap bundle size; image lazy-load/compress; CDN for static assets.
- Run heavy non-UI work outside `ngZone` via `runOutsideAngular`.

---

## NG-7. 为什么 `*ngFor` 里要加 `trackBy`？没有它会发生什么？
**EN:** Why add `trackBy` in `*ngFor`? What happens without it?

**中文答案：**
`*ngFor` 默认用**对象引用**追踪列表项。列表更新（如重新取数据返回新数组）时，即使数据内容没变，Angular 也会销毁并重建所有 DOM 节点，导致性能差、输入框失焦、动画重置。`trackBy` 返回稳定标识（如 `item.id`），让 Angular 只更新变化项、复用既有 DOM。

```html
<li *ngFor="let item of items; trackBy: trackById">{{ item.name }}</li>
```
```ts
trackById(index: number, item: Item) { return item.id; }
```

**English answer:**
`*ngFor` tracks items by **object reference** by default. When the list updates (e.g. a new array from a fetch), even if content is unchanged, Angular destroys and recreates all DOM nodes — poor performance, lost input focus, reset animations. `trackBy` returns a stable identity (e.g. `item.id`) so Angular only updates changed items and reuses existing DOM.

```html
<li *ngFor="let item of items; trackBy: trackById">{{ item.name }}</li>
```
```ts
trackById(index: number, item: Item) { return item.id; }
```

---

## NG-8. 纯管道(pure pipe)与非纯管道(impure pipe)的区别？
**EN:** Pure vs impure pipes?

**中文答案：**
- **纯管道**（默认）：输入**引用不变**就不重新计算（结果缓存），只在 `@Input`/参数引用变化时执行——性能好、结果可预测。
- **非纯管道** `pure: false`：每次变更检测都重新执行——适合「输入引用不变但内部状态变化」的场景（如数组内元素变化、异步数据），但代价是每次 CD 都跑，需谨慎。

```ts
@Pipe({ name: 'filter', pure: false })
export class FilterPipe implements PipeTransform {
  transform(items: any[], term: string) { return items.filter(i => i.includes(term)); }
}
```

**English answer:**
- **Pure pipe** (default): won't recompute if the input **reference** is unchanged (result cached); runs only when `@Input`/arg references change — fast and predictable.
- **Impure pipe** `pure: false`: runs on every change detection — needed when the reference is stable but inner state changes (e.g. array elements mutate, async data); costs a run each CD, so use carefully.

```ts
@Pipe({ name: 'filter', pure: false })
export class FilterPipe implements PipeTransform {
  transform(items: any[], term: string) { return items.filter(i => i.includes(term)); }
}
```

---

## NG-9. 响应式表单(Reactive Forms) vs 模板驱动表单(Template-driven)，以及常用校验器。
**EN:** Reactive Forms vs Template-driven forms, and common validators.

**中文答案：**
- **响应式表单**：表单模型在 TS 中显式构建（`FormGroup`/`FormControl`），同步、可预测、易做复杂校验/动态表单/单元测试——适合复杂表单。
- **模板驱动**：用 `[(ngModel)]` + 指令在模板中声明，逻辑散在模板，适合简单表单，上手快。
- 校验器：内置 `Validators.required/min/max/minLength/pattern/email`；自定义校验器返回 `{ [key]: value } | null`；异步校验器返回 `Promise/Observable`。

```ts
const form = new FormGroup({
  email: new FormControl('', [Validators.required, Validators.email]),
  age: new FormControl(null, [Validators.min(18)]),
});
form.valueChanges.pipe(debounceTime(300)).subscribe(...);
```

**English answer:**
- **Reactive forms**: the form model is built explicitly in TS (`FormGroup`/`FormControl`); synchronous, predictable, easy for complex/dynamic forms and unit tests — best for complex forms.
- **Template-driven**: declared in the template via `[(ngModel)]` + directives; logic spread in template; quick for simple forms.
- Validators: built-ins `Validators.required/min/max/minLength/pattern/email`; custom validators return `{ [key]: value } | null`; async validators return `Promise/Observable`.

```ts
const form = new FormGroup({
  email: new FormControl('', [Validators.required, Validators.email]),
  age: new FormControl(null, [Validators.min(18)]),
});
form.valueChanges.pipe(debounceTime(300)).subscribe(...);
```

---

## NG-10. 路由守卫(guards)与解析器(resolvers)的作用？懒加载如何实现？
**EN:** Route guards and resolvers? How to implement lazy loading?

**中文答案：**
- **守卫**：`CanActivate`(能否进入)、`CanDeactivate`(能否离开，如未保存表单)、`CanActivateChild`、`CanLoad`(能否加载懒模块)、`Resolve`(进入前预取数据)。返回 `boolean | UrlTree | Promise | Observable`。
- **解析器 Resolver**：路由激活前预取数据，进入组件时数据已就绪，避免闪烁。
- **懒加载**：`{ path: 'admin', loadChildren: () => import('./admin/admin.module').then(m => m.AdminModule) }`（standalone 直接 `loadComponent`），Angular 打包成独立 chunk 按需加载。

```ts
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  canActivate(): boolean { return this.auth.isLoggedIn(); }
}
```

**English answer:**
- **Guards**: `CanActivate` (may enter), `CanDeactivate` (may leave, e.g. unsaved form), `CanActivateChild`, `CanLoad` (may load lazy module), `Resolve` (prefetch before entry). Return `boolean | UrlTree | Promise | Observable`.
- **Resolver**: prefetches data before activation so the component arrives with data ready (no flicker).
- **Lazy loading**: `{ path: 'admin', loadChildren: () => import('./admin/admin.module').then(m => m.AdminModule) }` (standalone uses `loadComponent`); Angular bundles it into a separate chunk loaded on demand.

```ts
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  canActivate(): boolean { return this.auth.isLoggedIn(); }
}
```

---

## NG-11. Standalone Components 与 NgModules 的关系？迁移的好处？
**EN:** Standalone components vs NgModules? Benefits of migrating?

**中文答案：**
- **NgModules**：历史默认，`@NgModule` 声明/导入/提供依赖，样板代码多。
- **Standalone components**（v14+）：组件 `standalone: true`，用 `imports` 直接声明依赖，无需模块；路由可用 `loadComponent` 懒加载单组件。
- 好处：减少样板、按组件粒度组织依赖、更小的初始包（tree-shake 更好）、渐进迁移（可混用）。

```ts
@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  selector: 'app-cart',
  template: `...`,
})
export class CartComponent {}
```

**English answer:**
- **NgModules**: legacy default; `@NgModule` declares/imports/provides deps — lots of boilerplate.
- **Standalone components** (v14+): `standalone: true`, declare deps via `imports`; routes can `loadComponent` a single component.
- Benefits: less boilerplate, dependency organization at component granularity, smaller initial bundle (better tree-shaking), incremental migration (mixable).

```ts
@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  selector: 'app-cart',
  template: `...`,
})
export class CartComponent {}
```

---

## NG-12. Angular 依赖注入(DI)的层次结构？`providedIn: 'root'` 与模块 provider 的区别？
**EN:** Angular DI hierarchy? `providedIn: 'root'` vs module providers?

**中文答案：**
Angular 有**分层注入器**（EnvironmentInjector + 每个组件的 ElementInjector）。依赖查找从组件自身 → 父组件 → 根，逐级向上，找到即用。
- `providedIn: 'root'`：服务注册到**根注入器**，全应用单例，可 tree-shake（未用到则被移除）——推荐。
- 模块 `providers`：注册到该模块的注入器，作用域受模块边界影响；惰性加载模块有独立注入器，可能产生**多个实例**（不同模块各一份）。
- `providedIn: 'any'`：每个懒加载模块一份实例。

**English answer:**
Angular has **hierarchical injectors** (EnvironmentInjector + a per-component ElementInjector). Lookup goes component → parent → root until found.
- `providedIn: 'root'`: registers in the **root injector**, app-wide singleton, tree-shakeable (dropped if unused) — recommended.
- Module `providers`: registers in that module's injector, scoped by module boundaries; lazy modules have separate injectors, so you may get **multiple instances** (one per module).
- `providedIn: 'any'`: one instance per lazy module.

---

## NG-13. 如何在 Angular 中处理 SSR/SSG（Angular Universal），以及它解决什么问题？
**EN:** How does Angular handle SSR/SSG (Angular Universal)? What problem does it solve?

**中文答案：**
Angular Universal 在**服务端**渲染 Angular 应用成 HTML，再在浏览器端**水合(hydration)**接管交互。解决的问题：① **SEO**——SPA 首屏是空 `app-root`，爬虫抓不到内容；② **首屏性能/白屏**——用户更早看到内容。SSG 在构建期预渲染静态页面。注意事项：避免直接访问 `window`/`document`（用 `isPlatformBrowser` 或 DI 抽象）、`TransferState` 把服务端数据传给客户端避免重复请求。

**English answer:**
Angular Universal **server-renders** the Angular app to HTML, then the browser **hydrates** to take over interactivity. Problems solved: ① **SEO** — an SPA's first paint is an empty `app-root` that crawlers can't read; ② **first-paint performance** — users see content sooner. SSG pre-renders static pages at build time. Caveats: avoid direct `window`/`document` access (`isPlatformBrowser` or DI abstraction); use `TransferState` to pass server data to the client and avoid duplicate requests.

---

## NG-14. 如何避免 RxJS 订阅的内存泄漏？`async` 管道 vs `takeUntil` vs `takeUntilDestroyed`。
**EN:** How to avoid RxJS subscription leaks? `async` pipe vs `takeUntil` vs `takeUntilDestroyed`.

**中文答案：**
- **`async` 管道**（首选）：自动订阅/退订，模板里 `obs | async`，零手动清理。
- **`takeUntil(notifier)`**：在 `ngOnDestroy` 里 `notifier.next()` 触发退订；经典模式。
- **`takeUntilDestroyed()`**（v16+）：自动在组件销毁时退订，无需手动 subject。
- 其他：`subscription.add(...)` 组合、`first()` 只取一次、`unsubscribe()` on destroy。
原则：**每个订阅都要有对应清理**，否则组件销毁后仍持有引用 → 内存泄漏 + 幽灵回调。

```ts
export class Comp {
  private destroy$ = new Subject<void>();
  ngOnInit() {
    this.api.get().pipe(takeUntil(this.destroy$)).subscribe();
  }
  ngOnDestroy() { this.destroy$.next(); this.destroy$.complete(); }
}
```

**English answer:**
- **`async` pipe** (preferred): auto subscribe/unsubscribe; `obs | async` in the template; zero manual cleanup.
- **`takeUntil(notifier)`**: call `notifier.next()` in `ngOnDestroy`; classic pattern.
- **`takeUntilDestroyed()`** (v16+): auto-unsubscribes on destroy, no manual subject.
- Others: `subscription.add(...)`, `first()`, `unsubscribe()` on destroy.
Principle: **every subscription needs cleanup**, otherwise the destroyed component still holds references → memory leaks + ghost callbacks.

```ts
export class Comp {
  private destroy$ = new Subject<void>();
  ngOnInit() {
    this.api.get().pipe(takeUntil(this.destroy$)).subscribe();
  }
  ngOnDestroy() { this.destroy$.next(); this.destroy$.complete(); }
}
```
