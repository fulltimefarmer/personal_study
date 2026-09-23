// ============================================================
// React 基础语法 01：JSX 基础
// JSX 是一种“在 JS 里写 HTML 标签”的语法，编译后变成 jsx() 调用。
// 说明：本文件是 .tsx，需在 React 项目（Vite/CRA）或在线 Playground 里运行。
// ============================================================

// 注意：新版 JSX 转换（react-jsx）下，使用 JSX 无需手动 import React。

// ---------- 1. 基本 JSX ----------
const element = <h1>Hello, Apple Store</h1>; // 一个 React 元素

// ---------- 2. 用变量包裹多个标签 ----------
// 返回多个元素时必须用一个父元素包裹（或使用 Fragment）
function Greeting() {
  return (
    <div>                         {/* 小括号包裹，多行 JSX */}
      <h1>标题</h1>
      <p>段落内容</p>
    </div>
  );
}

// ---------- 3. Fragment：不产生多余 DOM 的包裹 ----------
function FragmentExample() {
  return (
    <>
      <h1>用空标签</h1>
      <h2>不会渲染额外的 DOM 节点</h2>
    </>
  );
}

// ---------- 4. 在 JSX 中嵌入 JS 表达式（用花括号 {}） ----------
const userName = "Tom";
const count = 3;
function EmbedExpression() {
  return (
    <div>
      <p>你好，{userName}</p>              {/* 字符串 */}
      <p>你有 {count + 1} 条消息</p>        {/* 计算表达式 */}
      <p>今天是 {new Date().getFullYear()} 年</p>
      <p>{count > 0 ? "有消息" : "无消息"}</p> {/* 三元表达式 */}
    </div>
  );
}

// ---------- 5. JSX 注释 ----------
// JSX 内部注释要用 {/* ... */}，不能直接用 //
function CommentExample() {
  return (
    <div>
      {/* 这是 JSX 注释 */}
      <span>内容</span>
    </div>
  );
}

// ---------- 6. 属性（props）与驼峰命名 ----------
// HTML 属性在 JSX 里用驼峰：class -> className，for -> htmlFor
function AttributeExample() {
  return (
    <div
      className="card"               // class -> className
      id="main"
      data-testid="card"             // data-* 保留原样
      style={{ color: "red", fontSize: 16 }} // style 接收对象，键用驼峰
    >
      {/* 布尔属性：值为 true 可省略 ={true} */}
      <input type="checkbox" checked disabled />
      <button aria-hidden="true">按钮</button>
    </div>
  );
}

// ---------- 7. 条件渲染与列表渲染基础 ----------
function BasicList() {
  const items = ["iPhone", "iPad", "Mac"];
  return (
    <ul>
      {/* map 生成列表，每个元素需要唯一 key */}
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个组件，返回一个 <div>，里面有一个 <h2> 标题和一段 <p> 文字，
//         并用花括号显示一个变量的值。
// function MyComponent() { /* 你的代码 */ }

export { Greeting, FragmentExample, EmbedExpression, CommentExample, AttributeExample, BasicList };
