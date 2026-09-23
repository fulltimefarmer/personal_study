// Event Emitter — 代码空壳（CoderPad 中填充）
// 实现 on/once/off/emit/removeAllListeners。

type Listener = (...args: any[]) => void;

class EventEmitter {
  // TODO: Map<事件, Set<监听器>>；once 用 wrapper；emit 用快照遍历
  on(event: string, listener: Listener): this { return this; }
  once(event: string, listener: Listener): this { return this; }
  off(event: string, listener: Listener): this { return this; }
  emit(event: string, ...args: any[]): boolean { return false; }
  removeAllListeners(event?: string): this { return this; }
}

// —— 测试（可运行验证）——
function run() {
  const emitter = new EventEmitter();

  const out: string[] = [];
  const a = (x: number) => out.push(`a${x}`);
  const b = (x: number) => out.push(`b${x}`);

  emitter.on("data", a).on("data", b); // 链式
  console.log(emitter.emit("data", 1)); // true
  console.log(JSON.stringify(out));     // ["a1","b1"]

  const onceOut: string[] = [];
  emitter.once("init", () => onceOut.push("once"));
  emitter.emit("init");
  emitter.emit("init");
  console.log(JSON.stringify(onceOut)); // ["once"]

  emitter.off("data", a);
  out.length = 0;
  emitter.emit("data", 2);
  console.log(JSON.stringify(out));     // ["b2"]

  console.log(emitter.emit("nothing")); // false

  emitter.removeAllListeners("data");
  console.log(emitter.emit("data", 3)); // false
}

run();
