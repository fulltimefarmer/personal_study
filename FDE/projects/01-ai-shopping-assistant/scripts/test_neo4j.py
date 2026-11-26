"""Neo4j 连接测试脚本"""

import os

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local", override=True)

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


def test_connection():
    print(f"尝试连接 Neo4j: {URI} (用户: {USER})")
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        driver.verify_connectivity()
        print("✅ Neo4j 连接成功！")

        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j!' AS greeting")
            print(f"   测试查询: {result.single()['greeting']}")

            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            record = result.single()
            print(f"   数据库: {record['name']} {record['versions'][0]} ({record['edition']})")

            result = session.run("MATCH (n) RETURN count(n) AS count")
            print(f"   节点数: {result.single()['count']}")

        driver.close()
    except Exception as e:
        print(f"❌ 连接失败: {e}")


if __name__ == "__main__":
    test_connection()
