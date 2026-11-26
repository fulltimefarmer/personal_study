"""
日志配置模块 — 购物助手应用的统一日志门面。

【角色】本模块负责为整个应用提供标准化的日志输出能力。
它基于 loguru 库封装，是应用的"日志中枢"——所有模块通过 loguru 的
`logger` 对象输出日志，而本模块定义输出格式、级别和目的地。

【机制】在应用启动时调用一次 `setup_logging()`，随后代码中任何
`from loguru import logger` 然后 `logger.info(...)` 都会按统一格式输出。

【设计决策】选用 loguru 而非 Python 标准库 logging，因为：
  - 零配置即可获得彩色、结构清晰的输出
  - 支持结构化日志（字典自动序列化，方便后续对接日志聚合平台）
  - 更简洁的 API（无需 logger.getLogger 等样板代码）
  - 支持日志分片、轮转、压缩等高级功能开箱即用
"""

import sys

from loguru import logger


def setup_logging(debug: bool = False) -> None:
    """
    初始化全局日志配置 — 移除默认 handler 后重新注册统一的日志输出。

    【作用】设置整个应用的日志级别、输出格式和输出目标。
    【调用时机】必须在应用启动最早期调用一次（通常在 `main.py` 或入口脚本中）。
             调用后，所有后续 `logger.info()` / `logger.error()` 等调用都会按新格式输出。
    【参数】
        debug: 是否开启 DEBUG 级别日志。True 时输出所有 debug 及以上级别；
               False 时只输出 INFO 及以上级别（生产环境推荐）。
    【原理】
        1. `logger.remove()` 清空 loguru 默认绑定的 handler（避免重复输出）
        2. 根据 debug 标志决定日志级别
        3. `logger.add()` 注册一个输出到 stderr 的 handler，
           格式为 `时间 | 级别 | 消息`，时间绿色、级别和消息按级别自动着色
    """
    # 清空 loguru 自带的默认 handler，避免重复打印
    logger.remove()
    # 根据 debug 标志决定日志级别：调试模式输出 DEBUG，生产模式输出 INFO
    level = "DEBUG" if debug else "INFO"
    # 注册统一的日志 handler → 输出到标准错误流（stderr）
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )


# ═══════════════════════════════════════════════════════════════
# 入口 — setup_logging() 是日志模块的唯一公共接口
# ═══════════════════════════════════════════════════════════════
# 在 `main.py` 或应用入口处调用此函数后，
# 全局 logger 即配置完毕，所有模块无需再关心日志配置细节。
