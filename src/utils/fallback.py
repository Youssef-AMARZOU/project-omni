import asyncio
import json
from typing import Any, Dict, List, Optional
import httpx
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.fallback")

class LLMClient:
    """
    Client LLM avec Fallback automatique.
    Ordre : OpenAI GPT-4o → Anthropic Claude → Erreur structurée.
    """

    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.anthropic_key = settings.anthropic_api_key
        self.timeout = httpx.Timeout(30.0, connect=5.0)

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Envoie une requête chat. Bascule sur fallback en cas d'erreur.
        """
        try:
            return await self._openai_chat(model, messages, max_tokens, temperature, response_format)
        except Exception as e:
            logger.warning("openai_failed", error=str(e), model=model)
            if "429" in str(e) or "500" in str(e) or "Timeout" in str(e):
                return await self._fallback_chat(messages, max_tokens, temperature)
            raise

    async def _openai_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _fallback_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """
        Fallback sur Anthropic Claude 3.5 Sonnet.
        """
        logger.info("fallback_to_anthropic", reason="openai_error")
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # Conversion format OpenAI → Anthropic
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m.get("role") == "system":
                system_msg = m.get("content", "")
            else:
                user_msgs.append(m)

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_msg,
            "messages": user_msgs,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
