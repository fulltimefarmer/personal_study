"""Unit tests for data models — Product and ProductFilter"""

import pytest
from pydantic import ValidationError

from app.data.models import Product, ProductFilter


class TestProduct:
    def test_create_from_dict(self):
        data = {
            "sku": "60374",
            "name": "消防指挥车",
            "series": "城市系列",
            "age_min": 7,
            "price": 59.99,
        }
        p = Product.from_dict(data)
        assert p.sku == "60374"
        assert p.name == "消防指挥车"
        assert p.series == "城市系列"
        assert p.age_min == 7
        assert p.price == 59.99

    def test_from_dict_with_missing_fields(self):
        p = Product.from_dict({"sku": "001", "name": "test"})
        assert p.series == ""
        assert p.age_min == 0
        assert p.price == 0.0

    def test_format_card(self):
        p = Product(
            sku="60374",
            name="消防指挥车",
            series="城市系列",
            age_min=7,
            price=59.99,
            description="灯光声音效果",
        )
        card = p.format_card()
        assert "消防指挥车" in card
        assert "60374" in card
        assert "城市系列" in card
        assert "7+" in card
        assert "$59.99" in card
        assert "灯光声音效果" in card

    def test_default_values(self):
        p = Product(sku="001", name="test", series="s")
        assert p.age_min == 0
        assert p.price == 0.0
        assert p.description == ""


class TestProductFilter:
    def test_empty_filter_returns_none(self):
        pf = ProductFilter()
        assert pf.to_chroma_filter() is None

    def test_series_only(self):
        pf = ProductFilter(series="城市系列")
        f = pf.to_chroma_filter()
        assert f == {"series": "城市系列"}

    def test_age_only(self):
        pf = ProductFilter(max_age=6)
        f = pf.to_chroma_filter()
        assert f == {"age_min": {"$lte": 6}}

    def test_price_range(self):
        pf = ProductFilter(min_price=10, max_price=50)
        f = pf.to_chroma_filter()
        assert f == {"price": {"$gte": 10, "$lte": 50}}

    def test_min_price_only(self):
        pf = ProductFilter(min_price=20)
        f = pf.to_chroma_filter()
        assert f == {"price": {"$gte": 20}}

    def test_max_price_only(self):
        pf = ProductFilter(max_price=100)
        f = pf.to_chroma_filter()
        assert f == {"price": {"$lte": 100}}

    def test_combined_filter(self):
        pf = ProductFilter(series="城市系列", max_age=7, min_price=10, max_price=100)
        f = pf.to_chroma_filter()
        assert "$and" in f
        conditions = f["$and"]
        assert {"series": "城市系列"} in conditions
        assert {"price": {"$gte": 10, "$lte": 100}} in conditions
        assert {"age_min": {"$lte": 7}} in conditions

    def test_model_validation(self):
        pf = ProductFilter(series="test", min_price=10.5, max_price=99.9, max_age=8)
        assert pf.series == "test"
        assert pf.min_price == 10.5
        assert pf.max_price == 99.9
        assert pf.max_age == 8

    def test_none_fields_default(self):
        pf = ProductFilter()
        assert pf.series is None
        assert pf.min_price is None
        assert pf.max_price is None
        assert pf.max_age is None
