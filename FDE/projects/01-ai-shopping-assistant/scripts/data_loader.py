"""商品数据加载器 — 独立运行入口"""
from loguru import logger

from app.config import settings
from app.core.logging import setup_logging
from app.data.loader import ProductDataLoader


def main():
    setup_logging(settings.debug)
    loader = ProductDataLoader(settings.product_csv_path)
    docs = loader.build_embed_docs()
    logger.success(f"数据预处理完成，共 {len(docs)} 条商品")


if __name__ == "__main__":
    main()
