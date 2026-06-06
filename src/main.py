import asyncio
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.agents.extractor import ExtractorAgent
from src.agents.planner import PlannerAgent
from src.agents.validator import ValidatorAgent
from src.orchestrator.workflow_engine import WorkflowEngine
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.main")

# ─── Lifespan ───────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OMNI Engine starting...", version="2.0.0")
    app.state.engine = WorkflowEngine()
    await app.state.engine.start()
    logger.info("Workflow engine ready")
    yield
    logger.info("OMNI Engine shutting down...")
    await app.state.engine.stop()
    logger.info("Shutdown complete")

app = FastAPI(
    title="Project OMNI Enterprise",
    description="Multi-Agent ETL Orchestration & Optimization Engine",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── Health Check ─────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "omni-agents",
        "version": "2.0.0",
        "uptime": "n/a",
    }

# ─── Main Entry ─────────────────────────────────────────────────────────
async def main():
    """CLI entry point for standalone agent execution."""
    logger.info("Starting OMNI Agents in standalone mode")
    engine = WorkflowEngine()
    await engine.start()

    # Register shutdown
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
