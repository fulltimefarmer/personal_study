"""
数据库初始化脚本 — 创建商品表和库存表，导入 CSV 数据
默认使用 SQLite；DATABASE_URL 可切换 PostgreSQL。
══════════════════════════════════════════════════════════

用法：
  python scripts/init_db.py                 # 初始化 + 导入数据
  python scripts/init_db.py --reset         # 清空重建
  python scripts/init_db.py --dry-run       # 仅打印将要导入的数据，不实际写入
"""
import argparse
import csv
import random
import sys
from datetime import datetime, timezone

from app.config import settings
from app.data.database import (
    ProductDB,
    Inventory,
    Base,
    get_engine,
    get_session,
    init_db,
)


def load_products_from_csv(csv_path: str) -> list[dict]:
    """从 CSV 文件读取商品数据"""
    products = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f, skipinitialspace=True)
        for row in reader:
            if not row or not row[0].strip():
                continue
            products.append({
                "sku": row[0].strip(),
                "name": row[1].strip(),
                "series": row[2].strip(),
                "age_min": int(row[3].replace("+", "").strip()) if len(row) > 3 else 0,
                "price": float(row[4].strip()) if len(row) > 4 else 0.0,
                # 商品介绍本身可能包含逗号，必须把第 6 列之后的内容重新拼起来
                "description": ",".join(row[5:]).strip() if len(row) > 5 else "",
            })
    return products


def seed_data(csv_path: str, reset: bool = False, dry_run: bool = False):
    """导入商品数据并生成随机库存"""
    init_db()
    engine = get_engine()

    if reset:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print("已清空所有表并重建")

    products = load_products_from_csv(csv_path)
    print(f"从 CSV 读取到 {len(products)} 个商品")

    if dry_run:
        for p in products[:5]:
            print(f"  {p['sku']}: {p['name']} | {p['series']} | ${p['price']:.2f}")
        if len(products) > 5:
            print(f"  ... 共 {len(products)} 条")
        print("(dry-run 模式，未实际写入)")
        return

    session = get_session()
    try:
        inserted = 0
        skipped = 0
        for pdata in products:
            existing = session.get(ProductDB, pdata["sku"])
            if existing:
                skipped += 1
                continue
            session.add(ProductDB(
                sku=pdata["sku"],
                name=pdata["name"],
                series=pdata["series"],
                age_min=pdata["age_min"],
                price=pdata["price"],
                description=pdata["description"],
            ))
            inserted += 1

        session.flush()  # 确保 products 先写入，这样 inventory 的外键才能生效

        inventory_inserted = 0
        inventory_skipped = 0
        for pdata in products:
            # 幂等：重复执行 init_db 时不要重复插入库存主键
            if session.get(Inventory, pdata["sku"]):
                inventory_skipped += 1
                continue
            session.add(Inventory(
                sku=pdata["sku"],
                quantity=random.randint(1, 50) if random.random() < 0.8 else 0,
                last_updated=datetime.now(timezone.utc),
            ))
            inventory_inserted += 1

        session.commit()
        print(
            f"导入完成: {inserted} 个商品已插入, {skipped} 个已存在被跳过, "
            f"{inventory_inserted} 条库存已创建, {inventory_skipped} 条库存已存在"
        )

        # 统计库存情况
        total = session.query(Inventory).count()
        in_stock = session.query(Inventory).filter(Inventory.quantity > 0).count()
        out_of_stock = total - in_stock
        print(f"库存统计: 总计 {total} 个 SKU | 有货 {in_stock} | 缺货 {out_of_stock}")

    except Exception as e:
        session.rollback()
        print(f"导入失败: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="初始化 shopping_bot 数据库")
    parser.add_argument("--reset", action="store_true", help="清空并重建所有表")
    parser.add_argument("--dry-run", action="store_true", help="仅打印操作，不实际写入")
    parser.add_argument("--csv", default=settings.product_csv_path, help=f"CSV 文件路径（默认: {settings.product_csv_path}）")
    args = parser.parse_args()

    print(f"数据库: {settings.database_url}")
    print(f"CSV 文件: {args.csv}")
    seed_data(args.csv, reset=args.reset, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
