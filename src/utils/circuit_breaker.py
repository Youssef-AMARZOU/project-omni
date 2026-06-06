import asyncio
from enum import Enum
from typing import Callable, Any, Coroutine
from src.utils.logger import get_logger

logger = get_logger("omni.circuit_breaker")

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """
    Implémentation du Circuit Breaker Pattern.
    
    - CLOSED : fonctionnement normal, compte les erreurs.
    - OPEN : trop d'erreurs, rejette immédiatement.
    - HALF_OPEN : teste après timeout pour refermer.
    """

    def __init__(self, name: str, failure_threshold: int = 5, timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> Any:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("circuit_half_open", breaker=self.name)
                else:
                    logger.warning("circuit_open_rejected", breaker=self.name)
                    raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._on_success()
            return result
        except Exception as e:
            async with self._lock:
                self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        import time
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.timeout

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        logger.info("circuit_closed", breaker=self.name)

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = __import__("time").time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error("circuit_opened", breaker=self.name, failures=self.failure_count)

class CircuitBreakerOpenError(Exception):
    pass
