import json
from typing import Any, Dict, List
import httpx
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.rag.embeddings")

class EmbeddingGenerator:
    """
    Génère des embeddings via OpenAI text-embedding-3-large.
    Fallback sur sentence-transformers si l'API est indisponible.
    """

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.embedding_model
        self._local_model = None

    async def embed(self, text: str) -> List[float]:
        """Retourne un vecteur d'embedding (dimension 3072 pour text-embedding-3-large)."""
        try:
            return await self._openai_embed(text)
        except Exception as e:
            logger.warning("openai_embed_failed", error=str(e))
            return self._local_embed(text)

    async def _openai_embed(self, text: str) -> List[float]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": text,
            "model": self.model,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    def _local_embed(self, text: str) -> List[float]:
        """Fallback local avec sentence-transformers."""
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("local_embedding_model_loaded")
        return self._local_model.encode(text).tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding pour ingestion ETL."""
        results = []
        for t in texts:
            vec = await self.embed(t)
            results.append(vec)
        return results
