"""
DevSmart Configuration Settings
根据 DevSmart_PRD_v1.0.md Section 7.1 定义的优先级规则
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    app_name: str = "DevSmart"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "devsmart-secret-key-change-in-production"
    environment: str = "development"
    port: int = 8000

    # 数据库配置
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://devsmart:devsmart@localhost:5432/devsmart"
    )

    # 项目存储路径
    projects_dir: Path = Path(os.getenv("PROJECTS_DIR", "/home/bxf123/workspace/devsmart/projects"))
    
    # 应用基础目录
    base_dir: Path = Path(__file__).resolve().parent.parent

    # LLM 配置（环境变量优先）
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY")
    llm_base_url: Optional[str] = os.getenv("LLM_BASE_URL")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "8192"))
    llm_streaming: bool = os.getenv("LLM_STREAMING", "true").lower() == "true"

    # 对话上下文配置
    conversation_short_term_limit: int = 20  # 短期记忆轮数
    conversation_token_threshold: int = 8000  # 摘要触发阈值
    summary_trigger_interval: int = 20  # 每 N 轮对话触发摘要

    # 需求完整度阈值
    completeness_threshold: float = 80.0

    # 自动修复重试次数
    max_autofix_retries: int = 3

    # API Key 加密密钥
    encryption_key: Optional[str] = os.getenv("ENCRYPTION_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def get_llm_config() -> dict:
    """
    获取 LLM 配置，按照优先级规则：
    1. 环境变量（最高优先级）
    2. 全局 LLM 设置（数据库）
    3. 项目级别设置（project.json）
    4. 默认值（最低优先级）
    """
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "base_url": settings.llm_base_url,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "streaming": settings.llm_streaming,
    }