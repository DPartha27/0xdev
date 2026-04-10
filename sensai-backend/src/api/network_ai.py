from typing import List
from pydantic import BaseModel
from api.llm import run_llm_with_openai
from api.prompts import compile_prompt
from api.prompts.network import (
    QUALITY_CHECK_SYSTEM_PROMPT,
    QUALITY_CHECK_USER_PROMPT,
    AUTO_TAG_SYSTEM_PROMPT,
    AUTO_TAG_USER_PROMPT,
    SUMMARIZE_SYSTEM_PROMPT,
    SUMMARIZE_USER_PROMPT,
    ANSWER_SUGGEST_SYSTEM_PROMPT,
    ANSWER_SUGGEST_USER_PROMPT,
    APPLY_SUGGESTIONS_SYSTEM_PROMPT,
    APPLY_SUGGESTIONS_USER_PROMPT,
)
from api.config import openai_plan_to_model_name

MODEL = openai_plan_to_model_name["text-mini"]


# ─── Response Models ───


class QualityCheckResponse(BaseModel):
    quality_tier: str  # high, medium, low, spam
    suggestions: List[str]
    auto_action: str  # publish, needs_improvement, auto_reject
    reason: str


class AutoTagResponse(BaseModel):
    tags: List[str]


class SummarizeResponse(BaseModel):
    summary: str


class ApplySuggestionsResponse(BaseModel):
    title: str
    content: str
    tags: List[str]


class AnswerSuggestResponse(BaseModel):
    answer: str
    code_example: str | None = None
    coding_language: str | None = None


# ─── AI Functions ───


async def ai_quality_check(
    post_type: str,
    title: str,
    content: str | None = None,
    code_content: str | None = None,
    coding_language: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    messages = compile_prompt(
        QUALITY_CHECK_SYSTEM_PROMPT,
        QUALITY_CHECK_USER_PROMPT,
        post_type=post_type,
        title=title,
        content=content or "(no text content)",
        code_content=code_content or "(no code)",
        coding_language=coding_language or "(none)",
        tags=", ".join(tags) if tags else "(no tags selected)",
    )

    result = await run_llm_with_openai(
        model=MODEL,
        messages=messages,
        response_model=QualityCheckResponse,
        max_output_tokens=500,
    )

    return {
        "quality_tier": result.quality_tier,
        "suggestions": result.suggestions,
        "auto_action": result.auto_action,
        "reason": result.reason,
    }


async def ai_auto_tag(
    post_type: str,
    title: str,
    content: str | None = None,
    code_content: str | None = None,
    existing_tags: list[str] | None = None,
) -> dict:
    messages = compile_prompt(
        AUTO_TAG_SYSTEM_PROMPT,
        AUTO_TAG_USER_PROMPT,
        post_type=post_type,
        title=title,
        content=content or "(no text content)",
        code_content=code_content or "(no code)",
        existing_tags=", ".join(existing_tags) if existing_tags else "(none yet)",
    )

    result = await run_llm_with_openai(
        model=MODEL,
        messages=messages,
        response_model=AutoTagResponse,
        max_output_tokens=200,
    )

    return {"tags": result.tags}


async def ai_summarize(
    title: str,
    content: str | None = None,
    code_content: str | None = None,
) -> dict:
    messages = compile_prompt(
        SUMMARIZE_SYSTEM_PROMPT,
        SUMMARIZE_USER_PROMPT,
        title=title,
        content=content or "(no text content)",
        code_content=code_content or "(no code)",
    )

    result = await run_llm_with_openai(
        model=MODEL,
        messages=messages,
        response_model=SummarizeResponse,
        max_output_tokens=200,
    )

    return {"summary": result.summary}


async def ai_suggest_answer(
    title: str,
    content: str | None = None,
    code_content: str | None = None,
) -> dict:
    messages = compile_prompt(
        ANSWER_SUGGEST_SYSTEM_PROMPT,
        ANSWER_SUGGEST_USER_PROMPT,
        title=title,
        content=content or "(no text content)",
        code_content=code_content or "(no code)",
    )

    result = await run_llm_with_openai(
        model=MODEL,
        messages=messages,
        response_model=AnswerSuggestResponse,
        max_output_tokens=1000,
    )

    return {
        "answer": result.answer,
        "code_example": result.code_example,
        "coding_language": result.coding_language,
    }


async def ai_apply_suggestions(
    post_type: str,
    title: str,
    content: str | None = None,
    code_content: str | None = None,
    tags: list[str] | None = None,
    suggestions: list[str] | None = None,
) -> dict:
    suggestions_text = "\n".join(f"- {s}" for s in (suggestions or []))

    messages = compile_prompt(
        APPLY_SUGGESTIONS_SYSTEM_PROMPT,
        APPLY_SUGGESTIONS_USER_PROMPT,
        post_type=post_type,
        title=title,
        content=content or "(no text content)",
        code_content=code_content or "(no code)",
        tags=", ".join(tags) if tags else "(no tags)",
        suggestions=suggestions_text or "(no suggestions)",
    )

    result = await run_llm_with_openai(
        model=MODEL,
        messages=messages,
        response_model=ApplySuggestionsResponse,
        max_output_tokens=1000,
    )

    return {
        "title": result.title,
        "content": result.content,
        "tags": result.tags,
    }
