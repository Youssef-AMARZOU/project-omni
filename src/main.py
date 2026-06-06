import asyncio
import platform
import signal
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.main")
START_TIME = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OMNI Engine starting...", version="2.0.0")
    try:
        from src.orchestrator.workflow_engine import WorkflowEngine
        app.state.engine = WorkflowEngine()
        await app.state.engine.start()
        logger.info("Workflow engine ready")
    except Exception as e:
        logger.error("engine_start_failed", error=str(e))
        app.state.engine = None
    yield
    logger.info("OMNI Engine shutting down...")
    if hasattr(app.state, "engine") and app.state.engine:
        try:
            await app.state.engine.stop()
        except Exception as e:
            logger.warning("engine_stop_error", error=str(e))
    logger.info("Shutdown complete")


app = FastAPI(
    title="Project OMNI Enterprise",
    description="Multi-Agent ETL Orchestration & Optimization Engine",
    version="2.0.0",
    lifespan=lifespan,
)


# ─── Request / Response Models ─────────────────────────────────────

class ExtractRequest(BaseModel):
    payload: Dict[str, Any]


class ExtractResponse(BaseModel):
    task_id: str
    source: str
    priority: str
    cleaned_data: Dict[str, Any]
    pii_masked: bool
    confidence: float


class PlanRequest(BaseModel):
    extracted_payload: Dict[str, Any]


class PlanResponse(BaseModel):
    task_id: str
    estimated_duration_minutes: int
    assigned_resources: list
    constraints: list
    confidence: float
    rag_context_used: bool


class ValidateRequest(BaseModel):
    plan: Dict[str, Any]
    original_payload: Dict[str, Any]


class ValidateResponse(BaseModel):
    task_id: str
    is_valid: bool
    violations: list
    corrected_plan: Dict[str, Any] | None
    audit_score: float
    confidence: float


class PipelineRequest(BaseModel):
    raw_payload: Dict[str, Any]


class PipelineResponse(BaseModel):
    task_id: str
    status: str
    extracted: Dict[str, Any] | None = None
    plan: Dict[str, Any] | None = None
    validation: Dict[str, Any] | None = None
    error: str | None = None


# ─── Health & Root ─────────────────────────────────────────────────

@app.get("/health")
async def health():
    uptime = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    return {
        "status": "healthy",
        "service": "omni-agents",
        "version": "2.0.0",
        "uptime_seconds": int(uptime),
    }


@app.get("/")
async def root():
    return {
        "project": "OMNI Enterprise",
        "version": "2.0.0",
        "status": "running",
        "agents": ["Extractor", "Planner", "Validator"],
        "endpoints": ["/health", "/", "/extract", "/plan", "/validate", "/pipeline"],
        "docs": "/docs",
    }


# ─── Agent Endpoints ───────────────────────────────────────────────

@app.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest):
    from src.agents.extractor import ExtractorAgent
    agent = ExtractorAgent()
    try:
        result = await agent.process(req.payload)
        return ExtractResponse(
            task_id=result.task_id,
            source=result.source,
            priority=result.priority,
            cleaned_data=result.cleaned_data,
            pii_masked=result.pii_masked,
            confidence=result.confidence,
        )
    except Exception as e:
        logger.error("extract_endpoint_failed", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/plan", response_model=PlanResponse)
async def plan(req: PlanRequest):
    from src.agents.planner import PlannerAgent
    agent = PlannerAgent()
    try:
        result = await agent.plan(req.extracted_payload)
        return PlanResponse(
            task_id=result.task_id,
            estimated_duration_minutes=result.estimated_duration_minutes,
            assigned_resources=result.assigned_resources,
            constraints=result.constraints,
            confidence=result.confidence,
            rag_context_used=result.rag_context_used,
        )
    except Exception as e:
        logger.error("plan_endpoint_failed", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest):
    from src.agents.validator import ValidatorAgent
    agent = ValidatorAgent()
    try:
        result = await agent.validate(req.plan, req.original_payload)
        return ValidateResponse(
            task_id=result.task_id,
            is_valid=result.is_valid,
            violations=result.violations,
            corrected_plan=result.corrected_plan,
            audit_score=result.audit_score,
            confidence=result.confidence,
        )
    except Exception as e:
        logger.error("validate_endpoint_failed", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/pipeline", response_model=PipelineResponse)
async def pipeline(req: PipelineRequest):
    from src.agents.extractor import ExtractorAgent
    from src.agents.planner import PlannerAgent
    from src.agents.validator import ValidatorAgent

    task_id = req.raw_payload.get("id", "unknown")
    extractor = ExtractorAgent()
    planner = PlannerAgent()
    validator = ValidatorAgent()

    try:
        extracted = await extractor.process(req.raw_payload)
        plan = await planner.plan(extracted.model_dump())
        validation = await validator.validate(plan.model_dump(), extracted.model_dump())

        status = "approved" if validation.is_valid else "correction_required"

        return PipelineResponse(
            task_id=task_id,
            status=status,
            extracted=extracted.model_dump(),
            plan=plan.model_dump(),
            validation=validation.model_dump(),
        )
    except Exception as e:
        logger.error("pipeline_endpoint_failed", task_id=task_id, error=str(e))
        return PipelineResponse(task_id=task_id, status="failed", error=str(e))


# ─── Main Entry ────────────────────────────────────────────────────

async def main():
    logger.info("Starting OMNI Agents in standalone mode")
    from src.orchestrator.workflow_engine import WorkflowEngine
    engine = WorkflowEngine()
    await engine.start()

    if platform.system() != "Windows":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(engine.stop()))

    try:
        await engine.run()
    except asyncio.CancelledError:
        logger.info("Main loop cancelled")
    finally:
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())