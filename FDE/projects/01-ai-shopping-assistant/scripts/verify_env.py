"""跨平台环境自检脚本。

用法：
    uv run python scripts/verify_env.py

检查 Python、uv、Node/npm、Ollama、商品 CSV、关系数据库和向量库。
只做诊断，不修改系统；缺失项会打印对应的安装建议。
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from loguru import logger

from app.config import PROJECT_ROOT, settings
from app.core.logging import setup_logging


def _run(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        return output.splitlines()[0] if output else ""
    except Exception:
        return None


def _check_command(name: str) -> bool:
    path = shutil.which(name)
    if path:
        print(f"  [OK]   {name:10s} {path}")
        return True
    print(f"  [MISS] {name:10s} 未找到")
    return False


def _ollama_models() -> list[str]:
    try:
        with urllib.request.urlopen(
            f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=3
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [item.get("name", "") for item in payload.get("models", [])]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return []


def main() -> int:
    setup_logging(settings.debug)
    print("=" * 62)
    print("  AI Shopping Assistant · 环境自检")
    print("=" * 62)
    print(f"  OS:       {platform.system()} {platform.release()}")
    print(f"  Python:   {sys.version.split()[0]} ({sys.executable})")
    print(f"  Project:  {PROJECT_ROOT}")
    print()

    print("[工具链]")
    _check_command("uv")
    _check_command("node")
    _check_command("npm")
    ollama_ok = _check_command("ollama")
    print()

    print("[运行配置]")
    print(f"  LLM_PROVIDER   = {settings.llm_provider}")
    print(f"  LLM_MODEL      = {settings.llm_model}")
    print(f"  EMBED_PROVIDER = {settings.embed_provider}")
    print(f"  EMBED_MODEL    = {settings.embed_model}")
    print(f"  DATABASE_URL   = {settings.database_url}")
    print(f"  CHROMA_DIR     = {settings.chroma_persist_dir}")
    print()

    print("[Ollama 模型]")
    if ollama_ok:
        models = _ollama_models()
        if models:
            for model in models:
                print(f"  [OK]   {model}")
            needed = ["qwen2.5:3b"]
            if settings.embed_provider == "ollama":
                needed.append(settings.embed_model)
            for model in needed:
                if not any(model.split(":")[0] in item for item in models):
                    print(f"  [MISS] {model}（运行 ollama pull {model}）")
        else:
            print("  [WARN] Ollama 未启动或 API 不可达：ollama serve")
    else:
        print("  [WARN] 未安装 Ollama：聊天功能需要它；检索/健康检查仍可用")
    print()

    print("[数据与向量库]")
    csv_path = Path(settings.product_csv_path)
    print(f"  [{'OK' if csv_path.exists() else 'MISS'}]   CSV: {csv_path}")

    try:
        from app.data.database import ProductDB, get_session, init_db

        init_db()
        with get_session() as session:
            product_count = session.query(ProductDB).count()
        print(f"  [OK]   关系数据库可用，商品 {product_count} 条")
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] 关系数据库不可用：{exc}")
        print("         本地可直接使用 SQLite；或启动 PostgreSQL 并修改 DATABASE_URL")

    try:
        from app.vector_store.chroma_store import ChromaStore

        count = ChromaStore().count()
        print(f"  [{'OK' if count else 'MISS'}]   向量库文档 {count} 条")
        if count == 0:
            print("         运行：uv run python main.py ingest")
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] 向量库检查失败：{exc}")

    print()
    print("提示：完整的 Windows / macOS 安装步骤见 README.md 和 ENVIRONMENT-SETUP.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
