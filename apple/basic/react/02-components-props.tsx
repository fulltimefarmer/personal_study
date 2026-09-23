// ============================================================
// React 基础语法 02：函数组件 / Props / children
// 组件是 React 的核心：一个返回 JSX 的函数。
// ============================================================

import type { ReactNode } from "react";

// ---------- 1. 函数组件 ----------
function Welcome() {
  return <h1>Welcome</h1>;
}

// 箭头函数组件
const Footer = () => <footer>© 2026</footer>;

// ---------- 2. Props：组件接收外部数据 ----------
// props 是组件的第一参数，只读（不能修改）
interface GreetingProps {
  name: string;
  age?: number; // 可选属性
}

function Greeting(props: GreetingProps) {
  return (
    <p>
      Hello, {props.name}
      {props.age ? ` (${props.age} 岁)` : ""}
    </p>
  );
}

// 用法：<Greeting name="Tom" age={30} />

// ---------- 3. 解构 props（更常用） ----------
function GreetingDestructured({ name, age }: GreetingProps) {
  return <p>Hello, {name}{age ? ` (${age})` : ""}</p>;
}

// ---------- 4. 默认值 ----------
function Button({ label = "确定" }: { label?: string }) {
  return <button>{label}</button>;
}

// ---------- 5. children：组件标签之间夹的内容 ----------
interface CardProps {
  title: string;
  children?: ReactNode; // children 类型
}

function Card({ title, children }: CardProps) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div>{children}</div> {/* 渲染传入的子内容 */}
    </div>
  );
}

// 用法：
// <Card title="商品">
//   <p>这是商品详情</p>
// </Card>

// ---------- 6. 传递 JSX 作为 prop ----------
function Layout({ sidebar, main }: { sidebar: ReactNode; main: ReactNode }) {
  return (
    <div style={{ display: "flex" }}>
      <aside>{sidebar}</aside>
      <section>{main}</section>
    </div>
  );
}

// ---------- 7. 组件组合：一个组件渲染另一个组件 ----------
function App() {
  return (
    <Layout
      sidebar={<nav>侧边栏</nav>}
      main={
        <Card title="欢迎">
          <GreetingDestructured name="Alice" />
        </Card>
      }
    />
  );
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件 UserCard，接收 name 和 email 两个 props，
//         渲染成一行文本（用解构写法）。
// function UserCard({ name, email }: { name: string; email: string }) {
//   /* 你的代码 */
// }

// TODO 2：写一个组件 Wrapper，把 children 包在一个 <section> 里。
// function Wrapper({ children }: { children: ReactNode }) {
//   /* 你的代码 */
// }

export { Welcome, Footer, Greeting, GreetingDestructured, Button, Card, Layout, App };
