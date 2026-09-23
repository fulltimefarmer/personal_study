// ============================================================
// React 基础语法 03：useState —— 组件状态
// useState 让函数组件拥有“状态”，状态变化会触发重新渲染。
// ============================================================

// ── useState 详解 ─────────────────────────────────────────────
// 作用：让函数组件拥有“状态”，状态变化会触发组件重新渲染。
// 特点：
//   - 更新是异步的，同一事件里多次 set 会被批量合并
//   - 更新对象/数组必须返回新引用（不可变更新），否则不触发渲染
//   - 支持函数式更新 setX(prev => ...)，避免闭包过期
//   - 支持惰性初始化 useState(() => 计算初值)，只在首次渲染执行
// 使用场景：任何需要记住并展示/交互的数据：计数器、表单输入、开关、列表、加载状态等。
// ─────────────────────────────────────────────────────────────

import { useState } from "react";

// ---------- 1. 基本用法 ----------
// const [state, setState] = useState(初始值)
// state：当前值；setState：更新函数
function Counter() {
  const [count, setCount] = useState(0); // 初始值 0

  return (
    <div>
      <p>当前计数：{count}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}

// ---------- 2. 函数式更新 ----------
// setCount(prev => prev + 1)：基于上一次状态更新，避免闭包过期问题
function CounterFunctional() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => {
      setCount((prev) => prev + 1);
      setCount((prev) => prev + 1); // 连续两次，都会基于最新值
    }}>
      {count}
    </button>
  );
}

// ---------- 3. 多种状态：对象 / 数组 ----------
function FormState() {
  const [form, setForm] = useState({ name: "", email: "" });
  const [tags, setTags] = useState<string[]>([]);

  // 更新对象：必须返回新对象（不可变更新），否则不会触发渲染
  const updateName = (name: string) => {
    setForm((prev) => ({ ...prev, name })); // 展开旧值 + 覆盖 name
  };

  // 更新数组：返回新数组
  const addTag = (tag: string) => {
    setTags((prev) => [...prev, tag]);
  };

  return <div>{/* ... */}</div>;
}

// ---------- 4. 惰性初始化：初始值需要计算时传函数 ----------
function ExpensiveInit() {
  // useState(() => ...) 只在首次渲染时执行一次
  const [value] = useState(() => {
    console.log("只执行一次");
    return computeExpensiveValue();
  });
  return <div>{value}</div>;
}
function computeExpensiveValue(): number { return 42; }

// ---------- 5. 多个 useState ----------
function MultiState() {
  const [name, setName] = useState("");
  const [age, setAge] = useState(0);
  const [active, setActive] = useState(false);
  // 或者合并到一个对象，按需选择
  return <div>{name}{age}{active}</div>;
}

// ---------- 6. 常见误区：状态是异步更新的 ----------
function AsyncUpdateExample() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setCount(count + 1);
    console.log(count); // 打印的是旧值！状态更新是异步的
    // 想要拿到新值：用变量接收 或 在 useEffect 里观察
  };

  return <button onClick={handleClick}>{count}</button>;
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件，用 useState 保存购物车商品数量，
//         提供 +、- 两个按钮（数量不能小于 0）。
// function CartQuantity() { /* 你的代码 */ }

// TODO 2：写一个组件，用 useState 保存一个字符串数组，
//         点按钮就往数组末尾加一个新元素，并渲染列表。
// function TodoList() { /* 你的代码 */ }

export { Counter, CounterFunctional, FormState, ExpensiveInit, MultiState, AsyncUpdateExample };
