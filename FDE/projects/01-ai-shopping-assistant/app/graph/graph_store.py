"""
Neo4j 图存储模块 — 知识图谱的查询与维护接口
"""

from functools import lru_cache
from typing import Any

from neo4j import Driver, GraphDatabase
from app.config import settings


class Neo4jStore:
    def __init__(self):
        self._driver: Driver | None = None

    def _get_driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
        return self._driver

    def _session(self):
        return self._get_driver().session(database=settings.neo4j_database)

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def health_check(self) -> dict:
        try:
            driver = self._get_driver()
            driver.verify_connectivity()
            with self._session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS cnt")
                count = result.single()["cnt"]
            return {"status": "connected", "node_count": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def graph_recommend(self, sku: str, top_k: int = 5) -> list[dict]:
        """基于图谱关系推荐相关商品。"""
        with self._session() as session:
            result = session.run("""
                MATCH (p:Product {sku: $sku})
                MATCH (other:Product)
                WHERE other.sku <> $sku
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(s:Series)<-[:BELONGS_TO]-(other)
                OPTIONAL MATCH (p)-[:THEME_OF]-(t:Theme)-[:THEME_OF]-(other)
                OPTIONAL MATCH (p)-[:IN_PRICE_RANGE]->(pt:PriceTier)<-[:IN_PRICE_RANGE]-(other)
                OPTIONAL MATCH (p)-[:SUITABLE_FOR]->(ag:AgeGroup)<-[:SUITABLE_FOR]-(other)
                WITH other,
                     CASE WHEN s IS NOT NULL THEN 0.4 ELSE 0 END +
                     CASE WHEN t IS NOT NULL THEN 0.3 ELSE 0 END +
                     CASE WHEN ag IS NOT NULL THEN 0.2 ELSE 0 END +
                     CASE WHEN pt IS NOT NULL THEN 0.1 ELSE 0 END AS score
                WHERE score > 0
                RETURN other.sku AS sku, other.name AS name, other.price AS price,
                       other.age_min AS age_min, other.series AS series, score
                ORDER BY score DESC
                LIMIT $top_k
            """, sku=sku, top_k=top_k)
            return [record.data() for record in result]

    def graph_browse(self, traversal_type: str, keyword: str = "", top_k: int = 10) -> list[dict]:
        """按维度浏览图谱。"""
        queries = {
            "series": """
                MATCH (s:Series)-[:BELONGS_TO]-(p:Product)
                WHERE s.name CONTAINS $keyword OR $keyword = ''
                RETURN p.sku AS sku, p.name AS name, p.price AS price,
                       p.age_min AS age_min, p.series AS series, s.name AS match_key
                ORDER BY p.price LIMIT $top_k
            """,
            "theme": """
                MATCH (t:Theme)-[:THEME_OF]-(s:Series)-[:BELONGS_TO]-(p:Product)
                WHERE t.name CONTAINS $keyword OR $keyword = ''
                RETURN p.sku AS sku, p.name AS name, p.price AS price,
                       p.age_min AS age_min, p.series AS series, t.name AS match_key
                ORDER BY p.price LIMIT $top_k
            """,
            "age_group": """
                MATCH (ag:AgeGroup)-[:SUITABLE_FOR]-(p:Product)
                WHERE ag.range CONTAINS $keyword OR $keyword = ''
                RETURN p.sku AS sku, p.name AS name, p.price AS price,
                       p.age_min AS age_min, p.series AS series, ag.range AS match_key
                ORDER BY p.price LIMIT $top_k
            """,
            "price_tier": """
                MATCH (pt:PriceTier)-[:IN_PRICE_RANGE]-(p:Product)
                WHERE pt.range CONTAINS $keyword OR $keyword = ''
                RETURN p.sku AS sku, p.name AS name, p.price AS price,
                       p.age_min AS age_min, p.series AS series, pt.range AS match_key
                ORDER BY p.price LIMIT $top_k
            """,
        }
        query = queries.get(traversal_type)
        if not query:
            return []
        with self._session() as session:
            result = session.run(query, keyword=keyword, top_k=top_k)
            return [record.data() for record in result]

    def graph_upgrade_downgrade(self, sku: str, direction: str = "up", top_k: int = 5) -> list[dict]:
        """按价位升/降级推荐同主题商品。"""
        price_op = ">" if direction == "up" else "<"
        sort_order = "ASC" if direction == "up" else "DESC"
        with self._session() as session:
            result = session.run(f"""
                MATCH (p:Product {{sku: $sku}})
                OPTIONAL MATCH (p)-[:THEME_OF]-(t:Theme)-[:THEME_OF]-(other:Product)
                WHERE other.sku <> $sku AND other.price {price_op} p.price
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(s:Series)<-[:BELONGS_TO]-(other2:Product)
                WHERE other2.sku <> $sku AND other2.price {price_op} p.price
                WITH other, other2
                WITH collect(DISTINCT other) + collect(DISTINCT other2) AS candidates
                UNWIND candidates AS c
                WITH DISTINCT c
                WHERE c IS NOT NULL
                RETURN c.sku AS sku, c.name AS name, c.price AS price,
                       c.age_min AS age_min, c.series AS series
                ORDER BY c.price {sort_order}
                LIMIT $top_k
            """, sku=sku, top_k=top_k)
            return [record.data() for record in result]

    def graph_cross_series(self, theme: str = "", age: int = 0, top_k: int = 10) -> list[dict]:
        """跨系列发现：同一主题/年龄段下不同系列的商品。"""
        conditions = []
        params: dict[str, Any] = {"top_k": top_k}
        if theme:
            conditions.append("t.name CONTAINS $theme")
            params["theme"] = theme
        if age > 0:
            conditions.append("p.age_min <= $age")
            params["age"] = age
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        with self._session() as session:
            result = session.run(f"""
                MATCH (t:Theme)-[:THEME_OF]-(s:Series)-[:BELONGS_TO]-(p:Product)
                WHERE {where_clause}
                RETURN p.sku AS sku, p.name AS name, p.price AS price,
                       p.age_min AS age_min, p.series AS series, t.name AS theme
                ORDER BY p.price
                LIMIT $top_k
            """, **params)
            return [record.data() for record in result]

    def list_entities(self, entity_type: str) -> list[dict]:
        """列出图中所有特定类型的实体。"""
        label_map = {
            "series": "Series",
            "theme": "Theme",
            "price_tier": "PriceTier",
            "age_group": "AgeGroup",
        }
        label = label_map.get(entity_type)
        if not label:
            return []
        with self._session() as session:
            result = session.run(
                f"MATCH (n:{label}) RETURN n.name AS name, labels(n) AS labels",
            )
            return [record.data() for record in result]


@lru_cache()
def get_neo4j_store() -> Neo4jStore:
    return Neo4jStore()
