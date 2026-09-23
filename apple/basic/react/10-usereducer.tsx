// ============================================================
// React 基础语法 10：useReducer —— 复杂状态管理
// 当状态逻辑复杂、多个状态互相影响时，用 reducer 更清晰。
// ============================================================

// ── useReducer 详解 ──────────────────────────────────────────
// 作用：用 reducer 纯函数管理复杂状态，通过 dispatch(action) 触发更新。
// 特点：
//   - 更新逻辑集中在一个纯函数里，便于测试与复用
//   - 适合多个状态互相耦合、更新逻辑复杂的情况
//   - action 通常用可辨识联合（type 字段区分）
// 使用场景：购物车、多字段联动表单、状态机、需要把更新逻辑抽离测试的场景。
// ─────────────────────────────────────────────────────────────

import { useReducer } from "react";

// ---------- 1. reducer：纯函数，接收 (state, action)，返回新 state ----------
type State = { count: number };

// action 用可辨识联合（type 字段区分）
type Action =
  | { type: "increment" }
  | { type: "decrement" }
  | { type: "reset" }
  | { type: "add"; amount: number };

const initialState: State = { count: 0 };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "increment": return { count: state.count + 1 };
    case "decrement": return { count: state.count - 1 };
    case "reset":     return { count: 0 };
    case "add":       return { count: state.count + action.amount };
    default:          return state;
  }
}

// ---------- 2. 使用 useReducer ----------
// const [state, dispatch] = useReducer(reducer, initialState)
function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <div>
      <p>{state.count}</p>
      <button onClick={() => dispatch({ type: "increment" })}>+1</button>
      <button onClick={() => dispatch({ type: "decrement" })}>-1</button>
      <button onClick={() => dispatch({ type: "add", amount: 10 })}>+10</button>
      <button onClick={() => dispatch({ type: "reset" })}>重置</button>
    </div>
  );
}

// ---------- 3. 惰性初始化：第三个参数 ----------
function init(initial: number): State {
  return { count: initial };
}
function CounterWithInit({ start }: { start: number }) {
  const [state, dispatch] = useReducer(reducer, start, init);
  return <button onClick={() => dispatch({ type: "increment" })}>{state.count}</button>;
}

// ---------- 4. useReducer vs useState ----------
// useState：简单、独立的状态。
// useReducer：多个状态互相耦合、更新逻辑复杂（如购物车增删改清空）、便于测试与复用。

// ---------- 5. 实战：购物车 reducer ----------
type CartState = { items: { id: number; qty: number }[] };
type CartAction =
  | { type: "add"; id: number }
  | { type: "remove"; id: number }
  | { type: "clear" };

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case "add": {
      const found = state.items.find((i) => i.id === action.id);
      if (found) {
        return { items: state.items.map((i) => i.id === action.id ? { ...i, qty: i.qty + 1 } : i) };
      }
      return { items: [...state.items, { id: action.id, qty: 1 }] };
    }
    case "remove":
      return { items: state.items.filter((i) => i.id !== action.id) };
    case "clear":
      return { items: [] };
    default:
      return state;
  }
}

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：写一个 reducer 管理「待办列表」，支持 add、toggle、remove 三种 action。
// type Todo = { id: number; text: string; done: boolean };
// type TodoAction = /* 你的代码 */;
// function todoReducer(state: Todo[], action: TodoAction): Todo[] { /* 你的代码 */ }

export { Counter, CounterWithInit, reducer, cartReducer };
