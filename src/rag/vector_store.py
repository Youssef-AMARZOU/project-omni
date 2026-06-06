import json
from typing import Any, Dict, List, Optional
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.rag.vector_store")

class VectorStore:
    """
    High-level Qdrant interface for vector storage and semantic search.
    Gracefully degrades when Qdrant is unavailable.
    """

    COLLECTION_DIMENSION = 3072

    def __init__(self, url: Optional[str] = None, collection: Optional[str] = None):
        self.url = url or settings.qdrant_url
        self.collection_name = collection or settings.collection_name
        self.client = None
        self._connect()

    def _connect(self):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            self.client = QdrantClient(url=self.url)
            self._ensure_collection(Distance, VectorParams)
        except Exception as e:
            logger.warning("qdrant_unavailable", error=str(e))
            self.client = None

    def _ensure_collection(self, Distance, VectorParams):
        if self.client is None:
            return
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
            if self.collection_name not in names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.COLLECTION_DIMENSION, distance=Distance.COSINE),
                )
                logger.info("collection_created", name=self.collection_name)
        except Exception as e:
            logger.warning("collection_ensure_failed", error=str(e))

    async def upsert(self, task_id: str, embedding: List[float], payload: Dict[str, Any]):
        if self.client is None:
            logger.warning("qdrant_unavailable_skip_upsert", task_id=task_id)
            return
        try:
            from qdrant_client.models import PointStruct
            point = PointStruct(id=task_id, vector=embedding, payload=payload)
            self.client.upsert(collection_name=self.collection_name, points=[point])
            logger.info("vector_upserted", task_id=task_id)
        except Exception as e:
            logger.error("vector_upsert_failed", task_id=task_id, error=str(e))

    async def search_similar(self, query: str, top_k: int = 3, query_vector: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        Semantic similarity search.
        If query_vector is provided, performs proper vector search.
        Otherwise, falls back to scrolling recent entries.
        """
        if self.client is None:
            logger.warning("qdrant_unavailable_skip_search")
            return []

        try:
            if query_vector is not None:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True,
                )
                return [
                    {"id": str(r.id), "score": float(r.score), "payload": r.payload}
                    for r in results
                ]
            else:
                results = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=top_k,
                    with_payload=True,
                )[0]
                return [
                    {"id": str(r.id), "score": 1.0, "payload": r.payload}
                    for r in results
                ]
        except Exception as e:
            logger.warning("vector_search_failed", error=str(e))
            return []

    async def delete(self, task_id: str):
        if self.client is None:
            return
        try:
            from qdrant_client.models import PointIdsList
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=[task_id]),
            )
            logger.info("vector_deleted", task_id=task_id)
        except Exception as e:
            logger.warning("vector_delete_failed", task_id=task_id, error=str(e))