"""
AI Client - 支持多种AI API的调用
支持 OpenAI / Claude / MiniMax API
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """支持的AI提供商"""
    OPENAI = "openai"
    CLAUDE = "claude"
    MINIMAX = "minimax"
    LOCAL = "local"  # 预留本地模型接口


@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    provider: AIProvider
    model: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict[str, Any]] = None


class AIClient:
    """AI客户端 - 支持多种提供商的API调用"""

    def __init__(
        self,
        provider: Optional[AIProvider] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """
        初始化AI客户端

        Args:
            provider: AI提供商 (默认从环境变量读取)
            api_key: API密钥 (默认从环境变量读取)
            base_url: API基础URL (可选)
            model: 模型名称 (默认根据provider设置)
            max_retries: 最大重试次数
            timeout: 请求超时时间(秒)
        """
        # 从环境变量读取配置
        self.provider = AIProvider(
            provider.value if provider else 
            os.getenv("AI_PROVIDER", "minimax").lower()
        )
        self.api_key = api_key or self._get_api_key()
        self.base_url = base_url or self._get_base_url()
        self.model = model or self._get_default_model()
        self.max_retries = max_retries
        self.timeout = timeout

    def _get_api_key(self) -> str:
        """根据provider获取API密钥"""
        env_keys = {
            AIProvider.OPENAI: "OPENAI_API_KEY",
            AIProvider.CLAUDE: "CLAUDE_API_KEY",
            AIProvider.MINIMAX: "MINIMAX_API_KEY",
            AIProvider.LOCAL: "LOCAL_MODEL_API_KEY",
        }
        key = env_keys.get(self.provider, "OPENAI_API_KEY")
        return os.getenv(key, "")

    def _get_base_url(self) -> str:
        """根据provider获取API基础URL"""
        base_urls = {
            AIProvider.OPENAI: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            AIProvider.CLAUDE: os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com"),
            AIProvider.MINIMAX: os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
            AIProvider.LOCAL: os.getenv("LOCAL_MODEL_URL", "http://localhost:8000/v1"),
        }
        return base_urls.get(self.provider, "")

    def _get_default_model(self) -> str:
        """获取默认模型"""
        models = {
            AIProvider.OPENAI: os.getenv("OPENAI_MODEL", "gpt-4o"),
            AIProvider.CLAUDE: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            AIProvider.MINIMAX: os.getenv("MINIMAX_MODEL", "MiniMax-M2.5"),
            AIProvider.LOCAL: os.getenv("LOCAL_MODEL_NAME", "llama3"),
        }
        return models.get(self.provider, "MiniMax-M2.5")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数 (0-2)
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            AIResponse对象
        """
        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                if self.provider == AIProvider.OPENAI:
                    return self._call_openai(messages, temperature, max_tokens, **kwargs)
                elif self.provider == AIProvider.CLAUDE:
                    return self._call_claude(messages, temperature, max_tokens, **kwargs)
                elif self.provider == AIProvider.MINIMAX:
                    return self._call_minimax(messages, temperature, max_tokens, **kwargs)
                elif self.provider == AIProvider.LOCAL:
                    return self._call_local(messages, temperature, max_tokens, **kwargs)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # 指数退避
                    logger.warning(f"AI API call failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"AI API call failed after {self.max_retries} retries: {e}")

        raise last_error or Exception("Unknown error occurred")

    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AIResponse:
        """调用OpenAI API"""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()

        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            provider=self.provider,
            model=self.model,
            usage=data.get("usage"),
            raw_response=data,
        )

    def _call_claude(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AIResponse:
        """调用Claude API"""
        import requests

        # Claude API需要不同的消息格式
        claude_messages = []
        system_message = ""

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append(msg)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": claude_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        if system_message:
            payload["system"] = system_message
        payload.update(kwargs)

        response = requests.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()

        return AIResponse(
            content=data["content"][0]["text"],
            provider=self.provider,
            model=self.model,
            usage=data.get("usage"),
            raw_response=data,
        )

    def _call_minimax(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AIResponse:
        """调用MiniMax API"""
        import requests

        # MiniMax API格式
        minimax_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # 系统消息转为第一条user消息
                minimax_messages.append({
                    "role": "user",
                    "content": msg["content"]
                })
            else:
                minimax_messages.append(msg)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": minimax_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        payload.update(kwargs)

        response = requests.post(
            f"{self.base_url}/text/chatcompletion_v2",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()

        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            provider=self.provider,
            model=self.model,
            usage=data.get("usage"),
            raw_response=data,
        )

    def _call_local(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AIResponse:
        """调用本地模型API (预留接口)"""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()

        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            provider=self.provider,
            model=self.model,
            usage=data.get("usage"),
            raw_response=data,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        简化接口 - 直接生成文本

        Args:
            prompt: 用户提示
            system_prompt: 系统提示 (可选)
            **kwargs: 其他参数

        Returns:
            生成的文本内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.chat(messages, **kwargs)
        return response.content


# 全局客户端实例
_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """获取全局AI客户端实例"""
    global _client
    if _client is None:
        _client = AIClient()
    return _client


def set_ai_client(client: AIClient) -> None:
    """设置全局AI客户端实例"""
    global _client
    _client = client
