from typing import Dict, List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger
from tqdm import tqdm

from app.config import settings
from app.data.models import ProductFilter
from app.vector_store.base import VectorStoreBase
from app.vector_store.embeddings import get_embeddings


"""
向量存储模块 — RAG 检索层
═══════════════════════════════════════════════════════

【在整个 RAG 架构中的角色】
    ┌──────────┐    ┌──────────────┐    ┌──────────┐
    │ 用户提问  │ → │  向量存储     │ → │  LLM     │
    │          │    │ (本模块)      │    │ 生成回答  │
    └──────────┘    │              │    └──────────┘
                    │ 1. embedding │
                    │ 2. 向量检索   │
                    │ 3. 业务重排序 │
                    │ 4. 返回 top-k │
                    └──────────────┘

【为什么需要这个模块】
    - 商品数据量大（数千 SKU），不能全部塞进 LLM 上下文
    - 用户用自然语言描述需求（"适合3岁男孩的积木"），
      传统关键词搜索无法理解语义
    - 需要结合业务条件（年龄、价格）做综合排序，
      纯向量相似度不足以满足推荐质量

【核心能力】
    - 语义搜索：把文本转为高维向量，用余弦/L2 距离衡量相似度
    - 混合搜索：语义(55%) + 年龄匹配(20%) + 价格匹配(25%)
    - 元数据过滤：系列、品类、年龄段等精确筛选
    - 持久化：ChromaDB 数据落盘，重启不丢失
"""


# ══════════════════════════════════════════════════════════
# ChromaStore — 向量存储核心
# ══════════════════════════════════════════════════════════
# 【定位】RAG（检索增强生成）架构中的"检索器"角色。
#         负责将用户查询转为向量，在 ChromaDB 中检索最相似
#         的商品文档，并融合业务权重（年龄/价格）做混合排序，
#         最终把 top-k 结果注入 LLM 的上下文窗口。
# 【数据流】用户提问 → embedding → 向量检索 → 业务重排序 → LLM
# 【底层】langchain_chroma 封装 ChromaDB，元数据过滤用
#         Chroma 原生 where 语法。
class ChromaStore(VectorStoreBase):
    """商品向量存储管理器（ChromaDB 实现）

    WHAT:  封装 ChromaDB 的写入/检索/删除/统计操作，
           提供纯语义搜索 + 加权混合搜索两种模式。
    WHY:   商品数据需要高效语义检索（而非关键词匹配），
           同时业务场景要求价格、年龄等条件参与排序，
           不能用纯向量相似度作为最终排序依据。
    HOW:   通过 langchain_chroma 的 API 操作底层集合，
           在 Python 层做分数归一化与加权融合。
    """
    def __init__(self) -> None:
        # 初始化 embedding 模型（如 BGE-M3）
        self.embeddings = get_embeddings()
        # 连接/创建 ChromaDB 集合（持久化到本地磁盘）
        # 集合名带上 embedding provider，避免 hash 与 bge-m3 维度不一致时互相污染。
        self.collection_name = (
            f"{settings.chroma_collection}_{settings.embed_provider}"
        )
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
        # 底层 Chroma 原生 collection 句柄，用于直接操作（批量获取/删除）
        self._collection = self.vector_store._collection

    # ── 写入 ──────────────────────────────────────────────

    # ═══ 入口 ═══ 批量写入商品文档到向量库（分批处理 + 进度条）
    def add_documents(self, docs: List[Dict], batch_size: int = 8) -> int:
        """批量写入商品文档（分批处理 + 进度条）

        WHAT:  将商品文本向量化后分批次存入 ChromaDB。
        WHY:   全量一次性写入在文档数多时可能 OOM（内存溢出），
              分批写入控制每批内存占用，同时用 tqdm 显示进度。
        HOW:   将文档列表按 batch_size 切片，每批独立调用
              vector_store.add_documents()，显示进度条。

        Args:
            docs: [{"id": str, "text": str, "metadata": dict}, ...]
            batch_size: 每批写入的文档数（默认 100）
        """
        n = len(docs)
        logger.info(f"[chroma] 开始批量写入 {n} 条文档 (批大小={batch_size})")

        total_written = 0
        for start in tqdm(range(0, n, batch_size), desc="向量化写入"):
            batch = docs[start:start + batch_size]
            documents = [
                Document(page_content=doc["text"], metadata=doc["metadata"])
                for doc in batch
            ]
            ids = [doc["id"] for doc in batch]
            self.vector_store.add_documents(documents, ids=ids)
            total_written += len(batch)

        logger.success(f"[chroma] 写入完成: {total_written} 条, 集合总数 {self.count()}")
        return self.count()

    def upsert_documents(self, docs: List[Dict]) -> int:
        """增量同步：新增或更新已有文档

        WHAT:  按 ID 覆盖式写入——ID 已存在的更新，不存在的插入。
        WHY:   商品数据会变动（价格调整、描述更新），
               全量重建太慢，需要增量同步能力。
        HOW:   ChromaDB 的 add_documents 以 ID 为键，
               相同 ID 会自动覆盖旧数据（upsert 语义）。"""
        documents = [
            Document(page_content=doc["text"], metadata=doc["metadata"])
            for doc in docs
        ]
        ids = [doc["id"] for doc in docs]
        self.vector_store.add_documents(documents, ids=ids)
        logger.info(f"upsert {len(ids)} 条记录")
        return self.count()

    def delete_by_ids(self, ids: List[str]) -> None:
        """按 SKU 删除商品"""
        if ids:
            self._collection.delete(ids=ids)
            logger.info(f"删除 {len(ids)} 条记录")

    # ── 检索 ──────────────────────────────────────────────

    # ═══ 入口 ═══ 纯语义搜索（按向量相似度排序）
    def search(
        self, query: str, k: int | None = None, product_filter: ProductFilter | None = None
    ) -> List[Dict]:
        """纯语义相似度搜索

        WHAT:  将用户查询转为向量，在 ChromaDB 中做 ANN 近似最近邻检索。
        WHY:   这是最基本的 RAG 检索方式——找到语义上最匹配的商品。
               适合用户意图明确、不需要额外条件干预的场景。
        HOW:   1. embedding 模型将 query 转为向量
               2. ChromaDB 用 HNSW 索引做近似邻近搜索
               3. 返回 L2 距离，经 _normalize_score() 转为 [0,1] 相似度
               4. 可叠加 Chroma 原生 where 过滤（系列/品类/年龄段精确筛选）

        Args:
            query: 用户搜索文本，如 "孩子3岁喜欢恐龙有什么推荐"
            k: 返回结果数量，默认取 settings.top_k
            product_filter: 元数据过滤条件（系列/品类/年龄段/送礼场合等）
        """
        if k is None:
            k = settings.top_k
        chroma_filter = product_filter.to_chroma_filter() if product_filter else None
        results = self.vector_store.similarity_search_with_score(
            query, k=k, filter=chroma_filter
        )
        return [
            {
                "score": self._normalize_score(score),
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc, score in results
        ]

    # ═══ 入口 ═══ 混合搜索（语义 + 业务权重加权排序）
    def search_hybrid(
        self,
        query: str,
        k: int | None = None,
        product_filter: ProductFilter | None = None,
        target_age: int | None = None,
        price_range: Dict[str, float] | None = None,
    ) -> List[Dict]:
        """混合排序：语义相似度 + 业务权重（价格/年龄匹配）

        WHAT:  先语义检索扩大候选集，再用业务条件加权重排。
        WHY:   纯语义搜索不够精确——用户买3岁玩具，语义相近但
               年龄不匹配的商品不应排在前面；用户有预算限制时，
               价格严重超预算的商品也应降权。因此需要多因子加权。
        HOW:   1. 用 2k 做候选池扩大召回（semantic recall）
               2. 对每个候选计算三因子得分：语义 + 年龄 + 价格
               3. 加权公式: 0.55*sem + 0.20*age + 0.25*price
               4. 按最终得分降序排列，截断取 top-k

        Args:
            query:         用户搜索文本
            k:             最终返回数量
            product_filter: 元数据过滤条件
            target_age:    用户孩子的年龄（用于年龄匹配得分）
            price_range:   {"min": float, "max": float} 用户预算范围
        """
        if k is None:
            k = settings.top_k

        candidate_k = k * 2
        chroma_filter = product_filter.to_chroma_filter() if product_filter else None
        results = self.vector_store.similarity_search_with_score(
            query, k=candidate_k, filter=chroma_filter
        )

        if not results:
            return []

        scored = self._apply_business_scores(results, target_age, price_range)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]

    # ═══ 入口 ═══ 按 ID 批量获取商品全文（不经过向量检索）
    def get_by_ids(self, ids: List[str]) -> List[Dict]:
        """按 SKU 批量查询商品详情

        WHAT:  绕过向量检索，直接用主键 ID 查询原始文档。
        WHY:   向量检索返回的是 top-k 候选，有时需要按已知 ID
               精确获取商品完整信息（如搜索结果二次展示详情页）。
        HOW:   直接操作底层 _collection.get(ids=[...])，
               ChromaDB 内部用哈希索引 O(1) 查找。"""
        results = self._collection.get(ids=ids)
        if not results or not results["ids"]:
            return []
        return [
            {
                "id": results["ids"][i],
                "content": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
            }
            for i in range(len(results["ids"]))
        ]

    # ── 统计 ──────────────────────────────────────────────

    def count(self) -> int:
        """返回当前集合中的商品总数"""
        return self._collection.count()

    def list_series(self) -> List[str]:
        """列出所有系列名称（去重排序）

        WHAT:  扫描全量元数据，提取不重复的系列名。
        WHY:   前端筛选器需要系列选项列表供用户选择，
               不能硬编码——商品数据会变化。
        HOW:   调用 _collection.get() 取全部元数据，
               用集合推导去重后排序返回。
               注意：全量扫描在数千量级内可接受，
               更大规模需改为维护独立的系列索引表。"""
        all_data = self._collection.get()
        if not all_data or not all_data["metadatas"]:
            return []
        series_set = {m.get("series", "") for m in all_data["metadatas"] if m.get("series")}
        return sorted(series_set)

    def delete_collection(self) -> None:
        self.vector_store.delete_collection()
        logger.info("已删除向量集合")

    # ── 内部方法 ──────────────────────────────────────────

    @staticmethod
    def _normalize_score(l2_distance: float) -> float:
        r"""L2 距离 → [0, 1] 相似度

        WHAT:  将 ChromaDB 返回的 L2 距离转换为 [0,1] 区间的相似度分数。
               距离越小 → 相似度越高 → 分数接近 1。
               距离越大 → 相似度越低 → 分数接近 0。

        WHY:   1. L2 距离范围是 [0, +∞)，无法直接跟年龄/价格得分做加权。
                  必须统一到 [0,1] 量纲后，才能公平融合。
               2. 用户看到 0.89 的相似度比分比看到 1.23 的 L2 距离更直观。

        HOW:   用单调递减变换:  score = 1 / (1 + dist)
               这个公式的性质：
                 dist=0    → score=1.0   完全相同
                 dist=0.5  → score≈0.667 比较相似
                 dist=1.0  → score=0.5   中等
                 dist=2.0  → score≈0.333 不太相似
                 dist→∞    → score→0     完全不相似
               （这是常见的 L2→Similarity 转换，L2 与余弦距离
                 在归一化向量上等价，ChromaDB 默认用 L2。）

        公式推导：
          L2(x,y) = sqrt( Σ(xᵢ - yᵢ)² ),  范围 [0, +∞)
          sim = 1/(1+L2),  范围 (0, 1]
          • L2=0 时 sim=1      （向量完全重合）
          • L2→∞ 时 sim→0      （向量无限远）
          • 单调递减:  L2 越大 sim 越小
        """
        return 1.0 / (1.0 + l2_distance)

    def _apply_business_scores(
        self,
        results: list,
        target_age: int | None,
        price_range: Dict[str, float] | None,
    ) -> List[Dict]:
        """加权混合评分：语义 + 年龄 + 价格

        WHAT:  对候选集里的每个商品，计算三项得分的加权和作最终排序依据。

        WHY:   单一语义排序不够——用户想买 "3岁孩子的玩具"，
               语义相近但适用年龄写 "8+" 的商品应被降权；
               用户预算 200 元，卖 500 元的商品也应靠后。
               多因子加权能让排序兼顾语义相关性 + 业务适配度。

        HOW:   最终得分 = 0.55×语义 + 0.20×年龄 + 0.25×价格
               ─────────────────────────────────────────────

        【权重设计理由】
          语义 55%: 核心相关性（内容是否匹配用户描述）
          年龄 20%: 安全门槛（年龄不匹配有安全隐患，但非硬过滤）
          价格 25%: 购买决策关键（超预算影响大，但预算内不拉开差距）

        ─────────────────────────────────────────────

        【年龄匹配得分算法】
          age_score = 1 / (1 + |target_age - product_age| × 0.15)

          原理：以用户年龄为锚点，距离越近分数越高。
          衰减系数 0.15 的含义：
            差 0 岁 → 1.00  完全匹配
            差 1 岁 → 0.87  接近
            差 3 岁 → 0.69  一般
            差 7 岁 → 0.49  不推荐
            差 10岁→ 0.40  很差

          如果用户未提供年龄（target_age=None），
          给默认中性分 0.5，不影响排序。

        【价格匹配得分算法】
          情况1: 商品价格在预算内 (min ≤ price ≤ max)  → price_score = 1.0
                 预算内产品不分高低，都给满分。

          情况2: 商品低于预算下限 (price < min)       → 线性衰减
                 price_score = max(0, 1 - (min-price)/min × 0.5)
                 例：预算 [100,300], 商品80元
                      score = 1 - 20/100×0.5 = 0.90  轻微降权（便宜一点无妨）

          情况3: 商品高于预算上限 (price > max)       → 线性衰减
                 price_score = max(0, 1 - (price-max)/price × 0.5)
                 例：预算 [100,300], 商品500元
                      score = 1 - 200/500×0.5 = 0.80  明显降权（超预算较多）

          如果用户未提供预算（price_range=None），
          给默认中性分 0.5，不影响排序。

        Returns:
          带详细分解分的混合排序结果列表:
          [{
            "score":   最终加权分,
            "content": 商品描述文本,
            "metadata": 商品元数据（价格/年龄/系列等）,
            "detail": {
              "semantic": 语义得分,
              "age":      年龄匹配得分,
              "price":    价格匹配得分,
            }
          }, ...]
        """
        # ── 权重配置（和为 1.0）──
        w_sem = 0.55   # 语义相关性权重：核心因子
        w_age = 0.20   # 年龄匹配权重：安全+适龄
        w_price = 0.25 # 价格匹配权重：购买决策

        scored = []
        for doc, l2_distance in results:
            meta = doc.metadata
            # 1️⃣ 语义得分：L2距离 → [0,1] 相似度
            sem_score = self._normalize_score(l2_distance)

            # 2️⃣ 年龄匹配得分：用户年龄越接近商品下限越高
            age_score = 0.5
            if target_age is not None:
                product_age = meta.get("age_min", 0)
                diff = abs(target_age - product_age)
                age_score = 1.0 / (1.0 + diff * 0.15)

            # 3️⃣ 价格匹配得分：商品价格在预算内得满分, 超出按比例衰减
            price_score = 0.5
            product_price = meta.get("price", 0)
            if price_range and product_price > 0:
                min_p = price_range.get("min", 0)
                max_p = price_range.get("max", float("inf"))
                if min_p <= product_price <= max_p:
                    price_score = 1.0  # 预算内：满分
                elif product_price < min_p:
                    # 低于预算：轻微降权（便宜不是大问题）
                    price_score = max(0, 1.0 - (min_p - product_price) / max(min_p, 1) * 0.5)
                else:
                    # 高于预算：明显降权（超预算影响购买决策）
                    price_score = max(0, 1.0 - (product_price - max_p) / max(product_price, 1) * 0.5)

            # 4️⃣ 加权融合
            final_score = w_sem * sem_score + w_age * age_score + w_price * price_score

            scored.append(
                {
                    "score": round(final_score, 4),
                    "content": doc.page_content,
                    "metadata": meta,
                    "detail": {
                        "semantic": round(sem_score, 4),
                        "age": round(age_score, 4),
                        "price": round(price_score, 4),
                    },
                }
            )
        return scored
