import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict
import structlog
from pymongo import MongoClient
from src.utils.config import get_settings

settings = get_settings()

# ─── Shared Processors ──────────────────────────────────────────────────
shared_processors = [
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.add_log_level,
    structlog.processors.CallsiteParameterAdder(
        [structlog.processors.CallsiteParameter.FILENAME,
         structlog.processors.CallsiteParameter.FUNC_NAME,
         structlog.processors.CallsiteParameter.LINENO]
    ),
    structlog.processors.format_exc_info,
]

# ─── JSON Renderer (stdout) ─────────────────────────────────────────────
structlog.configure(
    processors=shared_processors + [structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(structlog, settings.log_level.upper(), 20)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# ─── MongoDB Backend ────────────────────────────────────────────────────
class MongoLogHandler:
    """Handler persistant vers MongoDB pour audit complet."""

    def __init__(self):
        self.client = MongoClient(settings.mongo_url)
        self.db = self.client.get_default_database()
        self.collection = self.db["omni_audit_logs"]

    def write(self, record: Dict[str, Any]):
        record["timestamp"] = datetime.now(timezone.utc)
        self.collection.insert_one(record)

_mongo_handler = MongoLogHandler()

# ─── Logger Factory ─────────────────────────────────────────────────────
def get_logger(name: str) -> structlog.BoundLogger:
    """Retourne un logger structuré avec préfixe OMNI."""
    logger = structlog.get_logger(f"omni.{name}")
    return logger

class AuditLogger:
    """
    Logger d'audit pour les décisions IA.
    Stocke : entrée brute, prompt, sortie, confiance.
    """

    @staticmethod
    def log_agent_decision(
        agent_name: str,
        task_id: str,
        raw_input: Dict[str, Any],
        prompt: str,
        output: Dict[str, Any],
        confidence: float,
    ):
        entry = {
            "agent": agent_name,
            "task_id": task_id,
            "raw_input": raw_input,
            "prompt": prompt,
            "output": output,
            "confidence": confidence,
            "model_used": output.get("model", "unknown"),
        }
        _mongo_handler.write(entry)
        get_logger("audit").info("agent_decision", **entry)
