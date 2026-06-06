import json
import re
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, ValidationError
from src.utils.logger import get_logger
from src.utils.fallback import LLMClient

logger = get_logger("omni.extractor")

class ExtractedPayload(BaseModel):
    task_id: str
    source: str
    priority: str
    raw_input: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    schema_version: str = "1.0.0"
    pii_masked: bool = True
    confidence: float = 0.95

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in ("critical", "standard", "complex"):
            return "standard"
        return v

class ExtractorAgent:
    PII_PATTERNS = [
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
        (r"(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}", "[PHONE]"),
        (r"\b\d{1,2}\s+\w+\s+\d{4}\b", "[DATE]"),
    ]
    LLM_TIMEOUT = 10.0

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.logger = logger

    async def process(self, raw_payload: Dict[str, Any]) -> ExtractedPayload:
        if not raw_payload or not isinstance(raw_payload, dict):
            raw_payload = {}
        task_id = raw_payload.get("id", "unknown")
        self.logger.info("extractor_start", task_id=task_id)
        cleaned = self._sanitize(raw_payload)
        cleaned = self._mask_pii(cleaned)
        priority = await self._classify_priority(cleaned)
        try:
            payload = ExtractedPayload(
                task_id=cleaned.get("id", "unknown"),
                source=cleaned.get("source", "webhook"),
                priority=priority,
                raw_input=raw_payload if raw_payload else {},
                cleaned_data=cleaned,
            )
        except ValidationError as e:
            self.logger.error("schema_validation_failed", error=str(e))
            raise
        self.logger.info("extractor_complete", task_id=payload.task_id, priority=priority)
        return payload

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for k, v in data.items():
            if v is None or v == "":
                continue
            if isinstance(v, str):
                v = v.strip()
            cleaned[k] = v
        return cleaned

    def _mask_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            text = json.dumps(data, default=str)
            for pattern, replacement in self.PII_PATTERNS:
                text = re.sub(pattern, replacement, text)
            return json.loads(text)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.warning("pii_masking_failed", error=str(e))
            return data

    async def _classify_priority(self, data: Dict[str, Any]) -> str:
        prompt = (
            "Classifie la priorite du ticket suivant en UN seul mot : "
            "critical (urgent, production down), standard (tache reguliere), "
            "ou complex (besoin d'enrichissement ou analyse approfondie).\n\n"
            f"{json.dumps(data, ensure_ascii=False, default=str)[:500]}\n\n"
            "Reponds UNIQUEMENT par le mot : critical, standard, ou complex."
        )
        try:
            response = await asyncio.wait_for(
                self.llm.chat(
                    model="claude-3-5-haiku-20241022",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.0,
                ),
                timeout=self.LLM_TIMEOUT,
            )
            classification = response.strip().lower()
            if classification not in ("critical", "standard", "complex"):
                classification = "standard"
            return classification
        except asyncio.TimeoutError:
            self.logger.warning("classification_timeout")
            return "standard"
        except Exception as e:
            self.logger.warning("classification_failed", error=str(e))
            return "standard"