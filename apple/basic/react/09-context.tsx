// ============================================================
// React 基础语法 09：Context —— 跨层级共享状态
// 避免层层传递 props（props drilling），如主题、用户信息、语言。
// ============================================================

// ── createContext / useContext 详解 ──────────────────────────
// createContext(默认值)：创建共享数据的“上下文”容器。
// useContext(Context)：在组件里读取最近 Provider 提供的值。
// 特点：
//   - 不用层层传 props，可跨任意层级读取
//   - Provider 的 value 变化会导致所有消费该 context 的组件重渲染
//   - 适合低频变化、全局共享的数据；高频数据慎用
// 使用场景：主题、语言、当前登录用户、全局配置等。
// ─────────────────────────────────────────────────────────────

import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

// ---------- 1. 创建 Context ----------
// createContext(默认值)
const ThemeContext = createContext<"light" | "dark">("light");

// ---------- 2. Provider：提供值 ----------
function App() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  return (
    // 用 Provider 包裹需要访问该值的组件树
    <ThemeContext.Provider value={theme}>
      <Toolbar />
      <button onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
        切换主题
      </button>
    </ThemeContext.Provider>
  );
}

// ---------- 3. useContext：消费值 ----------
function Toolbar() {
  return <ThemedButton />; // 中间组件无需传 props
}

function ThemedButton() {
  const theme = useContext(ThemeContext); // 直接拿到值
  return (
    <button style={{ background: theme === "dark" ? "#333" : "#fff", color: theme === "dark" ? "#fff" : "#000" }}>
      当前主题：{theme}
    </button>
  );
}

// ---------- 4. 更完整的封装：Context + 自定义 Provider + Hook ----------
interface User { name: string; vip: boolean }

interface AuthValue {
  user: User | null;
  login: (name: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | undefined>(undefined); // 无默认值

function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const login = (name: string) => setUser({ name, vip: false });
  const logout = () => setUser(null);
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// 自定义 Hook：封装 useContext，并做空值校验
function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth 必须在 AuthProvider 内使用");
  return ctx;
}

function UserPanel() {
  const { user, login, logout } = useAuth();
  return (
    <div>
      {user ? (
        <div>
          <p>{user.name}</p>
          <button onClick={logout}>退出</button>
        </div>
      ) : (
        <button onClick={() => login("Tom")}>登录</button>
      )}
    </div>
  );
}

// ---------- 5. Context 的注意事项 ----------
// - 适合低频变化、全局共享的数据（主题、语言、用户）；
// - value 变化会导致所有消费该 Context 的组件重渲染，高频数据慎用（可用 Redux/Zustand 或拆分 Context）；
// - 复杂场景把「状态 + 方法」一起放进 value。

// ============================================================
// 练习：补全 TODO
// ============================================================

// TODO 1：创建一个 LanguageContext，保存当前语言，并提供切换方法。
// TODO 2：写一个组件，用 useContext 显示当前语言。

export { App, Toolbar, ThemedButton, AuthProvider, UserPanel, useAuth };
