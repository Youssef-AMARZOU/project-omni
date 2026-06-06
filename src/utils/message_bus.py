import asyncio
import json
from typing import Any, Dict
from redis.asyncio import Redis
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.message_bus")

class MessageBus:
    """
    Bus de messages asynchrone basé sur Redis Pub/Sub.
    Découple les agents de l'orchestrateur.
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._redis: Redis = None
        self._pubsub = None
        self._queue = asyncio.Queue()

    async def start(self):
        self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe("omni.events")
        asyncio.create_task(self._listen())
        logger.info("message_bus_connected")

    async def stop(self):
        if self._pubsub:
            await self._pubsub.unsubscribe("omni.events")
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("message_bus_disconnected")

    async def publish(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        await self._redis.publish("omni.events", payload)
        logger.debug("message_published", type=message.get("type"))

    async def consume(self) -> Dict[str, Any]:
        return await self._queue.get()

    async def _listen(self):
        async for msg in self._pubsub.listen():
            if msg["type"] == "message":
                data = json.loads(msg["data"])
                await self._queue.put(data)
