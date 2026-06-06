import asyncio
import json
from typing import Any, Dict, List
from src.agents.extractor import ExtractorAgent
from src.agents.planner import PlannerAgent
from src.agents.validator import ValidatorAgent
from src.utils.message_bus import MessageBus
from src.utils.state_manager import StateManager
from src.utils.logger import get_logger, AuditLogger
from src.utils.circuit_breaker import CircuitBreaker

logger = get_logger("omni.orchestrator")

class WorkflowEngine:
    """
    Orchestrateur central — Event-driven coordination.
    Implémente un bus de messages asynchrone et une machine à états.
    """

    def __init__(self):
        self.bus = MessageBus()
        self.state = StateManager()
        self.extractor = ExtractorAgent()
        self.planner = PlannerAgent()
        self.validator = ValidatorAgent()
        self.circuit = CircuitBreaker("llm_pipeline", failure_threshold=5, timeout=60)
        self._running = False
        self._tasks = []

    async def start(self):
        """Démarre le bus et les workers."""
        await self.bus.start()
        self._running = True
        logger.info("orchestrator_started")

    async def stop(self):
        """Arrêt gracieux."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        await self.bus.stop()
        logger.info("orchestrator_stopped")

    async def run(self):
        """Boucle principale d'écoute d'événements."""
        while self._running:
            try:
                event = await self.bus.consume()
                await self._process_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("event_processing_error", error=str(e))

    async def submit(self, raw_payload: Dict[str, Any]):
        """Soumet une tâche brute au pipeline."""
        await self.bus.publish({"type": "task_submitted", "payload": raw_payload})

    async def _process_event(self, event: Dict[str, Any]):
        event_type = event.get("type")
        if event_type == "task_submitted":
            await self._run_pipeline(event["payload"])
        elif event_type == "plan_correction_required":
            await self._run_correction(event["payload"])
        else:
            logger.warning("unknown_event", event_type=event_type)

    async def _run_pipeline(self, raw_payload: Dict[str, Any]):
        task_id = raw_payload.get("id", "unknown")
        logger.info("pipeline_start", task_id=task_id)

        try:
            # Étape 1 — Extraction (avec Circuit Breaker)
            extracted = await self.circuit.call(self.extractor.process, raw_payload)
            self.state.update(task_id, "extracted", extracted.model_dump())

            # Étape 2 — Planification (avec RAG)
            plan = await self.circuit.call(self.planner.plan, extracted.model_dump())
            self.state.update(task_id, "planned", plan.model_dump())

            # Étape 3 — Validation
            validation = await self.circuit.call(
                self.validator.validate,
                plan.model_dump(),
                extracted.model_dump(),
            )
            self.state.update(task_id, "validated", validation.model_dump())

            if validation.is_valid:
                self.state.update(task_id, "status", "approved")
                await self.bus.publish({
                    "type": "task_approved",
                    "task_id": task_id,
                    "plan": plan.model_dump(),
                })
                logger.info("pipeline_approved", task_id=task_id)
            else:
                self.state.update(task_id, "status", "correction_required")
                await self.bus.publish({
                    "type": "plan_correction_required",
                    "task_id": task_id,
                    "violations": validation.violations,
                    "corrected_plan": validation.corrected_plan,
                })
                logger.info("pipeline_correction_required", task_id=task_id, violations=validation.violations)

            # Audit
            AuditLogger.log_agent_decision(
                agent_name="orchestrator",
                task_id=task_id,
                raw_input=raw_payload,
                prompt="pipeline_execution",
                output={"status": self.state.get(task_id, "status")},
                confidence=0.95,
            )

        except Exception as e:
            logger.error("pipeline_failed", task_id=task_id, error=str(e))
            self.state.update(task_id, "status", "failed")
            await self.bus.publish({
                "type": "task_failed",
                "task_id": task_id,
                "error": str(e),
            })

    async def _run_correction(self, event: Dict[str, Any]):
        """Relance la planification avec le plan corrigé."""
        task_id = event["task_id"]
        corrected_plan = event.get("corrected_plan")
        logger.info("correction_applied", task_id=task_id)
        self.state.update(task_id, "planned", corrected_plan)
        self.state.update(task_id, "status", "approved")
        await self.bus.publish({
            "type": "task_approved",
            "task_id": task_id,
            "plan": corrected_plan,
        })
