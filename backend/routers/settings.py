"""
Settings Router
LLM 设置 API 路由 - 使用环境变量作为唯一配置来源
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.settings_service import SettingsService
from utils.llm_client import get_available_models
from config.settings import settings


router = APIRouter(prefix="/api/settings", tags=["Settings"])


class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    status: str
    message: str
    provider: str
    model: str
    response_time: Optional[int] = None


class LLMConfigResponse(BaseModel):
    """LLM 配置响应"""
    provider: str
    model: str
    base_url: Optional[str]
    temperature: float
    max_tokens: int
    streaming: bool


@router.get("", response_model=LLMConfigResponse)
async def get_settings():
    """获取当前 LLM 配置（从环境变量）"""
    return LLMConfigResponse(
        provider=settings.llm_provider,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        streaming=settings.llm_streaming
    )


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection():
    """测试 LLM 连接"""
    service = SettingsService()
    result = await service.test_connection()
    return TestConnectionResponse(**result)


@router.get("/models/{provider}")
async def get_models_by_provider(
    provider: str
):
    """获取指定提供商的可用模型列表"""
    available_models = get_available_models(provider)
    if not available_models:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的提供商 '{provider}'"
        )

    return {
        "provider": provider,
        "models": available_models
    }