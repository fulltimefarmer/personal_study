"""
Structured Output Enforcement — Pydantic 强制结构化输出
══════════════════════════════════════════════════════════

架构角色：
  LLM 的默认输出是自然语言，格式不可控。在生产环境中，
  常常需要 LLM 返回结构化的 JSON 结果（用于前端直接渲染、
  下游系统消费、API 响应规范化等）。

  本项目当前的 guardrails.py 是"后置检测"（回答已生成后再查错），
  而 Structured Output 是"前置约束"（生成时即强制格式）。

  面试考点：
  这是 LLM 工程化中的核心技能。从 prompt engineering（"请用 JSON 返回"）
  到 function calling（OpenAI 的 JSON mode），再到这里的
  LangChain OutputParser + Pydantic 模式，展示了格式控制的
  演进路径。

三种结构化输出方案对比：
  ┌─────────────────┬──────────────┬──────────────┬─────────────┐
  │ 方案             │ 可靠性       │ LLM 兼容性    │ 复杂度      │
  ├─────────────────┼──────────────┼──────────────┼─────────────┤
  │ 1. Prompt 要求   │ 低（50-70%） │ 所有模型     │ 极简        │
  │    在 prompt 中  │              │              │             │
  │    写"请用JSON"  │              │              │             │
  ├─────────────────┼──────────────┼──────────────┼─────────────┤
  │ 2. OutputParser  │ 中（80-90%） │ 通用（字符串  │ 中          │
  │    正则/JSON     │              │  解析）       │             │
  │    解析 + 重试    │              │              │             │
  ├─────────────────┼──────────────┼──────────────┼─────────────┤
  │ 3. JSON Mode     │ 高（95%+）   │ 需模型支持    │ 低          │
  │    with_structured│             │  OpenAI/Ollama│             │
  │    _output()     │             │  特定模型     │             │
  └─────────────────┴──────────────┴──────────────┴─────────────┘

  本模块实现方案2（通用兼容 + Ollama适配）。

面试中常见追问：
   Q: 为什么不用 with_structured_output()？
   A: with_structured_output() 依赖模型原生 JSON mode 或 tool calling
      schema 约束。当前使用 DeepSeek API（ChatOpenAI 兼容），
      其 JSON mode 支持完善，OutputParser 作为补充保障。

   Q: 输出解析失败怎么办？
  A: 重试机制（最多3次），每次重试时在 prompt 中明确指出
     解析失败的原因，让 LLM 修正格式。3次都失败则降级为
     自然语言输出。

  Q: Structured Output 和 Function Calling 有什么区别？
  A: Function Calling 是 LLM 决定"调用哪个函数 + 传什么参数"，
     输出的是 tool_call 决策而非内容本身。
     Structured Output 是约束"回答内容的格式"，
     输出的是结构化的自然语言内容（如推荐列表）。
     两者可以组合使用（function calling 决定用哪个工具，
     structured output 约束工具返回的内容格式）。
"""
import json
import re
from typing import Generic, Type, TypeVar

from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import BaseModel, Field

from app.config import create_llm

T = TypeVar("T", bound=BaseModel)


class ProductRecommendation(BaseModel):
    name: str = Field(description="商品名称")
    sku: str = Field(description="商品SKU编号")
    reason: str = Field(description="推荐理由")
    price: float = Field(description="价格（美元）")
    series: str = Field(default="", description="所属系列")
    age_min: int = Field(default=0, description="适用最小年龄")


class SearchAnalysis(BaseModel):
    """搜索结果分析 — 结构化理解用户需求与检索结果的关系"""
    query_intent: str = Field(description="用户核心需求概括（一句话）")
    match_quality: str = Field(
        description="匹配质量评估: high/medium/low/none"
    )
    top_candidates: list[ProductRecommendation] = Field(
        default_factory=list, description="Top 3 推荐商品"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="如果匹配不好，给出搜索建议",
    )


class MultiProductComparison(BaseModel):
    """多商品对比分析"""
    products: list[ProductRecommendation] = Field(
        description="参与对比的商品列表"
    )
    comparison_dimensions: dict[str, str] = Field(
        default_factory=dict,
        description="对比维度 (如 价格: A更便宜, 年龄: B更适合幼儿)",
    )
    winner: str = Field(default="", description="最终推荐的商品名称")
    winner_reason: str = Field(default="", description="推荐理由")


class StructuredOutputParser(Generic[T]):
    """
    WHAT: 通用结构化输出解析器 — 将 LLM 文本可靠地转为 Pydantic 模型

    WHY:  LLM 输出的 JSON 可能格式错误（缺括号、多逗号、嵌套引号），
          直接 json.loads() 容易失败。封装重试 + 容错逻辑提升可靠性。

    HOW:  1. 用 PydanticOutputParser 生成格式说明注入 prompt
          2. LLM 生成后尝试多种解析策略（JSON直接解析→清理→正则提取）
          3. 解析失败最多重试3次，每次注入更明确的格式纠错指令
          4. 3次均失败降级为自然语言输出
    """

    def __init__(self, pydantic_model: Type[T], max_retries: int = 3):
        self.model = pydantic_model
        self.max_retries = max_retries
        self._parser = PydanticOutputParser(pydantic_object=pydantic_model)

    def get_format_instructions(self) -> str:
        """生成输出格式说明，注入 prompt"""
        return self._parser.get_format_instructions()

    def parse(self, text: str) -> T | None:
        """
        WHAT: 尝试从 LLM 文本输出中解析出 Pydantic 模型

        WHY:  容错解析 — LLM 输出的 JSON 可能包裹在 markdown 中
              或包含非标准格式，需要多次尝试。
        """
        strategies = [
            self._try_direct_json,
            self._try_clean_json,
            self._try_regex_json,
        ]

        for i, strategy in enumerate(strategies):
            try:
                result = strategy(text)
                if result:
                    return self.model.model_validate(result)
            except Exception:
                continue

        return None

    def invoke_with_retry(
        self,
        llm: ChatOpenAI,
        system_prompt: str,
        user_input: str,
    ) -> T | None:
        """
        WHAT: 带重试的 LLM 调用 + 结构化解析

        WHY:  LLM 首次生成可能格式不正确，通过重试 + 错误反馈
              让 LLM 自我修正格式。

        HOW:  最多 max_retries 次尝试：
              - 每次将上次失败原因告诉 LLM
              - 要求 LLM 严格遵守格式说明
              - 如果仍失败，返回 None 降级处理
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        format_instructions = self.get_format_instructions()
        last_error = ""

        for attempt in range(self.max_retries):
            error_context = ""
            if last_error:
                error_context = (
                    f"\n\n⚠ 上次输出格式错误: {last_error}\n"
                    "请严格按照格式说明输出，不要加任何额外文本。"
                )

            full_prompt = (
                f"{system_prompt}\n\n"
                f"## 输出格式要求（必须严格遵守）\n{format_instructions}"
                f"{error_context}"
            )

            response = llm.invoke([
                SystemMessage(content=full_prompt),
                HumanMessage(content=user_input),
            ])

            content = str(response.content).strip()
            logger.debug(f"[structured] 尝试 {attempt+1}: {content[:200]}...")

            parsed = self.parse(content)
            if parsed is not None:
                logger.info(f"[structured] 解析成功 (第{attempt+1}次)")
                return parsed
            last_error = "JSON 格式不正确，请检查括号匹配和逗号使用。"

        logger.warning("[structured] 已达最大重试次数，解析失败")
        return None

    def _try_direct_json(self, text: str) -> dict | None:
        """策略1：直接解析（先从 markdown 代码块提取）"""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())

    def _try_clean_json(self, text: str) -> dict | None:
        """策略2：从文本中提取 JSON 对象的起止位置"""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        return None

    def _try_regex_json(self, text: str) -> dict | None:
        """策略3：正则从文本中提取嵌套 JSON 对象"""
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
