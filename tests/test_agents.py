import pytest
from unittest.mock import AsyncMock, patch
from src.agents.extractor import ExtractorAgent, ExtractedPayload
from src.agents.planner import PlannerAgent, TaskPlan
from src.agents.validator import ValidatorAgent, ValidationResult

class TestExtractorAgent:
    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        agent = ExtractorAgent()
        raw = {
            "id": "task-001",
            "source": "webhook",
            "priority": "standard",
            "description": "Mise à jour base clients"
        }
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            assert isinstance(result, ExtractedPayload)
            assert result.task_id == "task-001"
            assert result.priority == "standard"

    @pytest.mark.asyncio
    async def test_pii_masking(self):
        agent = ExtractorAgent()
        raw = {
            "id": "task-002",
            "email": "test@example.com",
            "phone": "0601020304",
            "description": "Test"
        }
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="standard"):
            result = await agent.process(raw)
            cleaned = str(result.cleaned_data)
            assert "test@example.com" not in cleaned
            assert "0601020304" not in cleaned

class TestPlannerAgent:
    @pytest.mark.asyncio
    async def test_plan_generation(self):
        agent = PlannerAgent()
        payload = {
            "task_id": "task-003",
            "cleaned_data": {"description": "Extraction SAP", "complexity": "high"}
        }
        with patch.object(agent, "_classify_priority", new_callable=AsyncMock, return_value="complex"):
            with patch.object(agent.vs, "search_similar", new_callable=AsyncMock, return_value=[]):
                with patch.object(agent.llm, "chat", new_callable=AsyncMock, return_value='{"estimated_duration_minutes": 45, "assigned_resources": ["data-team"], "constraints": [], "schedule": [], "dependencies": [], "confidence": 0.9}'):
                    result = await agent.plan(payload)
                    assert isinstance(result, TaskPlan)
                    assert result.task_id == "task-003"
                    assert result.estimated_duration_minutes == 45

class TestValidatorAgent:
    @pytest.mark.asyncio
    async def test_valid_plan(self):
        agent = ValidatorAgent()
        plan = {
            "task_id": "task-004",
            "estimated_duration_minutes": 30,
            "assigned_resources": ["dev"],
            "schedule": [],
        }
        payload = {"task_id": "task-004", "cleaned_data": {}}
        result = await agent.validate(plan, payload)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.violations == []

    @pytest.mark.asyncio
    async def test_invalid_duration(self):
        agent = ValidatorAgent()
        plan = {
            "task_id": "task-005",
            "estimated_duration_minutes": 0,
            "assigned_resources": [],
            "schedule": [],
        }
        payload = {"task_id": "task-005", "cleaned_data": {}}
        result = await agent.validate(plan, payload)
        assert result.is_valid is False
        assert any("Durée estimée invalide" in v for v in result.violations)

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
        payload = {"task_id": "task-006", "cleaned_data": {}}
        result = await agent.validate(plan, payload)
        assert result.is_valid is False
        assert any("Chevauchement" in v for v in result.violations)
