import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.fallback")

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

class LLMClient:
    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.anthropic_key = settings.anthropic_api_key
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.anthropic_url = "https://api.anthropic.com/v1/messages"

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        try:
            return await self._openai_chat(model, messages, max_tokens, temperature, response_format)
        except Exception as e:
            error_str = str(e)
            status_code = self._extract_status_code(e)
            logger.warning("openai_failed", error=error_str, model=model)
            is_retryable = status_code in RETRYABLE_STATUS_CODES
            is_timeout = "Timeout" in error_str or "timeout" in error_str.lower() or isinstance(e, (asyncio.TimeoutError, httpx.TimeoutException))
            if is_retryable or is_timeout:
                return await self._fallback_chat(messages, max_tokens, temperature)
            raise

    def _extract_status_code(self, exc: Exception) -> Optional[int]:
        if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
            return exc.response.status_code
        import re
        match = re.search(r'\b(429|500|502|503|504)\b', str(exc))
        if match:
            return int(match.group(1))
        return None

    async def _openai_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        if not self.openai_key:
            raise ValueError("OpenAI API key is not configured")
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.openai_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError(f"OpenAI returned no choices: {data}")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError(f"OpenAI returned empty content: {data}")
            return content

    async def _fallback_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        if not self.anthropic_key:
            raise ValueError("Anthropic API key is not configured for fallback")
        logger.info("fallback_to_anthropic", reason="openai_error")
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        system_msg = ""
        user_msgs = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_msg = content
            elif role == "assistant":
                user_msgs.append({"role": "assistant", "content": content})
            else:
                user_msgs.append({"role": "user", "content": content})

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_msg,
            "messages": user_msgs,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.anthropic_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content_blocks = data.get("content", [])
            if not content_blocks:
                raise ValueError(f"Anthropic returned no content: {data}")
            return content_blocks[0].get("text", "")