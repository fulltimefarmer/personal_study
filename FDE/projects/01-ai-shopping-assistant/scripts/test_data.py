"""验证预处理数据"""
from loguru import logger

from app.config import settings
from app.core.logging import setup_logging
from app.data.loader import ProductDataLoader


def main():
    setup_logging(settings.debug)
    loader = ProductDataLoader(settings.product_csv_path)
    docs = loader.build_embed_docs()

    logger.info("=== 验证1：数据总量 ===")
    logger.info(f"解析商品总数: {len(docs)}")
    assert len(docs) >= 100, f"商品数量不足100，实际{len(docs)}"
    logger.success("数量校验通过")

    logger.info("=== 验证2：字段完整性 ===")
    sample = docs[0]
    required_fields = ["id", "text", "metadata"]
    for field in required_fields:
        assert field in sample, f"缺少字段: {field}"

    meta_required = ["sku", "name", "series", "age_min", "price"]
    for field in meta_required:
        assert field in sample["metadata"], f"元数据缺少字段: {field}"
    logger.success("所有必填字段齐全")

    logger.info("=== 验证3：数据类型 ===")
    assert isinstance(sample["metadata"]["age_min"], int), "age_min 必须是整数"
    assert isinstance(sample["metadata"]["price"], float), "price 必须是浮点数"
    assert sample["metadata"]["price"] > 0, "价格必须大于0"
    logger.success(
        f"数据类型正确，样例价格: ${sample['metadata']['price']}，年龄下限: {sample['metadata']['age_min']}+"
    )

    logger.info("=== 验证4：前2条数据样例 ===")
    for i, doc in enumerate(docs[:2]):
        logger.info(f"【第{i + 1}条】")
        logger.info(f"SKU: {doc['metadata']['sku']}")
        logger.info(f"名称: {doc['metadata']['name']}")
        logger.info(f"系列: {doc['metadata']['series']}")
        logger.info(f"年龄: {doc['metadata']['age_min']}+")
        logger.info(f"价格: ${doc['metadata']['price']}")
        logger.info(f"向量化文本(前80字): {doc['text'][:80]}...")

    logger.success("数据预处理全部验证通过")


if __name__ == "__main__":
    main()
