import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from src.utils.state_manager import StateManager


class TestAPIEndpoints:
    """Tests for the REST API endpoints."""

    def test_health_endpoint(self):
        from src.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "uptime_seconds" in data

    def test_root_endpoint(self):
        from src.main import app
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] == "OMNI Enterprise"
        assert "/extract" in data["endpoints"]
        assert "/plan" in data["endpoints"]
        assert "/validate" in data["endpoints"]
        assert "/pipeline" in data["endpoints"]

    def test_extract_endpoint_with_mock(self):
        from src.main import app
        from src.agents.extractor import ExtractedPayload
        client = TestClient(app)
        mock_result = ExtractedPayload(
            task_id="task-api-001",
            source="api",
            priority="standard",
            raw_input={"id": "task-api-001", "description": "Test"},
            cleaned_data={"id": "task-api-001", "description": "Test"},
        )
        with patch("src.agents.extractor.ExtractorAgent") as MockCls:
            MockCls.return_value.process = AsyncMock(return_value=mock_result)
            resp = client.post("/extract", json={"payload": {"id": "task-api-001", "description": "Test"}})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task_id"] == "task-api-001"
            assert data["priority"] == "standard"

    def test_validate_endpoint_with_mock(self):
        from src.main import app
        from src.agents.validator import ValidationResult
        client = TestClient(app)
        mock_result = ValidationResult(
            task_id="task-v-001",
            is_valid=True,
            violations=[],
            audit_score=1.0,
            confidence=0.95,
        )
        with patch("src.agents.validator.ValidatorAgent") as MockCls:
            MockCls.return_value.validate = AsyncMock(return_value=mock_result)
            resp = client.post("/validate", json={
                "plan": {"task_id": "task-v-001", "estimated_duration_minutes": 30, "assigned_resources": ["dev"], "schedule": []},
                "original_payload": {"task_id": "task-v-001"},
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_valid"] is True

    def test_pipeline_endpoint_with_mock(self):
        from src.main import app
        from src.agents.extractor import ExtractedPayload
        from src.agents.planner import TaskPlan
        from src.agents.validator import ValidationResult
        client = TestClient(app)

        ext = ExtractedPayload(task_id="p-001", source="api", priority="standard", raw_input={"id": "p-001"}, cleaned_data={"id": "p-001"})
        plan = TaskPlan(task_id="p-001", estimated_duration_minutes=30, assigned_resources=["dev"], constraints=[], schedule=[], dependencies=[], confidence=0.9)
        val = ValidationResult(task_id="p-001", is_valid=True, violations=[], audit_score=1.0, confidence=0.95)

        with patch("src.agents.extractor.ExtractorAgent") as MockExt, \
             patch("src.agents.planner.PlannerAgent") as MockPlan, \
             patch("src.agents.validator.ValidatorAgent") as MockVal:
            MockExt.return_value.process = AsyncMock(return_value=ext)
            MockPlan.return_value.plan = AsyncMock(return_value=plan)
            MockVal.return_value.validate = AsyncMock(return_value=val)

            resp = client.post("/pipeline", json={"raw_payload": {"id": "p-001", "description": "Test"}})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "approved"

    def test_docs_endpoint(self):
        from src.main import app
        client = TestClient(app)
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_endpoint(self):
        from src.main import app
        client = TestClient(app)
        resp = client.get("/redoc")
        assert resp.status_code == 200


class TestWorkflowEngine:
    """Tests for the WorkflowEngine orchestration."""

    @pytest.mark.asyncio
    async def test_state_manager_lifecycle(self, tmp_path):
        sm = StateManager(data_dir=str(tmp_path))
        sm.update("task-001", "status", "running")
        sm.update("task-001", "progress", "50%")
        assert sm.get("task-001", "status") == "running"
        assert sm.get("task-001", "progress") == "50%"
        assert sm.get("task-001", "nonexistent", "default") == "default"

    @pytest.mark.asyncio
    async def test_circuit_breaker_full_cycle(self):
        cb = CircuitBreaker("test-cycle", failure_threshold=2, timeout=60)
        success = AsyncMock(return_value="ok")
        fail = AsyncMock(side_effect=Exception("fail"))

        result = await cb.call(success)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

        with pytest.raises(Exception):
            await cb.call(fail)
        with pytest.raises(Exception):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(success)

    @pytest.mark.asyncio
    async def test_circuit_breaker_stays_closed_on_success(self):
        cb = CircuitBreaker("test-stay", failure_threshold=3, timeout=60)
        success = AsyncMock(return_value="ok")
        for _ in range(5):
            result = await cb.call(success)
            assert result == "ok"
        assert cb.state == CircuitState.CLOSED