"""
LLM Settings Service
LLM 全局设置管理服务 - 使用环境变量作为唯一配置来源
"""

import logging
from typing import Dict

from config.settings import settings

logger = logging.getLogger(__name__)


class SettingsService:
    """LLM 设置管理服务"""

    def __init__(self, db=None):
        self.db = db

    async def get_effective_llm_config(self) -> Dict:
        """
        获取有效的 LLM 配置
        使用环境变量作为唯一配置来源
        """
        logger.info(f"[设置服务] 使用环境变量配置")
        logger.info(f"[设置服务] provider: {settings.llm_provider}")
        logger.info(f"[设置服务] model: {settings.llm_model}")
        logger.info(f"[设置服务] base_url: {settings.llm_base_url}")
        
        return {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "api_key": settings.llm_api_key,
            "base_url": settings.llm_base_url,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "streaming": settings.llm_streaming,
        }

    async def test_connection(self) -> Dict:
        """测试 LLM 连接"""
        from utils.llm_client import LLMClient

        config = await self.get_effective_llm_config()
        client = LLMClient(config)

        try:
            # 发送简单测试消息
            response = await client.chat([{"role": "user", "content": "Hello"}])
            return {
                "status": "success",
                "message": "LLM 连接测试成功",
                "provider": config["provider"],
                "model": config["model"],
                "response_time": response.get("response_time", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"LLM 连接测试失败: {str(e)}",
                "provider": config["provider"],
                "model": config["model"],
            }