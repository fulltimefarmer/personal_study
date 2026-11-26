"""
向量存储抽象接口 — 支持多后端切换（ChromaDB / Milvus Lite / FAISS）

架构角色：数据访问层（Repository 模式），定义向量存储的标准契约。
上游调用方（RAGChain / Agent Tools / CLI）只需依赖此接口，
不感知底层实现，实现真正的存储后端可插拔。

设计原则：
  - 接口分离（ISP）：最小化抽象方法，每个方法有单一职责
  - 依赖倒置（DIP）：高层模块依赖抽象，不依赖具体实现
  - 开闭原则（OCP）：新增存储后端无需修改调用方代码

后端对比：
  ChromaDB    — 开发原型，嵌入式，零配置，适合 <10万文档
  Milvus Lite — 生产环境，支持分布式，亿级文档，需独立服务
  FAISS       — 纯内存，极致速度，适合 <100万文档的离线实验
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from app.data.models import ProductFilter


class VectorStoreBase(ABC):
    """向量存储抽象基类 — 定义所有向量存储后端的标准契约

    WHAT: 所有具体向量存储实现（ChromaDB、Milvus、FAISS等）必须实现的接口。
    WHY:  1. 允许不修改代码切换存储后端（开发/测试/生产环境不同）
          2. 方便集成测试（可以用 FAISS mock 替代 ChromaDB）
          3. 未来技术演进无需大规模重构
    HOW:  使用 Python ABC（抽象基类），@abstractmethod 强制子类实现，
          调用方通过工厂函数 create_vector_store() 获取具体实例。
    """

    @abstractmethod
    def add_documents(self, docs: List[Dict]) -> int:
        """批量写入文档到向量库

        Args:
            docs: [{"id": str, "text": str, "metadata": dict}, ...]

        Returns:
            写入后向量库中的总文档数
        """
        raise NotImplementedError

    @abstractmethod
    def upsert_documents(self, docs: List[Dict]) -> int:
        """增量写入：按 ID 覆盖已存在文档，插入新文档

        Args:
            docs: 同 add_documents

        Returns:
            操作后向量库中的总文档数
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
        k: int | None = None,
        product_filter: ProductFilter | None = None,
    ) -> List[Dict]:
        """纯语义相似度搜索

        Args:
            query: 用户搜索文本
            k: 返回结果数量
            product_filter: 元数据过滤条件

        Returns:
            [{"score": float, "content": str, "metadata": dict}, ...]
        """
        raise NotImplementedError

    @abstractmethod
    def search_hybrid(
        self,
        query: str,
        k: int | None = None,
        product_filter: ProductFilter | None = None,
        target_age: int | None = None,
        price_range: Dict[str, float] | None = None,
    ) -> List[Dict]:
        """混合排序搜索（语义 + 业务权重）

        Args:
            query: 用户搜索文本
            k: 返回结果数量
            product_filter: 元数据过滤条件
            target_age: 用户孩子年龄
            price_range: {"min": float, "max": float}

        Returns:
            按最终得分降序的检索结果列表
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_ids(self, ids: List[str]) -> List[Dict]:
        """按 ID 批量查询文档

        Args:
            ids: 文档 ID 列表

        Returns:
            [{"id": str, "content": str, "metadata": dict}, ...]
        """
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """返回向量库中的文档总数"""
        raise NotImplementedError

    @abstractmethod
    def list_series(self) -> List[str]:
        """列出所有系列名称（去重排序）"""
        raise NotImplementedError

    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """按 ID 批量删除文档"""
        raise NotImplementedError

    @abstractmethod
    def delete_collection(self) -> None:
        """删除整个集合（清空所有数据）"""
        raise NotImplementedError
