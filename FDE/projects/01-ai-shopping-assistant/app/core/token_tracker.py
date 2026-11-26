"""Token 用量追踪与预算管理

面试考点：
  FDE 必问：如何在生产中控制 LLM 成本？
  Agentic Engineer 必问：如何优化 Agent 的 token 消耗？

核心指标：
  1. 每请求 token 数 — 监控 prompt 是否膨胀
  2. 每日/每月总 token — 预算告警
  3. 工具调用开销 — Agent 多轮调用的 token 瀑布效应
  4. 模型选择对成本的影响 — DeepSeek vs Ollama 的成本对比

优化策略（本模块覆盖）：
  - 滑动窗口记忆：限制历史消息数量，旧消息压缩为摘要
  - 工具调用上限：MAX_TOOL_CALLS 防止 Agent 无限循环
  - 本地优先路由：简单问题走 Ollama 不消耗 API token
  - 检索去重：同一 SKU 只保留最高分文档，减少 context 长度

面试追问：
  Q: 如何估算生产环境的 token 成本？
  A: 基准测试 × 预估 QPS：
     - 单次 Agent 调用平均 3000 input + 500 output tokens
     - DeepSeek: $0.14/1M input + $0.28/1M output
     - 单次成本 ≈ $0.00056
     - 1000 QPS → $0.56/day → $16.8/month
     注意：Agent 多轮工具调用会放大 2-5 倍！

  Q: 为什么不用 tiktoken 精确统计？
  A: tiktoken 只支持 OpenAI 模型。DeepSeek 用不同 tokenizer。
     生产环境通常用 API 返回的 usage 字段做精确统计，
     本地估算用字符数/4 作为近似值（英文）或字符数/1.5（中文）。

  Q: 如何向非技术方解释成本优化策略？
  A: 三层漏斗：路由拦截(50%+) → 上下文压缩(30%) → 模型选择(20%)
     - 第一层（免费）：规则引擎拦截闲聊/无关问题
     - 第二层（免费）：简单问题走本地 Ollama
     - 第三层（省钱）：只有复杂问题才用付费 API
"""
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class TokenUsage:
    """单次调用用量"""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            model=self.model or other.model,
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
        )


# 各模型每百万 token 价格（USD）
MODEL_PRICING = {
    "deepseek-chat":     (0.14, 0.28),  # input, output per 1M
    "deepseek-v4-flash": (0.14, 0.28),
    "deepseek-reasoner": (0.55, 2.19),
    "ollama":            (0.0,  0.0),   # 本地免费
    "qwen2.5:3b":        (0.0,  0.0),
}


def estimate_tokens(text: str) -> int:
    """估算 token 数（中文约 1.5 字符/token，英文约 4 字符/token）

    生产环境应使用 API 返回的 usage 字段做精确统计。
    """
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other = len(text) - chinese
    return int(chinese / 1.5 + other / 4)


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """根据模型定价计算费用"""
    input_price, output_price = MODEL_PRICING.get(model, (0.0, 0.0))
    cost = (prompt_tokens / 1_000_000) * input_price
    cost += (completion_tokens / 1_000_000) * output_price
    return round(cost, 6)


class TokenTracker:
    """Token 用量追踪器 — 按会话和模型分组统计

    Usage:
        tracker = get_token_tracker()
        tracker.record("deepseek-v4-flash", prompt="你好", completion="你好！")
        print(tracker.summary())
    """

    def __init__(self, daily_budget_usd: float = 10.0, alert_threshold: float = 0.8):
        self.daily_budget = daily_budget_usd
        self.alert_threshold = alert_threshold
        self._lock = threading.Lock()
        self._daily_start = time.time()
        self._sessions: dict[str, TokenUsage] = defaultdict(TokenUsage)
        self._models: dict[str, TokenUsage] = defaultdict(TokenUsage)
        self._total = TokenUsage()

    def record(
        self,
        model: str,
        prompt: str = "",
        completion: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        session_id: str = "default",
    ) -> TokenUsage:
        """记录一次 LLM 调用并返回本次用量"""
        if not prompt_tokens and prompt:
            prompt_tokens = estimate_tokens(prompt)
        if not completion_tokens and completion:
            completion_tokens = estimate_tokens(completion)
        total = prompt_tokens + completion_tokens
        cost = calculate_cost(model, prompt_tokens, completion_tokens)

        usage = TokenUsage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost_usd=cost,
        )

        with self._lock:
            self._sessions[session_id] += usage
            self._models[model] += usage
            self._total += usage

        self._check_budget_alert()
        return usage

    def _check_budget_alert(self):
        if self._total.cost_usd >= self.daily_budget * self.alert_threshold:
            logger.warning(
                f"[token-budget] 已达到日预算的 "
                f"{self._total.cost_usd/self.daily_budget:.0%} "
                f"(${self._total.cost_usd:.4f}/${self.daily_budget:.2f})"
            )

    def summary(self) -> dict:
        with self._lock:
            return {
                "total": self._total,
                "by_model": dict(self._models),
                "by_session": dict(self._sessions),
                "daily_budget": self.daily_budget,
                "budget_remaining": round(self.daily_budget - self._total.cost_usd, 4),
            }

    def reset_daily(self):
        with self._lock:
            self._daily_start = time.time()
            self._sessions.clear()
            self._models.clear()
            self._total = TokenUsage()


# ── 全局单例 ──
_tracker: TokenTracker | None = None


def get_token_tracker() -> TokenTracker:
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker()
    return _tracker
