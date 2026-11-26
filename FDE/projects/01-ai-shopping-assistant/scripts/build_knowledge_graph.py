"""
知识图谱构建脚本 — 从商品 CSV 构建 Neo4j 图数据库

生成以下图结构：
  - (Product) 节点：sku, name, price, age_min, series
  - (Series) 节点：乐高系列
  - (Theme) 节点：主题分类（城市/赛车/奇幻/科幻/超级英雄…）
  - (AgeGroup) 节点：年龄段分组
  - (PriceTier) 节点：价位分组

关系：
  - (Product)-[:BELONGS_TO]->(Series)
  - (Product)-[:SUITABLE_FOR]->(AgeGroup)
  - (Product)-[:IN_PRICE_RANGE]->(PriceTier)
  - (Series)-[:THEME_OF]->(Theme)

用法：
  uv run python scripts/build_knowledge_graph.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv

dotenv.load_dotenv(".env")
dotenv.load_dotenv(".env.local", override=True)

from neo4j import GraphDatabase
from app.config import settings
from app.data.loader import ProductDataLoader

# ── 主题映射：系列 → 主题列表 ──────────────────────────────────

SERIES_THEME_MAP: dict[str, list[str]] = {
    "城市系列": ["城市生活", "紧急救援", "交通", "太空"],
    "好朋友系列": ["日常生活", "友情", "户外", "动物"],
    "幻影忍者": ["动作", "奇幻", "机甲", "冒险"],
    "超级赛车": ["赛车", "速度", "机械"],
    "哈利波特": ["魔法", "奇幻", "电影"],
    "星球大战": ["科幻", "太空", "电影"],
    "创意三合一": ["创意", "建筑", "动物", "DIY"],
    "得宝系列": ["启蒙", "动物", "安全"],
    "漫威": ["超级英雄", "电影", "动作"],
    "DC": ["超级英雄", "电影", "动作"],
    "迪士尼": ["公主", "动画", "收藏"],
    "建筑系列": ["城市", "建筑", "收藏"],
    "中国传统节日": ["文化", "节日", "装饰"],
    "冬季村庄": ["季节", "节日", "建筑"],
    "植物系列": ["装饰", "手工", "自然"],
}

# ── 年龄段分组 ──────────────────────────────────

AGE_GROUPS: list[tuple[str, int, int]] = [
    ("2-4岁", 2, 4),
    ("5-7岁", 5, 7),
    ("8-11岁", 8, 11),
    ("12-15岁", 12, 15),
    ("16岁以上", 16, 99),
]

# ── 价位分组 ──────────────────────────────────

PRICE_TIERS: list[tuple[str, float, float]] = [
    ("入门($0-25)", 0, 25),
    ("中档($25-60)", 25, 60),
    ("高端($60-150)", 60, 150),
    ("收藏($150+)", 150, 10000),
]


def classify_age(age: int) -> str:
    for label, lo, hi in AGE_GROUPS:
        if lo <= age <= hi:
            return label
    return "16岁以上"


def classify_price(price: float) -> str:
    for label, lo, hi in PRICE_TIERS:
        if lo <= price <= hi:
            return label
    return "收藏($150+)"


def build(driver, csv_path: str):
    loader = ProductDataLoader(csv_path=csv_path)
    df = loader.load_clean()

    with driver.session(database=settings.neo4j_database) as session:
        # 清空旧数据
        session.run("MATCH (n) DETACH DELETE n")

        # 1. 创建 Series + Theme 节点
        for series, themes in SERIES_THEME_MAP.items():
            session.run(
                "MERGE (s:Series {name: $name})", name=series
            )
            for theme_name in themes:
                session.run(
                    "MERGE (t:Theme {name: $name})", name=theme_name
                )
                session.run("""
                    MATCH (s:Series {name: $series})
                    MATCH (t:Theme {name: $theme})
                    MERGE (s)-[:THEME_OF]->(t)
                """, series=series, theme=theme_name)

        # 2. 创建 AgeGroup 节点
        for label, lo, hi in AGE_GROUPS:
            session.run(
                "MERGE (a:AgeGroup {name: $name, range: $range, lo: $lo, hi: $hi})",
                name=label, range=label, lo=lo, hi=hi,
            )

        # 3. 创建 PriceTier 节点
        for label, lo, hi in PRICE_TIERS:
            session.run(
                "MERGE (pt:PriceTier {name: $name, range: $range, lo: $lo, hi: $hi})",
                name=label, range=label, lo=lo, hi=hi,
            )

        # 4. 创建 Product 节点及关系
        count = 0
        for _, row in df.iterrows():
            sku = str(row["SKU"])
            name = row["商品名称"]
            series = row["系列"]
            age_min = int(row["age_min"])
            price = float(row["price_num"])
            description = row.get("商品介绍", "")
            themes = SERIES_THEME_MAP.get(series, ["其他"])
            age_group = classify_age(age_min)
            price_tier = classify_price(price)

            session.run("""
                MERGE (p:Product {sku: $sku})
                SET p.name = $name, p.price = $price, p.age_min = $age_min,
                    p.series = $series, p.description = $description
                WITH p
                MATCH (s:Series {name: $series})
                MERGE (p)-[:BELONGS_TO]->(s)
                WITH p
                MATCH (ag:AgeGroup {range: $age_group})
                MERGE (p)-[:SUITABLE_FOR]->(ag)
                WITH p
                MATCH (pt:PriceTier {range: $price_tier})
                MERGE (p)-[:IN_PRICE_RANGE]->(pt)
            """, sku=sku, name=name, price=price, age_min=age_min,
                 series=series, description=description,
                 age_group=age_group, price_tier=price_tier)

            # 连接产品到主题（通过系列间接关联的直接连接）
            for theme_name in themes:
                session.run("""
                    MATCH (p:Product {sku: $sku})
                    MATCH (t:Theme {name: $theme})
                    MERGE (p)-[:THEME_OF]->(t)
                """, sku=sku, theme=theme_name)

            count += 1

        # 5. 建立 COMPLEMENTS 关系（同系列 + 同年龄段 + 不同价格 → 搭配推荐）
        session.run("""
            MATCH (a:Product)-[:BELONGS_TO]->(s:Series)<-[:BELONGS_TO]-(b:Product)
            MATCH (a)-[:SUITABLE_FOR]->(ag:AgeGroup)<-[:SUITABLE_FOR]-(b)
            WHERE a.sku < b.sku AND abs(a.price - b.price) > 5
            MERGE (a)-[:COMPLEMENTS]->(b)
            MERGE (b)-[:COMPLEMENTS]->(a)
        """)

        print(f"✅ 知识图谱构建完成！")
        print(f"   Product:  {count} 个")
        print(f"   Series:   {len(SERIES_THEME_MAP)} 个")
        print(f"   Theme:    {len(set(t for ts in SERIES_THEME_MAP.values() for t in ts))} 个")
        print(f"   AgeGroup: {len(AGE_GROUPS)} 个")
        print(f"   PriceTier:{len(PRICE_TIERS)} 个")

        # 统计关系
        result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC")
        for record in result:
            print(f"   关系 {record['rel']}: {record['cnt']} 条")


def main():
    uri = settings.neo4j_uri
    user = settings.neo4j_user
    password = settings.neo4j_password
    csv_path = settings.product_csv_path

    print(f"连接 Neo4j: {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        print("✅ Neo4j 连接成功")
    except Exception as e:
        print(f"❌ Neo4j 连接失败: {e}")
        print("请确保 Neo4j 已启动（Neo4j Desktop 或 docker），然后重试。")
        sys.exit(1)

    build(driver, csv_path)
    driver.close()
    print("🎉 全部完成！")


if __name__ == "__main__":
    main()
