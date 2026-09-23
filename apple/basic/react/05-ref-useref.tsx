// ============================================================
// React 基础语法 05：useRef —— 引用
// useRef 返回一个可变对象 { current: ... }，其变化不触发重新渲染。
// 用途：① 访问 DOM 元素；② 保存跨渲染的可变值。
// ============================================================

// ── useRef 详解 ──────────────────────────────────────────────
// 作用：返回一个可变的 { current } 引用，跨渲染保持不变，修改它不触发重渲染。
// 特点：
//   - 变化不触发重渲染（与 useState 的最大区别）
//   - 常用于通过 ref 绑定访问 DOM 节点
//   - React 19 必须传初始值（如 useRef(null)）
//   - current 可随时读写
// 使用场景：访问/操作 DOM（聚焦、滚动、播放）、保存定时器 ID、保存上一次的值、非渲染的可变数据。
// ─────────────────────────────────────────────────────────────

import { useRef, useState, useEffect } from "react";

// ---------- 1. 访问 DOM 元素 ----------
function FocusInput() {
  const inputRef = useRef<HTMLInputElement>(null); // 泛型指定 DOM 类型

  const focus = () => {
    inputRef.current?.focus(); // current 可能是 null，用可选链
  };

  return (
    <div>
      <input ref={inputRef} type="text" /> {/* 用 ref 绑定 */}
      <button onClick={focus}>聚焦输入框</button>
    </div>
  );
}

// ---------- 2. 保存跨渲染的可变值（不触发渲染） ----------
function RenderCount() {
  const renderCount = useRef(0);
  const [count, setCount] = useState(0);

  renderCount.current += 1; // 每次渲染自增，但不触发新渲染

  return (
    <div>
      <p>按钮点击：{count}</p>
      <p>已渲染次数：{renderCount.current}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}

// ---------- 3. 保存上一次的值 ----------
function usePrevious<T>(value: T): T | undefined {
  // React 19 的 useRef 必须传初始值，这里用 undefined 占位
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => {
    ref.current = value; // 渲染后才更新，所以 current 始终是“上一次”的值
  });
  return ref.current;
}
function PreviousDemo() {
  const [count, setCount] = useState(0);
  const prev = usePrevious(count);
  return (
    <div>
      <p>当前 {count}，上一次 {prev ?? "无"}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}

// ---------- 4. 保存定时器 ID（配合清理） ----------
function TimerWithRef() {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const start = () => {
    if (timerRef.current) return;
    timerRef.current = setInterval(() => console.log("tick"), 1000);
  };
  const stop = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
  };

  return (
    <div>
      <button onClick={start}>开始</button>
      <button onClick={stop}>停止</button>
    </div>
  );
}

// ---------- 5. useRef vs useState ----------
// useState：变化触发重渲染，用于“界面数据”。
// useRef：变化不触发重渲染，用于“DOM 引用 / 非渲染的可变值”。

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件，用 useRef 拿到一个 <video> 元素，
//         点按钮调用 video.play()。
// function VideoPlayer() { /* 你的代码 */ }

// TODO 2：写一个组件，用 useRef 统计按钮点击次数，但不触发重渲染。
// function ClickCounter() { /* 你的代码 */ }

export { FocusInput, RenderCount, PreviousDemo, TimerWithRef, usePrevious };
