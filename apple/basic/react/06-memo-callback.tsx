// ============================================================
// React 基础语法 06：useMemo / useCallback / memo —— 性能优化
// 目的：避免不必要的计算与不必要的子组件重渲染。
// ============================================================

// ── useMemo / useCallback / memo 详解 ────────────────────────
// useMemo：缓存“计算结果”，依赖不变时直接返回缓存值，避免重复计算。
//   场景：大数组过滤/排序、复杂派生数据（如购物车总价）。
// useCallback：缓存“函数引用”，依赖不变时返回同一个函数。
//   场景：把回调传给 memo 子组件、作为其它 Hook 依赖时需要稳定引用。
// memo：缓存“组件”，props 浅比较没变就跳过重渲染。
//   场景：子组件渲染昂贵 + props 稳定 + 父组件频繁重渲染。
// 提醒：三者是“优化手段”，不是默认必写；先保证正确，再用 Profiler 定位瓶颈。
// ─────────────────────────────────────────────────────────────

import { useMemo, useCallback, useState, memo } from "react";

// ---------- 1. useMemo：缓存计算结果 ----------
// 依赖不变时，直接返回缓存值，不重新计算
function ExpensiveList({ items }: { items: number[] }) {
  const [filter, setFilter] = useState(0);

  // 只有当 items 或 filter 变化时才重新计算
  const filtered = useMemo(() => {
    console.log("重新计算 filtered");
    return items.filter((n) => n > filter);
  }, [items, filter]);

  return (
    <div>
      <button onClick={() => setFilter(filter + 1)}>提高阈值</button>
      <ul>{filtered.map((n) => <li key={n}>{n}</li>)}</ul>
    </div>
  );
}

// ---------- 2. useCallback：缓存函数引用 ----------
// 返回一个“记忆化”的函数，依赖不变时引用不变。
// 主要用于：把回调传给用 memo 包裹的子组件，避免子组件因函数引用变化而重渲染。
function Parent() {
  const [count, setCount] = useState(0);

  // 普通写法：每次渲染都生成新函数，子组件 memo 失效
  // const handleClick = () => setCount(c => c + 1);

  // useCallback：依赖 []，函数引用稳定
  const handleClick = useCallback(() => setCount((c) => c + 1), []);

  return (
    <div>
      <p>{count}</p>
      <MemoButton onClick={handleClick} label="+1" />
    </div>
  );
}

// ---------- 3. memo：记忆化组件 ----------
// props 没变就跳过重渲染（浅比较）
interface ButtonProps { onClick: () => void; label: string }
const MemoButton = memo(function Button({ onClick, label }: ButtonProps) {
  console.log("Button 渲染了");
  return <button onClick={onClick}>{label}</button>;
});

// ---------- 4. 三者配合 ----------
// memo 子组件 + useCallback 回调 + useMemo 计算：
// 父组件重渲染时，稳定的 props 引用让子组件跳过重渲染。

// ---------- 5. 何时使用 / 何时不用 ----------
// 使用：计算昂贵（大数组过滤/排序）、子组件重渲染频繁且 props 稳定。
// 不用：简单计算、组件本身很轻 —— 过早优化会增加复杂度。
// 原则：先保证正确，遇到性能问题再优化（用 Profiler 定位）。

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件，用 useMemo 缓存一个数组的排序结果。
// function SortedList({ nums }: { nums: number[] }) { /* 你的代码 */ }

// TODO 2：用 memo 包裹一个小组件，接收 onDelete 和 text，
//         并在父组件用 useCallback 传入稳定的 onDelete。
// const MemoItem = memo(/* 你的组件 */);

export { ExpensiveList, Parent, MemoButton };
