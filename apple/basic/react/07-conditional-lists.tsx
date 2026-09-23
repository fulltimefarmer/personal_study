// ============================================================
// React 基础语法 07：条件渲染 / 列表渲染 / key
// ============================================================

import { useState } from "react";

// ---------- 1. 条件渲染：if 语句（在 return 之前） ----------
function Greeting({ isLoggedIn }: { isLoggedIn: boolean }) {
  if (isLoggedIn) {
    return <h1>欢迎回来</h1>;
  }
  return <h1>请登录</h1>;
}

// ---------- 2. 三元表达式 ----------
function StatusBadge({ online }: { online: boolean }) {
  return <span>{online ? "在线" : "离线"}</span>;
}

// ---------- 3. 逻辑与 && ----------
// 条件为 true 才渲染右侧；注意：左侧若为 0 或 "" 会被渲染出来（falsy 陷阱）
function Notification({ count }: { count: number }) {
  return (
    <div>
      {count > 0 && <span>你有 {count} 条未读消息</span>}
      {/* 更安全写法：count > 0 ? <span>...</span> : null */}
    </div>
  );
}

// ---------- 4. 逻辑或 ||（提供兜底） ----------
function UserName({ name }: { name?: string }) {
  return <span>{name || "匿名用户"}</span>;
}

// ---------- 5. 立即执行函数（IIFE）包裹复杂逻辑 ----------
function Complex({ score }: { score: number }) {
  return (
    <div>
      {(() => {
        if (score >= 90) return <b>优秀</b>;
        if (score >= 60) return <span>及格</span>;
        return <i>不及格</i>;
      })()}
    </div>
  );
}

// ---------- 6. 列表渲染：map + key ----------
function ProductList() {
  const products = [
    { id: 1, name: "iPhone" },
    { id: 2, name: "iPad" },
    { id: 3, name: "Mac" },
  ];
  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>{p.name}</li> // key 用稳定唯一 id，不用数组下标
      ))}
    </ul>
  );
}

// ---------- 7. key 的作用与陷阱 ----------
// key 帮助 React 识别哪些元素变化了（复用/销毁/移动）。
// 陷阱：用数组下标 index 作 key，在“插入/删除/排序”时会导致状态错乱。

function BadKeys() {
  const [items, setItems] = useState(["a", "b", "c"]);
  return (
    <ul>
      {items.map((item, index) => (
        // ❌ 用 index 作 key：删除中间项时，后面的组件会被错误复用
        <li key={index}>{item}</li>
      ))}
    </ul>
  );
}

// ---------- 8. 在列表里渲染条件 ----------
function FilteredList() {
  const nums = [1, 2, 3, 4, 5];
  return (
    <ul>
      {nums
        .filter((n) => n % 2 === 0) // 先过滤
        .map((n) => <li key={n}>{n}</li>)}
    </ul>
  );
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件，接收 items: string[]，渲染成列表，
//         如果数组为空则显示“暂无数据”。
// function ListOrEmpty({ items }: { items: string[] }) { /* 你的代码 */ }

// TODO 2：写一个组件，根据 level（"success"|"error"|"info"）渲染不同颜色的提示框。
// function Alert({ level }: { level: "success" | "error" | "info" }) { /* 你的代码 */ }

export { Greeting, StatusBadge, Notification, UserName, Complex, ProductList, BadKeys, FilteredList };
