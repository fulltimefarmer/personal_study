"""初始化向量库：读取CSV数据 → 向量化 → 写入ChromaDB"""
from loguru import logger

from app.config import settings
from app.core.logging import setup_logging
from app.data.loader import ProductDataLoader
from app.vector_store.chroma_store import ChromaStore


def main():
    setup_logging(settings.debug)
    logger.info("开始初始化向量库")

    loader = ProductDataLoader(settings.product_csv_path)
    docs = loader.build_embed_docs()

    store = ChromaStore()
    count = store.add_documents(docs)

    logger.success(f"向量库初始化完成，共写入 {count} 条商品数据")


if __name__ == "__main__":
    main()
