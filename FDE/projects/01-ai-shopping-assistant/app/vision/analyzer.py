"""
图像识别 / 多模态视觉模块 — DeepSeek API + 本地 Ollama 双通道图片分析
══════════════════════════════════════════════════════════════

架构角色：
  在 RAG/Agent 系统中，纯文本有时不够——用户拍摄乐高包装盒、
  散落零件或拼装成品，需要让 Agent "看懂"图片内容。
  本模块是 Agent 的"眼睛"，将图片输入转化为结构化文字描述。

LangChain 多模态核心概念：
  在 LangChain 中，多模态消息通过 HumanMessage 的 content 字段传递。
  content 可以是：
    - 纯字符串 content="hello"                    （纯文本消息）
    - 列表 content=[{"type": "text", ...}, {"type": "image_url", ...}]  （多模态消息）

  当 content 是列表时，LLM 会同时处理文本和图片：
  1. {"type": "text", "text": "描述这张图片"} → 文本指令
  2. {"type": "image_url", "image_url": {"url": "data:image/...;base64,..."}} → 图片数据

  这个 content 列表直接传给 ChatOpenAI.invoke([HumanMessage(content=[...])])，
  LangChain 会自动转换为 OpenAI Vision API 的多模态请求格式。

多模态 LLM 支持情况：
  ┌──────────────────┬──────────────┬─────────────────────────┐
  │ 模型              │ 接入方式     │ 说明                    │
  ├──────────────────┼──────────────┼─────────────────────────┤
  │ DeepSeek V4-Flash │ ChatOpenAI   │ 兼容 OpenAI Vision API  │
  │ qwen2.5vl:3b      │ ChatOllama   │ Ollama 本地多模态推理   │
  └──────────────────┴──────────────┴─────────────────────────┘

双通道设计：
  1. DeepSeek 远程 API (analyze_image_base64) — 云端视觉模型，能力强但收费
  2. 本地 Ollama (analyze_image_ollama)     — 本地推理，免费但能力较弱

  生产策略：默认用 DeepSeek（质量优先），DeepSeek 不可用时
           降级到本地 Ollama（通过 resilience 模块的 fallback 链）。
"""
import base64
import mimetypes
from typing import Optional

from langchain_core.messages import HumanMessage
from loguru import logger

from app.config import create_llm, create_ollama_llm, settings


def encode_image_file(file_path: str) -> str:
    """
    WHAT: 本地图片 → Base64 Data URL 编码

    WHY:  多模态 LLM API 期望通过 data URL 格式接收图片
          （如 data:image/jpeg;base64,/9j/4AAQ...）。
          不能直接传文件路径——API 无法访问本地文件系统。

    HOW:  1. mimetypes 自动检测文件 MIME 类型（jpg/png/gif/webp）
          2. 二进制读取 + base64 编码（转为纯文本 ASCII）
          3. 拼接为标准 data URL 格式: data:{mime};base64,{encoded}

    注意：base64 编码会使图片体积增大约 33%（3字节→4字符），
          大图可能导致 prompt token 大幅增加甚至超限。
    """
    mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{data}"


def encode_image_url(url: str) -> str:
    """
    WHAT: HTTP(S) URL 直接透传 — Web 图片直接使用原始链接

    WHY:  对于已经托管在 HTTP 服务器上的图片，不需要下载再编码。
          直接传 URL 给 LLM API，由 API 端自行下载处理。
          这避免了本地内存中的 base64 膨胀。

    HOW:  简单返回原始 URL 字符串，不做任何转换。
          注意：需要保证 URL 是公网可访问的，内网地址会失败。
    """
    return url


def analyze_image_base64(
    image_data_url: str,
    prompt: str = "请详细描述这张图片中与乐高有关的内容。"
                 "如果是乐高产品包装盒，请识别套装名称、编号、系列、适用年龄、颗粒数。"
                 "如果是乐高成品模型，请识别可能的套装或主题。"
                 "如果是积木零件，请描述颜色、形状和可能的用途。",
    temperature: float = 0.3,
) -> str:
    """
    WHAT: DeepSeek 多模态图片分析 — 远程 API 调用

    WHY:  DeepSeek V4-Flash 兼容 OpenAI Vision API 格式，
          通过 ChatOpenAI（langchain_openai）的 HumanMessage
          多模态 content 列表传递图片和文字指令。

    HOW:  
      1. 创建 ChatOpenAI（api_key=deepseek, base_url=deepseek, model=deepseek-v4-flash）
      2. 构造 HumanMessage(content=[{text}, {image_url}])
         - text 块：分析指令/提示词
         - image_url 块：base64 data URL 或 HTTP URL
      3. llm.invoke([HumanMessage]) 发送请求
      4. 返回 LLM 的图片描述文本

    LangChain 多模态消息格式详解：
      HumanMessage(content=[
          {"type": "text", "text": "请描述这张图片"},           # 文本块
          {"type": "image_url", "image_url": {"url": "data:..."}}  # 图片块
      ])
      → ChatOpenAI 将其转为 OpenAI Vision API 格式：
      {
        "model": "deepseek-v4-flash",
        "messages": [{
          "role": "user",
          "content": [
            {"type": "text", "text": "请描述这张图片"},
            {"type": "image_url", "image_url": {"url": "data:..."}}
          ]
        }]
      }

    Args:
        image_data_url: base64 data URL (data:image/...) 或 HTTP URL
        prompt:        分析提示词，告诉模型要关注什么
        temperature:   生成温度，越低越确定（图片识别建议 ≤0.3）

    Returns:
        str: 图片分析结果（中文文本描述）
    """
    llm = create_llm(
        model=settings.deepseek_vl_model,
        temperature=temperature,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    )

    try:
        response = llm.invoke([message])
        result = str(response.content).strip()
        logger.info(f"[vision] 图片分析完成，结果长度: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"[vision] 图片分析失败: {e}")
        return f"图片分析失败: {e}"


def analyze_image_file(
    file_path: str,
    prompt: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """分析本地图片文件"""
    data_url = encode_image_file(file_path)
    default_prompt = (
        "请详细描述这张图片中与乐高有关的内容。"
        "如果是乐高产品包装盒，请识别套装名称、编号、系列、适用年龄、颗粒数。"
        "如果是乐高成品模型，请识别可能的套装或主题。"
        "如果是积木零件，请描述颜色、形状和可能的用途。"
        "请用中文回答。"
    )
    return analyze_image_base64(
        data_url,
        prompt or default_prompt,
        temperature,
    )


def analyze_image_ollama(
    image_data_url: str,
    prompt: str = "请详细描述这张图片中与乐高有关的内容。"
                 "如果是乐高产品包装盒，请识别套装名称、编号、系列、适用年龄、颗粒数。"
                 "如果是乐高成品模型，请识别可能的套装或主题。"
                 "如果是积木零件，请描述颜色、形状和可能的用途。",
    temperature: float = 0.3,
) -> str:
    """
    WHAT: 本地 Ollama 多模态图片分析 — 使用 qwen2.5vl 模型

    WHY:  DeepSeek API 收费且依赖网络。当网络不可用或需要零成本
          运行时，降级到本地 Ollama 的 qwen2.5vl 多模态模型。

    HOW:  与 analyze_image_base64 完全相同的 LangChain 多模态消息格式，
          只是底层 LLM 从 ChatOpenAI 换成 ChatOllama：
          ChatOllama(base_url="http://localhost:11434", model="qwen2.5vl:3b")
          ChatOllama 同样支持 HumanMessage content 的多模态列表格式，
          LangChain 自动转换为 Ollama API 的 vision 请求。

    Ollama 多模态请求底层格式：
      LangChain ChatOllama 将 HumanMessage(content=[{text}, {image_url}])
      转换为 Ollama API 请求：
      POST /api/chat
      {
        "model": "qwen2.5vl:3b",
        "messages": [{
          "role": "user",
          "content": [
            {"type": "text", "text": "..."},
            {"type": "image_url", "image_url": {"url": "..."}}
          ]
        }]
      }
      Ollama 服务端会自动加载对应的视觉模型处理多模态输入。

    Args:
        image_data_url: base64 data URL 或 HTTP URL
        prompt:        分析提示词
        temperature:   生成温度

    Returns:
        str: 图片分析结果文本
    """
    llm = create_ollama_llm(
        model=settings.ollama_vl_model,
        temperature=temperature,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    )

    try:
        response = llm.invoke([message])
        result = str(response.content).strip()
        logger.info(f"[vision-ollama] 图片分析完成，结果长度: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"[vision-ollama] 图片分析失败: {e}")
        return f"图片分析失败: {e}"


def analyze_image_file_ollama(
    file_path: str,
    prompt: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """使用本地 Ollama 视觉模型分析本地图片文件"""
    data_url = encode_image_file(file_path)
    default_prompt = (
        "请详细描述这张图片中与乐高有关的内容。"
        "如果是乐高产品包装盒，请识别套装名称、编号、系列、适用年龄、颗粒数。"
        "如果是乐高成品模型，请识别可能的套装或主题。"
        "如果是积木零件，请描述颜色、形状和可能的用途。"
        "请用中文回答。"
    )
    return analyze_image_ollama(
        data_url,
        prompt or default_prompt,
        temperature,
    )
