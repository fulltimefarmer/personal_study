"""
全局异常处理与增强日志 — 生产级应用安全网

架构角色：应用基础架构层（Infrastructure），为整个 FastAPI 应用和
核心业务流程提供统一的异常捕获、错误响应格式化、日志追踪能力。

设计原则：
  - 快速失败（Fail-Fast）：异常在边界层统一处理，不扩散到业务逻辑
  - 优雅降级（Graceful Degradation）：错误时返回友好响应而非 500 堆栈
  - 全链路追踪：每个请求/操作都有 trace_id 贯穿日志
  - 不吞异常：所有异常至少记录 ERROR 级别日志后再返回响应
"""

import uuid
from contextlib import contextmanager
from typing import Generator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class AppException(Exception):
    """应用自定义异常基类

    WHAT: 所有业务异常的父类，携带结构化错误信息。
    WHY:  区分预期业务异常（如商品不存在）和未预期的系统异常。
          业务异常返回友好消息；系统异常返回通用错误 + 日志告警。
    """

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """为 FastAPI 应用注册全局异常处理器

    WHAT: 在 app 对象上注册 HTTPException 和通用 Exception 的处理器。
    WHY:  统一异常响应格式，确保前端始终收到 {"error": {...}} 结构，
          避免暴露内部堆栈信息到 API 响应中。
    HOW:  利用 FastAPI 的 exception_handler 装饰器绑定处理函数。
    """
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        trace_id = _get_trace_id(request)
        logger.warning(
            f"[{trace_id}] 业务异常: code={exc.code} msg={exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "trace_id": trace_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        trace_id = _get_trace_id(request)
        details = exc.errors()
        logger.warning(f"[{trace_id}] 请求参数校验失败: {details}")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "请求参数格式不正确",
                    "details": details,
                    "trace_id": trace_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        trace_id = _get_trace_id(request)
        logger.opt(exception=True).error(
            f"[{trace_id}] 未预期异常: {exc}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误，请联系管理员",
                    "trace_id": trace_id,
                }
            },
        )

    logger.info("[exception] 全局异常处理器已注册")


def _get_trace_id(request: Request) -> str:
    """从请求头提取或生成 trace_id"""
    trace_id = request.headers.get("X-Trace-ID")
    if not trace_id:
        trace_id = request.headers.get("x-trace-id", "")
    return trace_id if trace_id else str(uuid.uuid4())[:8]


@contextmanager
def operation_log(op_name: str, **context) -> Generator[None, None, None]:
    """操作日志上下文管理器

    WHAT:  为关键操作用 with block 包裹自动计时 + 异常日志。
    WHY:   统一关键路径的耗时监控和错误日志格式，避免每个方法手动写。
    HOW:   示例: with operation_log("向量检索", query="消防车") -> 自动记录耗时/错误

    Usage:
        with operation_log("向量检索", query="消防车") as op:
            results = store.search(query)
    """
    import time
    from loguru import logger

    t0 = time.time()
    ctx_str = " ".join(f"{k}={v!r}" for k, v in context.items())
    logger.debug(f"[op] {op_name} 开始 {ctx_str}")

    try:
        yield
        elapsed = time.time() - t0
        logger.debug(f"[op] {op_name} 完成 ({elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"[op] {op_name} 失败 ({elapsed:.2f}s): {e}")
        raise
