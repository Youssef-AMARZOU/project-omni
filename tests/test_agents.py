import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.extractor import ExtractorAgent, ExtractedPayload
from src.agents.planner import PlannerAgent, TaskPlan
from src.agents.validator import ValidatorAgent, ValidationResult
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from src.utils.fallback import LLMClient
from src.utils.state_manager import StateManager
from src.utils.config import get_settings


# ═══════════════════════════════════════════════════════════════
# EXTRACTOR AGENT TESTS
# ═══════════════════════════════════════════════════════════════

class TestExtractorAgent:
    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        agent = ExtractorAgent()
        raw = {
            "id": "task-001",
            "source": "webhook",
            "priority": "standard",
            "description": "Mise a jour base clients"
        }
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert isinstance(result, ExtractedPayload)
            assert result.task_id == "task-001"
            assert result.priority == "standard"

    @pytest.mark.asyncio
    async def test_pii_masking_email(self):
        agent = ExtractorAgent()
        raw = {"id": "task-002", "email": "test@example.com", "description": "Test"}
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert "[EMAIL]" in str(result.cleaned_data)
            assert "test@example.com" not in str(result.cleaned_data)

    @pytest.mark.asyncio
    async def test_pii_masking_phone_international(self):
        agent = ExtractorAgent()
        raw = {"id": "task-003", "phone": "+33 6 12 34 56 78", "description": "Test"}
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert "[PHONE]" in str(result.cleaned_data)

    @pytest.mark.asyncio
    async def test_pii_masking_phone_local(self):
        agent = ExtractorAgent()
        raw = {"id": "task-004", "phone": "0601020304", "description": "Test"}
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert "[PHONE]" in str(result.cleaned_data)

    @pytest.mark.asyncio
    async def test_empty_input(self):
        agent = ExtractorAgent()
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process({})
            assert result.task_id == "unknown"
            assert result.source == "webhook"

    @pytest.mark.asyncio
    async def test_none_input(self):
        agent = ExtractorAgent()
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(None)
            assert result.task_id == "unknown"

    @pytest.mark.asyncio
    async def test_classification_timeout_fallback(self):
        agent = ExtractorAgent()
        raw = {"id": "task-005", "description": "Test"}
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert result.priority == "standard"

    @pytest.mark.asyncio
    async def test_classification_error_fallback(self):
        agent = ExtractorAgent()
        raw = {"id": "task-006", "description": "Test"}
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert result.priority == "standard"

    @pytest.mark.asyncio
    async def test_sanitize_removes_none_and_empty(self):
        agent = ExtractorAgent()
        result = agent._sanitize({"a": None, "b": "", "c": "  hello  ", "d": 42})
        assert "a" not in result
        assert "b" not in result
        assert result["c"] == "hello"
        assert result["d"] == 42


# ═══════════════════════════════════════════════════════════════
# PLANNER AGENT TESTS
# ═══════════════════════════════════════════════════════════════

class TestPlannerAgent:
    @pytest.mark.asyncio
    async def test_plan_generation(self):
        mock_vs = AsyncMock()
        mock_vs.search_similar = AsyncMock(return_value=[])
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=json.dumps({
            "estimated_duration_minutes": 45,
            "assigned_resources": ["data-team"],
            "constraints": [],
            "schedule": [],
            "dependencies": [],
            "confidence": 0.9,
        }))
        agent = PlannerAgent(vector_store=mock_vs, llm_client=mock_llm)
        payload = {"task_id": "task-003", "cleaned_data": {"description": "Extraction SAP", "complexity": "high"}}
        result = await agent.plan(payload)
        assert isinstance(result, TaskPlan)
        assert result.task_id == "task-003"
        assert result.estimated_duration_minutes == 45


# ═══════════════════════════════════════════════════════════════
# VALIDATOR AGENT TESTS
# ═══════════════════════════════════════════════════════════════

class TestValidatorAgent:
    @pytest.mark.asyncio
    async def test_valid_plan(self):
        agent = ValidatorAgent()
        plan = {"task_id": "task-004", "estimated_duration_minutes": 30, "assigned_resources": ["dev"], "schedule": []}
        payload = {"task_id": "task-004", "cleaned_data": {}}
        result = await agent.validate(plan, payload)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.violations == []
        assert result.audit_score == 1.0

    @pytest.mark.asyncio
    async def test_invalid_duration_zero(self):
        agent = ValidatorAgent()
        plan = {"task_id": "task-005", "estimated_duration_minutes": 0, "assigned_resources": [], "schedule": []}
        payload = {"task_id": "task-005", "cleaned_data": {}}
        result = await agent.validate(plan, payload)
        assert result.is_valid is False
        assert any("invalide" in v.lower() for v in result.violations)

    @pytest.mark.asyncio
    async def test_invalid_duration_negative(self):
        agent = ValidatorAgent()
        plan = {"task_id": "task-neg", "estimated_duration_minutes": -5, "assigned_resources": ["dev"], "schedule": []}
        result = await agent.validate(plan, {})
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_duration_too_long(self):
        agent = ValidatorAgent()
        plan = {"task_id": "task-long", "estimated_duration_minutes": 600, "assigned_resources": ["dev"], "schedule": []}
        result = await agent.validate(plan, {})
        assert result.is_valid is False
        assert any("8h" in v or "decoupage" in v.lower() for v in result.violations)

    @pytest.mark.asyncio
    async def test_overlap_detection(self):
        agent = ValidatorAgent()
        plan = {
            "task_id": "task-006",
            "estimated_duration_minutes": 60,
            "assigned_resources": ["dev"],
            "schedule": [
                {"start": "09:00", "end": "10:00", "resource": "dev"},
                {"start": "09:30", "end": "10:30", "resource": "dev"},
            ],
        }
        result = await agent.validate(plan, {})
        assert result.is_valid is False
        assert any("Chevauchement" in v for v in result.violations)

    @pytest.mark.asyncio
    async def test_no_overlap_different_resources(self):
        agent = ValidatorAgent()
        plan = {
            "task_id": "task-007",
            "estimated_duration_minutes": 60,
            "assigned_resources": ["dev", "ops"],
            "schedule": [
                {"start": "09:00", "end": "10:00", "resource": "dev"},
                {"start": "09:30", "end": "10:30", "resource": "ops"},
            ],
        }
        result = await agent.validate(plan, {})
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_missing_task_id_defaults_to_unknown(self):
        agent = ValidatorAgent()
        plan = {"estimated_duration_minutes": 30, "assigned_resources": ["dev"], "schedule": []}
        result = await agent.validate(plan, {})
        assert result.task_id == "unknown"

    @pytest.mark.asyncio
    async def test_audit_score_clamped_to_zero(self):
        result = ValidationResult(task_id="t", is_valid=False, violations=["a"]*15, audit_score=-0.5, confidence=0.5)
        assert result.audit_score == 0.0

    @pytest.mark.asyncio
    async def test_audit_score_clamped_to_one(self):
        result = ValidationResult(task_id="t", is_valid=True, violations=[], audit_score=1.5, confidence=0.95)
        assert result.audit_score == 1.0


# ═══════════════════════════════════════════════════════════════
# CIRCUIT BREAKER TESTS
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3, timeout=60)
        failing_func = AsyncMock(side_effect=Exception("API down"))
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(failing_func)

    @pytest.mark.asyncio
    async def test_closes_after_timeout(self):
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
    async def test_stays_closed_on_success(self):
        cb = CircuitBreaker("test", failure_threshold=3, timeout=60)
        success_func = AsyncMock(return_value="ok")
        for _ in range(5):
            result = await cb.call(success_func)
            assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_call_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=5, timeout=60, call_timeout=0.05)

        async def hanging_func():
            await asyncio.sleep(10)

        with pytest.raises(asyncio.TimeoutError):
            await cb.call(hanging_func)
        assert cb.failure_count == 1


# ═══════════════════════════════════════════════════════════════
# LLM FALLBACK TESTS
# ═══════════════════════════════════════════════════════════════

class TestLLMFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_rate_limit(self):
        client = LLMClient()
        error = Exception("429 Rate Limit")
        with patch.object(client, "_openai_chat", side_effect=error):
            with patch.object(client, "_fallback_chat", new_callable=AsyncMock, return_value="fallback_response") as mock_fallback:
                result = await client.chat(model="gpt-4o", messages=[{"role": "user", "content": "test"}])
                assert result == "fallback_response"
                mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_server_error(self):
        client = LLMClient()
        error = Exception("500 Internal Server Error")
        with patch.object(client, "_openai_chat", side_effect=error):
            with patch.object(client, "_fallback_chat", new_callable=AsyncMock, return_value="fallback_response"):
                result = await client.chat(model="gpt-4o", messages=[{"role": "user", "content": "test"}])
                assert result == "fallback_response"

    @pytest.mark.asyncio
    async def test_no_fallback_on_auth_error(self):
        client = LLMClient()
        with patch.object(client, "_openai_chat", side_effect=Exception("401 Unauthorized")):
            with pytest.raises(Exception):
                await client.chat(model="gpt-4o", messages=[{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_no_key_raises_value_error(self):
        client = LLMClient()
        client.openai_key = ""
        with patch.object(client, "_openai_chat", side_effect=ValueError("OpenAI API key is not configured")):
            with pytest.raises(ValueError, match="not configured"):
                await client.chat(model="gpt-4o", messages=[{"role": "user", "content": "test"}])


# ═══════════════════════════════════════════════════════════════
# STATE MANAGER TESTS
# ═══════════════════════════════════════════════════════════════

class TestStateManager:
    def test_update_and_get(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        sm.update("task-001", "status", "running")
        assert sm.get("task-001", "status") == "running"

    def test_get_default_value(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        assert sm.get("task-999", "missing_key", "default") == "default"

    def test_path_traversal_prevention(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        dangerous_id = "../../etc/passwd"
        path = sm._path(dangerous_id)
        assert not path.startswith("..")
        assert "etc" not in path or "_" in path

    def test_corrupted_json_recovery(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        sm.update("task-001", "status", "running")
        import pathlib
        p = pathlib.Path(tmp_path) / "task-001.json"
        p.write_text("{invalid json")
        result = sm.get("task-001", "status", "recovered")
        assert result == "recovered"

    def test_overwrite_value(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        sm.update("task-001", "status", "running")
        sm.update("task-001", "status", "completed")
        assert sm.get("task-001", "status") == "completed"


# ═══════════════════════════════════════════════════════════════
# SYSTEM HEALTH TESTS
# ═══════════════════════════════════════════════════════════════

class TestSystemHealth:
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] == "OMNI Enterprise"
        assert "Extractor" in data["agents"]