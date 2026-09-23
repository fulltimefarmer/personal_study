// ============================================================
// React 基础语法 04：useEffect —— 副作用
// useEffect 在渲染后执行副作用（请求、订阅、操作 DOM、定时器）。
// ============================================================

// ── useEffect 详解 ───────────────────────────────────────────
// 作用：在渲染完成后执行“副作用”（请求、订阅、定时器、操作 DOM），并支持清理。
// 特点：
//   - 依赖数组决定执行时机：不传→每次渲染；[]→只挂载一次；[deps]→依赖变化时
//   - 返回清理函数：在组件卸载或下次执行前运行（清定时器/取消订阅）
//   - 是渲染之后的“后置”流程，不宜放阻塞渲染的重活
// 使用场景：请求数据、订阅事件/数据源、定时器、操作 DOM/初始化第三方库、响应状态变化的副作用。
// ─────────────────────────────────────────────────────────────

import { useEffect, useState } from "react";

// ---------- 1. 每次渲染后都执行（无依赖数组） ----------
function EveryRender() {
  useEffect(() => {
    console.log("每次渲染后执行");
  });
  return <div />;
}

// ---------- 2. 只在首次挂载时执行（依赖数组 []） ----------
function MountOnly() {
  useEffect(() => {
    console.log("只在挂载时执行一次");
    // 等价于类组件的 componentDidMount
  }, []);
  return <div />;
}

// ---------- 3. 依赖变化时执行 ----------
function OnCountChange() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    console.log(`count 变成了 ${count}`);
  }, [count]); // 依赖 count，count 变化才执行
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}

// ---------- 4. 清理函数（return 一个函数） ----------
// 在组件卸载 或 依赖变化重新执行前，先运行上一次的清理函数
function Timer() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    // 清理：组件卸载时清除定时器，避免内存泄漏
    return () => clearInterval(timer);
  }, []);

  return <div>{now.toLocaleTimeString()}</div>;
}

// ---------- 5. 请求数据 ----------
interface Product { id: number; name: string }

function ProductList() {
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    let cancelled = false; // 防止卸载后 setState

    async function load() {
      const res = await fetch("/api/products");
      const data: Product[] = await res.json();
      if (!cancelled) setProducts(data);
    }
    load();

    return () => { cancelled = true; }; // 清理
  }, []);

  return (
    <ul>
      {products.map((p) => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}

// ---------- 6. 订阅外部数据源（事件监听） ----------
function WindowSize() {
  const [size, setSize] = useState(window.innerWidth);

  useEffect(() => {
    const onResize = () => setSize(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize); // 清理监听器
  }, []);

  return <div>窗口宽度：{size}px</div>;
}

// ---------- 7. 依赖数组的正确性 ----------
// 规则：effect 里用到的所有响应式值（state/props）都要写进依赖数组
function BadExample({ id }: { id: number }) {
  const [data, setData] = useState<unknown>(null);
  useEffect(() => {
    fetch(`/api/${id}`).then((r) => r.json()).then(setData);
    // 依赖数组缺失 id：id 变化时不会重新请求
  }, []); // ❌ 应写 [id]
  return <div>{String(data)}</div>;
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件，挂载时设置 document.title = "我的页面"，
//         卸载时重置为默认值。
// function Title() { /* 你的代码 */ }

// TODO 2：写一个组件，用 useEffect 监听 count 变化并打印，带清理函数。
// function WatchCount() { /* 你的代码 */ }

export { EveryRender, MountOnly, OnCountChange, Timer, ProductList, WindowSize, BadExample };
