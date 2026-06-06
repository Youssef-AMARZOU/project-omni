import json
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.rag.vector_store")

class VectorStore:
    """
    Interface haut-niveau pour Qdrant (base vectorielle).
    Gère la collection OMNI et les opérations d'embedding.
    """

    def __init__(self, url: Optional[str] = None, collection: Optional[str] = None):
        self.url = url or settings.qdrant_url
        self.collection_name = collection or settings.collection_name
        self.client = QdrantClient(url=self.url)
        self._ensure_collection()

    def _ensure_collection(self):
        """Crée la collection si elle n'existe pas."""
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection_name not in names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
            logger.info("collection_created", name=self.collection_name)

    async def upsert(
        self,
        task_id: str,
        embedding: List[float],
        payload: Dict[str, Any],
    ):
        """Stocke un embedding avec son payload."""
        point = PointStruct(
            id=task_id,
            vector=embedding,
            payload=payload,
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        logger.info("vector_upserted", task_id=task_id)

    async def search_similar(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Recherche sémantique par similarité.
        Nécessite un embedding — ici on fait une recherche textuelle
        simplifiée via la recherche par vecteur (assumant l'embedding
        est calculé en amont).
        """
        # Note: Dans un vrai système, on calcule l'embedding du query ici.
        # Pour l'exemple, on retourne les points les plus récents.
        results = self.client.scroll(
            collection_name=self.collection_name,
            limit=top_k,
            with_payload=True,
        )[0]
        return [
            {
                "id": r.id,
                "score": 1.0,  # Simplifié
                "payload": r.payload,
            }
            for r in results
        ]

    async def delete(self, task_id: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[task_id],
        )
        logger.info("vector_deleted", task_id=task_id)
