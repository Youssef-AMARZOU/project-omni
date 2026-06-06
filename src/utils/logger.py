import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import structlog
from src.utils.config import get_settings

settings = get_settings()

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

structlog.configure(
    processors=shared_processors + [structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(structlog, settings.log_level.upper(), 20)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

_mongo_handler: Optional["MongoLogHandler"] = None

def _get_mongo_handler():
    global _mongo_handler
    if _mongo_handler is None:
        try:
            _mongo_handler = MongoLogHandler()
        except Exception:
            pass
    return _mongo_handler


class MongoLogHandler:
    def __init__(self):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
            self.db = self.client.get_default_database()
            self.collection = self.db["omni_audit_logs"]
        except Exception:
            self.client = None
            self.collection = None

    def write(self, record: Dict[str, Any]):
        if self.collection is None:
            return
        try:
            record_copy = dict(record)
            record_copy["timestamp"] = datetime.now(timezone.utc).isoformat()
            self.collection.insert_one(record_copy)
        except Exception:
            pass


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(f"omni.{name}")


class AuditLogger:
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
            "model_used": output.get("model", "unknown") if isinstance(output, dict) else "unknown",
        }
        handler = _get_mongo_handler()
        if handler:
            try:
                handler.write(entry)
            except Exception:
                pass
        get_logger("audit").info("agent_decision", **entry)