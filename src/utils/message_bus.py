import asyncio
import json
from typing import Any, Dict, Optional
from redis.asyncio import Redis
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.message_bus")

class MessageBus:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[Redis] = None
        self._pubsub = None
        self._queue = asyncio.Queue()
        self._listen_task: Optional[asyncio.Task] = None

    async def start(self):
        self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe("omni.events")
        self._listen_task = asyncio.create_task(self._listen())
        logger.info("message_bus_connected")

    async def stop(self):
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe("omni.events")
                await self._pubsub.close()
            except Exception as e:
                logger.warning("pubsub_close_error", error=str(e))
        if self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                logger.warning("redis_close_error", error=str(e))
        logger.info("message_bus_disconnected")

    async def publish(self, message: Dict[str, Any]):
        payload = json.dumps(message, default=str)
        if self._redis is None:
            raise RuntimeError("MessageBus not started")
        await self._redis.publish("omni.events", payload)
        logger.debug("message_published", type=message.get("type"))

    async def consume(self) -> Dict[str, Any]:
        return await self._queue.get()

    async def _listen(self):
        try:
            async for msg in self._pubsub.listen():
                if msg.get("type") == "message":
                    try:
                        data = json.loads(msg["data"])
                        await self._queue.put(data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning("message_parse_error", error=str(e))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("message_bus_listen_error", error=str(e))