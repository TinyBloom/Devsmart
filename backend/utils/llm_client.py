"""
LLM Client Adapter
LLM 适配层，支持 OpenAI / Anthropic / Google / Ollama / Kimi / GLM / ByteDance / MiniMax / Qwen / Custom
使用 litellm 实现多提供商统一接口
"""

import time
import logging
from typing import List, Dict, Optional, AsyncGenerator
import litellm
from litellm import acompletion

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端适配器"""

    def __init__(self, config: Dict):
        """
        初始化 LLM 客户端

        Args:
            config: 包含 provider, model, api_key, base_url, temperature, max_tokens, streaming
        """
        self.provider = config.get("provider", "anthropic")
        self.model = config.get("model", "claude-sonnet-4-6")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 8192)
        self.streaming = config.get("streaming", True)

    def _get_model_string(self) -> str:
        """获取 litellm 模型字符串"""
        return f"{self.provider}/{self.model}"

    def _get_llm_params(self) -> Dict:
        """获取 litellm 调用参数"""
        params = {
            "model": self._get_model_string(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key": self.api_key,
        }

        # 添加 base_url 支持（自定义提供商或 Ollama）
        if self.base_url:
            params["api_base"] = self.base_url

        return params

    async def chat(
        self,
        messages: List[Dict],
        stream: Optional[bool] = None
    ) -> Dict:
        """
        发送对话请求

        Args:
            messages: 对话消息列表 [{"role": "user/assistant/system", "content": "..."}]
            stream: 是否流式输出（覆盖默认设置）

        Returns:
            响应结果 {"content": "...", "response_time": ms, "token_count": int}
        """
        if stream is None:
            stream = self.streaming

        start_time = time.time()

        try:
            llm_params = self._get_llm_params()
            llm_params["messages"] = messages
            llm_params["stream"] = stream

            logger.info(f"[LLM 调用] provider={self.provider}, model={self.model}, api_base={self.base_url}")
            logger.info(f"[LLM 参数] temperature={self.temperature}, max_tokens={self.max_tokens}, stream={stream}")
            logger.info(f"[LLM 消息] {len(messages)} 条，首条角色={messages[0]['role']}, 内容长度={len(messages[0]['content'])}")
            logger.info(f"[LLM API Key] {self.api_key[:10]}...{self.api_key[-10:]}")
            logger.info(f"[LLM 完整参数] {dict((k, v[:20] + '...' if isinstance(v, str) and len(v) > 20 else v) for k, v in llm_params.items())}")

            response = await acompletion(**llm_params)

            if stream:
                content_chunks = []
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content_chunks.append(chunk.choices[0].delta.content)
                content = "".join(content_chunks)
            else:
                content = response.choices[0].message.content

            end_time = time.time()
            response_time = int((end_time - start_time) * 1000)

            token_count = self._estimate_tokens(content)

            logger.info(f"[LLM 响应] 成功，耗时={response_time}ms, token_count={token_count}, 内容长度={len(content)}")

            return {
                "content": content,
                "response_time": response_time,
                "token_count": token_count,
            }

        except Exception as e:
            logger.error(f"[LLM 调用失败] provider={self.provider}, model={self.model}, error={type(e).__name__}: {str(e)[:300]}")
            raise RuntimeError(f"LLM 调用失败: {str(e)}")

    async def chat_stream(
        self,
        messages: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """
        流式对话输出

        Args:
            messages: 对话消息列表

        Yields:
            内容片段
        """
        try:
            llm_params = self._get_llm_params()
            llm_params["messages"] = messages
            llm_params["stream"] = True

            response = await acompletion(**llm_params)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"LLM 流式调用失败: {str(e)}")

    async def generate_summary(self, conversations: List[Dict]) -> str:
        """
        生成对话摘要

        Args:
            conversations: 对话历史列表

        Returns:
            摘要内容
        """
        prompt = "请总结以下对话的核心内容，提取关键信息点：\n\n"
        for conv in conversations:
            prompt += f"[{conv['role']}]: {conv['content']}\n\n"

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, stream=False)
        return response["content"]

    def _estimate_tokens(self, text: str) -> int:
        """估算文本 token 数（简化估算）"""
        # 中文约 1.5 字/token，英文约 4 字/token
        # 简化处理：平均 2 字/token
        return len(text) // 2


def get_available_models(provider: str) -> List[str]:
    """获取指定提供商的可用模型列表"""
    models = {
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "anthropic": ["claude-sonnet-4-6", "claude-3-5-sonnet", "claude-3-opus", "claude-3-sonnet"],
        "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
        "ollama": ["llama3", "mistral", "phi3", "qwen"],
        "kimi": ["kimi", "kimi-8k", "kimi-32k", "kimi-128k"],
        "glm": ["glm-4", "glm-4-9b", "glm-3-turbo", "glm-3-9b"],
        "bytedance": ["doubao", "doubao-pro", "doubao-lite"],
        "minimax": ["abab6-chat", "abab5.5-chat", "abab5-chat", "minimax/maxim", "MiniMax-M3", "MiniMax-M2.1", "MiniMax-M2.1-lightning", "MiniMax-M2"],
        "qwen": ["qwen-2", "qwen-2.5", "qwen-plus", "qwen-turbo", "qwen-long"],
        "custom": [],
    }
    return models.get(provider, [])