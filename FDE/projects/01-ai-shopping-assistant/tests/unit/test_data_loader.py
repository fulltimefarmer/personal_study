"""Unit tests for ProductDataLoader — CSV parsing and document generation"""

import os
import tempfile

import pytest

from app.data.loader import ProductDataLoader


@pytest.fixture
def sample_csv():
    content = (
        "1,消防指挥车,城市系列,7+,59.99,指挥消防车带灯光和声音效果,赠送电池,推荐给喜欢扮演消防员的孩子\n"
        "2,警察局套装,城市系列,6+,39.99,模拟真实警察局的互动模型,包含警车和直升机,培养孩子的正义感\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        path = f.name
    yield path
    os.unlink(path)


class TestProductDataLoader:
    def test_parse_csv(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        df = loader._parse_markdown_csv()
        assert len(df) == 2
        assert df.iloc[0]["SKU"] == "1"
        assert df.iloc[0]["商品名称"] == "消防指挥车"

    def test_load_clean(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        df = loader.load_clean()
        assert len(df) == 2
        assert "price_num" in df.columns
        assert "age_min" in df.columns
        assert df.iloc[0]["price_num"] == 59.99
        assert df.iloc[0]["age_min"] == 7

    def test_build_embed_docs(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        docs = loader.build_embed_docs()
        assert len(docs) == 2
        doc = docs[0]
        assert "id" in doc
        assert "text" in doc
        assert "metadata" in doc
        assert doc["id"] == "1"
        assert doc["metadata"]["sku"] == "1"
        assert doc["metadata"]["name"] == "消防指挥车"
        assert doc["metadata"]["series"] == "城市系列"
        assert doc["metadata"]["age_min"] == 7
        assert doc["metadata"]["price"] == 59.99

    def test_build_embed_docs_multi_granularity(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        docs = loader.build_embed_docs_multi_granularity()
        assert len(docs) == 6  # 2 products x 3 granularities
        granularities = {d.get("granularity") for d in docs}
        assert granularities == {"name", "description", "full"}

    def test_deduplication(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        df = loader.load_clean()
        assert len(df) == 2
        # Should not change on re-load
        df2 = loader.load_clean()
        assert len(df2) == 2

    def test_embed_docs_auto_loads(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        docs = loader.build_embed_docs()
        assert len(docs) == 2

    def test_embed_docs_multi_auto_loads(self, sample_csv):
        loader = ProductDataLoader(sample_csv)
        docs = loader.build_embed_docs_multi_granularity()
        assert len(docs) > 0

    def test_description_with_commas(self):
        content = (
            "1,测试商品,系列,5+,10.00,这是一个测试,包含逗号,的描述文本\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            loader = ProductDataLoader(path)
            df = loader._parse_markdown_csv()
            assert "包含逗号" in df.iloc[0]["商品介绍"]
        finally:
            os.unlink(path)
