// ============================================================
// React 基础语法 11：自定义 Hook —— 复用逻辑
// 自定义 Hook 是「以 use 开头、内部可调用其他 Hook」的函数。
// ============================================================

// ── 自定义 Hook 详解 ─────────────────────────────────────────
// 作用：把“有状态的逻辑”抽取成可复用的函数（以 use 开头）。
// 特点：
//   - 必须以 use 开头（React 据此识别并应用 Hook 规则）
//   - 内部可调用其它 Hook
//   - 每个使用它的组件各自拥有独立状态实例（不共享）
// 使用场景：多组件复用的逻辑：useFetch、useLocalStorage、useToggle、useDebounce、usePrevious 等。
// ─────────────────────────────────────────────────────────────

import { useState, useEffect } from "react";

// ---------- 1. 自定义 Hook 命名规则 ----------
// 必须以 use 开头（React 靠名字识别 Hook 规则），内部可调用 useState/useEffect 等。

// ---------- 2. 例子：useToggle ----------
function useToggle(initial = false): [boolean, () => void] {
  const [on, setOn] = useState(initial);
  const toggle = () => setOn((v) => !v);
  return [on, toggle];
}

function ToggleDemo() {
  const [on, toggle] = useToggle();
  return <button onClick={toggle}>{on ? "开" : "关"}</button>;
}

// ---------- 3. 例子：useLocalStorage —— 把状态持久化 ----------
function useLocalStorage<T>(key: string, initialValue: T): [T, (v: T) => void] {
  const [stored, setStored] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(stored));
  }, [key, stored]);

  return [stored, setStored];
}

// ---------- 4. 例子：useFetch —— 封装请求逻辑 ----------
interface FetchState<T> { data: T | null; loading: boolean; error: string | null }

function useFetch<T>(url: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, loading: true, error: null });
    fetch(url)
      .then((r) => r.json())
      .then((data: T) => { if (!cancelled) setState({ data, loading: false, error: null }); })
      .catch((err: Error) => { if (!cancelled) setState({ data: null, loading: false, error: err.message }); });
    return () => { cancelled = true; };
  }, [url]);

  return state;
}

// ---------- 5. 自定义 Hook 的价值 ----------
// 1) 复用有状态的逻辑；2) 让组件更简洁；3) 可组合（一个 Hook 内部可调另一个 Hook）。

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个 useCounter Hook，返回 [count, increment, decrement, reset]。
// function useCounter(initial = 0) { /* 你的代码 */ }

// TODO 2：写一个 useDebounce Hook，接收 value 和 delay，返回防抖后的值。
// function useDebounce<T>(value: T, delay: number): T { /* 你的代码 */ }

export { useToggle, ToggleDemo, useLocalStorage, useFetch };
