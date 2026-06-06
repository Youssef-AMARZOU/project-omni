import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError
from src.utils.logger import get_logger
from src.utils.fallback import LLMClient

logger = get_logger("omni.extractor")

class ExtractedPayload(BaseModel):
    """Schéma strict de sortie de l'Agent Extracteur."""
    task_id: str
    source: str
    priority: str  # critical | standard | complex
    raw_input: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    schema_version: str = "1.0.0"
    pii_masked: bool = True
    confidence: float = 0.95

class ExtractorAgent:
    """
    Agent Extracteur — Nettoie la donnée brute, masque les PII,
    valide le schéma et qualifie la priorité via LLM rapide.
    """

    PII_PATTERNS = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
        (r"\b(?:\+33\s?|0)[1-9](?:\s?\d{2}){4}\b", "[PHONE]"),
        (r"\b\d{1,2}\s+\w+\s+\d{4}\b", "[DATE]"),
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.logger = logger

    async def process(self, raw_payload: Dict[str, Any]) -> ExtractedPayload:
        self.logger.info("extractor_start", task_id=raw_payload.get("id", "unknown"))

        # 1. Nettoyage basique
        cleaned = self._sanitize(raw_payload)

        # 2. Masquage PII
        cleaned = self._mask_pii(cleaned)

        # 3. Classification sémantique (LLM rapide)
        priority = await self._classify_priority(cleaned)

        # 4. Validation schéma
        try:
            payload = ExtractedPayload(
                task_id=cleaned.get("id", "unknown"),
                source=cleaned.get("source", "webhook"),
                priority=priority,
                raw_input=raw_payload,
                cleaned_data=cleaned,
            )
        except ValidationError as e:
            self.logger.error("schema_validation_failed", error=str(e))
            raise

        self.logger.info("extractor_complete", task_id=payload.task_id, priority=priority)
        return payload

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime les champs vides et normalise les types."""
        cleaned = {}
        for k, v in data.items():
            if v is None or v == "":
                continue
            if isinstance(v, str):
                v = v.strip()
            cleaned[k] = v
        return cleaned

    def _mask_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Masque les informations personnelles."""
        text = json.dumps(data)
        for pattern, replacement in self.PII_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return json.loads(text)

    async def _classify_priority(self, data: Dict[str, Any]) -> str:
        """
        Classification rapide : critical | standard | complex.
        Utilise un modèle rapide (Claude Haiku / Llama 3) pour le routage.
        """
        prompt = (
            "Classifie la priorité du ticket suivant en UN seul mot : "
            "critical (urgent, production down), standard (tâche régulière), "
            "ou complex (besoin d'enrichissement ou analyse approfondie).\n\n"
            f"{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
            "Réponds UNIQUEMENT par le mot : critical, standard, ou complex."
        )
        try:
            response = await self.llm.chat(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0,
            )
            classification = response.strip().lower()
            if classification not in ("critical", "standard", "complex"):
                classification = "standard"
            return classification
        except Exception as e:
            self.logger.warning("classification_failed", error=str(e))
            return "standard"
