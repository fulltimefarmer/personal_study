// Design Hit Counter — 代码空壳（CoderPad 中填充）
// 记录点击并查询过去 300 秒内的点击总数。

class HitCounter {
  private queue: number[] = [];

  hit(timestamp: number): void {
    // TODO: 记录一次点击
  }

  getHits(timestamp: number): number {
    // TODO: 淘汰 < timestamp - 299 的过期点击，返回剩余数量
    return 0;
  }
}

// —— 测试（可运行验证）——
function run() {
  const counter = new HitCounter();
  counter.hit(1);
  counter.hit(2);
  counter.hit(3);
  console.log(counter.getHits(4));   // 3
  counter.hit(300);
  console.log(counter.getHits(300)); // 4
  console.log(counter.getHits(301)); // 3
}

run();
