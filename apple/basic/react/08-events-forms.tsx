// ============================================================
// React 基础语法 08：事件处理 / 受控组件 / 表单
// ============================================================

import { useState, useRef } from "react";
import type { MouseEvent, ChangeEvent, FormEvent, KeyboardEvent } from "react";

// ---------- 1. 事件处理 ----------
// 事件名用驼峰：onClick、onChange、onSubmit、onKeyDown...
// 处理函数通常是箭头函数或单独定义
function ClickHandler() {
  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    console.log("点击了", e.target);
  };
  return <button onClick={handleClick}>点我</button>;
}

// 内联箭头函数（带参数）
function InlineHandler() {
  return (
    <div>
      {[1, 2, 3].map((n) => (
        <button key={n} onClick={() => console.log(n)}>{n}</button>
      ))}
    </div>
  );
}

// ---------- 2. 受控组件：表单值由 state 控制 ----------
// input 的 value 绑定 state，onChange 更新 state
function ControlledInput() {
  const [text, setText] = useState("");
  return (
    <div>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)} // e.target.value 是输入值
        placeholder="输入内容"
      />
      <p>你输入了：{text}</p>
    </div>
  );
}

// ---------- 3. 完整表单（多个字段 + 提交） ----------
function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); // 阻止页面刷新
    console.log({ email, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="邮箱"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="密码"
      />
      <button type="submit">登录</button>
    </form>
  );
}

// ---------- 4. 其他表单元素：checkbox / select / textarea ----------
function SurveyForm() {
  const [agree, setAgree] = useState(false);
  const [city, setCity] = useState("sh");
  const [note, setNote] = useState("");

  return (
    <div>
      {/* checkbox：用 checked 而非 value */}
      <label>
        <input
          type="checkbox"
          checked={agree}
          onChange={(e) => setAgree(e.target.checked)}
        />
        同意条款
      </label>

      {/* select */}
      <select value={city} onChange={(e) => setCity(e.target.value)}>
        <option value="sh">上海</option>
        <option value="bj">北京</option>
      </select>

      {/* textarea：value 绑定 */}
      <textarea value={note} onChange={(e) => setNote(e.target.value)} />
    </div>
  );
}

// ---------- 5. 事件对象的类型 ----------
// 常见事件类型：MouseEvent、ChangeEvent、FormEvent、KeyboardEvent（从 react 导入）
function TypedHandlers() {
  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.target.value; // string
  };
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    e.key; // 按下的键
    if (e.key === "Enter") console.log("回车");
  };
  return <input onChange={onChange} onKeyDown={onKeyDown} />;
}

// ---------- 6. 非受控组件（用 ref 而非 state，较少用） ----------
function Uncontrolled() {
  const inputRef = useRef<HTMLInputElement>(null);
  const read = () => console.log(inputRef.current?.value);
  return (
    <div>
      <input ref={inputRef} />
      <button onClick={read}>读取</button>
    </div>
  );
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个受控输入框，把输入转成大写显示在下方。
// function UpperInput() { /* 你的代码 */ }

// TODO 2：写一个表单，含姓名和年龄两个字段，提交时 console.log 出来。
// function ProfileForm() { /* 你的代码 */ }

export { ClickHandler, InlineHandler, ControlledInput, LoginForm, SurveyForm, TypedHandlers, Uncontrolled };
