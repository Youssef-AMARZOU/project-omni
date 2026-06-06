import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from src.utils.fallback import LLMClient
from src.utils.state_manager import StateManager
from src.agents.extractor import ExtractorAgent


class TestResilience:

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3, timeout=60)
        failing_func = AsyncMock(side_effect=Exception("API down"))
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(failing_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=1, timeout=0)
        failing_func = AsyncMock(side_effect=Exception("API down"))
        success_func = AsyncMock(return_value="ok")
        with pytest.raises(Exception):
            await cb.call(failing_func)
        assert cb.state == CircuitState.OPEN
        await asyncio.sleep(0.1)
        assert cb._should_attempt_reset() is True
        result = await cb.call(success_func)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_call_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=5, timeout=60, call_timeout=0.05)

        async def hanging_func():
            await asyncio.sleep(10)

        with pytest.raises(asyncio.TimeoutError):
            await cb.call(hanging_func)
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_llm_fallback_openai_to_anthropic(self):
        client = LLMClient()
        error = Exception("429 Rate Limit")
        with patch.object(client, "_openai_chat", side_effect=error):
            with patch.object(client, "_fallback_chat", new_callable=AsyncMock, return_value="fallback_response") as mock_fallback:
                result = await client.chat(model="gpt-4o", messages=[{"role": "user", "content": "test"}])
                assert result == "fallback_response"
                mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_no_fallback_on_auth_error(self):
        client = LLMClient()
        error = Exception("401 Unauthorized")
        with patch.object(client, "_openai_chat", side_effect=error):
            with pytest.raises(Exception):
                await client.chat(model="gpt-4o", messages=[{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_extractor_pii_masking(self):
        agent = ExtractorAgent()
        raw = {
            "id": "task-001",
            "email": "john.doe@entreprise.com",
            "phone": "+33 6 12 34 56 78",
            "description": "Extraction de donnees SAP"
        }
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert "[EMAIL]" in str(result.cleaned_data)
            assert "[PHONE]" in str(result.cleaned_data)
            assert result.pii_masked is True

    @pytest.mark.asyncio
    async def test_extractor_pii_masking_local_phone(self):
        agent = ExtractorAgent()
        raw = {"id": "task-002", "phone": "0612345678", "description": "Test"}
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert "[PHONE]" in str(result.cleaned_data)

    @pytest.mark.asyncio
    async def test_extractor_empty_input(self):
        agent = ExtractorAgent()
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process({})
            assert result.task_id == "unknown"
            assert result.source == "webhook"

    @pytest.mark.asyncio
    async def test_extractor_none_input(self):
        agent = ExtractorAgent()
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(None)
            assert result.task_id == "unknown"

    @pytest.mark.asyncio
    async def test_system_health_endpoints(self):
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_system_root_endpoint(self):
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] == "OMNI Enterprise"

    @pytest.mark.asyncio
    async def test_state_manager_recovery(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        sm.update("task-001", "status", "running")
        assert sm.get("task-001", "status") == "running"
        sm.update("task-001", "status", "completed")
        assert sm.get("task-001", "status") == "completed"

    @pytest.mark.asyncio
    async def test_graceful_degradation_queue_backup(self):
        from src.utils.message_bus import MessageBus
        bus = MessageBus(redis_url="redis://invalid:9999/0")
        with pytest.raises(Exception):
            await bus.start()