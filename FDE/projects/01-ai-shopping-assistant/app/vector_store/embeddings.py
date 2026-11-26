"""
嵌入模型封装模块 — 为向量检索提供统一的 embedding 生成接口。

默认使用本地 Hash Embedding（零依赖、离线可运行），
配置 `EMBED_PROVIDER=ollama` 后切换为 bge-m3 等 Ollama 嵌入模型。

【为什么默认 Hash】
  - Windows/macOS 新机器上不需要先下载 1GB+ 模型即可跑通检索；
  - CI、单元测试和 Demo 环境不需要启动 Ollama；
  - 需要更高质量时，只需改一个环境变量并重建向量库。

【切换方式】
  EMBED_PROVIDER=ollama
  EMBED_MODEL=bge-m3:latest
  然后执行 `python main.py ingest` 重建向量库。
"""

import hashlib
import math
import re

import httpx
from langchain_core.embeddings import Embeddings

from app.config import settings

_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokens(text: str) -> list[str]:
    """轻量分词：英文/数字词 + 中文单字与 bigram。"""
    lowered = text.casefold()
    tokens: list[str] = []

    for match in _WORD_RE.finditer(lowered):
        word = match.group()
        if len(word) >= 2:
            tokens.append(word)

    for sequence in _CJK_RE.findall(lowered):
        if len(sequence) == 1:
            tokens.append(sequence)
            continue
        tokens.extend(sequence)
        tokens.extend(sequence[i : i + 2] for i in range(len(sequence) - 1))

    if not tokens:
        tokens = [lowered or "empty"]
    return tokens


class HashEmbeddings(Embeddings):
    """确定性哈希向量：不联网、不下载模型，适合本地开发与测试。

    原理：把 token 哈希到固定维度，带符号累加并做 L2 归一化。
    相同/相近词汇会落在相同维度上，因此能提供可用的词法级语义相似度。
    它不是 bge-m3 的替代品，但足以让检索、引用、评估链路完整跑通。
    """

    def __init__(self, dimensions: int = 1024) -> None:
        if dimensions < 16:
            raise ValueError("embed_dimensions 不能小于 16")
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimensions
            sign = 1.0 if (value >> 63) & 1 else -1.0
            # 长词/短语权重略高，降低单字噪音
            vector[index] += sign * (1.0 + math.log1p(len(token)))

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class OllamaNativeEmbeddings(Embeddings):
    """直接调用 Ollama 原生 `/api/embed`。

    为什么不直接用 `langchain_ollama.OllamaEmbeddings`：
    该版本走 OpenAI 兼容的 `/v1/embeddings`，在 Ollama 0.40 + bge-m3
    组合下会触发 runner 400 / 连接重置；原生 `/api/embed` 稳定可用。
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        batch_size: int = 8,
        timeout: float = 120.0,
        # 部分 AMD ROCm + bge-m3 组合在 GPU 上会因特定 token 序列崩溃，
        # 嵌入默认走 CPU 最稳；聊天模型仍然使用 GPU。
        num_gpu: int = 0,
        num_ctx: int = 8192,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = batch_size
        self.timeout = timeout
        self.options = {"num_gpu": num_gpu, "num_ctx": num_ctx}

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": texts,
                    "options": self.options,
                },
            )
            response.raise_for_status()
            payload = response.json()
        embeddings = payload.get("embeddings")
        if not embeddings or len(embeddings) != len(texts):
            raise RuntimeError(f"Ollama embedding 返回异常: {payload}")
        return embeddings

    def _embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            try:
                results.extend(self._embed_batch(batch))
            except Exception:
                # 某些模型/长文本对批量输入敏感，逐条降级保证可用
                for text in batch:
                    results.extend(self._embed_batch([text]))
        return results

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


def get_embeddings() -> Embeddings:
    """按配置返回 embedding 实现。"""
    provider = (settings.embed_provider or "hash").strip().lower()

    if provider == "hash":
        return HashEmbeddings(settings.embed_dimensions)

    if provider == "ollama":
        return OllamaNativeEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.embed_model,
        )

    raise ValueError(
        f"未知的 EMBED_PROVIDER={settings.embed_provider!r}，可选值：hash / ollama"
    )
