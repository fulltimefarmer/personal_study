"""召回评测：命中率 / MRR / 精确率"""
from typing import Dict, List

from loguru import logger
from tabulate import tabulate

from app.config import settings
from app.core.logging import setup_logging
from app.rag.chain import RAGChain

EVAL_CASES = [
    {
        "query": "消防车",
        "expected_keywords": ["消防", "灭火", "救援"],
        "expected_series": [],
        "desc": "类别搜索：消防相关商品",
    },
    {
        "query": "适合5岁孩子玩的乐高",
        "expected_keywords": [],
        "expected_age_max": 6,
        "desc": "年龄过滤：5岁儿童适用",
    },
    {
        "query": "便宜的积木玩具",
        "expected_keywords": [],
        "expected_price_max": 30,
        "desc": "价格过滤：预算30美元以内",
    },
    {
        "query": "城市系列的警车",
        "expected_keywords": ["警", "警察"],
        "expected_series": ["城市系列"],
        "desc": "系列+类型：城市系列警察",
    },
    {
        "query": "太空火箭发射",
        "expected_keywords": ["火箭", "太空", "航天", "发射"],
        "expected_series": [],
        "desc": "语义搜索：太空主题",
    },
    {
        "query": "搭建复杂的机械模型",
        "expected_keywords": ["机械", "技术", "工程"],
        "expected_series": [],
        "desc": "语义搜索：机械/Technic",
    },
    {
        "query": "送给女儿的礼物",
        "expected_keywords": [],
        "expected_series": [],
        "desc": "推荐场景：送礼物",
    },
    {
        "query": "赛车竞速",
        "expected_keywords": ["赛车", "跑车", "竞速"],
        "expected_series": [],
        "desc": "类别搜索：赛车类",
    },
]


def _contains_keyword(text: str, keywords: List[str]) -> bool:
    return any(kw in text for kw in keywords)


def _get_expected_series(doc_meta: dict, expected: List[str]) -> bool:
    if not expected:
        return True
    return doc_meta.get("series", "") in expected


def _get_expected_age(doc_meta: dict, age_max: int) -> bool:
    return doc_meta.get("age_min", 99) <= age_max


def _get_expected_price(doc_meta: dict, price_max: float) -> bool:
    return doc_meta.get("price", float("inf")) <= price_max


def evaluate(chain: RAGChain, k: int = 4) -> Dict:
    results_per_case = []
    total_hits = 0
    total_reciprocal_rank = 0.0
    total_precision = 0.0

    for case in EVAL_CASES:
        docs = chain.search_only(case["query"], k=k)

        hits = 0
        first_hit_rank = 0

        for rank, doc in enumerate(docs, 1):
            meta = doc.get("metadata", {})
            content = doc.get("content", "")
            is_relevant = True

            if case.get("expected_keywords"):
                if not _contains_keyword(content, case["expected_keywords"]):
                    is_relevant = False

            if case.get("expected_series"):
                if not _get_expected_series(meta, case["expected_series"]):
                    is_relevant = False

            if case.get("expected_age_max"):
                if not _get_expected_age(meta, case["expected_age_max"]):
                    is_relevant = False

            if case.get("expected_price_max"):
                if not _get_expected_price(meta, case["expected_price_max"]):
                    is_relevant = False

            if is_relevant:
                hits += 1
                if first_hit_rank == 0:
                    first_hit_rank = rank

        case_hit = 1 if hits > 0 else 0
        total_hits += case_hit
        total_reciprocal_rank += 1.0 / first_hit_rank if first_hit_rank > 0 else 0
        total_precision += hits / len(docs) if docs else 0

        results_per_case.append(
            {
                "query": case["query"],
                "desc": case["desc"],
                "retrieved": len(docs),
                "hits": hits,
                "first_rank": first_hit_rank,
                "hit_rate": case_hit,
            }
        )

    n = len(EVAL_CASES)
    return {
        "k": k,
        "total_cases": n,
        "hit_rate": total_hits / n,
        "mrr": round(total_reciprocal_rank / n, 4),
        "precision": round(total_precision / n, 4),
        "details": results_per_case,
    }


def run_evaluation():
    setup_logging(settings.debug)
    logger.info("开始召回评测...")

    chain = RAGChain()
    result = evaluate(chain, k=4)

    headers = ["查询", "描述", "召回数", "命中数", "首次命中", "命中状态"]
    rows = [
        [
            r["query"],
            r["desc"],
            r["retrieved"],
            r["hits"],
            r["first_rank"],
            "✓" if r["hit_rate"] else "✗",
        ]
        for r in result["details"]
    ]

    logger.info(f"\n{tabulate(rows, headers=headers, tablefmt='grid')}")
    logger.info(f"\n评测汇总 (Top-{result['k']}):")
    logger.info(f"  命中率 (Hit Rate): {result['hit_rate']:.1%}")
    logger.info(f"  MRR:               {result['mrr']}")
    logger.info(f"  平均精确率:        {result['precision']:.1%}")


if __name__ == "__main__":
    run_evaluation()
