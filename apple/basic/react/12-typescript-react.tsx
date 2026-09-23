// ============================================================
// React 基础语法 12：TypeScript + React 类型
// 用 TS 给组件、props、children、事件、泛型组件标注类型。
// ============================================================

import { useState, useRef } from "react";
import type { ReactNode, MouseEvent, ChangeEvent, FormEvent } from "react";

// ---------- 1. 组件返回值类型 ----------
// 函数组件的返回类型由 TS 自动推断，通常无需手写注解。
function Hello() {
  return <div>Hello</div>;
}

// ---------- 2. Props 类型 ----------
interface ButtonProps {
  label: string;
  onClick?: () => void;        // 可选
  disabled?: boolean;
  children?: ReactNode;        // children
}
function Button({ label, onClick, disabled, children }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
      {children}
    </button>
  );
}

// ---------- 3. 显式 props 类型（推荐，替代 React.FC） ----------
// 现代推荐直接给 props 加类型，不用 React.FC（其隐式 children 容易引入问题）
type CardProps = { title: string; children?: ReactNode };
function Card({ title, children }: CardProps) {
  return (
    <div>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

// ---------- 4. 事件类型 ----------
function EventTypes() {
  const onClick = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
  };
  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value: string = e.target.value;
  };
  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
  };
  return <form onSubmit={onSubmit}><input onChange={onChange} /><button onClick={onClick}>ok</button></form>;
}

// ---------- 5. Hook 泛型：useState / useRef ----------
function TypedState() {
  const [user, setUser] = useState<{ name: string } | null>(null); // 联合类型 + null
  const [items, setItems] = useState<string[]>([]);                // 数组
  const inputRef = useRef<HTMLInputElement>(null);                 // DOM ref

  return <input ref={inputRef} />;
}

// ---------- 6. 泛型组件 ----------
// 让组件也能接收类型参数
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => ReactNode;
}
function List<T>({ items, renderItem }: ListProps<T>) {
  return <ul>{items.map((item, i) => <li key={i}>{renderItem(item)}</li>)}</ul>;
}

// 用法：
// <List items={[1,2,3]} renderItem={(n) => <b>{n}</b>} />
// <List items={[{id:1},{id:2}]} renderItem={(o) => <span>{o.id}</span>} />

// ---------- 7. 用 discriminated union 描述 props（不同形态组件） ----------
type Message =
  | { kind: "success"; text: string }
  | { kind: "error"; code: number };

function MessageBanner({ msg }: { msg: Message }) {
  if (msg.kind === "success") return <div className="ok">{msg.text}</div>;
  return <div className="err">错误码 {msg.code}</div>; // 收窄后只有 code
}

// ---------- 8. 常见 DOM/事件类型速查 ----------
// 元素：HTMLInputElement、HTMLButtonElement、HTMLDivElement、HTMLElement...
// 事件：MouseEvent、ChangeEvent、FormEvent、KeyboardEvent、FocusEvent、DragEvent...
// 从 react 里用 import type 导入，如 import type { ChangeEvent } from "react"。

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个泛型组件 Table<T>，接收 rows: T[] 和 columns: (keyof T)[]，
//         渲染一个表格。
// interface TableProps<T> { rows: T[]; columns: (keyof T)[] }
// function Table<T>({ rows, columns }: TableProps<T>) { /* 你的代码 */ }

export { Hello, Button, Card, EventTypes, TypedState, List, MessageBanner };
