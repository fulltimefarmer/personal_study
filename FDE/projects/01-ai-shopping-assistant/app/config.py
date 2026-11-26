"""
配置管理模块 — 购物助手应用的核心配置中心。

【角色】本模块负责集中管理所有可调参数（模型、向量库、记忆、幻觉防控等），
是整个应用的"控制面板"。所有其他模块都通过 `settings` 单例读取配置，
确保全局一致性和单一真相来源。

【机制】基于 Pydantic Settings，自动从 `.env` 文件和环境变量加载配置值，
实现"代码定义默认值，环境变量覆盖"的 12-Factor App 模式。

【使用】
    from app.config import settings
    print(settings.llm_model)  # → "qwen2.5:3b"（取决于 .env 配置）
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import field_validator
from pydantic_settings import BaseSettings

# 项目根目录（app/config.py -> app -> 项目根）
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """
    应用配置数据类 — 所有可调参数的定义和默认值集中于此。

    【作用】作为应用的"类型化配置表"，提供 IDE 自动补全和运行时类型校验。
    【原理】继承 Pydantic BaseSettings，自动从 `.env` 文件和环境变量读取同名字段。
            字段的 Python 变量名会自动映射为环境变量名（如 `llm_model` ← `LLM_MODEL`）。
            优先级：环境变量 > .env 文件 > 代码默认值。
    【为什么需要】集中管理避免配置散落各处，类型安全防止运行时拼写错误，
                 环境变量机制支持不同部署环境（开发/测试/生产）无缝切换。
    """

    # ═══════════════════════════════════════════════════════════
    # 模型配置 - 指定各环节使用的 Ollama 本地模型
    # ═══════════════════════════════════════════════════════════
    # 主对话模型：回答用户的自然语言问题，统一使用 qwen2.5:3b
    llm_model: str = "qwen2.5:3b"
    # 路由模型：判断用户意图应归属哪个工具/子流程，与主模型共用
    router_model: str = "qwen2.5:3b"
    # 嵌入模型：将文本转为向量用于语义搜索，bge-m3 支持中英文、效果均衡
    embed_model: str = "bge-m3:latest"
    # hash = 本地确定性哈希向量（默认，零依赖）
    # ollama = 使用上面的 bge-m3（质量更好，需要 Ollama）
    embed_provider: str = "hash"
    embed_dimensions: int = 1024
    # 本地视觉模型：用于图片识别，qwen2.5vl 支持多模态
    ollama_vl_model: str = "qwen2.5vl:3b"
    # Ollama 服务地址（默认本地 11434 端口）
    ollama_base_url: str = "http://localhost:11434"
    # 模型在显存中的保活时间（秒），-1 表示常驻内存不卸载
    ollama_keep_alive: int = -1

    # ═══════════════════════════════════════════════════════════
    # 本地优先策略 — 简单问题用本地 Ollama 节省 DeepSeek API 费用
    # ═══════════════════════════════════════════════════════════
    use_local_for_simple: bool = True
    # auto: 有有效 DeepSeek Key 用云端，否则自动回退本地 Ollama
    # ollama: 始终使用本地 Ollama
    # deepseek: 始终使用 DeepSeek（缺少 Key 时启动报错）
    llm_provider: str = "auto"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_vl_model: str = "deepseek-v4-flash"

    # ───────────────────────────────────────────────────────────
    # 数据路径 - 数据文件的位置
    # ───────────────────────────────────────────────────────────
    # 商品信息 CSV 文件路径（相对路径相对于项目根目录）
    product_csv_path: str = str(PROJECT_ROOT / "files" / "products.csv")

    # ═══════════════════════════════════════════════════════════
    # 数据库配置 - 本地默认 SQLite，无需安装 PostgreSQL
    # 需要 PostgreSQL 时改成 postgresql://user:pass@host:5432/db
    # ═══════════════════════════════════════════════════════════
    database_url: str = (
        f"sqlite:///{(PROJECT_ROOT / 'db' / 'shopping_bot.sqlite3').as_posix()}"
    )

    # ═══════════════════════════════════════════════════════════
    # Neo4j 图数据库配置 - 知识图谱
    # ═══════════════════════════════════════════════════════════
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"
    neo4j_database: str = "neo4j"

    # ═══════════════════════════════════════════════════════════
    # 向量库配置 - ChromaDB 持久化相关
    # ═══════════════════════════════════════════════════════════
    # ChromaDB 持久化存储目录（向量索引存在本地磁盘）
    chroma_persist_dir: str = str(PROJECT_ROOT / "db" / "chroma")
    # 向量集合名称（同一应用的不同数据集用不同 collection 隔离）
    chroma_collection: str = "lego_products"

    # ═══════════════════════════════════════════════════════════
    # 记忆配置 - 对话历史管理
    # ═══════════════════════════════════════════════════════════
    # 保留最近 N 轮对话作为上下文窗口
    memory_max_recent: int = 10
    # 总对话历史上限（超出后按策略淘汰旧记录）
    memory_max_total: int = 30

    # ═══════════════════════════════════════════════════════════
    # 幻觉防控配置 - Guardrails 安全防护
    # ═══════════════════════════════════════════════════════════
    # 是否启用幻觉防控机制（拦截模型编造不存在的商品信息）
    guardrails_enabled: bool = True

    # ═══════════════════════════════════════════════════════════
    # 网络搜索配置 - Tavily API
    # ═══════════════════════════════════════════════════════════
    tavily_api_key: str = ""

    # ═══════════════════════════════════════════════════════════
    # 超时配置 - LLM 思考和工具调用的超时限制
    # ═══════════════════════════════════════════════════════════
    # LLM API 请求超时（秒），控制每次 LLM thinking/inference 的最长等待时间
    llm_request_timeout: float = 60.0
    # 单个工具调用超时（秒），防止某个工具执行时间过长阻塞整个 Agent 循环
    tool_call_timeout: float = 30.0

    # ═══════════════════════════════════════════════════════════
    # 运行参数 - 调试与检索
    # ═══════════════════════════════════════════════════════════
    # 调试模式开关（开启后日志更详细、可能输出敏感信息）
    debug: bool = False
    # 向量检索时返回的候选文档数量（top-K 相似度排序后取前 K 个）
    top_k: int = 4

    # Pydantic 模型配置：从项目根目录加载 `.env`，因此无论从哪个目录启动都能读到配置。
    # `.env.local` 覆盖 `.env`，用于本地密钥等敏感配置（不提交到 git）。
    model_config = {
        "env_file": [
            str(PROJECT_ROOT / ".env"),
            str(PROJECT_ROOT / ".env.local"),
        ],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("product_csv_path", "chroma_persist_dir", mode="after")
    @classmethod
    def _resolve_project_path(cls, value: str) -> str:
        """相对路径统一按项目根目录解析，避免依赖启动时的工作目录。"""
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return str(path)


# ─── 缓存工厂函数 ───────────────────────────────────────────
# 使用 lru_cache 装饰器确保 Settings 对象只被创建一次，
# 后续调用直接返回缓存的同一个实例（单例模式）。

@lru_cache()
def get_settings() -> Settings:
    """
    配置工厂函数 — 创建并缓存唯一的 Settings 实例。

    【作用】作为单例工厂，保证整个应用运行期间只有一个 Settings 实例。
    【原理】`@lru_cache()` 装饰器缓存函数返回值，首次调用创建 Settings()，
            此后所有调用直接返回缓存的同一对象，不会重复解析 .env 文件。
    【为什么需要】避免每次 import 都重新创建对象和读取磁盘文件，
                 节省 I/O、保证配置在整个生命周期中一致。
    """
    return Settings()


# ═══════════════════════════════════════════════════════════════
# 入口 — 全局单例
# ═══════════════════════════════════════════════════════════════
# 模块被 import 时立即创建的单例配置对象。
# 所有模块统一通过 `from app.config import settings` 读取配置，
# 无需实例化 Settings 类，保证全局唯一真相来源。
settings = get_settings()


def has_deepseek_key() -> bool:
    """判断是否配置了真实 DeepSeek Key（过滤模板占位符）。"""
    key = (settings.deepseek_api_key or "").strip()
    if not key:
        return False
    lowered = key.lower()
    return not (lowered.startswith("your-") or lowered in {"changeme", "none", "null"})


def create_llm(
    temperature: float = 0.7,
    model: str | None = None,
    timeout: float | None = None,
    **kwargs: Any,
) -> ChatOpenAI | ChatOllama:
    """创建对话模型。

    LLM_PROVIDER 选择策略：
    - auto（默认）：有有效 DeepSeek Key 用云端，否则回退本地 Ollama；
    - ollama：始终本地 Ollama；
    - deepseek：始终云端，缺少 Key 时明确报错。

    这样同一份代码在“有 API Key 的云端环境”和“只有 Ollama 的本地环境”
    都能启动，不会因为缺少 Key 在 import 阶段崩溃。
    """
    provider = (settings.llm_provider or "auto").strip().lower()
    has_key = has_deepseek_key()

    if provider == "ollama" or (provider == "auto" and not has_key):
        return create_ollama_llm(
            temperature=temperature,
            model=model if model and model != settings.deepseek_model else None,
            timeout=timeout,
            **kwargs,
        )

    if not has_key:
        raise RuntimeError(
            "LLM_PROVIDER=deepseek 但 DEEPSEEK_API_KEY 未配置；"
            "请设置 API Key，或将 LLM_PROVIDER 改为 auto/ollama。"
        )

    return ChatOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=model or settings.deepseek_model,
        temperature=temperature,
        request_timeout=timeout if timeout is not None else settings.llm_request_timeout,
        **kwargs,
    )


def create_ollama_llm(temperature: float = 0.7, model: str | None = None, timeout: float | None = None, **kwargs: Any) -> ChatOllama:
    """创建本地 Ollama 模型实例。

    用于文本生成和视觉分析，使用本地运行的 Ollama 模型。

    Args:
        temperature: 生成温度
        model: 模型名（可覆盖默认的 llm_model）
        timeout: 请求超时（秒），默认使用 settings.llm_request_timeout
    """
    _timeout = timeout if timeout is not None else settings.llm_request_timeout
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=model or settings.llm_model,
        temperature=temperature,
        keep_alive=settings.ollama_keep_alive,
        client_kwargs={"timeout": _timeout},
        **kwargs,
    )
