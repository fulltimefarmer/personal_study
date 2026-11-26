"""Unit tests for resilience — CircuitBreaker state machine"""

import time

import pytest

from app.core.resilience import LLMResilience, CircuitBreaker, CircuitState


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.failure()
        cb.failure()
        assert cb.state == CircuitState.CLOSED
        cb.failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=5)
        cb.failure()
        cb.failure()
        cb.success()
        cb.failure()
        cb.failure()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_recovery(self):
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.001,
            half_open_max=1,
        )
        cb.failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.005)
        assert cb.state == CircuitState.HALF_OPEN
        cb.success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_back_to_open(self):
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.001,
            half_open_max=1,
        )
        cb.failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.005)
        assert cb.state == CircuitState.HALF_OPEN
        cb.failure()
        assert cb.state == CircuitState.OPEN

    def test_half_open_multiple_successes_needed(self):
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.001,
            half_open_max=2,
        )
        cb.failure()
        time.sleep(0.005)
        assert cb.state == CircuitState.HALF_OPEN
        cb.success()
        assert cb.state == CircuitState.HALF_OPEN
        cb.success()
        assert cb.state == CircuitState.CLOSED


class TestLLMResilience:
    def test_primary_succeeds(self):
        primary = lambda: "success"
        res = LLMResilience(primary)
        assert res.call() == "success"

    def test_retries_on_retryable_error(self):
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("timeout: connection refused")
            return "success"

        res = LLMResilience(flaky, max_retries=3, base_delay=0.01)
        assert res.call() == "success"
        assert call_count[0] == 3

    def test_non_retryable_error_bypasses(self):
        call_count = [0]

        def bad_key():
            call_count[0] += 1
            raise Exception("unauthorized: api key invalid")

        res = LLMResilience(bad_key, max_retries=3, base_delay=0.01)
        assert res.call() is None
        assert call_count[0] == 1

    def test_circuit_breaker_blocks_during_open(self):
        primary = lambda: 1 / 0
        res = LLMResilience(primary, max_retries=0)
        for _ in range(6):
            res.call()
        assert res.circuit.state == CircuitState.OPEN

    def test_fallback_called_on_all_failures(self):
        primary = lambda: 1 / 0
        fallback = lambda: "fallback result"
        res = LLMResilience(primary, fallback_func=fallback, max_retries=0)
        assert res.call() == "fallback result"

    def test_is_retryable(self):
        assert LLMResilience._is_retryable(Exception("429 rate limit")) is True
        assert LLMResilience._is_retryable(Exception("502 server error")) is True
        assert LLMResilience._is_retryable(Exception("timeout")) is True
        assert LLMResilience._is_retryable(Exception("unauthorized")) is False
        assert LLMResilience._is_retryable(Exception("api key invalid")) is False
