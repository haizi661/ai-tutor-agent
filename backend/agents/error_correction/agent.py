"""
错题本智能体工厂
- 内层：create_agent (langchain) + ToolStrategy — 结构化输出题目分割结果
"""

import logging
import threading
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import settings
from core.llm import init_model as _init_model
from .prompts import SPLIT_PROMPT, SPLIT_PROMPT_LITE, CORRECTION_PROMPT
from .schemas import QuestionSplitResult, CorrectionResult

logger = logging.getLogger(__name__)

# Agent 实例缓存（避免每次调用重复初始化模型和编译图）
_agent_cache = {}
_agent_cache_lock = threading.Lock()


def _build_tool_strategy_agent(*, model, system_prompt: str, schema):
    """延迟导入 create_agent，兼容 langgraph 预构建包版本漂移。"""
    from langchain.agents import create_agent
    from langchain.agents.structured_output import ToolStrategy

    return create_agent(
        model=model,
        tools=[],
        system_prompt=system_prompt,
        response_format=ToolStrategy(
            schema=schema,
            handle_errors=True,
        ),
    )


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _should_avoid_tool_strategy(*, provider: str, model_name: str | None, cfg) -> bool:
    """判断当前模型是否应绕过 ToolStrategy / tool_choice。

    DeepSeek 的 OpenAI-compatible 接口在部分模型上不接受 ToolStrategy
    自动生成的 `tool_choice` 参数。这里做显式回退，改走 json_mode。
    """
    provider_key = _normalize_text(provider)
    model_key = _normalize_text(model_name) or _normalize_text(getattr(cfg, "model_name", ""))
    base_url = _normalize_text(getattr(cfg, "base_url", ""))

    if not getattr(cfg, "supports_function_calling", True):
        return True
    if "deepseek" in provider_key:
        return True
    if "deepseek" in model_key:
        return True
    if "deepseek" in base_url:
        return True
    return False


def _is_tool_choice_compat_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "tool_choice" in message and "support" in message


def detect_subject_via_llm(ocr_text_sample: str, db_subjects: list, provider: str = "openai") -> str:
    """通过轻量 LLM 识别试卷科目

    Args:
        ocr_text_sample: 前几页 OCR 文本拼接
        db_subjects: 数据库已有科目列表
        provider: 模型供应商

    Returns:
        识别出的科目名称，失败时返回空字符串
    """
    model = _init_model(temperature=0.0, provider=provider, use_light=True)

    existing = '、'.join(db_subjects) if db_subjects else '无'
    prompt = (
        f'已有科目列表：{existing}\n\n'
        f'以下是一份试卷的 OCR 文字节选：\n{ocr_text_sample[:1500]}\n\n'
        '判断试卷科目，输出格式【学段+科目】。'
        '学段：小学/初中/高中/大学；未标注学段不默认，直接用"未知学段"。'
        '科目可能包含大学课程（如高等数学、线性代数、概率论、大学物理、数据结构等）。'
        '只输出结果，不要引号/解释/换行；无法判断输出"未知"。'
    )

    response = model.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()

    if not result or '未知' in result:
        return ""

    return result


def create_inner_split_agent(provider: str = "openai", model_name: str | None = None):
    """创建内层题目分割智能体

    使用 create_agent + ToolStrategy，保证结构化输出。
    无外部工具，专注于将 OCR 数据分割为 QuestionSplitResult。

    由 split_batch 工具内部调用。

    Args:
        provider: 模型供应商，"openai" 或 "anthropic"
        model_name: 指定模型名称，为 None 时使用 provider 默认模型

    Returns:
        create_agent 返回的 CompiledStateGraph
    """
    model = _init_model(temperature=0.1, provider=provider, model_name=model_name)

    return _build_tool_strategy_agent(
        model=model,
        system_prompt=SPLIT_PROMPT,
        schema=QuestionSplitResult,
    )


def create_correction_agent(provider: str = "openai", model_name: str | None = None):
    """创建内层 OCR 纠错智能体

    使用 create_agent + ToolStrategy，保证结构化输出。
    无外部工具，专注于修复 OCR 错误并输出 CorrectionResult。

    由 correct_batch 工具内部调用。

    Args:
        provider: 模型供应商，"openai" 或 "anthropic"
        model_name: 指定模型名称，为 None 时使用 provider 默认模型

    Returns:
        create_agent 返回的 CompiledStateGraph
    """
    model = _init_model(temperature=0.0, provider=provider, model_name=model_name)

    return _build_tool_strategy_agent(
        model=model,
        system_prompt=CORRECTION_PROMPT,
        schema=CorrectionResult,
    )


def _invoke_structured(
    *,
    prompt: str,
    provider: str,
    model_name: str | None,
    temperature: float,
    schema,
    system_prompt_fallback: str,
    cache_key: str,
    agent_factory,
):
    """通用结构化输出调用，屏蔽 ToolStrategy vs with_structured_output 差异"""
    cfg = settings.get_provider(provider)

    def _invoke_via_structured_output(method: str = "json_schema"):
        model = _init_model(temperature=temperature, provider=provider, model_name=model_name)
        return model.with_structured_output(schema, method=method).invoke([
            SystemMessage(content=system_prompt_fallback),
            HumanMessage(content=prompt),
        ])

    if _should_avoid_tool_strategy(provider=provider, model_name=model_name, cfg=cfg):
        logger.info(
            "模型 %s/%s 检测到 ToolStrategy 兼容性风险，改用 json_mode 结构化输出",
            provider,
            model_name or getattr(cfg, "model_name", ""),
        )
        return _invoke_via_structured_output(method="json_mode")

    full_key = f"{cache_key}_{provider}_{model_name or 'default'}"
    try:
        with _agent_cache_lock:
            if full_key not in _agent_cache:
                logger.info(f"创建 Agent 实例 (key={full_key})")
                _agent_cache[full_key] = agent_factory(provider=provider, model_name=model_name)
            agent = _agent_cache[full_key]
    except ImportError as exc:
        logger.warning(
            "Agent 结构化输出初始化失败，回退到 with_structured_output。"
            " 这通常是 langgraph/langgraph-prebuilt 版本不兼容导致的: %s",
            exc,
        )
        return _invoke_via_structured_output(method="json_schema")

    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 100},
        )
    except Exception as exc:
        if _is_tool_choice_compat_error(exc):
            logger.warning(
                "Agent ToolStrategy 调用遇到 tool_choice 兼容性错误，自动回退到 json_mode: %s",
                exc,
            )
            return _invoke_via_structured_output(method="json_mode")
        raise
    return response.get("structured_response")


def invoke_split(prompt: str, provider: str = "openai", model_name: str | None = None):
    """统一调用分割，屏蔽 ToolStrategy vs with_structured_output 差异"""
    return _invoke_structured(
        prompt=prompt, provider=provider, model_name=model_name,
        temperature=0.1, schema=QuestionSplitResult,
        system_prompt_fallback=SPLIT_PROMPT_LITE,
        cache_key="split", agent_factory=create_inner_split_agent,
    )


def invoke_correction(prompt: str, provider: str = "openai", model_name: str | None = None):
    """统一调用纠错，屏蔽 ToolStrategy vs with_structured_output 差异"""
    return _invoke_structured(
        prompt=prompt, provider=provider, model_name=model_name,
        temperature=0.0, schema=CorrectionResult,
        system_prompt_fallback=CORRECTION_PROMPT,
        cache_key="correction", agent_factory=create_correction_agent,
    )
