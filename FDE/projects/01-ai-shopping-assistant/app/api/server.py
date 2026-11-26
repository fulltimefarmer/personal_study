from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时准备本地开发所需的最小数据。

    - SQLite/PostgreSQL 建表；
    - 商品表为空时自动从 files/products.csv 导入；
    - 数据库不可用时只记录警告，健康检查仍然可用。

    向量库不在启动时自动构建：embedding 需要 Ollama bge-m3，
    首次运行请显式执行 `python main.py ingest`，避免启动被大模型下载阻塞。
    """
    try:
        from app.config import settings
        from app.data.database import ProductDB, get_session, init_db

        init_db()
        with get_session() as session:
            product_count = session.query(ProductDB).count()

        if product_count == 0:
            from scripts.init_db import seed_data

            logger.info("[server] 商品库为空，自动从 CSV 导入...")
            seed_data(settings.product_csv_path)

        logger.info("[server] 关系数据库就绪")
    except Exception as exc:  # noqa: BLE001 - 本地启动不应被外部数据库阻塞
        logger.warning(f"[server] 数据库初始化跳过: {exc}")

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="乐高智能导购助手 API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    register_exception_handlers(app)
    logger.info("[server] FastAPI 应用初始化完成")

    return app
