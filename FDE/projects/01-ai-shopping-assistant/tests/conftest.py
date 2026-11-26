import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv
import pytest

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local"), override=True)


@pytest.fixture
def sample_product_meta():
    return {
        "sku": "60374",
        "name": "消防指挥车",
        "series": "城市系列",
        "age_min": 7,
        "price": 59.99,
        "description": "消防指挥车带灯光和声音效果",
    }


@pytest.fixture
def sample_sources():
    return [
        {
            "metadata": {
                "sku": "60374",
                "name": "消防指挥车",
                "series": "城市系列",
                "age_min": 7,
                "price": 59.99,
            },
            "content": "消防指挥车 城市系列 7+ $59.99",
            "score": 0.95,
        },
        {
            "metadata": {
                "sku": "60216",
                "name": "市中心消防队",
                "series": "城市系列",
                "age_min": 6,
                "price": 99.99,
            },
            "content": "市中心消防队 城市系列 6+ $99.99",
            "score": 0.72,
        },
        {
            "metadata": {
                "sku": "60463",
                "name": "云梯消防车",
                "series": "城市系列",
                "age_min": 4,
                "price": 29.99,
            },
            "content": "云梯消防车 城市系列 4+ $29.99",
            "score": 0.60,
        },
    ]


@pytest.fixture
def sample_graph_results():
    return [
        {"sku": "60374", "name": "消防指挥车", "series": "城市系列",
         "age_min": 7, "price": 59.99, "score": 0.95},
        {"sku": "60216", "name": "市中心消防队", "series": "城市系列",
         "age_min": 6, "price": 99.99, "score": 0.72},
        {"sku": "60463", "name": "云梯消防车", "series": "城市系列",
         "age_min": 4, "price": 29.99, "score": 0.60},
    ]
