"""LLM 调用韧性层 — 重试、熔断、降级

面试考点：
  FDE/Agentic Engineer 必问：生产环境中 LLM API 不可靠怎么办？
  答案就是本模块实现的三层防护：重试 → 熔断 → 降级。

设计模式：
  1. 指数退避重试 (Exponential Backoff Retry)
     - 失败后等待 1s → 2s → 4s → ... 再重试
     - 避免雪崩（thundering herd）
  2. 熔断器 (Circuit Breaker)
     - 连续失败 N 次后"断开电路"，快速失败一段时间
     - 半开状态：允许探测请求，成功则恢复，失败则继续熔断
  3. 降级 (Fallback / Graceful Degradation)
     - 主模型挂了 → 自动切换到备用模型
     - DeepSeek API 不可用 → 降级到本地 Ollama

面试追问：
  Q: 和 HTTP 层面的 retry 有什么区别？
  A: HTTP retry 只处理网络层错误（超时/连接拒绝），
     不理解业务语义。LLM 层的 retry 可以区分：
     - 可重试错误：Rate Limit (429)、Server Error (5xx)
     - 不可重试错误：API Key 无效 (401)、内容过滤 (400)
     - 业务语义错误：输出解析失败 → 重试时修改 prompt

  Q: 熔断器怎么避免误触发？
  A: 半开状态 (Half-Open)：熔断一段时间后允许少量探测请求。
     如果探测成功，熔断器自动恢复；失败则重新计时。这是
     Netflix Hystrix / Resilience4j 的标准模式。

  Q: 多模型降级的顺序怎么决定？
  A: 按成本+能力排序。本项目策略：
     DeepSeek(主力, 能力强) → Ollama本地(免费, 能力弱) → 模板回复(零成本, 兜底)
"""
import asyncio
import functools
import time
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, TypeVar

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(Enum):
    CLOSED = "closed"       # 正常通行
    OPEN = "open"           # 熔断中，快速失败
    HALF_OPEN = "half_open"  # 半开，探测恢复


class CircuitBreaker:
    """熔断器 — 故障快速失败，防止级联故障

    State Machine:
        CLOSED ──连续失败N次──→ OPEN
        OPEN   ──冷却时间到──→ HALF_OPEN
        HALF_OPEN ──成功──→ CLOSED
        HALF_OPEN ──失败──→ OPEN
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_count = 0

    @property
    def state(self) -> CircuitState:
        self._transition()
        return self._state

    def _transition(self):
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_count = 0
                logger.info("[circuit] OPEN → HALF_OPEN (冷却完成)")
        elif self._state == CircuitState.HALF_OPEN:
            if self._half_open_count >= self.half_open_max:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("[circuit] HALF_OPEN → CLOSED (探测成功)")

    def success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_count += 1
        else:
            self._failure_count = 0
        self._transition()

    def failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("[circuit] HALF_OPEN → OPEN (探测失败)")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                f"[circuit] CLOSED → OPEN (连续失败 {self._failure_count} 次)"
            )


class LLMResilience:
    """LLM 韧性调用入口 — 组合重试 + 熔断 + 降级"""

    def __init__(
        self,
        primary_func: Callable,
        fallback_func: Callable | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self.primary = primary_func
        self.fallback = fallback_func
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.circuit = circuit_breaker or CircuitBreaker()

    def call(self, *args, **kwargs) -> Any:
        """带完整韧性策略的调用"""
        if self.circuit.state == CircuitState.OPEN:
            logger.warning("[resilience] 熔断器开路，直接降级")
            return self._fallback(*args, **kwargs)

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self.primary(*args, **kwargs)
                self.circuit.success()
                return result
            except Exception as e:
                last_exception = e
                self.circuit.failure()

                if self._is_retryable(e) and attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(
                        f"[resilience] 第{attempt+1}次重试 (delay={delay:.1f}s): {e}"
                    )
                    time.sleep(delay)
                else:
                    break

        logger.error(f"[resilience] 所有重试失败: {last_exception}")
        return self._fallback(*args, **kwargs)

    def _fallback(self, *args, **kwargs) -> Any:
        if self.fallback:
            try:
                return self.fallback(*args, **kwargs)
            except Exception as e:
                logger.error(f"[resilience] 降级也失败了: {e}")
        return None

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """判断异常是否值得重试"""
        retryable = (
            "rate limit", "too many requests", "429",
            "server error", "internal error", "500", "502", "503",
            "timeout", "connection", "temporary",
        )
        msg = str(exc).lower()
        return any(kw in msg for kw in retryable)


def with_resilience(
    max_retries: int = 3,
    base_delay: float = 1.0,
    fallback_value: Any = None,
):
    """装饰器：为 LLM 调用添加重试韧性"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), 30.0)
                        logger.warning(
                            f"[retry] {func.__name__} 第{attempt+1}次重试 "
                            f"(delay={delay:.1f}s): {e}"
                        )
                        time.sleep(delay)
            logger.error(f"[retry] {func.__name__} 所有重试失败: {last_exc}")
            return fallback_value
        return wrapper  # type: ignore[return-value]
    return decorator


# ── 全局熔断器实例（按服务分组）──
_circuits: dict[str, CircuitBreaker] = defaultdict(
    lambda: CircuitBreaker(failure_threshold=5, recovery_timeout=60)
)


def get_circuit(name: str = "deepseek") -> CircuitBreaker:
    """获取指定服务的熔断器（全局单例）"""
    return _circuits[name]


class ModelFallbackChain:
    """模型降级链 — 多级自动切换

    面试要点：
      降级不只是"主挂了用备"，要考虑：
      1. 降级触发条件：不仅是异常，还包括超时、质量不达标
      2. 降级代价：备用模型能力可能更弱，需修改 prompt 适配
      3. 恢复策略：主模型恢复后如何切回去（灰度切流）
    """

    def __init__(self, providers: list[Callable]):
        self.providers = providers

    def call(self, *args, **kwargs) -> Any:
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                logger.debug(f"[fallback] 尝试 provider[{i}]: {provider.__name__}")
                return provider(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[fallback] provider[{i}] ({provider.__name__}) 失败: {e}"
                )
        raise RuntimeError(
            f"[fallback] 所有 {len(self.providers)} 个 provider 都失败了。"
            f"最后错误: {last_error}"
        )
